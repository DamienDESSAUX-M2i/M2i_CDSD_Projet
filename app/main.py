import argparse
from pathlib import Path

from config import Dataset
from src.pipelines import (
    GuitarSetIngestionPipeline,
    IDMTSMTGuitarIngestionPipeline,
    PreprocessingPipeline,
)
from src.utils import (
    download_and_extract_dataset,
    initialize_logger,
)

DATA_RAW_DIR = Path("./app/data/raw")


def main() -> None:
    initialize_logger()

    parser = argparse.ArgumentParser(description="Audio Midi Pipeline")
    parser.add_argument(
        "--guitar_set", action="store_true", help="Launch Guitar Set ingestion pipeline"
    )
    parser.add_argument(
        "--idmt_smt_guitar",
        action="store_true",
        help="Launch IDMT-SMT-Guitar ingestion pipeline",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Max number of files ingested"
    )
    parser.add_argument(
        "--no-dataset1",
        dest="dataset1",
        action="store_false",
        help="Deactivate ingestion of subset 1 of the dataset IDMT-SMT-Guitar",
    )
    parser.add_argument(
        "--no-dataset2",
        dest="dataset2",
        action="store_false",
        help="Deactivate ingestion of subset 2 of the dataset IDMT-SMT-Guitar",
    )
    parser.add_argument(
        "--no-dataset3",
        dest="dataset3",
        action="store_false",
        help="Deactivate ingestion of subset 3 of the dataset IDMT-SMT-Guitar",
    )
    parser.add_argument(
        "--no-dataset4",
        dest="dataset4",
        action="store_false",
        help="Deactivate ingestion of subset 4 of the dataset IDMT-SMT-Guitar",
    )
    parser.add_argument(
        "--preprocessor", action="store_true", help="Launch preprocessing pipeline"
    )
    parser.add_argument(
        "--ml", action="store_true", help="Launch machine learning pipeline"
    )
    parser.add_argument("--download_guitarset", action="store_true")
    parser.add_argument("--download_idmt_smt_guitar", action="store_true")
    args = parser.parse_args()

    if args.download_guitarset:
        download_and_extract_dataset(
            dataset=Dataset.GUITARSET,
            base_dir=DATA_RAW_DIR,
        )

    if args.download_idmt_smt_guitar:
        download_and_extract_dataset(
            dataset=Dataset.IDMT_SMT_GUITAR,
            base_dir=DATA_RAW_DIR,
        )

    if args.guitar_set:
        ingestion_pipeline = GuitarSetIngestionPipeline(ingestion_limit=args.limit)
        ingestion_pipeline.run()
        ingestion_pipeline.close()

    if args.idmt_smt_guitar:
        ingestion_pipeline = IDMTSMTGuitarIngestionPipeline(
            ingestion_limit=args.limit,
            dataset1=args.dataset1,
            dataset2=args.dataset2,
            dataset3=args.dataset3,
            dataset4=args.dataset4,
        )
        ingestion_pipeline.run()
        ingestion_pipeline.close()

    if args.preprocessor:
        preprocessing_pipeline = PreprocessingPipeline()
        preprocessing_pipeline.run()
        ingestion_pipeline.close()


if __name__ == "__main__":
    main()
