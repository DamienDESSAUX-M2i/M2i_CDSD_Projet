import argparse

from src.pipelines import GuitarSetIngestionPipeline, PreprocessingPipeline
from src.utils import initialize_logger


def main() -> None:
    initialize_logger()

    parser = argparse.ArgumentParser(description="Audio Midi Pipeline")
    parser.add_argument(
        "--guitar_set", action="store_true", help="Launch guitar set ingestion pipeline"
    )
    parser.add_argument(
        "--limit", type=int, default=2, help="Max number of files ingested"
    )
    parser.add_argument(
        "--preprocessing", action="store_true", help="Launch preprocessing pipeline"
    )
    args = parser.parse_args()

    if args.guitar_set:
        ingestion_pipeline = GuitarSetIngestionPipeline(ingestion_limit=args.limit)
        ingestion_pipeline.run()
        ingestion_pipeline.close()

    if args.preprocessing:
        preprocessing_pipeline = PreprocessingPipeline()
        preprocessing_pipeline.run()


if __name__ == "__main__":
    main()
