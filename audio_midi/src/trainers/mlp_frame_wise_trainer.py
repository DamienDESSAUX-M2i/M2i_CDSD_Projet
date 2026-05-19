from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import (
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.preprocessing import StandardScaler

from src.trainers import AbstractTrainer


@dataclass
class MLPResults:
    """
    Aggregated evaluation metrics for the MLP frame-wise model.
    """

    precision: float
    recall: float
    f1: float
    threshold: float


class MLPFrameWiseTrainer(AbstractTrainer):
    """
    Frame-wise MLP baseline for guitar transcription.

    Model:
        Multi-label MLP (Dense Neural Network)

    Task:
        Multi-label classification

    Input:
        One frame of acoustic features (typically CQT)

    Output:
        One piano-roll frame (multi-hot vector)

    Typical shape:
        X.shape = (n_frames, n_features)
        y.shape = (n_frames, n_pitches)
    """

    def __init__(
        self,
        feature_prefix: str = "cqt_",
        pitch_prefix: str = "pitch_",
        threshold: float = 0.5,
        hidden_units_1: int = 512,
        hidden_units_2: int = 256,
        dropout_rate: float = 0.3,
        learning_rate: float = 1e-3,
        batch_size: int = 256,
        epochs: int = 50,
        random_state: int = 42,
    ) -> None:
        """
        Args:
            feature_prefix:
                Prefix used to select input feature columns.

            pitch_prefix:
                Prefix used to select piano-roll target columns.

            threshold:
                Probability threshold for binary decision.

            hidden_units_1:
                Number of neurons in first dense layer.

            hidden_units_2:
                Number of neurons in second dense layer.

            dropout_rate:
                Dropout rate for regularization.

            learning_rate:
                Adam optimizer learning rate.

            batch_size:
                Training batch size.

            epochs:
                Maximum number of training epochs.

            random_state:
                Random seed for reproducibility.
        """
        super().__init__()

        self.feature_prefix = feature_prefix
        self.pitch_prefix = pitch_prefix
        self.threshold = threshold

        self.hidden_units_1 = hidden_units_1
        self.hidden_units_2 = hidden_units_2
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        self.random_state = random_state

        self.scaler = StandardScaler()

        tf.keras.utils.set_random_seed(self.random_state)

        self.model: Optional[tf.keras.Model] = None

    def _split_xy(
        self,
        dataset: pd.DataFrame,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Extract X and y from a frame-wise dataset.

        Args:
            dataset:
                DataFrame containing feature columns and target columns.

        Returns:
            tuple[np.ndarray, np.ndarray]:
                X:
                    Feature matrix of shape
                    (n_samples, n_features)

                y:
                    Multi-label target matrix of shape
                    (n_samples, n_pitches)
        """
        feature_columns = [
            column
            for column in dataset.columns
            if column.startswith(self.feature_prefix)
        ]

        target_columns = [
            column for column in dataset.columns if column.startswith(self.pitch_prefix)
        ]

        if not feature_columns:
            raise ValueError("No feature columns found.")

        if not target_columns:
            raise ValueError("No pitch target columns found.")

        X = dataset[feature_columns].to_numpy(dtype=np.float32)
        y = dataset[target_columns].to_numpy(dtype=np.float32)

        return X, y

    def _build_model(
        self,
        input_dim: int,
        output_dim: int,
    ) -> tf.keras.Model:
        """
        Build the TensorFlow MLP model.

        Args:
            input_dim:
                Number of input features.

            output_dim:
                Number of output pitch labels.

        Returns:
            tf.keras.Model:
                Compiled Keras model.
        """
        self.logger.info(
            f"Building MLP model: input_dim={input_dim}, output_dim={output_dim}"
        )

        model = tf.keras.Sequential(
            [
                tf.keras.layers.Input(shape=(input_dim,)),
                tf.keras.layers.Dense(
                    self.hidden_units_1,
                    activation="relu",
                ),
                tf.keras.layers.Dropout(
                    self.dropout_rate,
                ),
                tf.keras.layers.Dense(
                    self.hidden_units_2,
                    activation="relu",
                ),
                tf.keras.layers.Dropout(
                    self.dropout_rate,
                ),
                tf.keras.layers.Dense(
                    output_dim,
                    activation="sigmoid",
                ),
            ]
        )

        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss="binary_crossentropy",
            metrics=[
                tf.keras.metrics.Precision(name="precision"),
                tf.keras.metrics.Recall(name="recall"),
            ],
        )

        return model

    def fit(
        self,
        train_dataset: pd.DataFrame,
        val_dataset: pd.DataFrame,
    ) -> tf.keras.callbacks.History:
        """
        Train the frame-wise MLP model.

        Args:
            train_dataset:
                Training dataset.

            val_dataset:
                Validation dataset.

        Returns:
            tf.keras.callbacks.History:
                Keras training history.
        """
        X_train, y_train = self._split_xy(train_dataset)
        X_val, y_val = self._split_xy(val_dataset)

        self.logger.info(
            f"Training dataset loaded: X_train={X_train.shape}, y_train={y_train.shape}"
        )

        self.logger.info(
            f"Validation dataset loaded: X_val={X_val.shape}, y_val={y_val.shape}"
        )

        X_train = self.scaler.fit_transform(X_train)
        X_val = self.scaler.transform(X_val)

        self.model = self._build_model(
            input_dim=X_train.shape[1],
            output_dim=y_train.shape[1],
        )

        early_stopping = tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=8,
            restore_best_weights=True,
            verbose=1,
        )

        reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=4,
            verbose=1,
        )

        self.logger.info("Starting MLP training.")

        history = self.model.fit(
            X_train,
            y_train,
            validation_data=(X_val, y_val),
            batch_size=self.batch_size,
            epochs=self.epochs,
            callbacks=[
                early_stopping,
                reduce_lr,
            ],
            verbose=1,
        )

        self.logger.info("MLP training completed.")

        return history

    def evaluate(
        self,
        dataset: pd.DataFrame,
    ) -> MLPResults:
        """
        Evaluate the trained MLP model.

        Args:
            dataset:
                Validation or test dataset.

        Returns:
            MLPResults:
                Aggregated evaluation metrics.

        Raises:
            RuntimeError:
                If model has not been trained.
        """
        if self.model is None:
            raise RuntimeError("Model is not trained. Call fit() first.")

        X, y_true = self._split_xy(dataset)

        X = self.scaler.transform(X)

        y_prob = self.model.predict(
            X,
            batch_size=self.batch_size,
            verbose=0,
        )

        y_pred = (y_prob >= self.threshold).astype(np.int32)

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

        self.logger.info(
            f"Evaluation completed: "
            f"precision={precision:.4f}, "
            f"recall={recall:.4f}, "
            f"f1={f1:.4f}"
        )

        return MLPResults(
            precision=precision,
            recall=recall,
            f1=f1,
            threshold=self.threshold,
        )
