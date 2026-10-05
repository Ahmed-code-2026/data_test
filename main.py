from pathlib import Path
import time

from app.sources.csv_source import extract_csv
from app.sources.api_source import extract_api
from app.sources.database_source import extract_database
from app.transformation.cleaner import clean_student_data, clean_api_data, clean_database_data
from app.validation.quality import (
    validate_student_source,
    validate_api_source,
    validate_database_source,
    validate_final_data,
)
from app.transformation.integration import integrate_data
from app.transformation.transformer import transform_data
from app.output.csv_writer import save_csv, save_rejected_records
from app.utils.logger import get_logger

logger = get_logger("pipeline")

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "data/raw/students.csv"
DB_PATH = BASE_DIR / "database/students.db"
FINAL_PATH = BASE_DIR / "data/processed/final_dataset.csv"
REJECTED_PATH = BASE_DIR / "data/rejected/rejected_records.csv"
API_URL = "http://127.0.0.1:8000/students"


def run_pipeline():
    start_time = time.time()
    logger.info("-----------------------------------")
    logger.info("PIPELINE EXECUTION STARTED")
    logger.info("-----------------------------------")

    # 1. Extract
    csv_raw = extract_csv(CSV_PATH)
    api_raw = extract_api(API_URL)
    db_raw = extract_database(DB_PATH)

    # 2. Clean/standardize each source
    csv_clean = clean_student_data(csv_raw)
    api_clean = clean_api_data(api_raw)
    db_clean = clean_database_data(db_raw)

    # 3. Validate each source
    csv_valid, csv_rejected = validate_student_source(csv_clean)
    api_valid, api_rejected = validate_api_source(api_clean)
    db_valid, db_rejected = validate_database_source(db_clean)

    rejected_parts = []

    for source, frame in [
        ("CSV", csv_rejected),
        ("API", api_rejected),
        ("DATABASE", db_rejected),
    ]:
        if not frame.empty:
            rejected = frame.copy()
            rejected["source"] = source
            rejected_parts.append(rejected)

    # 4. Integrate valid data
    integrated = integrate_data(csv_valid, api_valid, db_valid)

    # 5. Transform
    transformed = transform_data(integrated)

    # 6. Final validation
    final_valid, final_rejected = validate_final_data(transformed)
    if not final_rejected.empty:
        final_rejected = final_rejected.copy()
        final_rejected["source"] = "FINAL_VALIDATION"
        rejected_parts.append(final_rejected)

    # 7. Load outputs
    import pandas as pd
    if rejected_parts:
        rejected_all = pd.concat(rejected_parts, ignore_index=True, sort=False)
    else:
        rejected_all = pd.DataFrame(columns=["student_id", "error_reason", "source"])

    save_csv(final_valid, FINAL_PATH)
    save_rejected_records(rejected_all, REJECTED_PATH)

    elapsed = time.time() - start_time

    logger.info("-----------------------------------")
    logger.info("PIPELINE EXECUTION SUMMARY")
    logger.info("CSV Records: %d", len(csv_raw))
    logger.info("API Records: %d", len(api_raw))
    logger.info("Database Records: %d", len(db_raw))
    logger.info("Integrated Records: %d", len(integrated))
    logger.info("Valid Records: %d", len(final_valid))
    logger.info("Rejected Records: %d", len(rejected_all))
    logger.info("Duplicate Records: %d", csv_raw["student_id"].duplicated().sum())
    logger.info("Missing Values in final data: %d", int(final_valid.isna().sum().sum()))
    logger.info("Processing Time: %.2f seconds", elapsed)
    logger.info("-----------------------------------")

    return final_valid



if __name__ == "__main__":
    run_pipeline()
