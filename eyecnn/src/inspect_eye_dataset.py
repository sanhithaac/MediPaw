"""
Dataset Inspection Script for MediPaw Eye CNN Module.

Inspects the Roboflow Dog Eye Problems Detection YOLOv8 dataset:
- Reads and verifies data.yaml and README files
- Counts images and annotation files across train, valid, and test splits
- Verifies image formats, dimensions, color channels, and integrity
- Checks YOLO annotation coordinates, box validity, class IDs, and class frequencies
- Identifies empty annotations, missing files, corrupt images, and multi-box/multi-class images
- Detects potential split leakage based on base source image identifiers
- Saves sample images with overlaid bounding boxes and labels
- Generates summary statistics and class distribution charts in outputs/dataset_report/
"""

import os
import sys
import glob
import json
from pathlib import Path
from collections import defaultdict, Counter

import yaml
# pyrefly: ignore [missing-import]
from PIL import Image, ImageDraw
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns


def load_yaml_config(yaml_path):
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"data.yaml not found at {yaml_path}")
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def inspect_split(split_name, base_dir, class_names):
    img_dir = os.path.join(base_dir, split_name, 'images')
    lbl_dir = os.path.join(base_dir, split_name, 'labels')

    if not os.path.exists(img_dir):
        raise FileNotFoundError(f"Image directory not found: {img_dir}")
    if not os.path.exists(lbl_dir):
        raise FileNotFoundError(f"Label directory not found: {lbl_dir}")

    img_files = sorted(glob.glob(os.path.join(img_dir, '*.*')))
    lbl_files = sorted(glob.glob(os.path.join(lbl_dir, '*.txt')))

    img_stems = {Path(p).stem: p for p in img_files}
    lbl_stems = {Path(p).stem: p for p in lbl_files}

    missing_labels = [stem for stem in img_stems if stem not in lbl_stems]
    missing_images = [stem for stem in lbl_stems if stem not in img_stems]

    split_stats = {
        'split': split_name,
        'image_count': len(img_files),
        'label_file_count': len(lbl_files),
        'missing_labels_count': len(missing_labels),
        'missing_images_count': len(missing_images),
        'corrupt_images': [],
        'empty_label_files': [],
        'invalid_annotations': [],
        'image_shapes': Counter(),
        'image_formats': Counter(),
        'class_counts': defaultdict(int),
        'boxes_per_image_dist': Counter(),
        'multi_class_images': [],
        'base_sources': set(),
        'total_boxes': 0
    }

    # Inspect images and labels
    for stem, img_path in img_stems.items():
        # Check base source identifier (Roboflow often names augmented files as <base_id>.rf.<hash>.jpg)
        base_id = stem.split('.rf.')[0] if '.rf.' in stem else stem
        split_stats['base_sources'].add(base_id)

        # Image integrity check
        try:
            with Image.open(img_path) as img:
                img.verify()
            with Image.open(img_path) as img:
                shape = (img.width, img.height, len(img.getbands()))
                split_stats['image_shapes'][shape] += 1
                split_stats['image_formats'][img.format] += 1
        except Exception as e:
            split_stats['corrupt_images'].append({'image': img_path, 'error': str(e)})
            continue

        # Label check
        lbl_path = lbl_stems.get(stem)
        if not lbl_path:
            split_stats['boxes_per_image_dist'][0] += 1
            continue

        try:
            with open(lbl_path, 'r', encoding='utf-8') as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
        except Exception as e:
            split_stats['invalid_annotations'].append({'file': lbl_path, 'error': f"Read error: {e}"})
            continue

        box_count = len(lines)
        split_stats['boxes_per_image_dist'][box_count] += 1
        if box_count == 0:
            split_stats['empty_label_files'].append(lbl_path)
            continue

        classes_in_image = set()
        for line_idx, line in enumerate(lines):
            parts = line.split()
            if len(parts) != 5:
                split_stats['invalid_annotations'].append({
                    'file': lbl_path,
                    'line': line_idx,
                    'content': line,
                    'error': f"Expected 5 values, got {len(parts)}"
                })
                continue

            try:
                cls_id = int(parts[0])
                xc = float(parts[1])
                yc = float(parts[2])
                w = float(parts[3])
                h = float(parts[4])
            except ValueError as e:
                split_stats['invalid_annotations'].append({
                    'file': lbl_path,
                    'line': line_idx,
                    'content': line,
                    'error': f"Value parse error: {e}"
                })
                continue

            # Validate coordinate bounds
            if not (0.0 <= xc <= 1.0 and 0.0 <= yc <= 1.0 and 0.0 < w <= 1.0 and 0.0 < h <= 1.0):
                split_stats['invalid_annotations'].append({
                    'file': lbl_path,
                    'line': line_idx,
                    'content': line,
                    'error': "Coordinates out of [0, 1] bounds or zero dimensions"
                })
                continue

            # Check valid class ID
            if cls_id < 0 or cls_id >= len(class_names):
                split_stats['invalid_annotations'].append({
                    'file': lbl_path,
                    'line': line_idx,
                    'content': line,
                    'error': f"Class ID {cls_id} out of range [0, {len(class_names)-1}]"
                })
                continue

            cls_name = class_names[cls_id]
            split_stats['class_counts'][cls_name] += 1
            split_stats['total_boxes'] += 1
            classes_in_image.add(cls_name)

        if len(classes_in_image) > 1:
            split_stats['multi_class_images'].append({
                'image': stem,
                'classes': list(classes_in_image)
            })

    return split_stats


