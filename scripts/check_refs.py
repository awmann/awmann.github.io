"""Case-sensitive check of local src/href/url() references in a built site.

GitHub Pages serves from a case-sensitive filesystem, macOS does not, so a
reference like research_img/TOI1224.jpeg works locally but 404s online.
Run against the Jekyll output directory:

    python scripts/check_refs.py ~/website_local/_site
"""
import os
import re
import sys
from urllib.parse import unquote, urlparse

site = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "_site")

exact = set()
for root, dirs, files in os.walk(site):
    for f in files:
        exact.add(os.path.relpath(os.path.join(root, f), site))

pat = re.compile(r'(?:src|href|poster)\s*=\s*["\']([^"\']+)["\']|url\(\s*["\']?([^"\')]+)["\']?\s*\)', re.I)
bad = 0
for rel in sorted(exact):
    if not rel.endswith((".html", ".css")):
        continue
    text = open(os.path.join(site, rel), encoding="utf-8", errors="replace").read()
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    for m in pat.finditer(text):
        ref = (m.group(1) or m.group(2)).strip()
        u = urlparse(ref)
        if u.scheme or ref.startswith(("#", "//", "mailto:", "data:")):
            continue
        path = unquote(u.path)
        if not path:
            continue
        if path.startswith("/"):
            target = os.path.normpath(path.lstrip("/"))
        else:
            target = os.path.normpath(os.path.join(os.path.dirname(rel), path))
        if target in ("", "."):
            target = "index.html"
        if os.path.isdir(os.path.join(site, target)) or target.endswith("/"):
            target = os.path.join(target, "index.html")
        if target not in exact:
            lower = {e.lower(): e for e in exact}
            hint = lower.get(target.lower())
            kind = f"CASE MISMATCH (file is {hint})" if hint else "MISSING"
            print(f"{rel}: {ref} -> {kind}")
            bad += 1
print(f"{bad} bad reference(s)")
sys.exit(1 if bad else 0)
