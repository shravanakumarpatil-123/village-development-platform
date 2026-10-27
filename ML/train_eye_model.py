"""
Diabetic Retinopathy Classifier
================================
This script trains a model to predict diabetic retinopathy severity
from retinal images using:
    - MobileNetV2 as a feature extractor (pretrained on ImageNet)
    - Logistic Regression as the final classifier (scikit-learn)

Grades:
    0 = No DR (healthy)
    1 = Mild
    2 = Moderate
    3 = Severe
    4 = Proliferative DR (most serious)

Run this script from inside D:\village-development-platform\ML\
with the venv activated:
    python train_eye_model.py
"""

import os
import numpy as np
import pandas as pd
import joblib
import torch
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: CONFIGURATION
# Tell the script where your data lives and where to save the model.
# ─────────────────────────────────────────────────────────────────────────────

# Path to the folder containing all retinal images
IMAGE_DIR = r"D:\village-development-platform\ML\train_images"

# Path to train.csv — the file that maps image filename → diagnosis grade
CSV_PATH = r"D:\village-development-platform\ML\train.csv"

# Where to save the trained model after training is complete
MODEL_SAVE_PATH = r"D:\village-development-platform\ML\model_eye.joblib"

# Cache file for extracted image features, saved to disk to avoid reprocessing.
CACHE_PATH = "features_cache.npz"

# How many images to process at once before moving to the next batch.
# Lower = uses less RAM but takes longer. 16 is safe for most machines.
BATCH_SIZE = 16

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: IMAGE PREPROCESSING
# MobileNetV2 was trained expecting images in a specific format.
# We must convert our images to match that format before feeding them in.
# ─────────────────────────────────────────────────────────────────────────────

