"""
MediPaw Unified REST Backend API Server.

Built with FastAPI & Uvicorn. Exposes REST endpoints for all MediPaw AI models:
- Eye CNN (Ocular Pathology)
- Skin CNN (Dermatological Pathology)
- YOLOv8 (Wound / Trauma Localization)
- U-Net (Wound Area Geometry)
- Thoracic CNN (Vertebral Heart Score & Radiographs)
- Multi-image Patient Intake Pipeline
"""

import os
import sys
import uuid
import shutil
import time
from typing import Optional, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)
for _p in [_BACKEND_DIR, _PROJECT_ROOT]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from backend.adapters import (
        run_eye_analysis,
        run_skin_analysis,
        run_wound_detection,
        run_wound_segmentation,
        run_thoracic_analysis,
        run_vit_fusion,
        UPLOAD_DIR,
        OUTPUT_DIR
    )
except ImportError:
    from adapters import (
        run_eye_analysis,
        run_skin_analysis,
        run_wound_detection,
        run_wound_segmentation,
        run_thoracic_analysis,
        run_vit_fusion,
        UPLOAD_DIR,
        OUTPUT_DIR
    )


app = FastAPI(
    title="MediPaw Veterinary AI Backend",
    description="Multi-Modal Veterinary Triage and Decision Support API",
    version="1.0.0"
)

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory for visualization overlays and uploaded previews
app.mount("/static", StaticFiles(directory=os.path.join(_BACKEND_DIR, "static")), name="static")


