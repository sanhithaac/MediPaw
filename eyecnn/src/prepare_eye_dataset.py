"""
Dataset Preparation Script for MediPaw Eye CNN Classification.

Converts YOLOv8 detection annotations into a cropped classification dataset:
- Reads YOLO annotations and converts normalized bounding boxes into valid pixel coordinates
- Applies a safety padding margin to preserve surrounding eyelid and ocular pathology
- Validates box dimensions and skips invalid boxes with documented warnings
- Handles multi-box images cleanly by generating indexed crops without discarding labels
- Preserves the existing train, valid, and test partitions
- Prevents cross-split data leakage
- Generates a standard PyTorch ImageFolder hierarchy:
    datasets/eye/{split}/{class_name}/{crop_filename}
- Computes training-only class balance weights for cost-sensitive loss weighting
- Saves comprehensive crop provenance metadata (CSV and JSON)
"""

import os
import sys
import glob
import json
import argparse
from pathlib import Path
from collections import defaultdict, Counter

import yaml
import pandas as pd
from PIL import Image
from tqdm import tqdm


def parse_args():
    parser = argparse.ArgumentParser(description="Convert YOLO eye detection dataset into classification crops.")
    parser.add_argument("--source_dir", type=str, default=".", help="Root directory containing train, valid, test and data.yaml")
    parser.add_argument("--dest_dir", type=str, default="datasets/eye", help="Destination root directory for classification dataset")
    parser.add_argument("--padding", type=float, default=0.05, help="Proportional padding margin around bounding box (default: 0.05)")
    parser.add_argument("--min_size", type=int, default=16, help="Minimum crop width and height in pixels")
    return parser.parse_args()


