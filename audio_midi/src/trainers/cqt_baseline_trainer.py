from dataclasses import dataclass
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import KFold, learning_curve
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import StandardScaler

from src.trainers import AbstractTrainer


@dataclass
class BaselineResults:
    """
    Aggregated evaluation metrics for the baseline model.
    """

    precision: float
    recall: float
    f1: float
    threshold: float


class CQTBaselineTrainer(AbstractTrainer):
    """
    Frame-wise baseline for guitar transcription using CQT only.

    Model:
        One-vs-Rest Logistic Regression

    Task:
        Multi-label classification

    Input:
        CQT frame

    Output:
        Piano-roll frame
    """

    def __init__(
        self,
        cqt_prefix: str = "cqt_",
        pitch_prefix: str = "pitch_",
        threshold: float = 0.5,
        random_state: int = 42,
    ) -> None:
        """
        Args:
            cqt_prefix:
                Prefix used for CQT feature columns.
            pitch_prefix:
                Prefix used for piano-roll target columns.
            threshold:
                Probability threshold used for binary prediction.
            random_state:
                Random seed for reproducibility.
        """
        self.cqt_prefix = cqt_prefix
        self.pitch_prefix = pitch_prefix
        self.threshold = threshold
        self.random_state = random_state

        self.scaler = StandardScaler()

        self.model = OneVsRestClassifier(
            LogisticRegression(
                max_iter=2000,
                solver="lbfgs",
                random_state=self.random_state,
                class_weight="balanced",
                n_jobs=-1,
            )
        )

    def _split_xy(
        self,
        dataset: pd.DataFrame,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Extract features and targets from a frame-wise dataset.

        Args:
            dataset:
                Input dataframe containing CQT features and piano-roll targets.

        Returns:
            tuple[np.ndarray, np.ndarray]:
                X: feature matrix of shape (n_samples, n_features)
                y: target matrix of shape (n_samples, n_labels)
        """
        feature_columns = [
            column for column in dataset.columns if column.startswith(self.cqt_prefix)
        ]

        target_columns = [
            column for column in dataset.columns if column.startswith(self.pitch_prefix)
        ]

        if not feature_columns:
            raise ValueError("No CQT feature columns found.")

        if not target_columns:
            raise ValueError("No piano-roll target columns found.")

        X = dataset[feature_columns].to_numpy(dtype=np.float32)
        y = dataset[target_columns].to_numpy(dtype=np.int32)

        return X, y

    def fit(
        self,
        train_dataset: pd.DataFrame,
    ) -> None:
        """
        Train the baseline model.

        Args:
            train_dataset:
                Training dataset.
        """
        X_train, y_train = self._split_xy(train_dataset)

        X_train = self.scaler.fit_transform(X_train)

        self.model.fit(X_train, y_train)

    def evaluate(
        self,
        dataset: pd.DataFrame,
    ) -> BaselineResults:
        """
        Evaluate the model on a dataset.

        Args:
            dataset:
                Validation or test dataset.

        Returns:
            BaselineResults:
                Aggregated metrics.
        """
        X, y_true = self._split_xy(dataset)

        X = self.scaler.transform(X)

        y_prob = self.model.predict_proba(X)
        y_pred = (y_prob >= self.threshold).astype(int)

        precision = precision_score(
            y_true,
            y_pred,
            average="micro",
            zero_division=0,
        )

        recall = recall_score(
            y_true,
            y_pred,
            average="micro",
            zero_division=0,
        )

        f1 = f1_score(
            y_true,
            y_pred,
            average="micro",
            zero_division=0,
        )

        return BaselineResults(
            precision=precision,
            recall=recall,
            f1=f1,
            threshold=self.threshold,
        )

    def get_confusion_matrix(
        self,
        dataset: pd.DataFrame,
    ) -> np.ndarray:
        """
        Compute flattened confusion matrix.

        Args:
            dataset:
                Evaluation dataset.

        Returns:
            np.ndarray:
                Confusion matrix flattened across all labels.
        """
        X, y_true = self._split_xy(dataset)

        X = self.scaler.transform(X)
        y_prob = self.model.predict_proba(X)
        y_pred = (y_prob >= self.threshold).astype(int)

        return confusion_matrix(
            y_true.ravel(),
            y_pred.ravel(),
        )

    def plot_confusion_matrix(
        self,
        dataset: pd.DataFrame,
    ) -> None:
        """
        Plot the flattened confusion matrix for multi-label frame-wise prediction.

        The confusion matrix is computed after flattening all pitch labels across
        all frames:

            y_true.shape = (n_frames, n_pitches)
            y_pred.shape = (n_frames, n_pitches)

        becomes:

            y_true_flat.shape = (n_frames * n_pitches,)
            y_pred_flat.shape = (n_frames * n_pitches,)

        This provides a global binary confusion matrix:

            [[TN, FP],
            [FN, TP]]

        Args:
            dataset:
                Evaluation dataset.

        Returns:
            None
        """
        X, y_true = self._split_xy(dataset)

        X = self.scaler.transform(X)
        y_prob = self.model.predict_proba(X)
        y_pred = (y_prob >= self.threshold).astype(int)

        cm = confusion_matrix(
            y_true.ravel(),
            y_pred.ravel(),
        )

        plt.figure(figsize=(6, 5))
        plt.imshow(cm, interpolation="nearest")
        plt.title("Confusion Matrix")
        plt.colorbar()

        tick_marks = np.arange(2)
        plt.xticks(tick_marks, ["Negative", "Positive"])
        plt.yticks(tick_marks, ["Negative", "Positive"])

        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                plt.text(
                    j,
                    i,
                    format(cm[i, j], "d"),
                    ha="center",
                    va="center",
                )

        plt.ylabel("True Label")
        plt.xlabel("Predicted Label")
        plt.tight_layout()
        plt.show()

    def plot_pitch_confusion_matrix(
        self,
        dataset: pd.DataFrame,
        pitch_midi: int,
    ) -> None:
        """
        Plot the binary confusion matrix for a specific pitch.

        This method evaluates one pitch independently:
            active vs inactive

        Example:
            pitch_midi=40 → E2

        Args:
            dataset:
                Evaluation dataset.

            pitch_midi:
                MIDI pitch to evaluate.

        Returns:
            None

        Raises:
            ValueError:
                If the requested pitch column does not exist.
        """
        X, y_true = self._split_xy(dataset)

        target_columns = [
            column for column in dataset.columns if column.startswith(self.pitch_prefix)
        ]

        target_mapping = {
            int(column.replace(self.pitch_prefix, "")): idx
            for idx, column in enumerate(target_columns)
        }

        if pitch_midi not in target_mapping:
            raise ValueError(f"Pitch {pitch_midi} not found in dataset.")

        pitch_idx = target_mapping[pitch_midi]

        X = self.scaler.transform(X)
        y_prob = self.model.predict_proba(X)
        y_pred = (y_prob >= self.threshold).astype(int)

        y_true_pitch = y_true[:, pitch_idx]
        y_pred_pitch = y_pred[:, pitch_idx]

        cm = confusion_matrix(
            y_true_pitch,
            y_pred_pitch,
        )

        plt.figure(figsize=(6, 5))
        plt.imshow(cm, interpolation="nearest")
        plt.title(f"Confusion Matrix - Pitch {pitch_midi}")
        plt.colorbar()

        tick_marks = np.arange(2)
        plt.xticks(tick_marks, ["Inactive", "Active"])
        plt.yticks(tick_marks, ["Inactive", "Active"])

        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                plt.text(
                    j,
                    i,
                    format(cm[i, j], "d"),
                    ha="center",
                    va="center",
                )

        plt.ylabel("True Label")
        plt.xlabel("Predicted Label")
        plt.tight_layout()
        plt.show()

    def get_classification_report(
        self,
        dataset: pd.DataFrame,
    ) -> dict[str, Any]:
        """
        Generate classification report.

        Args:
            dataset:
                Evaluation dataset.

        Returns:
            dict[str, Any]:
                Classification report dictionary.
        """
        X, y_true = self._split_xy(dataset)

        X = self.scaler.transform(X)
        y_prob = self.model.predict_proba(X)
        y_pred = (y_prob >= self.threshold).astype(int)

        return classification_report(
            y_true,
            y_pred,
            output_dict=True,
            zero_division=0,
        )

    def plot_pitchwise_f1(
        self,
        dataset: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Compute and plot F1-score for each pitch independently.

        This helps identify:
            - weak pitches
            - octave bias
            - low-register / high-register failures
            - difficult strings

        Args:
            dataset:
                Evaluation dataset.

        Returns:
            pd.DataFrame:
                DataFrame containing:
                    - pitch_midi
                    - f1_score
        """
        X, y_true = self._split_xy(dataset)

        target_columns = [
            column for column in dataset.columns if column.startswith(self.pitch_prefix)
        ]

        pitch_values = [
            int(column.replace(self.pitch_prefix, "")) for column in target_columns
        ]

        X = self.scaler.transform(X)
        y_prob = self.model.predict_proba(X)
        y_pred = (y_prob >= self.threshold).astype(int)

        f1_scores = []

        for idx, pitch_midi in enumerate(pitch_values):
            score = f1_score(
                y_true[:, idx],
                y_pred[:, idx],
                zero_division=0,
            )

            f1_scores.append(
                {
                    "pitch_midi": pitch_midi,
                    "f1_score": score,
                }
            )

        df_scores = pd.DataFrame(f1_scores)

        plt.figure(figsize=(10, 6))
        plt.plot(
            df_scores["pitch_midi"],
            df_scores["f1_score"],
        )

        plt.title("F1-score per Pitch")
        plt.xlabel("MIDI Pitch")
        plt.ylabel("F1-score")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

        return df_scores

    def plot_precision_recall_curve(
        self,
        dataset: pd.DataFrame,
    ) -> None:
        """
        Plot global precision-recall curve.

        Args:
            dataset:
                Evaluation dataset.
        """
        X, y_true = self._split_xy(dataset)

        X = self.scaler.transform(X)
        y_prob = self.model.predict_proba(X)

        precision, recall, _ = precision_recall_curve(
            y_true.ravel(),
            y_prob.ravel(),
        )

        plt.figure(figsize=(8, 6))
        plt.plot(recall, precision)
        plt.title("Precision-Recall Curve")
        plt.xlabel("Recall")
        plt.ylabel("Precision")
        plt.grid(True)
        plt.show()

    def plot_roc_curve(
        self,
        dataset: pd.DataFrame,
    ) -> float:
        """
        Plot global ROC curve and compute ROC-AUC.

        Args:
            dataset:
                Evaluation dataset.

        Returns:
            float:
                ROC-AUC score.
        """
        X, y_true = self._split_xy(dataset)

        X = self.scaler.transform(X)
        y_prob = self.model.predict_proba(X)

        fpr, tpr, _ = roc_curve(
            y_true.ravel(),
            y_prob.ravel(),
        )

        auc_score = roc_auc_score(
            y_true,
            y_prob,
            average="micro",
        )

        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr)
        plt.title(f"ROC Curve (AUC={auc_score:.4f})")
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.grid(True)
        plt.show()

        return auc_score

    def plot_learning_curve(
        self,
        dataset: pd.DataFrame,
        cv: int = 5,
    ) -> None:
        """
        Plot learning curve.

        Args:
            dataset:
                Full dataset.
            cv:
                Number of folds.
        """
        X, y = self._split_xy(dataset)

        X = self.scaler.fit_transform(X)

        train_sizes, train_scores, val_scores = learning_curve(
            estimator=self.model,
            X=X,
            y=y,
            cv=cv,
            scoring="f1_micro",
            train_sizes=np.linspace(0.1, 1.0, 5),
            n_jobs=-1,
        )

        train_mean = train_scores.mean(axis=1)
        val_mean = val_scores.mean(axis=1)

        plt.figure(figsize=(8, 6))
        plt.plot(train_sizes, train_mean, label="Train")
        plt.plot(train_sizes, val_mean, label="Validation")
        plt.title("Learning Curve")
        plt.xlabel("Training Size")
        plt.ylabel("F1 Micro")
        plt.legend()
        plt.grid(True)
        plt.show()

    def cross_validate(
        self,
        dataset: pd.DataFrame,
        n_splits: int = 5,
    ) -> list[float]:
        """
        Perform manual K-Fold cross-validation.

        Args:
            dataset:
                Input dataset.
            n_splits:
                Number of folds.

        Returns:
            list[float]:
                F1-score for each fold.
        """
        X, y = self._split_xy(dataset)

        kf = KFold(
            n_splits=n_splits,
            shuffle=True,
            random_state=self.random_state,
        )

        scores = []

        for train_idx, val_idx in kf.split(X):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]

            scaler = StandardScaler()
            X_train = scaler.fit_transform(X_train)
            X_val = scaler.transform(X_val)

            model = clone(self.model)
            model.fit(X_train, y_train)

            y_prob = model.predict_proba(X_val)
            y_pred = (y_prob >= self.threshold).astype(int)

            score = f1_score(
                y_val,
                y_pred,
                average="micro",
                zero_division=0,
            )

            scores.append(score)

        return scores
