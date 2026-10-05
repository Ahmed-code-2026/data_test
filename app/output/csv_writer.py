from pathlib import Path
from app.utils.logger import get_logger

logger = get_logger("csv_writer")


def save_csv(df, file_path):
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info("Saved %d records to %s", len(df), path)


def save_rejected_records(df, file_path):
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info("Saved %d rejected records to %s", len(df), path)
