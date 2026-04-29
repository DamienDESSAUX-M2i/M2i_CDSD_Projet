from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler

from src.trainers import AbstractTrainer


@dataclass
class ContextWindowMLPResults:
    """
    Aggregated evaluation metrics for the context-window MLP model.
    """

    precision: float
    recall: float
    f1: float
    threshold: float


class ContextWindowMLPTrainer(AbstractTrainer):
    """
    Frame-wise multi-label transcription model using temporal context windows.

    Instead of predicting from a single frame:

        x_t -> y_t

    the model predicts from a centered temporal window:

        [x_(t-k), ..., x_t, ..., x_(t+k)] -> y_t

    This improves note activation detection by giving the model access to:
        - note attacks
        - sustain regions
        - local temporal transitions

    Model:
        Dense MLP with sigmoid multi-label output

    Task:
        Multi-label piano-roll prediction
    """

    def __init__(
        self,
        feature_prefix: str = "cqt_",
        pitch_prefix: str = "pitch_",
        threshold: float = 0.5,
        context_size: int = 5,
        hidden_units_1: int = 1024,
        hidden_units_2: int = 512,
        dropout_rate: float = 0.3,
        learning_rate: float = 1e-3,
        train_batch_size: int = 256,
        predict_batch_size: int = 4096,
        epochs: int = 50,
        random_state: int = 42,
    ) -> None:
        """
        Args:
            feature_prefix:
                Prefix used to identify feature columns.

            pitch_prefix:
                Prefix used to identify piano-roll target columns.

            threshold:
                Decision threshold applied to sigmoid outputs.

            context_size:
                Number of frames on each side of the center frame.

                Total window size is:

                    2 * context_size + 1

                Example:
                    context_size = 5 -> 11-frame window

            hidden_units_1:
                Number of units in first dense layer.

            hidden_units_2:
                Number of units in second dense layer.

            dropout_rate:
                Dropout regularization rate.

            learning_rate:
                Adam optimizer learning rate.

            train_batch_size:
                Batch size used during training.

            predict_batch_size:
                Batch size used during inference.

            epochs:
                Maximum number of training epochs.

            random_state:
                Random seed for reproducibility.
        """
        super().__init__()

        self.feature_prefix = feature_prefix
        self.pitch_prefix = pitch_prefix
        self.threshold = threshold
        self.context_size = context_size

        self.hidden_units_1 = hidden_units_1
        self.hidden_units_2 = hidden_units_2
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate

        self.train_batch_size = train_batch_size
        self.predict_batch_size = predict_batch_size
        self.epochs = epochs
        self.random_state = random_state

        self.scaler = StandardScaler()
        self.model: Optional[tf.keras.Model] = None

        tf.keras.utils.set_random_seed(self.random_state)

    def _split_xy(
        self,
        dataset: pd.DataFrame,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Extract features and targets from dataset.

        Args:
            dataset:
                Frame-wise dataset.

        Returns:
            tuple[np.ndarray, np.ndarray]:
                X:
                    Feature matrix of shape
                    (n_frames, n_features)

                y:
                    Piano-roll target matrix of shape
                    (n_frames, n_pitches)
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
            raise ValueError("No target columns found.")

        X = dataset[feature_columns].to_numpy(dtype=np.float32)
        y = dataset[target_columns].to_numpy(dtype=np.float32)

        return X, y

    def _build_context_windows(
        self,
        X: np.ndarray,
    ) -> np.ndarray:
        """
        Build centered temporal context windows.

        Example:
            context_size = 2
            input:
                [x0, x1, x2, x3]
            output:
                [
                    [x0, x0, x0, x1, x2],
                    [x0, x0, x1, x2, x3],
                    [x0, x1, x2, x3, x3],
                    [x1, x2, x3, x3, x3],
                ]

        Padding strategy:
            edge padding

        Args:
            X:
                Input feature matrix of shape
                (n_frames, n_features)

        Returns:
            np.ndarray:
                Context-window matrix of shape
                (
                    n_frames,
                    n_features * (2 * context_size + 1)
                )
        """
        self.logger.info(f"Building context windows: context_size={self.context_size}")

        pad = self.context_size
        window_size = 2 * pad + 1

        X_padded = np.pad(
            X,
            pad_width=((pad, pad), (0, 0)),
            mode="edge",
        )

        windows = []

        for i in range(len(X)):
            window = X_padded[i : i + window_size]
            windows.append(window.reshape(-1))

        X_context = np.stack(windows)

        self.logger.info(
            f"Context windows built: input={X.shape}, output={X_context.shape}"
        )

        return X_context

    def _build_model(
        self,
        input_dim: int,
        output_dim: int,
    ) -> tf.keras.Model:
        """
        Build TensorFlow MLP model.

        Args:
            input_dim:
                Number of input features.

            output_dim:
                Number of piano-roll output pitches.

        Returns:
            tf.keras.Model:
                Compiled model.
        """
        model = tf.keras.Sequential(
            [
                tf.keras.layers.Input(shape=(input_dim,)),
                tf.keras.layers.Dense(
                    self.hidden_units_1,
                    activation="relu",
                ),
                tf.keras.layers.Dropout(self.dropout_rate),
                tf.keras.layers.Dense(
                    self.hidden_units_2,
                    activation="relu",
                ),
                tf.keras.layers.Dropout(self.dropout_rate),
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
        Train the context-window MLP.

        Args:
            train_dataset:
                Training dataset.

            val_dataset:
                Validation dataset.

        Returns:
            tf.keras.callbacks.History:
                Training history.
        """
        X_train, y_train = self._split_xy(train_dataset)
        X_val, y_val = self._split_xy(val_dataset)

        X_train = self.scaler.fit_transform(X_train)
        X_val = self.scaler.transform(X_val)

        X_train = self._build_context_windows(X_train)
        X_val = self._build_context_windows(X_val)

        self.model = self._build_model(
            input_dim=X_train.shape[1],
            output_dim=y_train.shape[1],
        )

        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor="val_loss",
                patience=8,
                restore_best_weights=True,
                verbose=1,
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss",
                factor=0.5,
                patience=4,
                verbose=1,
            ),
        ]

        self.logger.info("Starting ContextWindowMLP training.")

        history = self.model.fit(
            X_train,
            y_train,
            validation_data=(X_val, y_val),
            batch_size=self.train_batch_size,
            epochs=self.epochs,
            callbacks=callbacks,
            verbose=1,
        )

        self.logger.info("Training completed.")

        return history

    def evaluate(
        self,
        dataset: pd.DataFrame,
    ) -> ContextWindowMLPResults:
        """
        Evaluate trained model.

        Args:
            dataset:
                Validation or test dataset.

        Returns:
            ContextWindowMLPResults:
                Aggregated evaluation metrics.

        Raises:
            RuntimeError:
                If model is not trained.
        """
        if self.model is None:
            raise RuntimeError("Model is not trained. Call fit() first.")

        X, y_true = self._split_xy(dataset)

        X = self.scaler.transform(X)
        X = self._build_context_windows(X)

        y_prob = self.model.predict(
            X,
            batch_size=self.predict_batch_size,
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

        return ContextWindowMLPResults(
            precision=precision,
            recall=recall,
            f1=f1,
            threshold=self.threshold,
        )
