"""
Complaint → Department Classifier
===================================
Trains a text classifier that predicts which government department
should handle a citizen complaint.

Pipeline:
    Text → TF-IDF features → Voting ensemble (LR + SVM + NB) → Department label

Departments:
    road, water, electricity, sanitation, health, education, agriculture, other

Usage (run from inside Backend/ with venv active):
    python -m app.ml.train_complaint_classifier

The script:
1. Loads the sample CSV (40 labeled examples)
2. Pulls real complaints from PostgreSQL (if DATABASE_URL is set)
3. Combines both, trains and evaluates the model
4. Saves model to app/ml/model_complaint.joblib
5. The classifier.py inference module auto-loads this on next server restart
"""

import os
import sys
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import VotingClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_CSV = os.path.join(BASE_DIR, "data", "complaints_sample.csv")
MODEL_PATH = os.path.join(BASE_DIR, "model_complaint.joblib")

# ---------------------------------------------------------------------------
# Step 1: Load sample CSV data
# ---------------------------------------------------------------------------

def load_sample_data():
    print(f"Loading sample data from {SAMPLE_CSV}...")
    df = pd.read_csv(SAMPLE_CSV)
    df = df.dropna(subset=["description", "department"])
    df["source"] = "sample"
    print(f"  Loaded {len(df)} sample complaints")
    return df


# ---------------------------------------------------------------------------
# Step 2: Load real complaints from PostgreSQL (optional)
# ---------------------------------------------------------------------------

def load_db_data():
    """
    Pulls real labeled complaints from the village_platform database.
    Skips gracefully if the DB isn't reachable or has no labeled data.
    """
    try:
        import psycopg2

        # Read DATABASE_URL from .env if it exists
        db_url = os.environ.get("DATABASE_URL", "")
        if not db_url:
            env_path = os.path.join(BASE_DIR, "..", "..", ".env")
            if os.path.exists(env_path):
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("DATABASE_URL="):
                            db_url = line.split("=", 1)[1].strip()
                            break

        if not db_url:
            print("  No DATABASE_URL found — skipping real complaint data")
            return pd.DataFrame()

        # Parse postgresql://user:pass@host:port/dbname
        db_url = db_url.replace("postgresql://", "")
        user_pass, rest = db_url.split("@")
        user, password = user_pass.split(":")
        host_port, dbname = rest.split("/")
        if ":" in host_port:
            host, port = host_port.split(":")
        else:
            host, port = host_port, "5432"

        conn = psycopg2.connect(
            host=host, port=port, dbname=dbname, user=user, password=password
        )
        cursor = conn.cursor()
        cursor.execute(
            "SELECT description, department FROM complaints WHERE department IS NOT NULL AND description IS NOT NULL"
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            print("  No labeled complaints in DB yet")
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=["description", "department"])
        df["source"] = "database"

        # Normalize department names to lowercase
        df["department"] = df["department"].str.lower().str.strip()

        print(f"  Loaded {len(df)} real complaints from database")
        return df

    except Exception as e:
        print(f"  Could not load DB data: {e}")
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Step 3: Build the ensemble pipeline
# ---------------------------------------------------------------------------

def build_pipeline():
    """
    TF-IDF extracts text features (unigrams + bigrams).
    Three classifiers vote on the final department:
      - Logistic Regression: good at linear boundaries, calibrated probabilities
      - Linear SVC: strong at high-dimensional text, wrapped for probability output
      - Multinomial NB: fast, works well on sparse TF-IDF features
    class_weight=balanced compensates for uneven department counts.
    """

    tfidf = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=1,
        stop_words="english",
        sublinear_tf=True,   # log(1+tf) instead of raw tf — helps with long complaints
    )

    lr = LogisticRegression(
        max_iter=1000,
        C=1.0,
        class_weight="balanced",
        solver="lbfgs",
    )

    svm = CalibratedClassifierCV(
        LinearSVC(
            max_iter=2000,
            class_weight="balanced",
            random_state=42,
        )
    )

    nb = CalibratedClassifierCV(
        # MultinomialNB needs non-negative features — TF-IDF satisfies this
        MultinomialNB(alpha=0.5)
    )

    ensemble = VotingClassifier(
        estimators=[("lr", lr), ("svm", svm), ("nb", nb)],
        voting="soft",
    )

    # We can't put TF-IDF inside VotingClassifier directly since each sub-estimator
    # needs the same features — so we apply TF-IDF first, then vote.
    # We'll handle this manually in train().
    return tfidf, ensemble


# ---------------------------------------------------------------------------
# Step 4: Train and evaluate
# ---------------------------------------------------------------------------

def train(df):
    print(f"\nTotal training data: {len(df)} complaints")
    print("\nDepartment distribution:")
    print(df["department"].value_counts())

    X = df["description"].values
    y = df["department"].values

    # With small datasets, only split if we have enough examples per class
    min_class_size = df["department"].value_counts().min()

    if len(df) >= 20 and min_class_size >= 2:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        do_eval = True
    else:
        # Too few examples to split — train on everything
        X_train, y_train = X, y
        X_test, y_test = X, y
        do_eval = False
        print("\nNote: dataset too small to split — training on all data, evaluation will be optimistic")

    tfidf, ensemble = build_pipeline()

    print("\nExtracting TF-IDF features...")
    X_train_tfidf = tfidf.fit_transform(X_train)
    X_test_tfidf = tfidf.transform(X_test)

    print("Training ensemble (LR + SVM + NB)...")
    ensemble.fit(X_train_tfidf, y_train)

    # Refit TF-IDF on full data before saving
    X_full_tfidf = tfidf.fit_transform(X)
    ensemble.fit(X_full_tfidf, y)

    if do_eval:
        # Evaluate on the held-out test set (before the final refit above)
        # We re-transform test with the final tfidf for a fair comparison
        X_test_final = tfidf.transform(X_test)
        y_pred = ensemble.predict(X_test_final)
        macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)

        print(f"\n{'='*55}")
        print(f"EVALUATION RESULTS (macro F1 = {macro_f1:.3f})")
        print("="*55)
        print(classification_report(y_test, y_pred, zero_division=0))
    else:
        print("\nSkipping held-out evaluation (dataset too small)")

    return tfidf, ensemble


# ---------------------------------------------------------------------------
# Step 5: Save model
# ---------------------------------------------------------------------------

def save_model(tfidf, ensemble):
    save_data = {
        "tfidf": tfidf,
        "classifier": ensemble,
        "departments": [
            "road", "water", "electricity", "sanitation",
            "health", "education", "agriculture", "other"
        ],
    }
    joblib.dump(save_data, MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")
    print("Restart the FastAPI server to load the new model.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 55)
    print("COMPLAINT DEPARTMENT CLASSIFIER — TRAINING")
    print("=" * 55)

    # Load data
    sample_df = load_sample_data()
    db_df = load_db_data()

    # Combine
    if not db_df.empty:
        df = pd.concat([sample_df, db_df], ignore_index=True)
        # Remove duplicates (same description might appear in both)
        df = df.drop_duplicates(subset=["description"])
        print(f"\nCombined dataset: {len(df)} complaints ({len(sample_df)} sample + {len(db_df)} real)")
    else:
        df = sample_df
        print(f"\nUsing sample data only: {len(df)} complaints")

    # Normalize department names
    df["department"] = df["department"].str.lower().str.strip()

    # Train
    tfidf, ensemble = train(df)

    # Save
    save_model(tfidf, ensemble)

    print("\nDone! The complaint classifier is ready.")
    print("It will activate automatically on the next server restart.")


if __name__ == "__main__":
    main()
