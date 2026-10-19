"""Resize, recompress, and strip metadata from site images, in place.

Usage (from the repo root):

    python scripts/optimize_images.py            # all rules below
    python scripts/optimize_images.py --dry-run  # report only
    python scripts/optimize_images.py --cards    # rebuild research cards

Rules (longest side is about 2x the displayed width):
  group photos 1800 px, headshots and member photos 700 px,
  in-page figures 1400 px, home-page photos 700 px.
Pixels are converted to sRGB from any embedded ICC profile before the
profile is dropped; HDR (PQ/HLG) photos are left untouched.
JPEG quality 82 (progressive); PNGs are resized, then run through pngquant
when available (only kept if smaller). EXIF/GPS is dropped from everything;
orientation is applied to the pixels first so photos stay upright.
A file is only rewritten when it was resized, carried EXIF, or the new file
is at least 10% smaller, so re-running the script is safe.
Requires Pillow (and pillow-heif for .heic inputs used by make_assets.py).
"""
import argparse
import io
import os
import shutil
import subprocess
import sys

from PIL import Image, ImageCms, ImageOps

SRGB = ImageCms.createProfile("sRGB")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GROUP = 1800
PHOTO = 700
FIGURE = 1400

PHOTOS = {
    "img/RoanMountain.png", "img/bandit2.png", "img/headshot_2026.jpg",
    "students/Barber.JPG", "students/Boyle.jpg", "students/Ian.jpg",
    "students/Isabel.jpeg", "students/Mese.jpg", "students/Walters.jpg",
    "students/Kremer.jpg", "students/Hannah.jpg", "students/slack-pfp.jpg",
    "students/Gnanakkumaran.jpg", "students/Boff.JPG",
}
GROUPS = {"img/Team2.JPG", "img/Team1_small.JPG", "img/Team3_small.JPG",
          "img/Team_sep2026.jpg"}
SKIP_DIRS = ("research_img/cards/",)
SKIP = {"img/star.png", "img/favicon.png", "img/apple-touch-icon.png"}
EXTS = (".jpg", ".jpeg", ".png", ".webp")


def limit_for(rel):
    if rel in GROUPS:
        return GROUP
    if rel in PHOTOS:
        return PHOTO
    return FIGURE


def icc_name(im):
    icc = im.info.get("icc_profile")
    if not icc:
        return None
    return ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(icc))).strip()


def is_hdr(im):
    name = icc_name(im) or ""
    return "PQ" in name or "2084" in name or "HLG" in name


def to_srgb(im):
    """Convert pixels to sRGB using the embedded ICC profile, so colors survive
    when the profile is stripped. Without this, Display P3 / Adobe RGB photos
    look washed out or tinted."""
    icc = im.info.get("icc_profile")
    if not icc or "sRGB" in (icc_name(im) or ""):
        return im
    mode = "RGBA" if "A" in im.getbands() or im.mode == "P" and "transparency" in im.info else "RGB"
    src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
    return ImageCms.profileToProfile(im.convert(mode), src, SRGB, outputMode=mode)


def encode(im, ext):
    buf = io.BytesIO()
    if ext in (".jpg", ".jpeg"):
        im.convert("RGB").save(buf, "JPEG", quality=82, optimize=True, progressive=True)
    elif ext == ".webp":
        im.save(buf, "WEBP", quality=82, method=6)
    else:
        im.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def pngquant(data):
    if not shutil.which("pngquant"):
        return data
    p = subprocess.run(["pngquant", "--quality=70-95", "--speed=1", "--strip", "-"],
                       input=data, capture_output=True)
    if p.returncode == 0 and 0 < len(p.stdout) < len(data):
        return p.stdout
    return data


