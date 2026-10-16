"""
Synthetic label generator for MediPaw Thoracic CNN.
Generates a CSV file mapping each image filename to a constant average VHS value.
This is a placeholder for training when real annotations are unavailable.
"""
import os
import csv
import argparse
from pathlib import Path

def generate_labels(data_dir: str, output_path: str, constant_vhs: float = 11.0):
    # Supported image extensions
    valid_ext = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
    files = [f for f in os.listdir(data_dir) if Path(f).suffix.lower() in valid_ext]
    files.sort()
    if not files:
        raise FileNotFoundError(f"No image files found in {data_dir}")
    with open(output_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["filename", "vhs"])
        for fname in files:
            writer.writerow([fname, f"{constant_vhs:.2f}"])
    print(f"Synthetic label file written to {output_path} ({len(files)} entries)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic VHS labels for thoracic radiographs")
    parser.add_argument("--data_dir", type=str, required=True, help="Path to directory containing radiograph images")
    parser.add_argument("--output_path", type=str, default="synthetic_labels.csv", help="CSV file to write labels to")
    parser.add_argument("--vhs", type=float, default=11.0, help="Constant VHS value to assign (default 11.0)")
    args = parser.parse_args()
    generate_labels(args.data_dir, args.output_path, args.vhs)
