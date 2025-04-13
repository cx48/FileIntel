import folium
import shutil
import re
import hashlib
import subprocess
import json
from docx import Document
import PyPDF2
from pathlib import Path
import argparse

def pretty_print(data, title):
    print(f"\n{'='*40}\n {title} Metadata\n{'='*40}")
    for key, value in data.items():
        print(f"\033[1m{key:20}\033[0m : {value}")
        
def extract_with_exiftool(file_path):
    metadata = {}
    try:
        result = subprocess.run(["exiftool", file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()
    except Exception as e:
        print(f"Failed to run exiftool: {e}")
    return metadata

def extract_docx_metadata(file_path):
    doc = Document(file_path)
    props = doc.core_properties
    return {
        "Title": props.title,
        "Author": props.author,
        "Created": props.created,
        "Modified": props.modified
    }

def extract_pdf_metadata(file_path):
    metadata = {}
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        info = reader.metadata
        for key, value in info.items():
            metadata[key.replace("/", "")] = value
    return metadata

def get_file_hashes(filepath):
    hashes = {}
    with open(filepath, "rb") as f:
        data = f.read()
        hashes["MD5"] = hashlib.md5(data).hexdigest()
        hashes["SHA1"] = hashlib.sha1(data).hexdigest()
        hashes["SHA256"] = hashlib.sha256(data).hexdigest()
    return hashes

def generate_timeline_html(metadata):
    entries = []
    # Simple pattern for detecting date/time strings
    date_pattern = re.compile(r"\d{4}[-/]\d{2}[-/]\d{2}|\d{2}:\d{2}:\d{2}")

    for key, value in metadata.items():
        if isinstance(value, str) and date_pattern.search(value):
            entries.append(f'''
            <div class="timeline-event">
                <div class="timeline-date">{key}</div>
                <div>{value}</div>
            </div>
            ''')

    return "\n".join(entries)

def save_html_report(metadata, filename, output_dir):
    from datetime import datetime

    template_path = Path("report_template/template.html")
    if not template_path.exists():
        print("Template file not found.")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()

    metadata_html = "\n".join(
        f'<div class="meta"><div class="label">{key}:</div><div class="value">{value}</div></div>'
        for key, value in metadata.items()
    )

    timeline_html = generate_timeline_html(metadata)

    html_output = html_template
    html_output = html_template.replace("{{FILENAME}}", filename)
    html_output = html_output.replace("{{DATE}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    html_output = html_output.replace("{{METADATA_BLOCK}}", metadata_html)
    html_output = html_output.replace("{{TIMELINE_BLOCK}}", timeline_html)

    # Copy template assets (CSS + JS) to output dir if not already
    for asset in ["style.css", "script.js"]:
        asset_path = Path("report_template") / asset
        if asset_path.exists():
            shutil.copy(asset_path, output_dir)

    out_path = output_dir / f"{Path(filename).stem}.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_output)

    print(f"\n Saved HTML report: {out_path}")


def save_json_report(metadata, filename, output_dir):
    filepath = output_dir / f"{Path(filename).stem}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    print(f"\n Saved JSON report: {filepath}")

def extract_coordinates(metadata):
    lat = (
        metadata.get("GPS Latitude")
        or metadata.get("GPSLatitude")
        or metadata.get("XMP:GPSLatitude")
    )
    lon = (
        metadata.get("GPS Longitude")
        or metadata.get("GPSLongitude")
        or metadata.get("XMP:GPSLongitude")
    )

    if not lat and not lon:
        gps_pos = metadata.get("GPS Position") or metadata.get("GPSPosition") or metadata.get("XMP:GPSPosition")
        if gps_pos and "," in gps_pos:
            lat_str, lon_str = map(str.strip, gps_pos.split(","))
            lat = lat_str
            lon = lon_str

    if lat and lon:
        try:
            lat = convert_to_decimal(lat)
            lon = convert_to_decimal(lon)
            return lat, lon
        except Exception as e:
            print(f"⚠️ Coordinate conversion failed: {e}")
    return None, None

def convert_to_decimal(coord_str):
    """
    Converts EXIF-style GPS coordinates to decimal degrees.
    Handles both "48 deg 51' 29.99\" N" and "37.7749 N" styles.
    """
    try:
        if "deg" in coord_str:
            parts = coord_str.strip().replace("deg", "").replace("'", "").replace("\"", "").split()
            deg, minutes, seconds, direction = float(parts[0]), float(parts[1]), float(parts[2]), parts[3]
        else:
            value, direction = coord_str.split()
            return float(value) * (-1 if direction in ['S', 'W'] else 1)

        decimal = deg + minutes / 60 + seconds / 3600
        if direction in ['S', 'W']:
            decimal *= -1
        return decimal
    except Exception as e:
        print(f"Failed to convert coordinates: {coord_str} -> {e}")
        return None

def generate_folium_map(lat, lon, output_dir):
    map_obj = folium.Map(location=[lat, lon], zoom_start=12)
    folium.Marker([lat, lon], tooltip="File Location").add_to(map_obj)
    map_path = output_dir / "map.html"
    map_obj.save(map_path)
    print(f"Saved folium map: {map_path}")

def generate_gmaps_link(lat, lon, output_dir):
    link = f"https://www.google.com/maps?q={lat},{lon}"
    print(f"[Google Maps] {link}")
    with open(output_dir / "gmaps.txt", "w", encoding="utf-8") as f:
        f.write(link + "\n")


def process_file(file_path, html=False, json_out=False, map_out=False, gmaps_out=False, all_out=False, include_hash=False, base_output_dir=Path(".")):
    ext = Path(file_path).suffix.lower()
    metadata = {}

    # Extensions that might carry GPS metadata
    gps_supported_exts = {'.jpg', '.jpeg', '.tif', '.tiff', '.heic', '.mp4', '.mov', '.3gp', '.arw', '.cr2', '.nef', '.dng'}

    if ext == ".docx":
        metadata = extract_docx_metadata(file_path)
    elif ext == ".pdf":
        metadata = extract_pdf_metadata(file_path)
    else:
        metadata = extract_with_exiftool(file_path)

    if include_hash:
        hashes = get_file_hashes(file_path)
        metadata.update({f"Hash - {k}": v for k, v in hashes.items()})

    # GPS extraction only if the format is expected to contain it
    lat, lon = (None, None)
    if ext in gps_supported_exts:
        lat, lon = extract_coordinates(metadata)

    if metadata:
        pretty_print(metadata, Path(file_path).name)
        file_output_dir = base_output_dir / Path(file_path).stem
        file_output_dir.mkdir(parents=True, exist_ok=True)
        if html or all_out:
            save_html_report(metadata, Path(file_path).name, file_output_dir)
        if json_out or all_out:
            save_json_report(metadata, Path(file_path).name, file_output_dir)
    else:
        print("\n No metadata found.")

    if lat and lon:
        if gmaps_out:
            generate_gmaps_link(lat, lon, file_output_dir)
        if map_out:
            generate_folium_map(lat, lon, file_output_dir)
    else:
        if map_out or gmaps_out:
            print(f"\n No coordinates found for {file_path.name}. Skipping map/gmaps generation.")

    print("\n📄 Summary for:", Path(file_path).name)
    print("├─ Metadata extracted:", "✅" if metadata else "❌ None found")
    print("├─ HTML report:", "✅" if (html or all_out) else "❌")
    print("├─ JSON report:", "✅" if (json_out or all_out) else "❌")
    print("├─ Hashes included:", "✅" if include_hash else "❌")
    print("├─ Coordinates found:", f"✅ ({lat}, {lon})" if lat and lon else "❌")
    print("├─ Folium map:", "✅" if lat and lon and (map_out or all_out) else "❌")
    print("└─ Google Maps link:", "✅" if lat and lon and (gmaps_out or all_out) else "❌")
    print("-" * 40)



def main():
    parser = argparse.ArgumentParser(description="Simple Metadata Scanner")
    parser.add_argument("path", help="Path to file or folder")
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    parser.add_argument("--json", action="store_true", help="Generate JSON report")
    parser.add_argument("--all", action="store_true", help="Save both HTML and JSON reports")
    parser.add_argument("--map", action="store_true", help="Generate offline folium map")
    parser.add_argument("--gmaps", action="store_true", help="Generate Google Maps link")
    parser.add_argument("--hash", action="store_true", help="Include hash (MD5, SHA1, SHA256)")


    args = parser.parse_args()

    input_path = Path(args.path)
    output_dir = Path("report")
    output_dir.mkdir(parents=True, exist_ok=True)

    if input_path.is_file():
        if args.all:
            html = json_out = map_out = gmaps_out = include_hash = True
        else:
            html = args.html
            json_out = args.json
            map_out = args.map
            gmaps_out = args.gmaps
            include_hash = args.hash

        process_file(input_path, html, json_out, map_out, gmaps_out, args.all, include_hash, output_dir)
    elif input_path.is_dir():
        if args.all:
            html = json_out = map_out = gmaps_out = include_hash = True
        else:
            html = args.html
            json_out = args.json
            map_out = args.map
            gmaps_out = args.gmaps
            include_hash = args.hash

        for item in input_path.iterdir():
            if item.is_file():
                process_file(item, html, json_out, map_out, gmaps_out, args.all, include_hash, output_dir)
    else:
        print("Invalid path or no files found")

if __name__ == "__main__":
    main()