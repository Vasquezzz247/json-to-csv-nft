#!/usr/bin/env python3
"""
json-to-csv-nft.py

Convert a folder of NFT metadata JSON files into CSV files OR convert a single aggregated
metadata.json into one CSV. Keeps per-file CSVs (for debugging) and can also produce one
aggregated CSV (recommended for OpenSea Studio).

Typical OpenSea Studio flow:
- Upload your media (images) in Studio.
- Upload ONE metadata CSV that maps each row (token) to its image filename and includes traits.
See OpenSea Studio UI ("Download Examples") for sample formats. This tool helps you build that CSV.

Usage examples:
    # If you have many JSON files inside ./json/
    python3 json-to-csv-nft.py --aggregate nfts.csv --filename-col filename --filename-template "{token_id}.png"

    # If you have a single aggregated JSON (array or dict)
    # Always produces metadata.csv if --aggregate is not given
    python3 json-to-csv-nft.py --metadata metadata.json --filename-col filename --filename-template "{token_id}.png"

Options:
    --metadata PATH        Read a single aggregated metadata.json instead of ./json folder
    --emit-per-file        When using --metadata, also emit per-item CSVs into ./csv (off by default)

    --sort / --no-sort     Sort aggregated CSV by token_id (default: sort)
    --id-from              "filename" | "json" (folder mode only; default: autodetect)
    --image-prefix         Prefix for ipfs:// or relative image paths (e.g., https://ipfs.io/ipfs/QmHASH)
    --aggregate PATH       Additionally write ONE combined CSV to PATH
                           (metadata mode: if omitted, output is always metadata.csv)

    --no-header            Do not write the header row
    --only-traits          Write only trait columns (omit base columns)
    --fields ...           Subset of base columns to include (ignored if --only-traits).
                           Allowed: token_id name description image external_url animation_url background_color youtube_url

    --filename-col NAME    Add a column (e.g., "filename") mapping each row to the uploaded image file
    --filename-template    Template for --filename-col (default: "{token_id}.png").
                           Variables: {token_id},{stem},{image},{image_name},{image_ext}
"""
import argparse
import json
import re
import csv
from pathlib import Path
from urllib.parse import urlparse

# ---------- helpers for both modes ----------

def guess_token_id_from_filename(p: Path):
    m = re.search(r'(\d+)', p.stem)
    return int(m.group(1)) if m else None

def get_token_id_from_json(d: dict):
    for k in ('token_id', 'edition', 'tokenId', 'id'):
        if k in d:
            try:
                return int(str(d[k]))
            except Exception:
                pass
    return None

def normalize_image(img: str, prefix: str | None):
    """Return image URL, optionally applying a gateway prefix to ipfs:// or relative paths."""
    if not isinstance(img, str):
        return ""
    if prefix and (img.startswith("ipfs://") or not img.startswith("http")):
        ipfs_path = img.replace("ipfs://", "")
        if ipfs_path.startswith("ipfs/"):
            ipfs_path = ipfs_path[5:]
        return prefix.rstrip("/") + "/" + ipfs_path.lstrip("/")
    return img

def read_all_json(in_dir: Path):
    return sorted([p for p in in_dir.iterdir() if p.suffix.lower() == ".json"])

def basename_from_url_or_path(s: str):
    """Return basename (file.ext) from URL or path; empty string if not available."""
    if not isinstance(s, str) or not s:
        return ""
    try:
        u = urlparse(s)
        if u.scheme and u.path:
            return Path(u.path).name
    except Exception:
        pass
    return Path(s).name

def ext_from_name(name: str, default: str = ".png"):
    e = Path(name).suffix
    return e if e else default

def render_filename_col(template: str, token_id, stem: str, image_raw: str):
    """Render the filename column from a template."""
    image_name = basename_from_url_or_path(image_raw)
    image_ext = ext_from_name(image_name or "", default=".png")
    safe_tid = "" if token_id is None else str(token_id)
    return template.format(
        token_id=safe_tid,
        stem=stem,
        image=image_raw or "",
        image_name=image_name or "",
        image_ext=image_ext or ".png",
    )

# ---------- folder mode: parse per-file ----------

