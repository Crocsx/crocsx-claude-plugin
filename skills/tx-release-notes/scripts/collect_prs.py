#!/usr/bin/env python3
"""Collect every pull request merged in a commit range, with the facts a release note
needs: title, body, labels, JIRA keys, which components it touched, and its images.

  collect_prs.py --repo telexistence-inc/tx-retail \
      --range FE=A..C --range BE=B..C \
      --component FE=frontend/ --component BE=backend/ --out prs.json --download imgs/

Each component has its own range, because FE and BE are deployed separately. A PR is
kept for a component only when it touches that component's paths and merged inside
that component's range. A one-component project passes a bare `--range A..B`.

PR numbers come from the first-parent log (`(#123)` squash subjects, `Merge pull request
#123` merges); a commit with neither is looked up through the GitHub commit -> PR API,
and kept as a bare commit if no PR exists. Images come from the PR body and comments.
With --download, each image is saved as <dir>/pr<N>-<k>.<ext> so it can be looked at
before it is chosen. Bare attachment links without image markup are usually videos and
are listed under `videos`, not downloaded.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request

ASSET = r"https://github\.com/(?:user-attachments/assets|[\w.-]+/[\w.-]+/assets/\d+)/[0-9a-f-]{36}"
IMG_TAG = re.compile(r"<img[^>]*?src=[\"']([^\"']+)[\"'][^>]*>", re.I)
IMG_MD = re.compile(r"!\[[^\]]*\]\((\S+?)(?:\s+\"[^\"]*\")?\)")
BARE_ASSET = re.compile(ASSET)
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
JIRA = re.compile(r"\b([A-Z][A-Z0-9]{1,9}-\d{1,6})\b")
PR_IN_SUBJECT = re.compile(r"\(#(\d+)\)\s*$|^Merge pull request #(\d+)")
NOT_JIRA = {"UTF-8", "SHA-256", "ISO-8601", "X-API", "HTTP-2"}


def run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else None


def gh_json(path, accept=None):
    cmd = ["gh", "api", path]
    if accept:
        cmd += ["-H", f"Accept: {accept}"]
    out = run(cmd)
    return json.loads(out) if out else None


def images_in(markdown):
    """Image URLs in markdown/HTML, in order, and bare asset links (likely videos)."""
    imgs = []
    for m in sorted([*IMG_TAG.finditer(markdown), *IMG_MD.finditer(markdown)], key=lambda m: m.start()):
        if m.group(1) not in imgs:
            imgs.append(m.group(1))
    videos = [u for u in dict.fromkeys(BARE_ASSET.findall(markdown)) if u not in imgs]
    return imgs, videos


def signed_urls(html_bodies):
    """asset uuid -> short-lived signed URL, from GitHub's rendered HTML."""
    out = {}
    for html in html_bodies:
        for src in IMG_TAG.findall(html or ""):
            src = src.replace("&amp;", "&")
            u = UUID.search(src)
            if u and "private-user-images" in src:
                out.setdefault(u.group(0), src)
    return out


def components_for(files, components):
    hit = [label for label, prefixes in components.items() if any(f.startswith(p) for f in files for p in prefixes)]
    return hit or ["other"]


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "tx-release-notes"})
    with urllib.request.urlopen(req, timeout=30) as r, open(dest, "wb") as f:
        f.write(r.read())


