"""Machine learning classifier for transaction categories.

This module provides a lightweight scikit-learn based classifier that can
assign categories to parsed SMS transactions. It includes utilities for
loading/saving the model, preparing training data from prior-month Excel
correction files, and exporting misclassified samples for human review.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pickle

try:
    import joblib

    JOBLIB_AVAILABLE = True
except ImportError as exc:  # pragma: no cover - environment-specific
    JOBLIB_AVAILABLE = False
    JOBLIB_IMPORT_ERROR = exc

import pandas as pd

try:  # Optional import to allow environments without scikit-learn to import the module
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    SKLEARN_AVAILABLE = True
except ImportError as exc:  # pragma: no cover - environment-specific
    SKLEARN_AVAILABLE = False
    SKLEARN_IMPORT_ERROR = exc
    TfidfVectorizer = LogisticRegression = Pipeline = None

from goldminer.utils import setup_logger


DEFAULT_TEXT_COLUMNS = [
    "sms_text",
    "payee",
    "normalized_merchant",
    "transaction_type",
]


@dataclass
class ClassificationResult:
    """Structured prediction output from :class:`TransactionClassifier`."""

    category: Optional[str]
    probability: float
    confidence: str

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Convert the result into a serializable dictionary."""

        return {
            "ml_category": self.category,
            "ml_category_score": self.probability,
            "ml_category_confidence": self.confidence,
        }


