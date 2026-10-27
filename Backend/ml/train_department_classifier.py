"""
Trains a model on the sample complaint data and saves it to disk.
Run this once with: python ml/train_department_classifier.py
Re-run it any time you add more rows to complaints_sample.csv.
"""
import os
import joblib
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline

HERE = os.path.dirname(__file__)
DATA_PATH = os.path.join(HERE, "data", "complaints_sample.csv")
MODEL_PATH = os.path.join(HERE, "department_classifier.joblib")


def make_vectorizer():
    # unigrams + bigrams ("no water", "power cut") capture more signal than
    # single words alone, and stop words strip out noise like "the", "is".
    return TfidfVectorizer(ngram_range=(1, 2), stop_words="english", min_df=1, sublinear_tf=True)


def main():
    df = pd.read_csv(DATA_PATH)
    X, y = df["text"], df["department"]

    candidates = {
        "logistic_regression": Pipeline([
            ("tfidf", make_vectorizer()),
            ("clf", LogisticRegression(max_iter=1000)),
        ]),
        "naive_bayes": Pipeline([
            ("tfidf", make_vectorizer()),
            ("clf", MultinomialNB()),
        ]),
        "linear_svm": Pipeline([
            ("tfidf", make_vectorizer()),
            ("clf", LinearSVC()),
        ]),
    }

    # With a small dataset, a single train/test split is noisy — 5-fold
    # cross-validation gives a more reliable accuracy estimate by testing
    # on every row exactly once, across 5 different splits.
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    best_name, best_model, best_score = None, None, -1
    for name, pipeline in candidates.items():
        scores = cross_val_score(pipeline, X, y, cv=cv)
        avg_score = scores.mean()
        print(f"{name}: accuracy={avg_score:.2f} (folds: {[round(s, 2) for s in scores]})")
        if avg_score > best_score:
            best_name, best_model, best_score = name, pipeline, avg_score

    # Refit the winning model on ALL the data before saving
    best_model.fit(X, y)
    joblib.dump(best_model, MODEL_PATH)
    print(f"Saved best model ({best_name}, cross-val accuracy={best_score:.2f}) to {MODEL_PATH}")


if __name__ == "__main__":
    main()