def ext_of(path):
    head = open(path, "rb").read(12)
    if head.startswith(b"\x89PNG"):
        return "png"
    if head[:3] == b"\xff\xd8\xff":
        return "jpg"
    if head[:4] == b"GIF8":
        return "gif"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return "bin"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--range", action="append", required=True, help="LABEL=prev..cur, or prev..cur")
    ap.add_argument("--repo-dir", default=".")
    ap.add_argument("--component", action="append", default=[], help="LABEL=path/prefix (repeatable, comma-separated prefixes)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--download", help="directory to save images into")
    args = ap.parse_args()

    components = {}
    for c in args.component:
        label, _, prefixes = c.partition("=")
        components[label] = [p for p in prefixes.split(",") if p]

    numbers, orphans, in_range = [], {}, {}
    for r in args.range:
        label, _, rng = r.rpartition("=")
        log = run(["git", "log", "--first-parent", "--format=%H\t%s", rng], cwd=args.repo_dir)
        if log is None:
            sys.exit(f"collect_prs: git log {rng} failed - fetch the repo or check the range")
        for line in log.strip().splitlines():
            sha, subject = line.split("\t", 1)
            m = PR_IN_SUBJECT.search(subject)
            found = [int(m.group(1) or m.group(2))] if m else []
            if not found:
                pulls = gh_json(f"repos/{args.repo}/commits/{sha}/pulls") or []
                found = [p["number"] for p in pulls if p.get("merged_at")]
            if not found:
                files = (run(["git", "show", "--name-only", "--format=", sha], cwd=args.repo_dir) or "").split()
                touched = components_for(files, components)
                if not label or label in touched:
                    orphans.setdefault(sha[:9], {"sha": sha[:9], "subject": subject, "components": touched})
            for n in found:
                numbers.append(n)
                in_range.setdefault(n, set()).add(label)

    if args.download:
        os.makedirs(args.download, exist_ok=True)

    prs = []
    for n in dict.fromkeys(numbers):
        out = run(["gh", "pr", "view", str(n), "-R", args.repo, "--json",
                   "number,title,body,url,author,mergedAt,labels,files,headRefName,comments"])
        if not out:
            print(f"collect_prs: PR #{n} not readable, skipped", file=sys.stderr)
            continue
        pr = json.loads(out)
        files = [f["path"] for f in pr.get("files", [])]
        touched = components_for(files, components)
        labels = in_range[n]
        # A PR is news for a component only if it is in that component's range.
        kept = touched if "" in labels else [c for c in touched if c in labels or c == "other"]
        if not kept:
            continue
        comments = [c for c in pr.get("comments", []) if not c["author"]["login"].endswith("[bot]")]
        texts = [pr.get("body") or ""] + [c["body"] for c in comments]
        imgs, videos = [], []
        for t in texts:
            i, v = images_in(t)
            imgs += [x for x in i if x not in imgs]
            videos += [x for x in v if x not in videos]

        html_bodies = []
        if any(UUID.search(u) for u in imgs):
            full = gh_json(f"repos/{args.repo}/pulls/{n}", "application/vnd.github.full+json") or {}
            html_bodies.append(full.get("body_html"))
            for c in gh_json(f"repos/{args.repo}/issues/{n}/comments", "application/vnd.github.full+json") or []:
                html_bodies.append(c.get("body_html"))
        signed = signed_urls(html_bodies)

        images = []
        for k, url in enumerate(imgs, 1):
            u = UUID.search(url)
            img = {"src": url, "asset": u.group(0) if u else None, "inComment": url not in (pr.get("body") or "")}
            fetch = signed.get(img["asset"]) if img["asset"] else (url if url.startswith("http") else None)
            if args.download and fetch:
                tmp = os.path.join(args.download, f"pr{n}-{k}")
                try:
                    download(fetch, tmp)
                    final = f"{tmp}.{ext_of(tmp)}"
                    os.replace(tmp, final)
                    img["local"] = final
                except Exception as e:  # noqa: BLE001 - an unreachable image is reported, not fatal
                    img["error"] = str(e)
            images.append(img)

        haystack = " ".join([pr["title"], pr.get("body") or "", pr.get("headRefName", "").upper()])
        prs.append({
            "number": n,
            "title": pr["title"],
            "url": pr["url"],
            "author": pr["author"]["login"],
            "mergedAt": pr["mergedAt"],
            "branch": pr.get("headRefName"),
            "labels": [l["name"] for l in pr.get("labels", [])],
            "jira": sorted({k for k in JIRA.findall(haystack) if k not in NOT_JIRA}),
            "components": kept,
            "files": files,
            "body": pr.get("body") or "",
            "comments": [c["body"] for c in comments if c["body"].strip()],
            "images": images,
            "videos": videos,
        })

    with open(args.out, "w") as f:
        json.dump({"repo": args.repo, "range": args.range, "prs": prs, "commitsWithoutPr": list(orphans.values())}, f, indent=2, ensure_ascii=False)

    for p in prs:
        got = sum(1 for i in p["images"] if i.get("local"))
        print(f"#{p['number']:<5} {'/'.join(p['components']):<6} img {got}/{len(p['images'])}  {p['title'][:80]}", file=sys.stderr)
    for o in orphans.values():
        print(f"{o['sha']} (no PR) {'/'.join(o['components'])}  {o['subject'][:80]}", file=sys.stderr)


if __name__ == "__main__":
    main()
