"""Check that every pre-existing public URL still resolves in the built site.

Old URLs = every .html file on master, plus everything under anc/, files/,
teaching_files/, and Jupyter_guide/ on master. Each must exist in the build
(as a real page or a redirect stub). Usage:

    python scripts/check_urls.py ~/website_local/_site [git-ref]
"""
import os
import re
import subprocess
import sys

site = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "_site")
ref = sys.argv[2] if len(sys.argv) > 2 else "master"
names = subprocess.run(["git", "ls-tree", "-r", ref, "--name-only"], capture_output=True,
                       text=True, check=True).stdout.splitlines()
keep = [n for n in names if n.endswith(".html") or
        n.startswith(("anc/", "files/", "teaching_files/", "Jupyter_guide/"))]
keep = [n for n in keep if not n.endswith(".DS_Store")]
# Pages removed on purpose (approved by Andrew, Oct 2026).
REMOVED = {"teaching.html", "youngworldslab_old.html"}
keep = [n for n in keep if n not in REMOVED]
missing, redirects = [], []
for n in keep:
    p = os.path.join(site, n)
    if not os.path.isfile(p):
        missing.append(n)
    elif n.endswith(".html") and re.search(r'http-equiv="refresh"', open(p, errors="replace").read()):
        redirects.append(n)
print(f"{len(keep)} old URLs checked, {len(redirects)} redirect(s): {', '.join(redirects) or 'none'}")
for n in missing:
    print(f"MISSING: {n}")
sys.exit(1 if missing else 0)
