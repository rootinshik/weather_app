"""ML pipeline factory: StandardScaler → RandomForestClassifier."""

from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build_pipeline() -> Pipeline:
    """Build and return the clothing recommendation pipeline.

    Steps:
        1. StandardScaler — normalise continuous features.
        2. RandomForestClassifier — multi-class classifier with
           class_weight="balanced" to compensate for skewed label distribution.

    Returns:
        Untrained sklearn Pipeline instance.
    """
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    class_weight="balanced",
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )
