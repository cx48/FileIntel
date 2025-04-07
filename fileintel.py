import os
import datetime
import subprocess
import json
from docx import Document
import PyPDF2
from pathlib import Path
import argparse

def pretty_print(data, title):
    print(f"\n{'='*40}\n📄 {title} Metadata\n{'='*40}")
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
        print(f"❌ Failed to run exiftool: {e}")
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

def save_html_report(metadata, filename, output_dir):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_name = f"{Path(filename).stem}.html"
    filepath = output_dir / safe_name

    html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <title>Metadata Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', sans-serif;
            background: #121212;
            color: #e0e0e0;
            padding: 20px;
        }}
        .container {{
            background: #1e1e1e;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.5);
            max-width: 600px;
            margin: auto;
        }}
        h2 {{
            color: #90caf9;
        }}
        .meta {{
            margin: 10px 0;
            padding: 10px;
            background: #2c2c2c;
            border-left: 5px solid #90caf9;
        }}
        .label {{
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class=\"container\">
        <h2>Metadata Report for {filename}</h2>
        <p><em>Generated on {now}</em></p>
        {"".join([f'<div class="meta"><span class="label">{key}:</span> {value}</div>' for key, value in metadata.items()])}
    </div>
</body>
</html>"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"💾 Saved HTML report: {filepath}")

def save_json_report(metadata, filename, output_dir):
    filepath = output_dir / f"{Path(filename).stem}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    print(f"💾 Saved JSON report: {filepath}")

def process_file(file_path, html=False, json_out=False, all_out=False, base_output_dir=Path(".")):
    ext = Path(file_path).suffix.lower()
    metadata = {}

    if ext == ".docx":
        metadata = extract_docx_metadata(file_path)
    elif ext == ".pdf":
        metadata = extract_pdf_metadata(file_path)
    else:
        metadata = extract_with_exiftool(file_path)

    if metadata:
        pretty_print(metadata, Path(file_path).name)
        file_output_dir = base_output_dir / Path(file_path).stem
        file_output_dir.mkdir(parents=True, exist_ok=True)
        if html or all_out:
            save_html_report(metadata, Path(file_path).name, file_output_dir)
        if json_out or all_out:
            save_json_report(metadata, Path(file_path).name, file_output_dir)
    else:
        print("❗ No metadata found.")

def main():
    parser = argparse.ArgumentParser(description="Simple Metadata Scanner")
    parser.add_argument("path", help="Path to file or folder")
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    parser.add_argument("--json", action="store_true", help="Generate JSON report")
    parser.add_argument("--all", action="store_true", help="Save both HTML and JSON reports")
    args = parser.parse_args()

    input_path = Path(args.path)
    output_dir = Path("report")
    output_dir.mkdir(parents=True, exist_ok=True)

    if input_path.is_file():
        process_file(input_path, args.html, args.json, args.all, output_dir)
    elif input_path.is_dir():
        for item in input_path.iterdir():
            if item.is_file():
                process_file(item, args.html, args.json, args.all, output_dir)
    else:
        print("❌ Invalid path.")

if __name__ == "__main__":
    main()

