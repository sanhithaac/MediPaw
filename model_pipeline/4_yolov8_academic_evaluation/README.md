# YOLOv8 Academic Evaluation & Results Pipeline

This directory contains the pipeline, methodology, and generated artifacts designed specifically to meet rigorous academic evaluation standards (e.g., for thesis committees or journal submissions to IEEE, Elsevier, or ACM).

## 1. Output Structure
When `train_yolov8_academic.py` is executed, it automatically bypasses standard YOLO logging and generates a clean, publication-ready `academic_results/` directory containing:
- `curves/`: Precision-Recall Curve (PRC), F1 Curve, Bias-Variance Plot, and Confusion Matrices.
- `metrics/`: A CSV report (`academic_metrics_report.csv`) documenting Precision, Recall, and mAP across Train, Validation, and Test splits.
- `sample_visuals/`: Raw input training batches (showing mosaic augmentation) and output prediction images showing bounding boxes.
- `weights/`: The `best.pt` file for final deployment.

## 2. Architecture & Parameters (YOLOv8s)
The model used is **YOLOv8s (Small)**. It was selected because it balances high-speed inference (crucial for real-time triage in rural settings) with excellent spatial localization capabilities.
- **Backbone:** CSPDarknet53 (Cross Stage Partial Networks)
- **Head:** Anchor-free Decoupled Head (separates classification and bounding box regression)
- **Loss Functions:**
  - Box Loss (CIoU / GIoU)
  - Distribution Focal Loss (DFL)
  - Classification Loss (BCE)

## 3. Hyperparameter Tuning Methodology
Hyperparameter optimization in this pipeline is achieved using the Ultralytics Native Tuner (which implements a **Genetic Algorithm** or Ray Tune).
- **How it works:** If you run the script with the `--tune` flag, it executes 30 iterations of training. In each iteration, it slightly mutates parameters like `lr0` (initial learning rate), `mosaic` (data augmentation probability), and `weight_decay`.
- **Selection:** After 30 generations, it selects the hyperparameters that yielded the highest `mAP@0.5:0.95` and saves them. These optimized parameters are then used for the final, full-length training run.

## 4. Evaluative Metrics
Faculty members and peer reviewers evaluate object detection systems differently than simple classifiers. This pipeline provides:
- **Precision-Recall Curve (PRC):** Instead of ROC/AUC (which is flawed for object detection due to infinite background negatives), the PRC demonstrates the model's ability to maintain high precision as recall increases.
- **Confusion Matrix:** Proves the model is accurately distinguishing the `Wound` class from the background.
- **Bias-Variance Tradeoff:** The plotted training vs. validation loss curve proves the model did not overfit the data.

## 5. Target Publication Venues
This methodology and architecture strongly align with the following Q1 journals:
- **IEEE Access** (Open Access, fast review, highly receptive to applied AI and YOLO)
- **Computers and Electronics in Agriculture** (Elsevier, Q1, ideal for livestock/telehealth framing)
- **ACM Transactions on Computing for Healthcare**

## 6. How to Run in Google Colab
Because this script uses the native YOLOv8 evaluation methods and requires the dataset path, follow these steps to run it on a Free T4 GPU in Colab:

1. **Zip the Dataset:** 
   Zip your unified dataset folder (`yolo_merged_wounds`) into a single file named `yolo_merged_wounds.zip`.
2. **Upload to Drive/Colab:** 
   Upload `yolo_merged_wounds.zip` and `train_yolov8_academic.py` to your Google Drive (e.g., in a folder named `medipaw_training`).
3. **Open Colab & Enable GPU:** 
   Create a new Notebook. Go to **Runtime -> Change runtime type** and select **T4 GPU**.
4. **Run the following commands in Colab cells:**

   **Cell 1: Mount Drive & Install YOLO**
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   !pip install -q ultralytics pandas matplotlib
   ```

   **Cell 2: Extract Dataset**
   ```bash
   !unzip -q "/content/drive/MyDrive/medipaw_training/yolo_merged_wounds.zip" -d "/content/dataset"
   ```

   **Cell 3: Update `data.yaml` Path**
   Ensure the `path:` variable in your `data.yaml` points to `/content/dataset/yolo_merged_wounds` rather than your local Windows `E:/...` drive. You can do this by double-clicking it in the Colab file explorer and editing it, or by running a sed command:
   ```bash
   !sed -i 's|path: .*|path: /content/dataset/yolo_merged_wounds|g' /content/dataset/yolo_merged_wounds/data.yaml
   ```

   **Cell 4: Run the Academic Training Script**
   ```bash
   !python "/content/drive/MyDrive/medipaw_training/train_yolov8_academic.py" --yaml "/content/dataset/yolo_merged_wounds/data.yaml" --epochs 50
   ```
   *(Add `--tune` to the end of the command if you want to run hyperparameter tuning first).*

5. **Download Results:** 
   Once training finishes, an `academic_results/` folder will be generated in Colab. You can zip it and download it to your local machine:
   ```bash
   !zip -r academic_results.zip academic_results/
   from google.colab import files
   files.download("academic_results.zip")
   ```