def main():
    args = parse_args()
    source_dir = os.path.abspath(args.source_dir)
    dest_dir = os.path.abspath(args.dest_dir)
    yaml_path = os.path.join(source_dir, "data.yaml")

    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"data.yaml not found at {yaml_path}")

    with open(yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    class_names = config.get("names", [])
    if not class_names:
        raise ValueError("No classes found in data.yaml")

    print("=" * 70)
    print("MediPaw Eye CNN: Dataset Conversion Pipeline")
    print("=" * 70)
    print(f"Source Directory: {source_dir}")
    print(f"Destination:      {dest_dir}")
    print(f"Classes ({len(class_names)}): {class_names}")
    print(f"Crop Padding:     {args.padding * 100:.1f}%")
    print(f"Min Crop Size:    {args.min_size}px")

    splits = ["train", "valid", "test"]
    metadata_records = []
    skipped_records = []
    split_class_counts = {s: defaultdict(int) for s in splits}

    for split in splits:
        img_dir = os.path.join(source_dir, split, "images")
        lbl_dir = os.path.join(source_dir, split, "labels")

        if not os.path.exists(img_dir) or not os.path.exists(lbl_dir):
            print(f"Warning: Skipping missing split '{split}'")
            continue

        lbl_files = sorted(glob.glob(os.path.join(lbl_dir, "*.txt")))
        print(f"\nProcessing {split} split ({len(lbl_files)} label files)...")

        for lbl_path in tqdm(lbl_files, desc=f"Cropping {split}"):
            stem = Path(lbl_path).stem
            img_candidates = glob.glob(os.path.join(img_dir, f"{stem}.*"))
            if not img_candidates:
                skipped_records.append({
                    "split": split,
                    "label_file": lbl_path,
                    "reason": "Missing corresponding image file"
                })
                continue

            img_path = img_candidates[0]
            try:
                img = Image.open(img_path).convert("RGB")
            except Exception as e:
                skipped_records.append({
                    "split": split,
                    "image_file": img_path,
                    "reason": f"Corrupt image file: {e}"
                })
                continue

            img_w, img_h = img.size

            with open(lbl_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]

            if not lines:
                skipped_records.append({
                    "split": split,
                    "label_file": lbl_path,
                    "reason": "Empty annotation file"
                })
                continue

            # Base identifier to trace duplicates / augmentations
            base_id = stem.split(".rf.")[0] if ".rf." in stem else stem

            for box_idx, line in enumerate(lines):
                parts = line.split()
                if len(parts) != 5:
                    skipped_records.append({
                        "split": split,
                        "label_file": lbl_path,
                        "line": box_idx,
                        "reason": f"Invalid format: expected 5 elements, got {len(parts)}"
                    })
                    continue

                try:
                    cls_id = int(parts[0])
                    xc = float(parts[1])
                    yc = float(parts[2])
                    w = float(parts[3])
                    h = float(parts[4])
                except ValueError as e:
                    skipped_records.append({
                        "split": split,
                        "label_file": lbl_path,
                        "line": box_idx,
                        "reason": f"Malformed numerical values: {e}"
                    })
                    continue

                if cls_id < 0 or cls_id >= len(class_names):
                    skipped_records.append({
                        "split": split,
                        "label_file": lbl_path,
                        "line": box_idx,
                        "reason": f"Class ID {cls_id} out of bounds"
                    })
                    continue

                cls_name = class_names[cls_id]

                # Convert normalized coordinates to absolute pixels
                bw = w * img_w
                bh = h * img_h
                cx = xc * img_w
                cy = yc * img_h

                # Apply padding margin
                pad_x = bw * args.padding
                pad_y = bh * args.padding

                xmin = max(0, int(cx - (bw / 2.0) - pad_x))
                ymin = max(0, int(cy - (bh / 2.0) - pad_y))
                xmax = min(img_w, int(cx + (bw / 2.0) + pad_x))
                ymax = min(img_h, int(cy + (bh / 2.0) + pad_y))

                crop_w = xmax - xmin
                crop_h = ymax - ymin

                if crop_w < args.min_size or crop_h < args.min_size:
                    skipped_records.append({
                        "split": split,
                        "label_file": lbl_path,
                        "line": box_idx,
                        "reason": f"Crop dimensions ({crop_w}x{crop_h}) below min_size ({args.min_size}px)"
                    })
                    continue

                # Crop image
                crop_img = img.crop((xmin, ymin, xmax, ymax))

                # Determine destination path
                crop_filename = f"{stem}_crop{box_idx}.jpg"
                crop_class_dir = os.path.join(dest_dir, split, cls_name)
                os.makedirs(crop_class_dir, exist_ok=True)
                crop_filepath = os.path.join(crop_class_dir, crop_filename)

                # Save cropped image (quality=95 JPEG)
                crop_img.save(crop_filepath, quality=95)

                rel_crop_path = os.path.relpath(crop_filepath, source_dir)
                metadata_records.append({
                    "crop_id": f"{split}_{cls_name}_{stem}_{box_idx}",
                    "crop_filename": crop_filename,
                    "crop_rel_path": rel_crop_path,
                    "split": split,
                    "class_id": cls_id,
                    "class_name": cls_name,
                    "source_image": os.path.basename(img_path),
                    "base_source_id": base_id,
                    "box_index": box_idx,
                    "orig_w": img_w,
                    "orig_h": img_h,
                    "norm_xc": xc,
                    "norm_yc": yc,
                    "norm_w": w,
                    "norm_h": h,
                    "pixel_xmin": xmin,
                    "pixel_ymin": ymin,
                    "pixel_xmax": xmax,
                    "pixel_ymax": ymax,
                    "crop_width": crop_w,
                    "crop_height": crop_h
                })

                split_class_counts[split][cls_name] += 1

    # Save metadata table
    df_meta = pd.DataFrame(metadata_records)
    csv_path = os.path.join(dest_dir, "crop_metadata.csv")
    df_meta.to_csv(csv_path, index=False)
    print(f"\nSaved crop metadata table ({len(df_meta)} rows) to: {csv_path}")

    # Compute training class weights (Inverse frequency: N / (K * n_c))
    train_counts = split_class_counts["train"]
    total_train = sum(train_counts.values())
    num_classes = len(class_names)
    class_weights = {}
    for idx, cname in enumerate(class_names):
        count = train_counts.get(cname, 0)
        weight = total_train / (num_classes * count) if count > 0 else 1.0
        class_weights[cname] = {
            "class_id": idx,
            "count": count,
            "weight": round(weight, 5)
        }

    weights_path = os.path.join(dest_dir, "class_weights.json")
    with open(weights_path, "w", encoding="utf-8") as f:
        json.dump(class_weights, f, indent=2)
    print(f"Saved class weights to: {weights_path}")

    # Save summary report
    summary = {
        "destination_directory": dest_dir,
        "classes": class_names,
        "padding_ratio": args.padding,
        "total_crops_generated": len(metadata_records),
        "total_skipped_annotations": len(skipped_records),
        "split_counts": {
            split: {
                "total": sum(split_class_counts[split].values()),
                "by_class": dict(split_class_counts[split])
            }
            for split in splits
        },
        "class_weights": class_weights,
        "skipped_records_sample": skipped_records[:10]
    }

    summary_path = os.path.join(dest_dir, "dataset_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 70)
    print("Crop Generation Summary")
    print("=" * 70)
    for split in splits:
        print(f"Split [{split.upper()}]: {sum(split_class_counts[split].values())} crops")
        for cname in class_names:
            print(f"   {cname:16s}: {split_class_counts[split].get(cname, 0):5d}")
    print(f"Total crops generated: {len(metadata_records)}")
    print(f"Total skipped:         {len(skipped_records)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