# transforms.Compose chains multiple operations together.
# Each image goes through ALL of these steps in order:
preprocess = transforms.Compose([

    # Step 1: Resize to 224×224 pixels
    # MobileNetV2 was designed for 224×224 input — non-negotiable.
    # Our retinal images could be 1000×1000 or larger, so we shrink them.
    transforms.Resize((224, 224)),

    # Step 2: Convert to a PyTorch tensor (a multi-dimensional array)
    # Changes shape from (224, 224, 3) → (3, 224, 224)
    # and pixel values from 0-255 → 0.0-1.0
    transforms.ToTensor(),

    # Step 3: Normalize pixel values
    # These specific mean/std values ([0.485, 0.456, 0.406] and [0.229, 0.224, 0.225])
    # are the exact values computed from the ImageNet dataset that MobileNetV2 was
    # trained on. We MUST use the same values so the network sees input in the
    # same range it was trained on — otherwise it would be like giving someone
    # instructions in a different unit system (feet vs meters).
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: LOAD MOBILENETV2 (FEATURE EXTRACTOR)
# We load the pretrained model, remove its final classification layer,
# and freeze all its weights so nothing changes during our training.
# ─────────────────────────────────────────────────────────────────────────────

def load_feature_extractor():
    """
    Loads MobileNetV2 pretrained on ImageNet.
    Removes the final 'classifier' layer so output is 1280 features per image.
    Freezes all weights — we are NOT training this network, just using it.
    """
    print("Loading MobileNetV2 pretrained weights...")

    # weights=DEFAULT means use the best available pretrained weights.
    # First time you run this, it downloads ~14MB from the internet.
    # After that it's cached locally so no re-download needed.
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)

    # MobileNetV2 has two main parts:
    #   model.features   → the convolutional layers that extract features
    #   model.classifier → the final layer that maps features to 1000 classes
    #
    # We only want model.features. We replace the classifier with an
    # "identity" function — meaning the output flows through unchanged.
    model.classifier = torch.nn.Identity()

    # torch.no_grad() tells PyTorch: "don't track gradients for this model"
    # Gradients are what allow a network to learn (update its weights).
    # Since we're NOT training MobileNetV2, we don't need them.
    # This saves memory and makes feature extraction faster.
    for param in model.parameters():
        param.requires_grad = False

    # model.eval() switches the model to evaluation mode.
    # Some layers (like Dropout and BatchNorm) behave differently
    # during training vs evaluation. We want evaluation behavior.
    model.eval()

    print("MobileNetV2 loaded and ready.")
    return model


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: EXTRACT FEATURES FROM ALL IMAGES
# Loop through every image, preprocess it, pass it through MobileNetV2,
# and collect the 1280-number fingerprint for each image.
# ─────────────────────────────────────────────────────────────────────────────

def extract_features(model, image_ids, image_dir, batch_size=16):
    """
    Takes a list of image filenames, processes them in batches,
    and returns a numpy array of shape (num_images, 1280).

    Why batches?
        Processing one image at a time is slow.
        Processing all at once might run out of RAM.
        Batches of 16 strike a balance.
    """
    all_features = []
    total = len(image_ids)

    print(f"\nExtracting features from {total} images...")
    print("This is the slow part on CPU — expect 15-40 minutes depending on your machine.")
    print("Progress will update every batch.\n")

    # torch.no_grad() context manager: within this block, PyTorch won't
    # store gradient information, saving significant memory.
    with torch.no_grad():
        for i in range(0, total, batch_size):
            batch_ids = image_ids[i: i + batch_size]
            batch_tensors = []

            for img_id in batch_ids:
                img_path = os.path.join(image_dir, img_id + ".png")

                # Some datasets use .jpg instead of .png — handle both
                if not os.path.exists(img_path):
                    img_path = os.path.join(image_dir, img_id + ".jpg")

                # Open image with Pillow.
                # .convert("RGB") ensures 3 channels (R, G, B).
                # Some images may be grayscale (1 channel) or RGBA (4 channels)
                # — this forces them all to RGB so shapes are consistent.
                img = Image.open(img_path).convert("RGB")

                # Apply our preprocessing pipeline defined in SECTION 2.
                # Output shape: (3, 224, 224) — a single image tensor
                tensor = preprocess(img)
                batch_tensors.append(tensor)

            # torch.stack combines a list of (3, 224, 224) tensors
            # into a single (batch_size, 3, 224, 224) tensor.
            # This is the format MobileNetV2 expects as input.
            batch_tensor = torch.stack(batch_tensors)

            # Pass the batch through MobileNetV2.
            # Output shape: (batch_size, 1280)
            # Each image is now represented by 1280 numbers.
            features = model(batch_tensor)

            # .numpy() converts PyTorch tensor → numpy array
            # We collect numpy arrays instead of tensors because
            # scikit-learn works with numpy, not PyTorch.
            all_features.append(features.numpy())

            # Progress indicator
            processed = min(i + batch_size, total)
            percent = (processed / total) * 100
            print(f"  Processed {processed}/{total} images ({percent:.1f}%)")

    # np.vstack stacks all our batches into one big array.
    # Shape: (total_images, 1280)
    return np.vstack(all_features)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: TRAIN THE CLASSIFIER
# Now that we have fingerprints for every image, we train a
# Logistic Regression to map fingerprints → grades 0-4.
# ─────────────────────────────────────────────────────────────────────────────

def train_classifier(X_train, y_train):
    """
    FIX A: class_weight="balanced"
    --------------------------------
    Tells every classifier: "treat rare grades as more important."
    Mathematically it multiplies the penalty for misclassifying a rare grade
    by (total_samples / (n_classes * samples_in_that_grade)).

    Example: Grade 3 has 39 samples vs Grade 0 with 361.
    With balanced weights, a grade 3 mistake costs ~9x more than a grade 0
    mistake — so the model tries much harder to get grade 3 right.

    FIX B: Ensemble of 3 classifiers (Voting Classifier)
    -------------------------------------------------------
    Instead of relying on one classifier, we train three different ones
    and let them VOTE on the final prediction.

    The 3 classifiers:
    1. Logistic Regression — good at linear patterns, fast
    2. Random Forest — 100 decision trees voting together, good at
       complex non-linear patterns, handles imbalance well
    3. Linear SVC — Support Vector Machine, draws the best possible
       boundary between classes in high-dimensional space (our 1280 features)

    Why voting works:
    Each classifier makes different kinds of mistakes. When they vote,
    the correct answer usually wins even if one classifier is wrong.
    This is called an ensemble — the same principle as asking 3 doctors
    instead of 1.

    voting="soft" means they vote using confidence scores (probabilities)
    rather than just yes/no — more nuanced and usually more accurate.
    """
    print("\nTraining ensemble classifier (3 models voting together)...")
    print("Fix A: class_weight=balanced — rare grades get more attention")
    print("Fix B: 3 classifiers voting — Random Forest + LR + SVM")
    print("Expected time: 5-10 minutes on CPU.\n")

    # Classifier 1: Logistic Regression with balanced weights
    lr = LogisticRegression(
        max_iter=1000,
        C=1.0,
        solver="lbfgs",
        class_weight="balanced",   # FIX A
        n_jobs=-1,
    )

    # Classifier 2: Random Forest with balanced weights
    # n_estimators=100 → 100 decision trees vote together
    # max_depth=20 → each tree can go 20 levels deep
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        class_weight="balanced",   # FIX A
        random_state=42,
        n_jobs=-1,
    )

    # Classifier 3: Linear SVC (SVM)
    # SVM finds the widest possible margin between classes
    # CalibratedClassifierCV wraps it to produce probabilities
    # (needed for soft voting)
    svm = CalibratedClassifierCV(
        LinearSVC(
            max_iter=2000,
            class_weight="balanced",   # FIX A
            random_state=42,
        )
    )

    # Voting Classifier: combines all three
    # voting="soft" → uses predicted probabilities, not just class labels
    ensemble = VotingClassifier(
        estimators=[
            ("lr", lr),
            ("rf", rf),
            ("svm", svm),
        ],
        voting="soft",
        n_jobs=-1,
    )

    ensemble.fit(X_train, y_train)
    print("\nEnsemble training complete.")
    return ensemble


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: EVALUATE THE MODEL
# Check how well the model performs on images it HASN'T seen during training.
# This is the honest measure of real-world performance.
# ─────────────────────────────────────────────────────────────────────────────

