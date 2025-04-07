# FileIntel

A lightweight Python-based CLI tool to extract metadata from files like `.pdf`, `.docx`, images, and more. Supports output in both **JSON** and **HTML** formats.

---

### Add screenshots

![Report Screenshot](assets/demo.png)

---

## Installation

1. **Clone the repo** (or copy the script)
   ```bash
   git clone https://github.com/cx48/FileIntel
   cd fileintel
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install `exiftool`** (used for image and general file metadata extraction)

   - **Debian/Ubuntu**
     ```bash
     sudo apt install libimage-exiftool-perl
     ```

   - **macOS** (via Homebrew)
     ```bash
     brew install exiftool
     ```

   - **Fedora/RHEL**
     ```bash
     sudo dnf install perl-Image-ExifTool
     ```

   - **Verify Installation**
     ```bash
     exiftool -ver
     ```

   > If `exiftool` isn't installed, image and certain file types will not yield full metadata.

---

## Usage

### Scan a single file
```bash
python fileintel.py file.docx
```

### Scan all files in a folder
```bash
python fileintel.py ./documents/
```

### Output HTML report
```bash
python fileintel.py file.pdf --html
```

### Output JSON report
```bash
python fileintel.py image.jpg --json
```

### Save both HTML and JSON
```bash
python fileintel.py report.pdf --all
```

> All reports are saved inside a `report/` folder with subdirectories per file.

---

## Supported File Types

- `.docx` (Word Documents)
- `.pdf` (PDF Documents)
- `.jpg`, `.png`, `.jpeg`, `.tiff`, `.gif` (via `exiftool`)
- Other formats supported by `exiftool`

---

## License

MIT — Free for personal and commercial use.