class TransactionClassifier:
    """Category classifier for parsed transactions using scikit-learn.

    The classifier trains a TF-IDF + Logistic Regression pipeline on text
    fields derived from parsed SMS records (e.g., SMS body, payee, merchant
    hints). It exposes helper methods for retraining, inference, and exporting
    misclassified samples for feedback loops.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        default_category: str = "Uncategorized",
        confidence_thresholds: Tuple[float, float] = (0.8, 0.6),
    ) -> None:
        self.logger = setup_logger(__name__)
        self.model_path = Path(model_path) if model_path else self._default_model_path()
        self.default_category = default_category
        self.confidence_thresholds = confidence_thresholds
        self.pipeline: Optional[Pipeline] = None

        if not SKLEARN_AVAILABLE:
            self.logger.warning(
                "scikit-learn is not available; transaction classification is disabled (%s)",
                SKLEARN_IMPORT_ERROR,
            )
            return

        if self.model_path.exists():
            self.load_model()
        else:
            self.logger.info(
                "Transaction classifier model not found at %s. Call train() to create one.",
                self.model_path,
            )

    @staticmethod
    def _default_model_path() -> Path:
        project_root = Path(__file__).parent.parent.parent
        model_dir = project_root / "data" / "processed"
        model_dir.mkdir(parents=True, exist_ok=True)
        return model_dir / "transaction_classifier.joblib"

    def _build_pipeline(self) -> Pipeline:
        if not SKLEARN_AVAILABLE:
            raise ImportError(
                "scikit-learn is required to build the transaction classifier pipeline"
            )
        return Pipeline(
            steps=[
                (
                    "tfidf",
                    TfidfVectorizer(
                        ngram_range=(1, 2),
                        max_features=5000,
                        min_df=2,
                    ),
                ),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=500,
                        class_weight="balanced",
                        n_jobs=-1,
                    ),
                ),
            ]
        )

    def _combine_text(self, row: pd.Series, text_columns: List[str]) -> str:
        usable_cols = [col for col in text_columns if col in row and pd.notna(row[col])]
        combined = " ".join(str(row[col]) for col in usable_cols if str(row[col]).strip())
        return combined.strip()

    def _confidence_from_prob(self, probability: float) -> str:
        high, medium = self.confidence_thresholds
        if probability >= high:
            return "high"
        if probability >= medium:
            return "medium"
        return "low"

    def load_model(self) -> None:
        """Load a previously trained model from disk."""

        if not SKLEARN_AVAILABLE:
            raise ImportError(
                "scikit-learn is required to load the transaction classifier"
            ) from SKLEARN_IMPORT_ERROR

        try:
            if JOBLIB_AVAILABLE:
                self.pipeline = joblib.load(self.model_path)
            else:
                with open(self.model_path, "rb") as f:
                    self.pipeline = pickle.load(f)
            self.logger.info("Loaded transaction classifier from %s", self.model_path)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Failed to load classifier: %s", exc)
            self.pipeline = None

    def save_model(self) -> None:
        """Persist the current pipeline to disk."""

        if self.pipeline is None:
            raise ValueError("No trained pipeline to save.")

        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        if JOBLIB_AVAILABLE:
            joblib.dump(self.pipeline, self.model_path)
        else:  # pragma: no cover - fallback for environments without joblib
            with open(self.model_path, "wb") as f:
                pickle.dump(self.pipeline, f)
        self.logger.info("Saved transaction classifier to %s", self.model_path)

    def train(
        self,
        training_df: pd.DataFrame,
        text_columns: Optional[List[str]] = None,
        target_column: str = "category",
    ) -> Dict[str, float]:
        """Train the classifier.

        Args:
            training_df: DataFrame containing text fields and target labels.
            text_columns: Columns to combine for the text representation.
            target_column: Name of the label column (default: ``category``).

        Returns:
            Dictionary with training statistics (row counts, unique labels).
        """

        if not SKLEARN_AVAILABLE:
            raise ImportError(
                "scikit-learn is required for training the transaction classifier"
            )

        if text_columns is None:
            text_columns = DEFAULT_TEXT_COLUMNS

        if target_column not in training_df.columns:
            raise ValueError(f"Target column '{target_column}' not found in training data")

        df = training_df.copy()
        df = df[df[target_column].notna()].copy()
        if df.empty:
            raise ValueError("No labeled rows available for training")

        df["_combined_text"] = df.apply(lambda row: self._combine_text(row, text_columns), axis=1)
        df = df[df["_combined_text"].str.len() > 0]
        if df.empty:
            raise ValueError("No usable text found in training data")

        self.pipeline = self._build_pipeline()
        self.pipeline.fit(df["_combined_text"], df[target_column])

        self.logger.info(
            "Trained classifier on %d samples across %d labels",
            len(df),
            df[target_column].nunique(),
        )

        return {
            "samples": float(len(df)),
            "labels": float(df[target_column].nunique()),
        }

    def predict_text(self, text: str) -> ClassificationResult:
        """Predict a category for free-form text."""

        if not text or self.pipeline is None:
            return ClassificationResult(None, 0.0, "low")

        proba = self.pipeline.predict_proba([text])[0]
        best_idx = proba.argmax()
        category = self.pipeline.classes_[best_idx]
        probability = float(proba[best_idx])
        confidence = self._confidence_from_prob(probability)
        return ClassificationResult(category, probability, confidence)

    def classify_sms(
        self,
        sms_text: str,
        parsed_fields: Optional[Dict[str, Optional[str]]] = None,
        text_columns: Optional[List[str]] = None,
    ) -> ClassificationResult:
        """Classify a parsed SMS message using available text features."""

        if text_columns is None:
            text_columns = DEFAULT_TEXT_COLUMNS

        if parsed_fields is None:
            parsed_fields = {}

        row_dict = {**{col: None for col in text_columns}, **parsed_fields}
        row_dict["sms_text"] = sms_text
        row = pd.Series(row_dict)
        combined = self._combine_text(row, text_columns)
        if not combined:
            return ClassificationResult(self.default_category, 0.0, "low")
        return self.predict_text(combined)

    def merge_corrections(
        self, parsed_df: pd.DataFrame, corrections_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Merge parsed SMS outputs with corrections for training.

        Corrections take precedence over parsed labels when an ``id`` column is
        present. Otherwise, the datasets are concatenated.
        """

        parsed_df = parsed_df.copy()
        corrections_df = corrections_df.copy()

        parsed_df["label_source"] = parsed_df.get("label_source", "parsed")
        corrections_df["label_source"] = corrections_df.get("label_source", "correction")

        if "id" in parsed_df.columns and "id" in corrections_df.columns:
            parsed_df = parsed_df.set_index("id")
            corrections_df = corrections_df.set_index("id")

            for col in ["category", "subcategory"]:
                if col in corrections_df.columns:
                    base = (
                        parsed_df[col]
                        if col in parsed_df.columns
                        else pd.Series(index=parsed_df.index, dtype=object)
                    )
                    parsed_df[col] = corrections_df[col].combine_first(base)

            combined = pd.concat(
                [parsed_df, corrections_df.loc[~corrections_df.index.isin(parsed_df.index)]],
                axis=0,
            )
            return combined.reset_index()

        return pd.concat([parsed_df, corrections_df], ignore_index=True)

    def load_corrections(self, correction_files: List[str]) -> pd.DataFrame:
        """Load one or more Excel correction files into a single DataFrame."""

        frames: List[pd.DataFrame] = []
        for path in correction_files:
            if not os.path.exists(path):
                self.logger.warning("Skipping missing correction file: %s", path)
                continue
            df = pd.read_excel(path)
            df["source_file"] = os.path.basename(path)
            frames.append(df)

        if not frames:
            return pd.DataFrame()

        combined = pd.concat(frames, ignore_index=True)
        self.logger.info("Loaded %d correction rows from %d file(s)", len(combined), len(frames))
        return combined

    def load_parsed_transactions(self, parsed_path: str) -> pd.DataFrame:
        """Load parsed SMS outputs from CSV, Parquet, or Excel."""

        if not os.path.exists(parsed_path):
            raise FileNotFoundError(f"Parsed SMS file not found: {parsed_path}")

        suffix = Path(parsed_path).suffix.lower()
        if suffix in {".csv", ".txt"}:
            df = pd.read_csv(parsed_path)
        elif suffix in {".parquet", ".pq"}:
            df = pd.read_parquet(parsed_path)
        elif suffix in {".xls", ".xlsx"}:
            df = pd.read_excel(parsed_path)
        else:
            raise ValueError(f"Unsupported parsed data format: {suffix}")

        self.logger.info("Loaded %d parsed transaction rows from %s", len(df), parsed_path)
        return df

    def retrain_from_files(
        self,
        parsed_path: str,
        correction_files: List[str],
        text_columns: Optional[List[str]] = None,
        target_column: str = "category",
    ) -> Dict[str, float]:
        """Convenience helper to retrain from parsed data and correction Excel files."""

        parsed_df = self.load_parsed_transactions(parsed_path)
        corrections_df = self.load_corrections(correction_files)

        if not corrections_df.empty:
            training_df = self.merge_corrections(parsed_df, corrections_df)
        else:
            training_df = parsed_df

        stats = self.train(training_df, text_columns=text_columns, target_column=target_column)
        self.save_model()
        return stats

    def export_misclassifications(
        self,
        dataset: pd.DataFrame,
        output_path: str,
        text_columns: Optional[List[str]] = None,
        target_column: str = "category",
    ) -> pd.DataFrame:
        """Generate a misclassification report and persist it to disk."""

        if self.pipeline is None:
            raise ValueError("Classifier is not trained or loaded")

        if not SKLEARN_AVAILABLE:
            raise ImportError(
                "scikit-learn is required to export misclassifications"
            ) from SKLEARN_IMPORT_ERROR

        if text_columns is None:
            text_columns = DEFAULT_TEXT_COLUMNS

        labeled = dataset.dropna(subset=[target_column]).copy()
        if labeled.empty:
            raise ValueError("No labeled rows available for misclassification export")

        labeled["_combined_text"] = labeled.apply(
            lambda row: self._combine_text(row, text_columns), axis=1
        )
        labeled = labeled[labeled["_combined_text"].str.len() > 0]

        predictions = self.pipeline.predict(labeled["_combined_text"])
        probabilities = self.pipeline.predict_proba(labeled["_combined_text"])
        max_probs = probabilities.max(axis=1)

        labeled["predicted_category"] = predictions
        labeled["predicted_probability"] = max_probs
        labeled["predicted_confidence"] = labeled["predicted_probability"].apply(
            self._confidence_from_prob
        )

        misclassified = labeled[labeled[target_column] != labeled["predicted_category"]]

        suffix = Path(output_path).suffix.lower()
        if suffix == ".xlsx":
            misclassified.to_excel(output_path, index=False)
        else:
            misclassified.to_csv(output_path, index=False)

        self.logger.info(
            "Exported %d misclassified rows (from %d labeled) to %s",
            len(misclassified),
            len(labeled),
            output_path,
        )

        return misclassified