def evaluate(clf, X_test, y_test):
    """
    Runs predictions on the test set and prints a full report.

    Key metrics explained:
        Accuracy    → % of images classified correctly overall
        Precision   → of all images predicted as grade X, how many actually are?
        Recall      → of all actual grade X images, how many did we catch?
        F1-score    → harmonic mean of precision and recall (balanced metric)
        Support     → how many images of each grade exist in the test set
    """
    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)

    y_pred = clf.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nOverall Accuracy: {accuracy * 100:.2f}%")
    print("\nPer-grade breakdown:")
    print(classification_report(
        y_test,
        y_pred,
        target_names=["Grade 0 (No DR)", "Grade 1 (Mild)", "Grade 2 (Moderate)",
                      "Grade 3 (Severe)", "Grade 4 (Proliferative)"]
    ))


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7: MAIN — WIRE EVERYTHING TOGETHER
# This is what actually runs when you execute the script.
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("="*60)
    print("DIABETIC RETINOPATHY CLASSIFIER — TRAINING PIPELINE")
    print("="*60)

    # --- Load the CSV ---
    # train.csv has two columns: id_code, diagnosis
    # id_code = image filename (without extension)
    # diagnosis = grade (0, 1, 2, 3, or 4)
    print(f"\nLoading labels from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    print(f"Total images in dataset: {len(df)}")
    print("\nGrade distribution (how many images per grade):")
    print(df["diagnosis"].value_counts().sort_index())
    print()

    # --- Load or extract features ---
    # We cache features to disk so if the script crashes after extraction,
    # we don't have to reprocess 3662 images again — loads in seconds next run.
    CACHE_PATH = r"D:illage-development-platform\MLeatures_cache.npz"

    if os.path.exists(CACHE_PATH):
        print("Found cached features — loading from disk (instant)...")
        cache = np.load(CACHE_PATH)
        X = cache["X"]
        y = cache["y"]
        print(f"Loaded {X.shape[0]} images from cache.")
    else:
        model = load_feature_extractor()
        X = extract_features(model, df["id_code"].tolist(), IMAGE_DIR, BATCH_SIZE)
        y = df["diagnosis"].values
        print("Saving features to cache so next run is instant...")
        np.savez(CACHE_PATH, X=X, y=y)
        print(f"Cache saved to {CACHE_PATH}")

    print(f"\nFeature matrix shape: {X.shape}")
    print("(rows = images, columns = features per image)")

    # --- Train/test split ---
    # We split BEFORE training so the model never sees test images.
    # test_size=0.2 → 80% train, 20% test
    # random_state=42 → fixed seed so results are reproducible
    # stratify=y → ensures each grade is proportionally represented
    #              in both train and test sets (important for imbalanced data)
    print("\nSplitting data: 80% train, 20% test...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Training set: {len(X_train)} images")
    print(f"Test set:     {len(X_test)} images")

    # --- Train the classifier ---
    clf = train_classifier(X_train, y_train)

    # --- Evaluate ---
    evaluate(clf, X_test, y_test)

    # --- Save the model ---
    # We save BOTH the classifier AND a note about what feature extractor was used.
    # When FastAPI loads this later, it needs to know to use MobileNetV2
    # for preprocessing new images before passing them to the classifier.
    save_data = {
        "classifier": clf,
        "feature_extractor": "mobilenet_v2",
        "input_size": 224,
        "classes": [0, 1, 2, 3, 4],
        "class_names": ["No DR", "Mild", "Moderate", "Severe", "Proliferative DR"],
    }
    joblib.dump(save_data, MODEL_SAVE_PATH)
    print(f"\nModel saved to: {MODEL_SAVE_PATH}")
    print("\nTraining pipeline complete!")
    print("Next step: integrate model_eye.joblib with the FastAPI backend.")


if __name__ == "__main__":
    main()
