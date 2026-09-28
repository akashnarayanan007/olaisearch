"""Validate labeled manuscript JSON files.

Checks:
- All required fields present
- Valid Unicode text
- Bounding boxes within image bounds
- No duplicate IDs
- Image files exist
"""
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
import sys

try:
    from PIL import Image
except ImportError:
    Image = None


def validate_label_file(label_path: Path, images_dir: Path) -> List[str]:
    """Validate a single label JSON file.

    Args:
        label_path: Path to label JSON file
        images_dir: Directory containing images

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    # Load JSON
    try:
        with open(label_path, encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]
    except Exception as e:
        return [f"Failed to read file: {e}"]

    # Check required fields
    required_fields = ['image_path', 'language', 'script', 'quality', 'lines']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors

    # Check image exists
    image_path = images_dir / Path(data['image_path']).name
    if not image_path.exists():
        errors.append(f"Image not found: {image_path}")
    else:
        # Load image to check bounds
        if Image:
            try:
                img = Image.open(image_path)
                img_width, img_height = img.size
            except Exception as e:
                errors.append(f"Failed to open image: {e}")
                img_width, img_height = None, None
        else:
            img_width, img_height = None, None

    # Check language and script
    valid_languages = ["Tamil", "Malayalam", "Sanskrit", "Kannada", "Telugu",
                      "Devanagari", "Bengali", "Odia", "Gujarati"]
    if data['language'] not in valid_languages:
        errors.append(f"Unknown language: {data['language']}")

    # Check quality
    valid_qualities = ["clean", "medium", "heavy"]
    if data['quality'] not in valid_qualities:
        errors.append(f"Invalid quality: {data['quality']} (must be clean/medium/heavy)")

    # Check lines
    if not isinstance(data['lines'], list):
        errors.append("'lines' must be a list")
        return errors

    if len(data['lines']) == 0:
        errors.append("No lines labeled (must have at least 1)")

    line_ids = set()
    for i, line in enumerate(data['lines']):
        # Required line fields
        required_line_fields = ['line_id', 'text', 'bbox']
        for field in required_line_fields:
            if field not in line:
                errors.append(f"Line {i}: missing field '{field}'")

        # Check line_id uniqueness
        line_id = line.get('line_id')
        if line_id:
            if line_id in line_ids:
                errors.append(f"Duplicate line_id: {line_id}")
            line_ids.add(line_id)

        # Check text is non-empty string
        text = line.get('text', '')
        if not isinstance(text, str):
            errors.append(f"Line {i}: 'text' must be a string")
        elif not text.strip():
            errors.append(f"Line {i}: 'text' is empty")

        # Check text is valid Unicode (contains non-ASCII for Indic scripts)
        if text and not any(ord(c) > 127 for c in text.replace('[?]', '').replace('[...]', '')):
            # Might be romanized instead of Unicode
            if data['language'] in ["Tamil", "Malayalam", "Sanskrit", "Kannada", "Telugu"]:
                errors.append(f"Line {i}: Text appears to be romanized, not Unicode. Use Unicode script.")

        # Check bbox
        bbox = line.get('bbox')
        if bbox:
            required_bbox_fields = ['x', 'y', 'width', 'height']
            for field in required_bbox_fields:
                if field not in bbox:
                    errors.append(f"Line {i}: bbox missing field '{field}'")

            # Check bbox types
            for field in required_bbox_fields:
                if field in bbox and not isinstance(bbox[field], (int, float)):
                    errors.append(f"Line {i}: bbox['{field}'] must be a number")

            # Check bbox bounds (if we have image dimensions)
            if img_width and img_height:
                x, y, w, h = bbox.get('x', 0), bbox.get('y', 0), bbox.get('width', 0), bbox.get('height', 0)
                if x < 0 or y < 0:
                    errors.append(f"Line {i}: bbox has negative coordinates")
                if x + w > img_width:
                    errors.append(f"Line {i}: bbox extends beyond image width ({x+w} > {img_width})")
                if y + h > img_height:
                    errors.append(f"Line {i}: bbox extends beyond image height ({y+h} > {img_height})")
                if w <= 0 or h <= 0:
                    errors.append(f"Line {i}: bbox has non-positive width or height")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate manuscript label files")
    parser.add_argument("labels_dir", help="Directory containing label JSON files")
    parser.add_argument("--images-dir", help="Directory containing images (default: ../images relative to labels_dir)")
    args = parser.parse_args()

    labels_dir = Path(args.labels_dir)
    if not labels_dir.exists():
        print(f"Error: Labels directory not found: {labels_dir}")
        sys.exit(1)

    if args.images_dir:
        images_dir = Path(args.images_dir)
    else:
        images_dir = labels_dir.parent / "images"

    if not images_dir.exists():
        print(f"Warning: Images directory not found: {images_dir}")
        print("Image existence checks will be skipped.")

    # Find all JSON files
    label_files = list(labels_dir.glob("*.json"))
    if not label_files:
        print(f"No JSON files found in {labels_dir}")
        sys.exit(1)

    print(f"Found {len(label_files)} label files")
    print("=" * 60)

    # Validate each file
    total_errors = 0
    valid_files = []
    invalid_files = []

    for label_file in sorted(label_files):
        errors = validate_label_file(label_file, images_dir)
        if errors:
            print(f"\n❌ {label_file.name}")
            for error in errors:
                print(f"   • {error}")
            invalid_files.append(label_file.name)
            total_errors += len(errors)
        else:
            print(f"✓ {label_file.name}")
            valid_files.append(label_file.name)

    # Summary
    print("\n" + "=" * 60)
    print(f"SUMMARY")
    print(f"  Valid files: {len(valid_files)}/{len(label_files)}")
    print(f"  Invalid files: {len(invalid_files)}/{len(label_files)}")
    print(f"  Total errors: {total_errors}")

    if invalid_files:
        print(f"\n⚠ Invalid files:")
        for fname in invalid_files:
            print(f"  • {fname}")
        sys.exit(1)
    else:
        print("\n✅ All label files are valid!")
        sys.exit(0)


if __name__ == "__main__":
    main()