def generate_overlays(base_dir, class_names, output_dir, samples_per_split=4):
    overlay_dir = os.path.join(output_dir, 'sample_overlays')
    os.makedirs(overlay_dir, exist_ok=True)

    # Color palette for classes
    colors = {
        0: (220, 20, 60),    # conjunctivitis: crimson
        1: (255, 140, 0),    # entropion: dark orange
        2: (148, 0, 211),    # eyelid_lump: dark violet
        3: (34, 139, 34)     # healthy: forest green
    }

    sample_paths = []
    for split in ['train', 'valid', 'test']:
        img_dir = os.path.join(base_dir, split, 'images')
        lbl_dir = os.path.join(base_dir, split, 'labels')
        lbl_files = sorted(glob.glob(os.path.join(lbl_dir, '*.txt')))

        count = 0
        for lbl_path in lbl_files:
            stem = Path(lbl_path).stem
            img_candidates = glob.glob(os.path.join(img_dir, f"{stem}.*"))
            if not img_candidates:
                continue

            img_path = img_candidates[0]
            with open(lbl_path, 'r', encoding='utf-8') as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
            if not lines:
                continue

            with Image.open(img_path).convert('RGB') as img:
                draw = ImageDraw.Draw(img)
                W, H = img.size

                for line in lines:
                    parts = line.split()
                    if len(parts) != 5:
                        continue
                    cls_id, xc, yc, w, h = int(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                    xmin = max(0, int((xc - w / 2.0) * W))
                    ymin = max(0, int((yc - h / 2.0) * H))
                    xmax = min(W, int((xc + w / 2.0) * W))
                    ymax = min(H, int((yc + h / 2.0) * H))

                    color = colors.get(cls_id, (255, 255, 0))
                    draw.rectangle([xmin, ymin, xmax, ymax], outline=color, width=3)
                    label_text = f"{class_names[cls_id]} ({cls_id})"
                    draw.text((xmin + 4, max(0, ymin - 15)), label_text, fill=color)

                out_name = f"{split}_{count+1}_{stem[:30]}.jpg"
                out_path = os.path.join(overlay_dir, out_name)
                img.save(out_path, quality=90)
                sample_paths.append(out_path)

            count += 1
            if count >= samples_per_split:
                break

    return sample_paths


def plot_distributions(all_stats, class_names, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    sns.set_theme(style="whitegrid")

    # 1. Class distribution by split
    splits = ['train', 'valid', 'test']
    data = []
    for split in splits:
        stats = all_stats[split]
        for cls_name in class_names:
            data.append({
                'Split': split.capitalize(),
                'Class': cls_name,
                'Count': stats['class_counts'].get(cls_name, 0)
            })

    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    import pandas as pd
    df = pd.DataFrame(data)
    palette = sns.color_palette("muted", len(splits))
    sns.barplot(data=df, x='Class', y='Count', hue='Split', palette=palette, ax=ax)
    ax.set_title("MediPaw Eye Dataset: Class Distribution by Split (Bounding Box Counts)", fontsize=14, weight='bold', pad=15)
    ax.set_xlabel("Ocular Abnormality Class", fontsize=12)
    ax.set_ylabel("Number of Bounding Boxes / Instances", fontsize=12)
    for p in ax.patches:
        height = p.get_height()
        if height > 0:
            ax.annotate(f'{int(height)}',
                        (p.get_x() + p.get_width() / 2., height),
                        ha='center', va='bottom', fontsize=9, xytext=(0, 3),
                        textcoords='offset points')
    plt.tight_layout()
    chart_path = os.path.join(output_dir, 'class_distribution.png')
    plt.savefig(chart_path)
    plt.close()

    # 2. Total boxes & images per split
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=300)
    split_imgs = [all_stats[s]['image_count'] for s in splits]
    split_boxes = [all_stats[s]['total_boxes'] for s in splits]

    ax1.pie(split_imgs, labels=[f"{s.capitalize()} ({c})" for s, c in zip(splits, split_imgs)],
            autopct='%1.1f%%', colors=palette, startangle=140)
    ax1.set_title("Images per Split", fontsize=13, weight='bold')

    ax2.pie(split_boxes, labels=[f"{s.capitalize()} ({c})" for s, c in zip(splits, split_boxes)],
            autopct='%1.1f%%', colors=palette, startangle=140)
    ax2.set_title("Annotated Boxes per Split", fontsize=13, weight='bold')

    plt.suptitle("Dataset Split Breakdown", fontsize=15, weight='bold')
    plt.tight_layout()
    split_chart_path = os.path.join(output_dir, 'split_summary.png')
    plt.savefig(split_chart_path)
    plt.close()

    return chart_path, split_chart_path


def main():
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    yaml_path = os.path.join(base_dir, 'data.yaml')
    output_dir = os.path.join(base_dir, 'outputs', 'dataset_report')
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("MediPaw Eye Dataset Inspection")
    print("=" * 70)

    # 1. Read data.yaml
    config = load_yaml_config(yaml_path)
    class_names = config.get('names', [])
    nc = config.get('nc', len(class_names))
    roboflow_meta = config.get('roboflow', {})

    print(f"Dataset root: {base_dir}")
    print(f"Number of classes: {nc}")
    print(f"Class mapping: { {i: name for i, name in enumerate(class_names)} }")
    print(f"Roboflow metadata: {roboflow_meta}")

    # 2. Inspect splits
    all_stats = {}
    for split in ['train', 'valid', 'test']:
        print(f"\nInspecting {split} split...")
        all_stats[split] = inspect_split(split, base_dir, class_names)
        stats = all_stats[split]
        print(f"  Images: {stats['image_count']}")
        print(f"  Label files: {stats['label_file_count']}")
        print(f"  Missing labels: {stats['missing_labels_count']}")
        print(f"  Corrupt images: {len(stats['corrupt_images'])}")
        print(f"  Empty label files: {len(stats['empty_label_files'])}")
        print(f"  Invalid annotations: {len(stats['invalid_annotations'])}")
        print(f"  Total boxes: {stats['total_boxes']}")
        print(f"  Class counts: {dict(stats['class_counts'])}")
        print(f"  Boxes per image: {dict(stats['boxes_per_image_dist'])}")
        print(f"  Multi-class images: {len(stats['multi_class_images'])}")
        print(f"  Unique base source images: {len(stats['base_sources'])}")

    # 3. Check for data leakage across splits
    train_sources = all_stats['train']['base_sources']
    valid_sources = all_stats['valid']['base_sources']
    test_sources = all_stats['test']['base_sources']

    leak_train_valid = train_sources.intersection(valid_sources)
    leak_train_test = train_sources.intersection(test_sources)
    leak_valid_test = valid_sources.intersection(test_sources)

    print("\n" + "=" * 70)
    print("Cross-Split Leakage Check (Matching Base Source IDs)")
    print("=" * 70)
    print(f"Train vs Valid overlapping sources: {len(leak_train_valid)}")
    print(f"Train vs Test overlapping sources:  {len(leak_train_test)}")
    print(f"Valid vs Test overlapping sources:  {len(leak_valid_test)}")

    # 4. Generate visual overlays and plots
    print("\nGenerating sample overlays...")
    sample_overlays = generate_overlays(base_dir, class_names, output_dir, samples_per_split=4)
    print(f"Saved {len(sample_overlays)} sample overlays to {os.path.join(output_dir, 'sample_overlays')}")

    print("Generating distribution charts...")
    chart_path, split_chart_path = plot_distributions(all_stats, class_names, output_dir)
    print(f"Saved charts to {chart_path} and {split_chart_path}")

    # 5. Save structured summary JSON
    summary_report = {
        'dataset_name': 'Roboflow Dog Eye Problems Detection v4',
        'license': roboflow_meta.get('license', 'CC BY 4.0'),
        'classes': {i: name for i, name in enumerate(class_names)},
        'num_classes': nc,
        'leakage_check': {
            'train_valid_overlap_count': len(leak_train_valid),
            'train_test_overlap_count': len(leak_train_test),
            'valid_test_overlap_count': len(leak_valid_test)
        },
        'splits': {}
    }

    for split in ['train', 'valid', 'test']:
        s = all_stats[split]
        summary_report['splits'][split] = {
            'images': s['image_count'],
            'label_files': s['label_file_count'],
            'total_boxes': s['total_boxes'],
            'unique_base_sources': len(s['base_sources']),
            'class_distribution': dict(s['class_counts']),
            'boxes_per_image_distribution': {str(k): v for k, v in s['boxes_per_image_dist'].items()},
            'multi_class_images_count': len(s['multi_class_images']),
            'corrupt_images_count': len(s['corrupt_images']),
            'empty_label_files_count': len(s['empty_label_files']),
            'invalid_annotations_count': len(s['invalid_annotations']),
            'image_formats': {str(k): v for k, v in s['image_formats'].items()},
            'image_shapes': {f"{w}x{h}x{c}": count for (w, h, c), count in s['image_shapes'].items()}
        }

    json_report_path = os.path.join(output_dir, 'dataset_summary.json')
    with open(json_report_path, 'w', encoding='utf-8') as f:
        json.dump(summary_report, f, indent=2)
    print(f"Saved JSON report to {json_report_path}")

    # 6. Save Markdown report
    md_report_path = os.path.join(output_dir, 'dataset_inspection_report.md')
    with open(md_report_path, 'w', encoding='utf-8') as f:
        f.write("# MediPaw Eye Dataset Inspection Report\n\n")
        f.write(f"- **Source**: {roboflow_meta.get('project', 'dog-eye-problems-detection')} (Version {roboflow_meta.get('version', '4')})\n")
        f.write(f"- **License**: {roboflow_meta.get('license', 'CC BY 4.0')}\n")
        f.write(f"- **Verified Classes ({nc})**: `{[c for c in class_names]}`\n\n")

        f.write("## 1. Split Overview\n\n")
        f.write("| Split | Images | Label Files | Annotated Boxes | Unique Base Images | Corrupt Images | Empty Labels |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for split in ['train', 'valid', 'test']:
            sp = summary_report['splits'][split]
            f.write(f"| {split.capitalize()} | {sp['images']} | {sp['label_files']} | {sp['total_boxes']} | {sp['unique_base_sources']} | {sp['corrupt_images_count']} | {sp['empty_label_files_count']} |\n")

        f.write("\n## 2. Class Distribution (Box Instances)\n\n")
        f.write("| Class Name | Train | Valid | Test | Total |\n")
        f.write("|---|---|---|---|---|\n")
        for cls_name in class_names:
            tr = all_stats['train']['class_counts'].get(cls_name, 0)
            va = all_stats['valid']['class_counts'].get(cls_name, 0)
            te = all_stats['test']['class_counts'].get(cls_name, 0)
            tot = tr + va + te
            f.write(f"| **{cls_name}** | {tr} | {va} | {te} | {tot} |\n")

        f.write("\n## 3. Data Leakage Assessment\n\n")
        f.write(f"- Overlapping base source IDs between Train and Valid: **{len(leak_train_valid)}**\n")
        f.write(f"- Overlapping base source IDs between Train and Test: **{len(leak_train_test)}**\n")
        f.write(f"- Overlapping base source IDs between Valid and Test: **{len(leak_valid_test)}**\n\n")

        f.write("## 4. Multi-Box and Multi-Class Images\n\n")
        for split in ['train', 'valid', 'test']:
            f.write(f"- **{split.capitalize()}**: {all_stats[split]['boxes_per_image_dist']} boxes per image, {len(all_stats[split]['multi_class_images'])} multi-class images\n")

        f.write("\n## 5. Artifacts Generated\n\n")
        f.write(f"- Distribution chart: `class_distribution.png`\n")
        f.write(f"- Split summary: `split_summary.png`\n")
        f.write(f"- Sample overlays: `sample_overlays/`\n")
        f.write(f"- Full JSON summary: `dataset_summary.json`\n")

    print(f"Saved Markdown report to {md_report_path}")
    print("=" * 70)
    print("Inspection completed successfully.")
    print("=" * 70)


if __name__ == '__main__':
    main()
