import cv2
import numpy as np
from ultralytics import YOLO
import tempfile
import os

model_paths = {
    "pol": "pol.pt",
    "hyn": "hyn.pt",
    "lad": "lad.pt",
    "szk": "szk.pt",
    "pdj": "pdj.pt",
    "kia": "kia.pt"
}

classification_model = YOLO("class.pt")

def classify_brand(image_bytes: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        results = classification_model(tmp_path)
        pred = int(results[0].probs.top1)
        if pred == 0: return "hyn"
        elif pred == 1: return "kia"
        elif pred == 2: return "lad"
        elif pred == 3: return "none"
        elif pred == 4: return "pdj"
        elif pred == 5: return "pol"
        else: return "szk"
    finally:
        os.remove(tmp_path)

def run_segmentation(image_bytes: bytes, brand: str) -> bytes:
    if brand not in model_paths:
        raise ValueError(f"No segmentation model found for brand '{brand}'")
    
    model = YOLO(model_paths[brand])

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    image = cv2.imread(tmp_path)
    results = model(image)
    os.remove(tmp_path)

    masks = results[0].masks.xy
    classes = results[0].boxes.cls.cpu().numpy().astype(int)

    output_mask_details = np.zeros((image.shape[0], image.shape[1]), dtype=np.uint8)
    output_mask_defects = np.zeros((image.shape[0], image.shape[1]), dtype=np.uint8)
    
    for mask, class_id in zip(masks, classes):  
        mask = np.array(mask).astype(np.int32)
        if class_id <= 73:
            cv2.fillPoly(output_mask_details, [mask], int(class_id + 1))
        elif class_id == 74:
            cv2.fillPoly(output_mask_defects, [mask], 1)
        elif class_id == 75:
            cv2.fillPoly(output_mask_defects, [mask], 2)
    
    output_mask = np.stack((output_mask_details, output_mask_defects, np.zeros_like(output_mask_details)), axis=-1)
    output_mask_rgb = cv2.cvtColor(output_mask, cv2.COLOR_BGR2RGB)

    _, png_bytes = cv2.imencode(".png", output_mask_rgb)
    return png_bytes.tobytes()