def save_upload_file(file: UploadFile) -> str:
    """Safely writes uploaded file to disk and returns its local path."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]:
        raise HTTPException(status_code=400, detail=f"Unsupported image format '{ext}'.")
    
    unique_name = f"{uuid.uuid4().hex[:12]}_{file.filename}"
    dest_path = os.path.join(UPLOAD_DIR, unique_name)
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return dest_path


@app.get("/api/health")
def health_check():
    """Returns system status and model readiness summary."""
    eye_ready = os.path.exists(os.path.join(_PROJECT_ROOT, "eyecnn", "models", "eye_cnn", "best_eye_model.pth"))
    yolo_ready = os.path.exists(os.path.join(_PROJECT_ROOT, "yolov8", "weights", "best.pt"))
    skin_ready = os.path.exists(os.path.join(_PROJECT_ROOT, "skincnn", "checkpoints", "best_skin_model.pth"))
    unet_ready = os.path.exists(os.path.join(_PROJECT_ROOT, "unet", "checkpoints", "best_model.pt"))
    thoracic_ready = os.path.exists(os.path.join(_PROJECT_ROOT, "thoraciccnn", "checkpoints", "best_thoracic_model.pth"))
    vit_ready = os.path.exists(os.path.join(_PROJECT_ROOT, "multimodal_vit", "checkpoints", "best_vit_model.pth"))

    return {
        "status": "online",
        "service": "MediPaw Veterinary AI Backend",
        "timestamp": time.time(),
        "disclaimer": "Clinical Decision-Support Prototype. All predictions must be confirmed by a veterinary clinician.",
        "models": {
            "eye_cnn": {"ready": eye_ready, "checkpoint": "best_eye_model.pth" if eye_ready else None},
            "yolov8_wound_detect": {"ready": yolo_ready, "checkpoint": "best.pt" if yolo_ready else None},
            "skin_cnn": {"ready": skin_ready, "status": "weights_missing_locally"},
            "unet_wound_segment": {"ready": unet_ready, "status": "untrained_fallback"},
            "thoracic_cnn": {"ready": thoracic_ready, "status": "unannotated_data_prototype"},
            "multimodal_vit": {"ready": vit_ready, "status": "architecture_prototype" if not vit_ready else "trained"}
        }
    }


@app.post("/api/predict/eye")
async def api_predict_eye(file: UploadFile = File(...)):
    """Run ocular pathology classification via Eye CNN."""
    saved_path = save_upload_file(file)
    result = run_eye_analysis(saved_path)
    result["image_url"] = f"/static/uploads/{os.path.basename(saved_path)}"
    return JSONResponse(content=result)


@app.post("/api/predict/skin")
async def api_predict_skin(file: UploadFile = File(...)):
    """Run dermatological pathology analysis via Skin CNN."""
    saved_path = save_upload_file(file)
    result = run_skin_analysis(saved_path)
    result["image_url"] = f"/static/uploads/{os.path.basename(saved_path)}"
    return JSONResponse(content=result)


@app.post("/api/predict/wound-detect")
async def api_predict_wound(file: UploadFile = File(...)):
    """Detect acute wounds and lesions via YOLOv8."""
    saved_path = save_upload_file(file)
    result = run_wound_detection(saved_path)
    result["image_url"] = f"/static/uploads/{os.path.basename(saved_path)}"
    return JSONResponse(content=result)


@app.post("/api/predict/wound-segment")
async def api_predict_segmentation(file: UploadFile = File(...)):
    """Segment wound region and compute surface area percentage via U-Net + YOLOv8."""
    saved_path = save_upload_file(file)
    result = run_wound_segmentation(saved_path)
    result["image_url"] = f"/static/uploads/{os.path.basename(saved_path)}"
    return JSONResponse(content=result)


@app.post("/api/predict/thoracic")
async def api_predict_thoracic(file: UploadFile = File(...)):
    """Analyze canine thoracic radiograph via Thoracic CNN."""
    saved_path = save_upload_file(file)
    result = run_thoracic_analysis(saved_path)
    result["image_url"] = f"/static/uploads/{os.path.basename(saved_path)}"
    return JSONResponse(content=result)


@app.post("/api/predict/fusion")
async def api_predict_fusion(file: UploadFile = File(...), modality: str = Form("ocular")):
    """
    Run Multi-Modal ViT fusion using a single image.
    The image is passed through the appropriate CNN (selected by 'modality') to extract
    a feature embedding, then fused by the ViT.

    modality: 'ocular' | 'thoracic'
    """
    saved_path = save_upload_file(file)
    if modality == "ocular":
        individual_result = run_eye_analysis(saved_path)
    elif modality == "thoracic":
        individual_result = run_thoracic_analysis(saved_path)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported modality '{modality}'. Choose 'ocular' or 'thoracic'.")
    
    individual_result["image_url"] = f"/static/uploads/{os.path.basename(saved_path)}"
    fusion_result = run_vit_fusion([individual_result])
    return JSONResponse(content={
        "status": "ok",
        "modality_result": individual_result,
        "fusion_result": fusion_result
    })


@app.post("/api/intake")
async def api_patient_intake(
    species: str = Form("Dog"),
    age: str = Form(""),
    shelter: str = Form(""),
    weight: str = Form(""),
    notes: str = Form(""),
    skin_image: Optional[UploadFile] = File(None),
    ocular_image: Optional[UploadFile] = File(None),
    membrane_image: Optional[UploadFile] = File(None),
    thoracic_image: Optional[UploadFile] = File(None),
):
    """
    Unified multi-image intake packet processing.
    Runs active models on their designated images and aggregates results.
    """
    case_id = f"MP-{uuid.uuid4().hex[:6].upper()}"
    start_time = time.time()
    model_results = []
    
    # 1. Skin & Wound Processing (YOLOv8 + Skin CNN + U-Net)
    if skin_image is not None and skin_image.filename:
        skin_path = save_upload_file(skin_image)
        skin_res = run_skin_analysis(skin_path)
        skin_res["image_url"] = f"/static/uploads/{os.path.basename(skin_path)}"
        model_results.append(skin_res)

        yolo_res = run_wound_detection(skin_path)
        yolo_res["image_url"] = f"/static/uploads/{os.path.basename(skin_path)}"
        model_results.append(yolo_res)

        unet_res = run_wound_segmentation(skin_path)
        unet_res["image_url"] = f"/static/uploads/{os.path.basename(skin_path)}"
        model_results.append(unet_res)

    # 2. Ocular Processing (Eye CNN)
    if ocular_image is not None and ocular_image.filename:
        ocular_path = save_upload_file(ocular_image)
        eye_res = run_eye_analysis(ocular_path)
        eye_res["image_url"] = f"/static/uploads/{os.path.basename(ocular_path)}"
        model_results.append(eye_res)

    # 3. Mucous Membrane / Gums Processing
    if membrane_image is not None and membrane_image.filename:
        membrane_path = save_upload_file(membrane_image)
        # Note: Gum color CNN not yet trained separately; provide prototype status
        model_results.append({
            "status": "unvalidated_prototype",
            "model_name": "CNN 3 (Mucous Membrane / Perfusion)",
            "prediction": "Evaluation Pending Separate Gum Classifier Weights",
            "confidence": None,
            "model_ready": False,
            "is_trained": False,
            "image_url": f"/static/uploads/{os.path.basename(membrane_path)}",
            "warnings": ["Mucous membrane color classifier is not yet trained with verified clinical perfusion labels."]
        })

    # 4. Thoracic X-ray Processing (Thoracic CNN)
    if thoracic_image is not None and thoracic_image.filename:
        thoracic_path = save_upload_file(thoracic_image)
        thoracic_res = run_thoracic_analysis(thoracic_path)
        thoracic_res["image_url"] = f"/static/uploads/{os.path.basename(thoracic_path)}"
        model_results.append(thoracic_res)

    # 5. Multi-Modal ViT Fusion (runs after all individual models)
    if model_results:
        vit_res = run_vit_fusion(model_results)
        model_results.append(vit_res)

    # Triage decision logic (rule-based clinical safety fallback, explicitly noted)
    # A true trained ViT fusion model is designated for a later phase
    has_ulcer = any(
        m.get("model_name", "").startswith("Eye CNN") and "Ulcer" in str(m.get("prediction", ""))
        for m in model_results
    )
    wound_count = sum(
        m.get("detection_count", 0) for m in model_results if "detection_count" in m
    )

    if has_ulcer or wound_count >= 3:
        suggested_priority = "High"
        triage_rationale = (
            f"Automated priority rule triggered: "
            f"{'Ocular ulcer detected' if has_ulcer else ''} "
            f"{f'Multiple wound foci detected ({wound_count})' if wound_count >= 3 else ''}. "
            f"Requires prompt veterinary evaluation."
        )
    elif wound_count > 0:
        suggested_priority = "Medium"
        triage_rationale = f"Single acute wound lesion localized. Patient flagged for regular queue review."
    else:
        suggested_priority = "Low"
        triage_rationale = "No acute ocular threats or high-confidence trauma wounds detected."

    elapsed = time.time() - start_time

    return {
        "status": "ok",
        "case_id": case_id,
        "patient": {
            "species": species,
            "age": age,
            "shelter": shelter,
            "weight": weight,
            "notes": notes
        },
        "priority": suggested_priority,
        "triage_rationale": triage_rationale,
        "processed_time_sec": round(elapsed, 2),
        "models": model_results,
        "disclaimer": (
            "Decision-Support Prototype: MediPaw does not provide final clinical diagnoses. "
            "A Multi-Modal Vision Transformer (ViT) fusion layer will combine validated feature embeddings in a subsequent phase."
        )
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
