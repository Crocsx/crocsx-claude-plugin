#!/usr/bin/env python3
"""Turn a release-note draft into upload-ready HTML by giving every PR image a fresh,
fetchable URL.

GitHub attachments of a private repo are only reachable through signed
private-user-images URLs, which expire five minutes after GitHub renders them. Google
fetches <img src> once, while converting the upload into a Doc, so the URL only has to
live until then. Run this immediately before each create_file call, never earlier.

In the draft, reference an image by PR and asset, leaving src empty:

    <img data-pr="289" data-asset="f4179204-d711-4e2f-9c71-56b323794670" alt="...">

  sign_images.py --repo telexistence-inc/tx-retail --prs prs.json draft.html out.html

Width is set from the local copy (max 600px, the Doc's text width). An image that cannot
be signed is embedded from its local copy, downscaled, when --embed-missing is given;
otherwise it is replaced by a link to the PR, and the script says so.

Google drops a fetched image above roughly 6 MB (seen with a 6.3 MB GIF; 5.3 MB worked)
and leaves a broken-image box. A local copy over --max-remote-mb (default 6) is
therefore left out (the entry's PR link still leads to it). Pick a smaller image for
that entry if one exists.

Embedding (--embed-missing) puts base64 in the HTML, which then has to be passed through
the upload call verbatim: tens of KB per image. Keep it for the rare unsignable image.
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time

IMG = re.compile(r"<img\b[^>]*>", re.I)
ATTR = re.compile(r'([\w-]+)="([^"]*)"')
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
MAX_WIDTH = 600


def gh_json(path):
    p = subprocess.run(["gh", "api", path, "-H", "Accept: application/vnd.github.full+json"], capture_output=True, text=True)
    return json.loads(p.stdout) if p.returncode == 0 else None


def signed_for(repo, pr):
    htmls = [(gh_json(f"repos/{repo}/pulls/{pr}") or {}).get("body_html")]
    htmls += [c.get("body_html") for c in gh_json(f"repos/{repo}/issues/{pr}/comments") or []]
    out = {}
    for h in htmls:
        for src in re.findall(r'<img[^>]*?src="([^"]+)"', h or ""):
            src = src.replace("&amp;", "&")
            u = UUID.search(src)
            if u and "private-user-images" in src:
                out.setdefault(u.group(0), src)
    return out


def size_of(path):
    p = subprocess.run(["magick", "identify", "-format", "%w %h\n", path], capture_output=True, text=True)
    if p.returncode != 0:
        return None
    w, h = p.stdout.splitlines()[0].split()
    return int(w), int(h)


def embedded(path):
    """A downscaled JPEG/PNG data URI; first frame only for an animated GIF."""
    p = subprocess.run(["magick", f"{path}[0]", "-resize", f"{MAX_WIDTH}x>", "-strip", "-quality", "60", "jpg:-"], capture_output=True)
    if p.returncode != 0:
        return None
    return "data:image/jpeg;base64," + base64.b64encode(p.stdout).decode()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--prs", help="prs.json from collect_prs.py, for local copies and sizes")
    ap.add_argument("--embed-missing", action="store_true")
    ap.add_argument("--max-remote-mb", type=float, default=6.0)
    ap.add_argument("--link-text", default="Screenshot in PR #{pr}", help="link for an unsignable image; JA: 'PR #{pr} の画像'")
    ap.add_argument("draft")
    ap.add_argument("out")
    args = ap.parse_args()

    local = {}
    if args.prs:
        for pr in json.load(open(args.prs))["prs"]:
            for img in pr["images"]:
                if img.get("asset") and img.get("local"):
                    local[img["asset"]] = img["local"]

    html = open(args.draft).read()
    wanted = {}
    for tag in IMG.findall(html):
        a = dict(ATTR.findall(tag))
        if a.get("data-pr") and a.get("data-asset"):
            wanted.setdefault(a["data-pr"], set()).add(a["data-asset"])

    signed = {}
    for pr in wanted:
        signed.update(signed_for(args.repo, pr))
    started = time.time()

    report = {"signed": 0, "embedded": 0, "linked": 0, "dropped": 0}

    def replace(m):
        tag = m.group(0)
        a = dict(ATTR.findall(tag))
        asset, pr = a.get("data-asset"), a.get("data-pr")
        if not asset:
            return tag
        alt = a.get("alt", "")
        width = ""
        if asset in local and (dims := size_of(local[asset])):
            width = f' width="{min(dims[0], MAX_WIDTH)}"'
        too_big = asset in local and os.path.getsize(local[asset]) > args.max_remote_mb * 1024 * 1024
        if too_big:
            report["dropped"] += 1
            print(f"sign_images: PR #{pr} asset {asset} is over {args.max_remote_mb:g} MB - left out", file=sys.stderr)
            return ""
        if asset in signed:
            report["signed"] += 1
            return f'<img src="{signed[asset]}" alt="{alt}"{width}>'
        if args.embed_missing and asset in local and (uri := embedded(local[asset])):
            report["embedded"] += 1
            return f'<img src="{uri}" alt="{alt}"{width}>'
        report["linked"] += 1
        print(f"sign_images: PR #{pr} asset {asset} could not be signed - replaced by a link", file=sys.stderr)
        return f'<a href="https://github.com/{args.repo}/pull/{pr}">{args.link_text.format(pr=pr)}</a>'

    html = IMG.sub(replace, html)
    html = re.sub(r"<p>\s*</p>\n?", "", html)
    with open(args.out, "w") as f:
        f.write(html)

    deadline = time.strftime("%H:%M:%S", time.localtime(started + 270))
    print(f"sign_images: {report['signed']} signed, {report['embedded']} embedded, {report['linked']} linked, {report['dropped']} left out; "
          f"{len(html) // 1024} KB. Upload before {deadline} (signed URLs expire after 5 minutes).", file=sys.stderr)


if __name__ == "__main__":
    main()
