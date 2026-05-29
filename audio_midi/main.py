import argparse

from src.pipelines import (
    DatasetsDownloadPipeline,
    GuitarSetIngestionPipeline,
    IDMTSMTGuitarIngestionPipeline,
    MLPipeline,
    PreprocessingPipeline,
)
from src.utils import initialize_logger


def main() -> None:
    logger = initialize_logger()

    parser = argparse.ArgumentParser(description="Audio Midi Pipeline")

    #  Download datasets
    parser.add_argument(
        "--download_datasets",
        action="store_true",
        help="Launch the download pipelines",
    )
    parser.add_argument(
        "--no_guitar_set",
        dest="guitar_set",
        action="store_false",
        help="Deactivate download of the dataset GuitarSet",
    )
    parser.add_argument(
        "--no_idmt_smt_guitar",
        dest="idmt_smt_guitar",
        action="store_false",
        help="Deactivate download of the dataset IDMT-SMT-Guitar",
    )

    # Ingest datasets
    parser.add_argument(
        "--ingest_datasets",
        action="store_true",
        help="Launch the ingestion pipelines",
    )
    parser.add_argument(
        "--ingest_guitar_set",
        action="store_true",
        help="Launch Guitar Set ingestion pipeline",
    )
    parser.add_argument(
        "--ingest_idmt_smt_guitar",
        action="store_true",
        help="Launch IDMT-SMT-Guitar ingestion pipeline",
    )
    parser.add_argument(
        "--no_dataset1",
        dest="dataset1",
        action="store_false",
        help="Deactivate ingestion of subset 1 of the dataset IDMT-SMT-Guitar",
    )
    parser.add_argument(
        "--no_dataset2",
        dest="dataset2",
        action="store_false",
        help="Deactivate ingestion of subset 2 of the dataset IDMT-SMT-Guitar",
    )
    parser.add_argument(
        "--no_dataset3",
        dest="dataset3",
        action="store_false",
        help="Deactivate ingestion of subset 3 of the dataset IDMT-SMT-Guitar",
    )
    parser.add_argument(
        "--no_dataset4",
        dest="dataset4",
        action="store_false",
        help="Deactivate ingestion of subset 4 of the dataset IDMT-SMT-Guitar",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max number of audio ingested per dataset",
    )

    # Preprocess datasets
    parser.add_argument(
        "--preprocess_datasets",
        action="store_true",
        help="Launch preprocessing pipeline",
    )

    # Predict notes
    parser.add_argument(
        "--run_ml",
        action="store_true",
        help="Launch machine learning pipeline",
    )

    args = parser.parse_args()

    if args.download_datasets:
        download_datasets_pipeline = DatasetsDownloadPipeline(
            logger=logger,
            guitar_set=args.guitar_set,
            idmt_smt_guitar=args.idmt_smt_guitar,
        )
        download_datasets_pipeline.run()

    if args.ingest_datasets:
        for ingestion_pipeline in [
            GuitarSetIngestionPipeline(logger=logger, ingestion_limit=args.limit),
            IDMTSMTGuitarIngestionPipeline(
                logger=logger,
                ingestion_limit=args.limit,
                dataset1=args.dataset1,
                dataset2=args.dataset2,
                dataset3=args.dataset3,
                dataset4=args.dataset4,
            ),
        ]:
            ingestion_pipeline.run()
            ingestion_pipeline.close()

    if args.ingest_guitar_set:
        ingestion_pipeline = GuitarSetIngestionPipeline(
            logger=logger,
            ingestion_limit=args.limit,
        )
        ingestion_pipeline.run()
        ingestion_pipeline.close()

    if args.ingest_idmt_smt_guitar:
        ingestion_pipeline = IDMTSMTGuitarIngestionPipeline(
            logger=logger,
            ingestion_limit=args.limit,
            dataset1=args.dataset1,
            dataset2=args.dataset2,
            dataset3=args.dataset3,
            dataset4=args.dataset4,
        )
        ingestion_pipeline.run()
        ingestion_pipeline.close()

    if args.preprocess_datasets:
        preprocessing_pipeline = PreprocessingPipeline(
            logger=logger,
            preprocessing_limit=args.limit,
            guitarset=args.guitar_set,
            idmt_smt_guitar=args.idmt_smt_guitar,
            dataset1=args.dataset1,
            dataset2=args.dataset2,
            dataset3=args.dataset3,
            dataset4=args.dataset4,
        )
        preprocessing_pipeline.run()
        preprocessing_pipeline.close()

    if args.run_ml:
        ml_pipeline = MLPipeline(
            logger=logger,
            guitarset=args.guitar_set,
            idmt_smt_guitar=args.idmt_smt_guitar,
        )
        ml_pipeline.run()
        ml_pipeline.close()


if __name__ == "__main__":
    main()
