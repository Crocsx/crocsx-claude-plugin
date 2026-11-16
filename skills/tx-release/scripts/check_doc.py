#!/usr/bin/env python3
"""Count the images that actually landed in an uploaded Doc.

Feed it the saved result of Drive download_file_content (a JSON file with a base64
`content`) exported as application/pdf (works at any size) or text/html:

  check_doc.py <saved-result.json> --expect 7 [--pages out-dir/]

With --pages, a PDF is also rendered to PNG pages (needs pdftoppm) for a visual check.

An image Google could not fetch (an expired signed URL) still shows as [image] in
read_file_content, but exports as an empty <img>. Only this export tells them apart.
Exits 1 when fewer real images arrived than expected: re-sign and upload again.

Prefer the PDF export: the HTML export refuses docs past about 10 MB ("File too large
for export"), which a few GIFs reach. A PDF keeps one embedded image per fetched image
and drops failed ones.
"""

import argparse
import base64
import json
import re
import os
import subprocess
import sys
import tempfile


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("export")
    ap.add_argument("--expect", type=int, required=True)
    ap.add_argument("--pages", help="directory to render PDF pages into")
    args = ap.parse_args()

    raw = open(args.export, "rb").read()
    try:
        data = base64.b64decode(json.loads(raw)["content"])
    except (ValueError, KeyError):
        data = raw

    if data.startswith(b"%PDF"):
        # Each fetched image is one image XObject; GIFs become their first frame.
        count = len(re.findall(rb"/Subtype\s*/Image", data))
        print(f"check_doc: {count} images in PDF (expected {args.expect})")
        if args.pages:
            os.makedirs(args.pages, exist_ok=True)
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(data)
            subprocess.run(["pdftoppm", "-r", "50", "-png", f.name, os.path.join(args.pages, "page")], check=False)
            print(f"check_doc: pages rendered to {args.pages}")
        sys.exit(0 if count >= args.expect else 1)

    html = data.decode("utf-8", "replace")

    tags = re.findall(r"<img\b[^>]*>", html, re.I)
    count = sum(1 for t in tags if re.search(r'src="[^"]+"', t))
    broken = len(tags) - count
    headings = re.findall(r"<h[1-3][^>]*>(.*?)</h[1-3]>", html, re.S)
    print(f"check_doc: {count} images (expected {args.expect}), {broken} broken, {len(headings)} headings")
    sys.exit(0 if count >= args.expect else 1)


if __name__ == "__main__":
    main()