def parse_json_file(p: Path, id_from: str | None, image_prefix: str | None):
    d = json.loads(p.read_text(encoding="utf-8"))

    tid_fn = guess_token_id_from_filename(p)
    tid_js = get_token_id_from_json(d)
    if id_from == "filename":
        token_id = tid_fn
    elif id_from == "json":
        token_id = tid_js
    else:
        token_id = tid_js if tid_js is not None else tid_fn

    name = d.get("name", "")
    description = d.get("description", "")
    image_raw = d.get("image", "")
    image = normalize_image(image_raw, image_prefix)
    external_url = d.get("external_url", "")
    animation_url = d.get("animation_url", "")
    background_color = d.get("background_color", "")
    youtube_url = d.get("youtube_url", "")

    trait_map = {}
    atts = d.get("attributes", [])
    if isinstance(atts, list):
        for a in atts:
            if not isinstance(a, dict):
                continue
            t = a.get("trait_type") or a.get("trait") or a.get("type")
            v = a.get("value", "")
            if t:
                trait_map[str(t)] = v

    return {
        "token_id": token_id,
        "name": name,
        "description": description,
        "image": image,
        "image_raw": image_raw,
        "external_url": external_url,
        "animation_url": animation_url,
        "background_color": background_color,
        "youtube_url": youtube_url,
        "traits": trait_map,
        "_stem": p.stem,
    }

# ---------- metadata.json mode: load aggregated ----------

def load_metadata_file(path: Path, image_prefix: str | None):
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = []

    def normalize_one(obj, key_for_stem: str | None):
        token_id = get_token_id_from_json(obj)
        name = obj.get("name", "")
        description = obj.get("description", "")
        image_raw = obj.get("image", "")
        image = normalize_image(image_raw, image_prefix)
        external_url = obj.get("external_url", "")
        animation_url = obj.get("animation_url", "")
        background_color = obj.get("background_color", "")
        youtube_url = obj.get("youtube_url", "")

        trait_map = {}
        atts = obj.get("attributes", [])
        if isinstance(atts, list):
            for a in atts:
                if not isinstance(a, dict):
                    continue
                t = a.get("trait_type") or a.get("trait") or a.get("type")
                v = a.get("value", "")
                if t:
                    trait_map[str(t)] = v

        stem = key_for_stem or (str(token_id) if token_id is not None else "item")

        return {
            "token_id": token_id,
            "name": name,
            "description": description,
            "image": image,
            "image_raw": image_raw,
            "external_url": external_url,
            "animation_url": animation_url,
            "background_color": background_color,
            "youtube_url": youtube_url,
            "traits": trait_map,
            "_stem": stem,
        }

    if isinstance(raw, list):
        for idx, obj in enumerate(raw, start=1):
            if isinstance(obj, dict):
                items.append(normalize_one(obj, key_for_stem=str(idx)))
    elif isinstance(raw, dict):
        for k, obj in raw.items():
            if isinstance(obj, dict):
                if "token_id" not in obj:
                    try:
                        obj = dict(obj)
                        obj["token_id"] = int(k)
                    except Exception:
                        pass
                items.append(normalize_one(obj, key_for_stem=str(k)))
    else:
        raise SystemExit("Unsupported metadata.json structure (must be list or dict).")

    return items

# ---------- main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata", help="Read a single aggregated metadata.json instead of ./json folder")
    ap.add_argument("--emit-per-file", action="store_true",
                    help="When using --metadata, also emit per-item CSVs into ./csv (off by default)")
    ap.add_argument("--sort", dest="do_sort", action=argparse.BooleanOptionalAction, default=True)
    ap.add_argument("--id-from", choices=["filename", "json"], default=None,
                    help="Folder mode only: choose how to get token_id (default: autodetect)")
    ap.add_argument("--image-prefix", default=None)
    ap.add_argument("--aggregate", help="Write a single combined CSV to this path "
                                        "(metadata mode: if omitted, output is always metadata.csv)")
    ap.add_argument("--no-header", action="store_true", help="Do not write the header row")
    ap.add_argument("--only-traits", action="store_true", help="Write only trait columns (omit base columns)")
    ap.add_argument("--fields", nargs="+", default=None,
                    help="Subset of base columns to include; e.g., --fields token_id name image")
    ap.add_argument("--filename-col", dest="filename_col", default=None,
                    help="Column name that maps to uploaded image files (e.g., 'filename')")
    ap.add_argument("--filename-template", dest="filename_tmpl", default="{token_id}.png",
                    help="Template for --filename-col. Vars: {token_id},{stem},{image},{image_name},{image_ext}")

    args = ap.parse_args()

    base_dir = Path(__file__).parent
    in_dir = base_dir / "json"
    out_dir = base_dir / "csv"
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.metadata:
        meta_path = Path(args.metadata)
        if not meta_path.exists():
            raise SystemExit(f"metadata file not found: {meta_path}")
        items_list = load_metadata_file(meta_path, args.image_prefix)
        folder_mode = False
    else:
        files = read_all_json(in_dir)
        if not files:
            raise SystemExit(f"No .json files found in: {in_dir} (or use --metadata metadata.json)")
        items_list = []
        for p in files:
            try:
                item = parse_json_file(p, args.id_from, args.image_prefix)
            except Exception as e:
                print(f"[WARN] Could not read {p.name}: {e}")
                continue
            items_list.append((p, item))
        folder_mode = True

    all_traits_order = []
    trait_seen = set()
    iter_items = (it for _, it in items_list) if folder_mode else items_list
    for it in iter_items:
        for t in it["traits"].keys():
            if t not in trait_seen:
                trait_seen.add(t)
                all_traits_order.append(t)

    default_base = ["token_id","name","description","image","external_url","animation_url","background_color","youtube_url"]

    if args.only_traits:
        base_cols = []
    elif args.fields:
        allowed = set(default_base)
        base_cols = [c for c in args.fields if c in allowed]
    else:
        base_cols = default_base

    filename_col_name = args.filename_col if args.filename_col else None
    header = base_cols + ([filename_col_name] if filename_col_name else []) + list(all_traits_order)

    # per-file CSVs
    written = 0
    if folder_mode:
        for p, it in items_list:
            out_file = (out_dir / p.name).with_suffix(".csv")
            with open(out_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                if not args.no_header:
                    writer.writerow(header)
                row = [it.get(c, "") for c in base_cols]
                if filename_col_name:
                    row.append(render_filename_col(args.filename_tmpl, it["token_id"], it["_stem"], it["image_raw"]))
                for t in all_traits_order:
                    row.append(it["traits"].get(t, ""))
                writer.writerow(row)
            written += 1
        print(f"Wrote {written} per-file CSV(s) into: {out_dir}")
    else:
        if args.emit_per_file:
            for it in items_list:
                out_file = (out_dir / (it["_stem"] + ".csv"))
                with open(out_file, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    if not args.no_header:
                        writer.writerow(header)
                    row = [it.get(c, "") for c in base_cols]
                    if filename_col_name:
                        row.append(render_filename_col(args.filename_tmpl, it["token_id"], it["_stem"], it["image_raw"]))
                    for t in all_traits_order:
                        row.append(it["traits"].get(t, ""))
                    writer.writerow(row)
                written += 1
            print(f"Wrote {written} per-file CSV(s) into: {out_dir}")
        else:
            print("Per-file CSVs skipped (use --emit-per-file to write them in metadata mode).")

    # aggregated CSV
    if args.aggregate:
        agg_path = Path(args.aggregate)
    elif not folder_mode:
        agg_path = Path("metadata.csv")
    else:
        agg_path = None

    if agg_path:
        agg_items = [it for _, it in items_list] if folder_mode else items_list
        if args.do_sort:
            agg_items.sort(key=lambda x: (x["token_id"] is None, x["token_id"]))
        agg_path.parent.mkdir(parents=True, exist_ok=True)
        with open(agg_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if not args.no_header:
                writer.writerow(header)
            for it in agg_items:
                row = [it.get(c, "") for c in base_cols]
                if filename_col_name:
                    row.append(render_filename_col(args.filename_tmpl, it["token_id"], it["_stem"], it["image_raw"]))
                for t in all_traits_order:
                    row.append(it["traits"].get(t, ""))
                writer.writerow(row)
        print(f"Aggregated CSV written: {agg_path}")
    else:
        print("No aggregated CSV requested (use --aggregate PATH, or use --metadata to auto-write metadata.csv).")

if __name__ == "__main__":
    main()