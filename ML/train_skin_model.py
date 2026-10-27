"""
Skin Disease Classifier
========================
Trains a model to identify common skin conditions from photos.

Pipeline:
    Image → MobileNetV2 (feature extractor) → Ensemble classifier → Disease label

Classes (10):
    eczema, melanoma, atopic_dermatitis, basal_cell_carcinoma,
    melanocytic_nevi, benign_keratosis, psoriasis,
    seborrheic_keratosis, fungal_infection, viral_infection

Dataset structure expected:
    D:/village-development-platform/ML/skin/IMG_CLASSES/
        1. Eczema 1677/          ← images directly inside
        2. Melanoma 15.75k/
        3. Atopic Dermatitis - 1.25k/
        ... etc

Usage (run from D:/village-development-platform/ML/ with venv active):
    python train_skin_model.py
"""

import os
import numpy as np
import pandas as pd
import joblib
import torch
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image, UnidentifiedImageError
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report, accuracy_score, f1_score
from sklearn.model_selection import train_test_split

# -----------------------------------------------------------------------------
# SECTION 1: CONFIGURATION
# -----------------------------------------------------------------------------

# Root folder containing the 10 condition subfolders
IMG_CLASSES_DIR = r"D:\village-development-platform\ML\skin\IMG_CLASSES"

# Where to save the trained model
MODEL_SAVE_PATH = r"D:\village-development-platform\ML\model_skin.joblib"

# Cache file — saves extracted features so you don't reprocess 40k images
# if training crashes or you want to retrain the classifier
CACHE_PATH = "skin_features_cache.npz"

# Batch size for MobileNetV2 feature extraction
# 16 is safe for most machines; reduce to 8 if you get memory errors
BATCH_SIZE = 16

# -----------------------------------------------------------------------------
# SECTION 2: CLASS MAPPING
# Folder name prefix → clean class label we use in predictions
# -----------------------------------------------------------------------------

# Maps the NUMBER prefix of each folder to a clean label
# This is more reliable than matching full folder names which may vary
FOLDER_TO_CLASS = {
    "1":  "eczema",
    "2":  "melanoma",
    "3":  "atopic_dermatitis",
    "4":  "basal_cell_carcinoma",
    "5":  "melanocytic_nevi",
    "6":  "benign_keratosis",
    "7":  "psoriasis",
    "8":  "seborrheic_keratosis",
    "9":  "fungal_infection",
    "10": "viral_infection",
}

# Human-readable names shown in the app
CLASS_DISPLAY_NAMES = {
    "eczema":                "Eczema",
    "melanoma":              "Melanoma",
    "atopic_dermatitis":     "Atopic Dermatitis",
    "basal_cell_carcinoma":  "Basal Cell Carcinoma",
    "melanocytic_nevi":      "Melanocytic Nevi (Mole)",
    "benign_keratosis":      "Benign Keratosis",
    "psoriasis":             "Psoriasis / Lichen Planus",
    "seborrheic_keratosis":  "Seborrheic Keratosis",
    "fungal_infection":      "Fungal Infection (Tinea / Ringworm)",
    "viral_infection":       "Viral Infection (Warts / Molluscum)",
}

# -----------------------------------------------------------------------------
# SECTION 3: IMAGE PREPROCESSING
# Same normalization as used during MobileNetV2's ImageNet training
# -----------------------------------------------------------------------------

preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])

# -----------------------------------------------------------------------------
# SECTION 4: DISCOVER ALL IMAGES
# Walks the IMG_CLASSES folder, maps each image to its class label
# -----------------------------------------------------------------------------

def discover_images(img_classes_dir):
    """
    Scans IMG_CLASSES_DIR and returns a DataFrame with columns:
        image_path  — full path to the image file
        label       — clean class label (e.g. "eczema")
    """
    records = []
    skipped_folders = []

    for folder_name in sorted(os.listdir(img_classes_dir)):
        folder_path = os.path.join(img_classes_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue

        # Extract the number prefix (e.g. "1" from "1. Eczema 1677")
        prefix = folder_name.split(".")[0].strip()

        if prefix not in FOLDER_TO_CLASS:
            skipped_folders.append(folder_name)
            continue

        label = FOLDER_TO_CLASS[prefix]

        for fname in os.listdir(folder_path):
            if fname.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".webp")):
                records.append({
                    "image_path": os.path.join(folder_path, fname),
                    "label": label,
                })

    df = pd.DataFrame(records)

    print(f"\nFound {len(df)} images across {df['label'].nunique()} classes")
    print("\nImages per class:")
    print(df["label"].value_counts().to_string())

    if skipped_folders:
        print(f"\nSkipped folders (no mapping): {skipped_folders}")

    return df


# -----------------------------------------------------------------------------
# SECTION 5: LOAD MOBILENETV2 FEATURE EXTRACTOR
# -----------------------------------------------------------------------------

def load_feature_extractor():
    """
    Loads MobileNetV2 pretrained on ImageNet.
    Removes the classifier head → outputs 1280 features per image.
    Freezes all weights — we are NOT training this network.
    """
    print("\nLoading MobileNetV2 pretrained weights...")
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    model.classifier = torch.nn.Identity()
    for param in model.parameters():
        param.requires_grad = False
    model.eval()
    print("MobileNetV2 ready.")
    return model


# -----------------------------------------------------------------------------
# SECTION 6: EXTRACT FEATURES
# Processes all images in batches → 1280-number fingerprint per image
# -----------------------------------------------------------------------------

