#!/usr/bin/env python3
"""Work out what is deployed to an environment, what was deployed before it, and the
commit range between the two, for every component of a project.

Reads the project's release config (the ```json block under `## Release notes` in
.claude/tx-shared/project.md, or a JSON file) and tries, per component and in order:

  version   1. --current / --previous overrides
            2. tx-manifests overlay history (what Argo actually runs)
            3. git tag line for the environment (tagGlob)
            4. GitHub Releases (prod only)
  commit    1. the version is a git tag
            2. the version embeds a short sha (v2026.10.22.3-96bd677-stg)
            3. the deploy workflow run that built it (title `env|build|ver`, or the
               closest successful run before the manifest change, checked against the
               version file at that commit)
            4. the commit that bumped the version file to it (low confidence)

Prints JSON to stdout and a readable summary to stderr. Never writes anything except
a fetch of the repo and of the manifests clone.

  release_range.py --project-md .claude/tx-shared/project.md --env prod
  release_range.py --config cfg.json --env stg --current FE=0.4.28-stg --previous FE=0.4.27-stg
"""

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta

SHA_IN_VERSION = re.compile(r"-([0-9a-f]{7,40})(?:-[a-z]+)?$")
ENV_SUFFIX = re.compile(r"-(dev|stg|prod)$")


def log(*a):
    print(*a, file=sys.stderr)


def run(cmd, cwd=None, check=True):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)}: {p.stderr.strip()}")
    return p.stdout.strip() if p.returncode == 0 else None


