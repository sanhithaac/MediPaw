import os
import sys
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
import cv2

# Set path to CNN architecture
CNN_DIR = os.path.join(os.path.dirname(__file__), "2_cnn_skin_classifier")
sys.path.append(CNN_DIR)
from model_architecture import MediPawSkinClassifier
from ultralytics import YOLO

OUT_DIR = os.path.join(os.path.dirname(__file__), "xai_results")
os.makedirs(OUT_DIR, exist_ok=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load CNN model
cnn_classes = [
    "Fungal Infections", 
    "Allergic Dermatitis", 
    "Demodicosis Mange", 
    "Bacterial Dermatosis", 
    "Healthy Control", 
    "Ringworm"
]

cnn_weights_path = os.path.join(CNN_DIR, "best_cnn1_weights.pth")
cnn_model = MediPawSkinClassifier(num_classes=6, backbone_type="efficientnet_v2_s").to(device)
cnn_model.load_state_dict(torch.load(cnn_weights_path, map_location=device, weights_only=True))
cnn_model.eval()

# Load YOLO model
yolo_weights_path = os.path.join(os.path.dirname(__file__), "3_yolo_wound_detection_only", "weights", "best.pt")
yolo_model = YOLO(yolo_weights_path)

# Grad-CAM class
class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        self.target_layer.register_forward_hook(self.save_activation)
        self.target_layer.register_full_backward_hook(self.save_gradient)
        
    def save_activation(self, module, input, output):
        self.activations = output.detach()
        
    def save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()
        
    def __call__(self, x, class_idx=None):
        self.model.zero_grad()
        logits = self.model(x)
        if class_idx is None:
            class_idx = torch.argmax(logits, dim=1).item()
        
        score = logits[0, class_idx]
        score.backward()
        
        # Global Average Pooling on gradients
        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True) # [1, C, 1, 1]
        cam = torch.sum(weights * self.activations, dim=1, keepdim=True) # [1, 1, H, W]
        cam = nn.functional.relu(cam)
        cam = cam.squeeze().cpu().numpy()
        
        cam = cv2.resize(cam, (224, 224))
        cam_min, cam_max = np.min(cam), np.max(cam)
        if cam_max > cam_min:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = np.zeros_like(cam)
            
        return cam, class_idx, torch.softmax(logits, dim=1)[0].detach().cpu().numpy()

# Hook the final conv layer of EfficientNet-V2-Small
target_layer = cnn_model.backbone.features[-1]
gradcam = GradCAM(cnn_model, target_layer)

cnn_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Process sample test images
test_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datasets", "cnn1_denoised_split", "test")
sample_cases = [
    ("3_Demodicosis_Mange", "demodicosis_mange_xai.png"),
    ("6_Ringworm", "ringworm_xai.png"),
    ("2_Allergic_Dermatitis", "allergic_dermatitis_xai.png"),
    ("5_Healthy_Control", "healthy_control_xai.png"),
]

for cls_folder, out_name in sample_cases:
    cls_path = os.path.join(test_dir, cls_folder)
    if not os.path.exists(cls_path):
        continue
    img_files = [f for f in os.listdir(cls_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not img_files:
        continue
    img_path = os.path.join(cls_path, img_files[0])
    
    orig_img = Image.open(img_path).convert("RGB")
    orig_resized = orig_img.resize((224, 224))
    
    tensor_img = cnn_transform(orig_resized).unsqueeze(0).to(device)
    cam, pred_idx, probs = gradcam(tensor_img)
    
    heatmap = cv2.applyColorMap(np.uint8(255 * cam), cv2.COLORMAP_JET)
    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
    
    orig_np = np.array(orig_resized)
    overlay = np.uint8(0.55 * orig_np + 0.45 * heatmap)
    
    # Run YOLO on the same image
    yolo_res = yolo_model.predict(orig_resized, conf=0.25, verbose=False)
    yolo_rendered = orig_np.copy()
    has_wound = False
    for box in yolo_res[0].boxes:
        has_wound = True
        coords = [int(v) for v in box.xyxy[0].tolist()]
        conf = float(box.conf[0].item())
        cv2.rectangle(yolo_rendered, (coords[0], coords[1]), (coords[2], coords[3]), (255, 0, 0), 2)
        cv2.putText(yolo_rendered, f"Wound {conf:.2f}", (coords[0], max(coords[1]-5, 12)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
    
    # Combine original, Grad-CAM, and YOLO side-by-side
    combined = np.hstack([orig_np, overlay, yolo_rendered])
    save_path = os.path.join(OUT_DIR, out_name)
    Image.fromarray(combined).save(save_path)
    print(f"[XAI GENERATED] {out_name}: Pred={cnn_classes[pred_idx]} ({probs[pred_idx]*100:.1f}%), Wound={has_wound}")

# Also test on an actual wound test image
wound_test_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datasets", "yolo_merged_wounds", "test", "images")
if os.path.exists(wound_test_dir):
    wound_imgs = [f for f in os.listdir(wound_test_dir) if f.lower().endswith(('.jpg', '.png'))]
    if wound_imgs:
        w_path = os.path.join(wound_test_dir, wound_imgs[0])
        w_orig = Image.open(w_path).convert("RGB").resize((224, 224))
        w_tensor = cnn_transform(w_orig).unsqueeze(0).to(device)
        cam, pred_idx, probs = gradcam(w_tensor)
        
        heatmap = cv2.applyColorMap(np.uint8(255 * cam), cv2.COLORMAP_JET)
        heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
        w_np = np.array(w_orig)
        overlay = np.uint8(0.55 * w_np + 0.45 * heatmap)
        
        yolo_res = yolo_model.predict(w_orig, conf=0.25, verbose=False)
        yolo_rendered = w_np.copy()
        for box in yolo_res[0].boxes:
            coords = [int(v) for v in box.xyxy[0].tolist()]
            conf = float(box.conf[0].item())
            cv2.rectangle(yolo_rendered, (coords[0], coords[1]), (coords[2], coords[3]), (255, 0, 0), 2)
            cv2.putText(yolo_rendered, f"Wound {conf:.2f}", (coords[0], max(coords[1]-5, 12)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
        
        combined = np.hstack([w_np, overlay, yolo_rendered])
        save_path = os.path.join(OUT_DIR, "acute_trauma_wound_xai.png")
        Image.fromarray(combined).save(save_path)
        print(f"[XAI GENERATED] acute_trauma_wound_xai.png: CNN={cnn_classes[pred_idx]} ({probs[pred_idx]*100:.1f}%), YOLO detections={len(yolo_res[0].boxes)}")

print("[SUCCESS] All Explainable AI artifacts generated in model_pipeline/xai_results/")