def extract_features(model, image_paths, batch_size=16):
    """
    Args:
        model: MobileNetV2 feature extractor
        image_paths: list of absolute paths to images
        batch_size: number of images to process at once

    Returns:
        numpy array of shape (num_images, 1280)
        valid_mask: boolean array — False for images that failed to load
    """
    all_features = []
    valid_mask = []
    total = len(image_paths)

    print(f"\nExtracting features from {total} images...")
    print("This is the slow part — expect 2-5 hours on CPU.")
    print("Features will be cached so you never need to do this again.\n")

    with torch.no_grad():
        for i in range(0, total, batch_size):
            batch_paths = image_paths[i: i + batch_size]
            batch_tensors = []
            batch_valid = []

            for img_path in batch_paths:
                try:
                    img = Image.open(img_path).convert("RGB")
                    tensor = preprocess(img)
                    batch_tensors.append(tensor)
                    batch_valid.append(True)
                except (UnidentifiedImageError, OSError, Exception):
                    # Skip corrupted or unreadable images
                    batch_valid.append(False)

            valid_mask.extend(batch_valid)

            if not batch_tensors:
                continue

            batch_tensor = torch.stack(batch_tensors)
            features = model(batch_tensor)
            all_features.append(features.numpy())

            processed = min(i + batch_size, total)
            percent = (processed / total) * 100
            # Print progress every 5% to avoid flooding the terminal
            if int(percent) % 5 == 0 or processed == total:
                valid_so_far = sum(valid_mask)
                print(f"  {processed}/{total} images ({percent:.1f}%) — {valid_so_far} valid")

    X = np.vstack(all_features)
    return X, np.array(valid_mask)


# -----------------------------------------------------------------------------
# SECTION 7: TRAIN ENSEMBLE CLASSIFIER
# LR + Random Forest + SVM voting together
# class_weight=balanced handles the heavy class imbalance (Melanoma >> Eczema)
# -----------------------------------------------------------------------------

def train_classifier(X_train, y_train):
    print("\nTraining ensemble classifier (LR + Random Forest + SVM)...")
    print("class_weight=balanced — handles imbalance between classes")
    print("Expected time: 20-40 minutes on CPU.\n")

    lr = LogisticRegression(
        max_iter=1000,
        C=1.0,
        class_weight="balanced",
        solver="lbfgs",
        n_jobs=-1,
    )

    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    svm = CalibratedClassifierCV(
        LinearSVC(
            max_iter=2000,
            class_weight="balanced",
            random_state=42,
        )
    )

    ensemble = VotingClassifier(
        estimators=[("lr", lr), ("rf", rf), ("svm", svm)],
        voting="soft",
        n_jobs=-1,
    )

    ensemble.fit(X_train, y_train)
    print("Ensemble training complete.")
    return ensemble


# -----------------------------------------------------------------------------
# SECTION 8: EVALUATE
# -----------------------------------------------------------------------------

def evaluate(clf, X_test, y_test):
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)

    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)

    print(f"\nOverall Accuracy : {accuracy * 100:.2f}%")
    print(f"Macro F1 Score   : {macro_f1:.3f}")
    print("\nPer-class breakdown:")
    print(classification_report(
        y_test, y_pred,
        target_names=[CLASS_DISPLAY_NAMES.get(c, c) for c in sorted(set(y_test))],
        zero_division=0,
    ))


# -----------------------------------------------------------------------------
# SECTION 9: MAIN
# -----------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("SKIN DISEASE CLASSIFIER — TRAINING PIPELINE")
    print("=" * 60)

    # Step 1: Discover all images
    df = discover_images(IMG_CLASSES_DIR)

    if len(df) == 0:
        print("ERROR: No images found. Check IMG_CLASSES_DIR path.")
        return

    # Step 2: Load from cache or extract features
    if os.path.exists(CACHE_PATH):
        print(f"\nFound cached features at {CACHE_PATH} — loading instantly...")
        cache = np.load(CACHE_PATH, allow_pickle=True)
        X = cache["X"]
        y = cache["y"]
        print(f"Loaded {X.shape[0]} image features from cache.")
    else:
        model = load_feature_extractor()
        X, valid_mask = extract_features(model, df["image_path"].tolist(), BATCH_SIZE)
        y = df["label"].values[valid_mask]

        print(f"\nSaving features to cache: {CACHE_PATH}")
        np.savez(CACHE_PATH, X=X, y=y)
        print("Cache saved — future runs will skip feature extraction.")

    print(f"\nFeature matrix shape: {X.shape}")
    print(f"(rows=images, cols=features per image)")

    # Step 3: Train/test split — stratified to keep class ratios equal
    print("\nSplitting: 80% train / 20% test (stratified)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Training set : {len(X_train)} images")
    print(f"Test set     : {len(X_test)} images")

    # Step 4: Train
    clf = train_classifier(X_train, y_train)

    # Step 5: Evaluate
    evaluate(clf, X_test, y_test)

    # Step 6: Refit on full dataset before saving
    print("\nRefitting on full dataset before saving...")
    clf.fit(X, y)

    # Step 7: Save everything needed for inference
    save_data = {
        "classifier": clf,
        "feature_extractor": "mobilenet_v2",
        "input_size": 224,
        "classes": list(FOLDER_TO_CLASS.values()),
        "class_display_names": CLASS_DISPLAY_NAMES,
    }
    joblib.dump(save_data, MODEL_SAVE_PATH)
    print(f"\nModel saved to: {MODEL_SAVE_PATH}")
    print("\nDone! Restart the FastAPI server to activate skin screening.")


if __name__ == "__main__":
    main()