def parse_time(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def load_config(args):
    if args.config:
        with open(args.config) as f:
            return json.load(f)
    with open(args.project_md) as f:
        text = f.read()
    section = re.search(r"^## Release notes\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not section:
        sys.exit("release_range: no `## Release notes` section in " + args.project_md)
    block = re.search(r"```json\s*(.*?)```", section.group(1), re.S)
    if not block:
        sys.exit("release_range: `## Release notes` has no ```json block")
    return json.loads(block.group(1))


def find_manifests(args, repo_dir):
    """A local tx-manifests clone, freshly fetched. Sibling clone first, then a cache."""
    candidates = [args.manifests] if args.manifests else []
    candidates.append(os.path.join(os.path.dirname(repo_dir), "tx-manifests"))
    for c in candidates:
        if c and os.path.isdir(os.path.join(c, ".git")):
            run(["git", "fetch", "--quiet", "origin"], cwd=c, check=False)
            return c
    cache = os.path.join(os.path.expanduser("~/.cache"), "tx-release-notes", "tx-manifests")
    if os.path.isdir(os.path.join(cache, ".git")):
        run(["git", "fetch", "--quiet", "origin"], cwd=cache, check=False)
        return cache
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    if run(["gh", "repo", "clone", "telexistence-inc/tx-manifests", cache, "--", "--quiet"], check=False) is None:
        return None
    return cache


def manifest_history(manifests, env, app):
    """Distinct image tags of one overlay, newest first, with the time each landed."""
    if not manifests:
        return []
    path = f"overlays/{env}/{app}/patch-deployment.yaml"
    ref = "origin/main" if run(["git", "rev-parse", "--verify", "-q", "origin/main"], cwd=manifests, check=False) else "HEAD"
    out = run(["git", "log", ref, "--format=%H\t%cI", "--", path], cwd=manifests, check=False)
    if not out:
        return []
    history = []
    for line in out.splitlines():
        sha, when = line.split("\t")
        content = run(["git", "show", f"{sha}:{path}"], cwd=manifests, check=False) or ""
        m = re.search(rf"image:\s*\S*/{re.escape(app)}:(\S+)", content)
        if not m:
            continue
        tag = m.group(1).strip("\"'")
        if history and history[-1]["version"] == tag:
            # An older commit with the same tag: the tag actually landed earlier.
            history[-1]["deployedAt"] = when
            history[-1]["manifestCommit"] = sha[:9]
            continue
        history.append({"version": tag, "deployedAt": when, "manifestCommit": sha[:9]})
    return history


def tag_history(repo_dir, env, globs):
    pattern = globs.get(env) if globs else None
    if not pattern:
        return []
    out = run(["git", "tag", "--sort=-creatordate", "--format=%(refname:short)\t%(creatordate:iso-strict)"], cwd=repo_dir) or ""
    tags = []
    for line in out.splitlines():
        name, when = line.split("\t")
        if not fnmatch.fnmatch(name, pattern):
            continue
        # The prod glob also matches staging tags; keep each line separate.
        if env == "prod" and ENV_SUFFIX.search(name):
            continue
        tags.append({"version": name, "deployedAt": when, "source": "git tag"})
    return tags


def release_history(repo):
    out = run(["gh", "release", "list", "-R", repo, "-L", "20", "--json", "tagName,publishedAt"], check=False)
    if not out:
        return []
    return [{"version": r["tagName"], "deployedAt": r["publishedAt"], "source": "GitHub release"} for r in json.loads(out)]


_runs_cache = {}


def workflow_runs(repo, workflow):
    if workflow not in _runs_cache:
        out = run(["gh", "run", "list", "-R", repo, "--workflow", workflow, "-L", "200",
                   "--json", "displayTitle,headSha,createdAt,conclusion"], check=False)
        _runs_cache[workflow] = json.loads(out) if out else []
    return _runs_cache[workflow]


def version_file_at(repo_dir, sha, path):
    return (run(["git", "show", f"{sha}:{path}"], cwd=repo_dir, check=False) or "").strip()


def resolve_sha(repo_dir, repo, comp, env, entry):
    """Commit a deployed version was built from, with how it was found."""
    version = entry["version"]
    base = ENV_SUFFIX.sub("", version)

    sha = run(["git", "rev-parse", "--verify", "-q", f"refs/tags/{version}^{{commit}}"], cwd=repo_dir, check=False)
    if sha:
        return sha, "git tag", "high"

    m = SHA_IN_VERSION.search(version)
    if m:
        sha = run(["git", "rev-parse", "--verify", "-q", f"{m.group(1)}^{{commit}}"], cwd=repo_dir, check=False)
        if sha:
            return sha, "sha embedded in version", "high"

    wf, vfile = comp.get("workflow"), comp.get("versionFile")
    if wf:
        runs = [r for r in workflow_runs(repo, wf) if r["conclusion"] == "success"]
        titled = [r for r in runs if re.search(rf"\|build\|{re.escape(base)}\)", r["displayTitle"])]
        if titled:
            return titled[0]["headSha"], f"deploy run '{titled[0]['displayTitle']}'", "high"
        if entry.get("deployedAt"):
            landed = parse_time(entry["deployedAt"])
            near = [r for r in runs if landed - timedelta(hours=3) <= parse_time(r["createdAt"]) <= landed + timedelta(minutes=5)
                    and "promote" not in r["displayTitle"]]
            near.sort(key=lambda r: abs((landed - parse_time(r["createdAt"])).total_seconds()))
            for r in near:
                if not vfile or version_file_at(repo_dir, r["headSha"], vfile) == base:
                    return r["headSha"], f"deploy run at {r['createdAt']} ('{r['displayTitle']}')", "medium"

    if vfile:
        out = run(["git", "log", "origin/main", "--format=%H", "--reverse", "--", vfile], cwd=repo_dir, check=False) or ""
        for sha in out.splitlines():
            if version_file_at(repo_dir, sha, vfile) == base:
                return sha, f"commit that set {vfile} to {base}", "low"

    return None, "not found", "none"


def pick(history, override):
    """(current, previous) from a newest-first history, honouring overrides."""
    by_version = {h["version"]: h for h in history}
    cur = by_version.get(override.get("current"), {"version": override["current"]}) if override.get("current") else (history[0] if history else None)
    if override.get("previous"):
        prev = by_version.get(override["previous"], {"version": override["previous"]})
    elif cur and cur["version"] in by_version:
        idx = [h["version"] for h in history].index(cur["version"])
        prev = history[idx + 1] if idx + 1 < len(history) else None
    else:
        prev = None
    return cur, prev


def parse_overrides(pairs, labels):
    result = {}
    for p in pairs or []:
        label, _, version = p.rpartition("=")
        if not label and len(labels) == 1:
            label = labels[0]
        result[label] = version
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--project-md")
    src.add_argument("--config")
    ap.add_argument("--env", required=True, choices=["dev", "stg", "prod"])
    ap.add_argument("--repo-dir", default=".")
    ap.add_argument("--manifests", help="path to a tx-manifests clone")
    ap.add_argument("--current", action="append", help="LABEL=version, or version for a one-component project")
    ap.add_argument("--previous", action="append", help="LABEL=version")
    args = ap.parse_args()

    cfg = load_config(args)
    repo_dir = run(["git", "rev-parse", "--show-toplevel"], cwd=args.repo_dir)
    run(["git", "fetch", "--quiet", "--tags", "origin"], cwd=repo_dir, check=False)
    repo = cfg["repo"]
    labels = [c.get("label", "") for c in cfg["components"]]
    cur_over = parse_overrides(args.current, labels)
    prev_over = parse_overrides(args.previous, labels)

    manifests = None
    if any(c.get("manifestApp") for c in cfg["components"]):
        manifests = find_manifests(args, repo_dir)

    result = {"project": cfg["project"], "repo": repo, "env": args.env, "components": []}
    for comp in cfg["components"]:
        label = comp.get("label", "")
        sources = []
        if comp.get("manifestApp"):
            sources.append(("tx-manifests", manifest_history(manifests, args.env, comp["manifestApp"])))
        sources.append(("git tag", tag_history(repo_dir, args.env, comp.get("tagGlob"))))
        if args.env == "prod":
            sources.append(("GitHub release", release_history(repo)))

        override = {"current": cur_over.get(label), "previous": prev_over.get(label)}
        cur = prev = None
        source = "override" if override["current"] else None
        for name, history in sources:
            if not history and not override["current"]:
                continue
            c, p = pick(history, override)
            # A source that does not know the overridden version cannot say what preceded it.
            if c and (p or not cur):
                cur, prev, source = c, p, source or name
            if cur and prev:
                break

        entry = {"label": label, "paths": comp.get("paths", []), "versionSource": source,
                 "current": cur, "previous": prev, "warnings": []}
        for side in ("current", "previous"):
            e = entry[side]
            if not e:
                entry["warnings"].append(f"{side} version not found - ask the user")
                continue
            sha, how, confidence = resolve_sha(repo_dir, repo, comp, args.env, e)
            e.update({"sha": sha, "shaSource": how, "confidence": confidence})
            if confidence in ("low", "none"):
                entry["warnings"].append(f"{side} {e['version']}: commit is {confidence} confidence ({how}) - confirm with the user")
        if cur and prev and cur.get("sha") and prev.get("sha"):
            entry["range"] = f"{prev['sha'][:12]}..{cur['sha'][:12]}"
            count = run(["git", "rev-list", "--count", f"{prev['sha']}..{cur['sha']}"], cwd=repo_dir, check=False)
            entry["commitCount"] = int(count) if count else None
            if count == "0":
                entry["warnings"].append("empty range - nothing new in this component")
        result["components"].append(entry)

        log(f"[{label or cfg['project']}] {args.env} via {source}")
        for side in ("previous", "current"):
            e = entry[side]
            if e:
                log(f"  {side:8} {e['version']:<34} {str(e.get('sha'))[:9]}  {e.get('confidence')}  ({e.get('shaSource')})")
        if entry.get("range"):
            log(f"  range    {entry['range']}  ({entry.get('commitCount')} commits)")
        for w in entry["warnings"]:
            log(f"  WARNING  {w}")

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
