"""Training script for the clothing recommendation ML model.

Workflow:
    1. Load or generate synthetic dataset.
    2. Encode labels with LabelEncoder.
    3. Split 80/20 train/test (stratified).
    4. Train pipeline (StandardScaler + RandomForestClassifier).
    5. Evaluate with classification_report (logged at INFO).
    6. Persist model.joblib + label_encoder.joblib to artifacts/.
"""

import logging
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from ml.generate_dataset import OUTPUT_PATH, generate_dataset
from ml.model.features import FEATURE_NAMES
from ml.model.pipeline import build_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "model.joblib"
LABEL_ENCODER_PATH = ARTIFACTS_DIR / "label_encoder.joblib"

TEST_SIZE = 0.2
RANDOM_STATE = 42


def load_or_generate_dataset() -> pd.DataFrame:
    """Load CSV if it exists, otherwise generate and save it."""
    if OUTPUT_PATH.exists():
        logger.info("Loading existing dataset: %s", OUTPUT_PATH)
        return pd.read_csv(OUTPUT_PATH)

    logger.info("Dataset not found — generating synthetic data...")
    df = generate_dataset()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    logger.info("Dataset saved: %s  shape=%s", OUTPUT_PATH, df.shape)
    return df


def main() -> None:
    # 1. Data
    df = load_or_generate_dataset()
    X = df[FEATURE_NAMES].values
    y_raw = df["label"].values

    # 2. Label encoding
    le = LabelEncoder()
    y = le.fit_transform(y_raw)
    logger.info("Classes (%d): %s", len(le.classes_), list(le.classes_))

    # 3. Train/test split — stratified to preserve class distribution
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    logger.info("Split — train: %d  test: %d", len(X_train), len(X_test))

    # 4. Train
    pipeline = build_pipeline()
    logger.info("Training pipeline...")
    pipeline.fit(X_train, y_train)

    # 5. Evaluate
    y_pred = pipeline.predict(X_test)
    report = classification_report(
        y_test, y_pred, target_names=le.classes_, zero_division=0
    )
    logger.info("Classification report:\n%s", report)

    # 6. Persist
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    joblib.dump(le, LABEL_ENCODER_PATH)
    logger.info("Saved model         → %s", MODEL_PATH)
    logger.info("Saved label_encoder → %s", LABEL_ENCODER_PATH)


if __name__ == "__main__":
    main()
