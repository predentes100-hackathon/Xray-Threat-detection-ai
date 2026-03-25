"""
train_yolo.py

This script implements a pipeline to train a YOLOv11 model for the Shieldex backend.
It assumes you are using a Hugging Face object detection dataset.

Features:
1. Downloads a PIDray dataset from Hugging Face.
2. Applies Contrast Limited Adaptive Histogram Equalization (CLAHE) to images.
3. Formats the data into the structure required by YOLO.
4. Trains a YOLOv11 model and outputs a .pt file.
5. Calculates mAP, Precision, and Recall.

Ensure you install dependencies inside your backend virtual environment:
    pip install ultralytics datasets opencv-python-headless numpy pyyaml
"""
import os
import cv2
import yaml
import numpy as np
from pathlib import Path
from datasets import load_dataset
from ultralytics import YOLO

# Configuration
# "Voxel51/PIDray" represents the official dataset format on HF.
# You can update dataset_name, but be mindful of the bounding box format logic.
HF_DATASET_NAME = "Voxel51/PIDray" 
BASE_DIR = Path("hf_yolo_dataset")
IMAGES_DIR = BASE_DIR / "images"
LABELS_DIR = BASE_DIR / "labels"

def apply_clahe(image_np):
    """
    Applies Contrast Limited Adaptive Histogram Equalization (CLAHE) 
    to enhance image contrast and x-ray surface details.
    """
    # Convert RGB (from PIL) to BGR for OpenCV
    bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
    
    # Convert to LAB color space
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE to the Lightness channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    
    # Merge and convert back
    merged = cv2.merge((cl, a, b))
    enhanced_bgr = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    enhanced_rgb = cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2RGB)
    
    return enhanced_rgb

def prepare_split(dataset_split, split_name, class_names):
    """
    Iterates through HF dataset split, applies CLAHE, and saves YOLO format.
    """
    img_dir = IMAGES_DIR / split_name
    lbl_dir = LABELS_DIR / split_name
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Processing {split_name} split ({len(dataset_split)} images)...")
    
    for i, item in enumerate(dataset_split):
        try:
            pil_image = item["image"]
            width, height = pil_image.size
            img_np = np.array(pil_image)
            
            # 1. Apply CLAHE Enhancement
            enhanced_img = apply_clahe(img_np)
            
            # Save Image (convert to BGR for imwrite)
            img_path = img_dir / f"{split_name}_{i}.jpg"
            cv2.imwrite(str(img_path), cv2.cvtColor(enhanced_img, cv2.COLOR_RGB2BGR))
            
            # 2. Save Labels (YOLO format: class_id center_x center_y width height)
            lbl_path = lbl_dir / f"{split_name}_{i}.txt"
            with open(lbl_path, "w") as f:
                if "objects" in item:
                    objects = item["objects"]
                    for bbox, cat_id in zip(objects["bbox"], objects["category"]):
                        # Assuming COCO format bbox: [x_min, y_min, width, height]
                        x_min, y_min, w, h = bbox
                        
                        # Normalize coordinates
                        x_center = (x_min + w / 2.0) / width
                        y_center = (y_min + h / 2.0) / height
                        norm_w = w / width
                        norm_h = h / height
                        
                        # Clip to bounds [0, 1]
                        x_center = max(0.0, min(1.0, x_center))
                        y_center = max(0.0, min(1.0, y_center))
                        norm_w = max(0.0, min(1.0, norm_w))
                        norm_h = max(0.0, min(1.0, norm_h))
                        
                        f.write(f"{cat_id} {x_center} {y_center} {norm_w} {norm_h}\n")
        except Exception as e:
            if i < 3:
                print(f"Warning: skipped index {i} due to Error: {e}")
            continue

def create_yaml(class_names):
    """Generates the data.yaml file that YOLO uses for dataset mapping."""
    yaml_path = BASE_DIR / "dataset.yaml"
    data = {
        "path": str(BASE_DIR.absolute()),
        "train": "images/train",
        "val": "images/val",
        "names": {i: name for i, name in enumerate(class_names)}
    }
    with open(yaml_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
    return yaml_path

def main():
    print("--- 1. Loading Hugging Face Dataset ---")
    print(f"Loading '{HF_DATASET_NAME}'...")
    try:
        dataset = load_dataset(HF_DATASET_NAME)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        print("Tip: If the dataset requires authentication, run 'huggingface-cli login'.")
        return

    # Standard HF splits
    train_split = dataset.get("train")
    val_split = dataset.get("validation") or dataset.get("test")
    
    if not train_split:
        print("Error: Could not find 'train' split!")
        return

    # To run a quick test, we select a small subset.
    # To train on the FULL dataset, comment out or remove the `.select(...)` lines below.
    print("Restricting to a small subset (100 images) for quick demonstration...")
    train_subset = train_split.select(range(min(100, len(train_split))))
    if val_split:
        val_subset = val_split.select(range(min(20, len(val_split))))
    else:
        val_subset = None

    # Extract class names safely
    try:
        class_names = train_split.features["objects"].feature["category"].names
    except:
        class_names = ["Threat_Item"] # Fallback if specific ontology isn't populated

    print("\n--- 2. Applying CLAHE Preprocessing & Formatting ---")
    prepare_split(train_subset, "train", class_names)
    if val_subset:
        prepare_split(val_subset, "val", class_names)

    yaml_path = create_yaml(class_names)

    print("\n--- 3. Initializing and Training YOLOv11 ---")
    # Using 'n' for nano model. Ensure ultralytics package is up to date for v11 support
    model = YOLO("yolo11n.pt") 
    
    # Run Training
    results = model.train(
        data=str(yaml_path),
        epochs=5,       # Increase (e.g., 50-100) for real long-term training
        batch=4,        # Low batch size to prevent OOM
        imgsz=640,
        project="models",
        name="pidray_detector"
    )

    print("\n--- 4. Evaluating Metrics (mAP, Precision, Recall) ---")
    # Evaluate performance on validation dataset
    metrics = model.val()
    
    try:
        # Access Bounding Box ('B') metrics natively
        precision = metrics.results_dict['metrics/precision(B)']
        recall = metrics.results_dict['metrics/recall(B)']
        map50 = metrics.results_dict['metrics/mAP50(B)']
        map50_95 = metrics.results_dict['metrics/mAP50-95(B)']

        print(f"\n✅ --- Validation Metrics ---")
        print(f"Precision: {precision:.4f}")
        print(f"Recall:    {recall:.4f}")
        print(f"mAP@50:    {map50:.4f}")
        print(f"mAP@50-95: {map50_95:.4f}")
    except KeyError:
        print("Metrics structure varied; fallback to terminal log. Check the table above.")

    # Show location of output .pt weights
    model_file_path = Path("models/pidray_detector/weights/best.pt")
    if model_file_path.exists():
        print(f"\n[Success] Your trained YOLO model (.pt) has been saved at:")
        print(f"--> {model_file_path.absolute()}")

if __name__ == "__main__":
    main()
