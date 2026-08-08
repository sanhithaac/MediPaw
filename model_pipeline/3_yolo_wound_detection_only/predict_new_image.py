"""
=====================================================================================
            MEDIPAW MODULE 3: YOLOv8 UNIFIED INFERENCE (PREDICTION) SCRIPT
=====================================================================================
This script demonstrates how to load the peak performance weights (`best.pt`) 
to achieve the highest accuracy (82.6% mAP) when predicting on new images!
=====================================================================================
"""

import os
import cv2
from ultralytics import YOLO

def predict_wound(image_path, weights_path="weights/best.pt"):
    print("="*85)
    print(" [MEDIPAW INFERENCE] RUNNING UNIFIED WOUND DETECTOR ")
    print("="*85)

    if not os.path.exists(weights_path):
        print(f"[ERROR] Could not find the peak performance weights at: {weights_path}")
        print("Please ensure you downloaded the 'weights/best.pt' file from Colab.")
        return

    if not os.path.exists(image_path):
        print(f"[ERROR] Could not find the input image at: {image_path}")
        return

    print(f"[INFO] 1. Loading PEAK performance weights from: {weights_path}")
    # Initialize the model with the BEST weights (epoch 35) to guarantee max accuracy!
    model = YOLO(weights_path)

    print(f"[INFO] 2. Running inference on new image: {image_path}")
    # Run the prediction
    # conf=0.25 sets the confidence threshold (ignore guesses below 25% certainty)
    results = model.predict(source=image_path, conf=0.25, save=True, save_txt=True)

    print("\n" + "="*85)
    print(" [INFERENCE COMPLETE]")
    print("="*85)
    
    # Process the results
    result = results[0] # Get the first (and only) image result
    boxes = result.boxes
    
    if len(boxes) == 0:
        print("[RESULT] No wounds detected in this image.")
    else:
        print(f"[RESULT] Detected {len(boxes)} potential wound(s)!")
        for i, box in enumerate(boxes):
            # Extract coordinates [x1, y1, x2, y2]
            coords = box.xyxy[0].tolist()
            conf = box.conf[0].item() * 100
            
            print(f" -> Wound #{i+1}: Confidence {conf:.1f}% | Bounding Box Coordinates: "
                  f"[{coords[0]:.1f}, {coords[1]:.1f}, {coords[2]:.1f}, {coords[3]:.1f}]")
            
            print("    (These coordinates will be passed to the U-Net in Module 4 for cropping!)")

    print(f"\n[SUCCESS] An image showing the drawn bounding boxes has been saved to:")
    print(f"          {result.save_dir}")

if __name__ == "__main__":
    # Example usage: Replace this with the path to a test image of a dog!
    # Make sure you place a test image in this folder and rename it to 'test_image.jpg'
    sample_image = "test_image.jpg" 
    
    # Check if the user has provided a file in arguments
    import sys
    if len(sys.argv) > 1:
        sample_image = sys.argv[1]
        
    predict_wound(sample_image)
