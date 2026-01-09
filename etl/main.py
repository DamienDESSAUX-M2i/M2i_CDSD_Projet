import argparse

from src.pipelines import PreprocessingPipeline
from src.utils import initialize_logger


def main() -> None:
    initialize_logger()

    parser = argparse.ArgumentParser(description="Audio Midi Pipeline")
    parser.add_argument(
        "--preprocessing", action="store_true", help="Launch preprocessing pipeline"
    )
    args = parser.parse_args()

    if args.preprocessing:
        preprocessing_pipeline = PreprocessingPipeline()
        preprocessing_pipeline.run()


if __name__ == "__main__":
    main()
