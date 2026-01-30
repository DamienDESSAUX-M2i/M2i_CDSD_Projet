import argparse

from src.pipelines import (
    GuitarSetIngestionPipeline,
    IDMTSMTGuitarIngestionPipeline,
    PreprocessingPipeline,
)
from src.utils import initialize_logger


def main() -> None:
    initialize_logger()

    parser = argparse.ArgumentParser(description="Audio Midi Pipeline")
    parser.add_argument(
        "--guitar_set", action="store_true", help="Launch Guitar Set ingestion pipeline"
    )
    parser.add_argument(
        "--idmt_smt_guitar",
        action="store_true",
        help="Launch IDMT SMT Guitar ingestion pipeline",
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

    if args.idmt_smt_guitar:
        ingestion_pipeline = IDMTSMTGuitarIngestionPipeline(ingestion_limit=args.limit)
        ingestion_pipeline.run()
        ingestion_pipeline.close()

    if args.preprocessing:
        preprocessing_pipeline = PreprocessingPipeline()
        preprocessing_pipeline.run()
        ingestion_pipeline.close()


if __name__ == "__main__":
    main()