def process(rel, dry):
    path = os.path.join(ROOT, rel)
    ext = os.path.splitext(rel)[1].lower()
    old = os.path.getsize(path)
    im = Image.open(path)
    if is_hdr(im):
        print(f"{rel}: HDR (PQ/HLG) color profile, left untouched")
        return 0
    has_exif = bool(im.info.get("exif")) or bool(im.getexif())
    has_icc = bool(im.info.get("icc_profile"))
    im = to_srgb(ImageOps.exif_transpose(im))
    lim = limit_for(rel)
    resized = max(im.size) > lim
    if resized:
        im.thumbnail((lim, lim), Image.LANCZOS)
    if im.mode not in ("RGB", "RGBA", "L", "LA", "P"):
        im = im.convert("RGBA" if "A" in im.getbands() else "RGB")
    data = encode(im, ext)
    if ext == ".png":
        data = pngquant(data)
    has_exif = has_exif or has_icc
    if not (resized or has_exif or len(data) < 0.9 * old):
        return 0
    if len(data) >= old and not has_exif:
        return 0
    print(f"{rel}: {old/1e6:.2f} MB -> {len(data)/1e6:.2f} MB, {im.size[0]}x{im.size[1]}"
          f"{' (resized)' if resized else ''}{' (exif stripped)' if has_exif else ''}")
    if not dry:
        with open(path, "wb") as f:
            f.write(data)
    return old - len(data)


# Research-page cards: real 3:2 crops (or pads, for plots on a flat background,
# so no axes are cut). (source, output, mode, arg)
#   crop: arg = (left, top, right, bottom) in source pixels, already 3:2
#   pad:  arg = background color used to extend the image to 3:2
#   croppad: arg = (crop box, background color): crop, then pad to 3:2
CARD_SIZE = (900, 600)
CARDS = [
    ("video/young_discovery_poster.jpg", "thyme.jpg", "pad", (0, 0, 0)),
    ("research_img/irasb_cropped.jpg", "tidye.jpg", "crop", (0, 160, 1400, 1093)),
    ("research_img/pleiades_well.jpg", "tars.jpg", "crop", (0, 28, 1400, 961)),
    ("research_img/taurus_orientation.png", "soysauce.jpg", "croppad", ((1052, 8, 1396, 540), (255, 255, 255))),
    ("research_img/TTV.jpeg", "tir.jpg", "crop", (0, 0, 659, 439)),
    ("research_img/star.jpg", "ages.jpg", "crop", (0, 7, 804, 543)),
    ("research_img/LDB_model.png", "ldb.jpg", "pad", (255, 255, 255)),
    ("research_img/alpha_centauri_AB.jpg", "molusc.jpg", "crop", (10, 0, 1015, 670)),
]


def make_cards(dry):
    out_dir = os.path.join(ROOT, "research_img", "cards")
    os.makedirs(out_dir, exist_ok=True)
    for src, out, mode, arg in CARDS:
        im = to_srgb(ImageOps.exif_transpose(Image.open(os.path.join(ROOT, src)))).convert("RGB")
        if mode == "croppad":
            box, arg = arg
            im = im.crop(box)
        if mode == "crop":
            im = im.crop(arg)
        else:
            w, h = im.size
            if w / h > 1.5:
                canvas = Image.new("RGB", (w, round(w / 1.5)), arg)
            else:
                canvas = Image.new("RGB", (round(h * 1.5), h), arg)
            canvas.paste(im, ((canvas.width - w) // 2, (canvas.height - h) // 2))
            im = canvas
        im = im.resize(CARD_SIZE, Image.LANCZOS)
        path = os.path.join(out_dir, out)
        print(f"card {out} from {src} ({mode})")
        if not dry:
            im.save(path, "JPEG", quality=82, optimize=True, progressive=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cards", action="store_true", help="only (re)build research cards")
    ap.add_argument("paths", nargs="*", help="limit to these repo-relative files")
    a = ap.parse_args()
    if a.cards:
        return make_cards(a.dry_run)
    if a.paths:
        todo = a.paths
    else:
        todo = []
        for d in ("img", "students", "research_img"):
            for f in sorted(os.listdir(os.path.join(ROOT, d))):
                rel = f"{d}/{f}"
                if f.lower().endswith(EXTS) and rel not in SKIP and not rel.startswith(SKIP_DIRS):
                    todo.append(rel)
    saved = sum(process(rel, a.dry_run) for rel in todo)
    print(f"total saved: {saved/1e6:.1f} MB")


if __name__ == "__main__":
    sys.exit(main())
