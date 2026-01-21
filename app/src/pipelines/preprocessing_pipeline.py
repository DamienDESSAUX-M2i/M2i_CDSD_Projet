from src.pipelines import AbstractPipeline


class PreprocessingPipeline(AbstractPipeline):
    """Preprocessing Pipeline."""

    def run(self):
        """Run pipeline.

        Raises:
            RuntimeError: If pipeline failed.
        """
        try:
            self.logger.info("Preprocessing pipeline stars.")
            self.logger.info("Preprocessing pipeline ends successfully.")
        except Exception as exc:
            self.logger.info("Preprocessing pipeline failed.")
            raise RuntimeError("Preprocessing pipeline failed") from exc
