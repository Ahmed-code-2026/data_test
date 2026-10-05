from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

try:
    from app.utils.logger import get_logger
except ImportError: 
    import logging

    def get_logger(name="books_pipeline"):
        return logging.getLogger(name)


logger = get_logger("books_pipeline")

BASE_URL = "https://books.toscrape.com/"
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_CSV = BASE_DIR / "data" / "processed" / "books_dataset.csv"

RATING_VALUES = ["One", "Two", "Three", "Four", "Five"]
RATING_NUMBERS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

data: pd.DataFrame | None = None


def extract_books(base_url: str = BASE_URL, max_pages: int | None = 5,
                  timeout: int = 20) -> pd.DataFrame:
    
    rows: list[dict] = []
    url = base_url
    page = 0

    while url:
        page += 1
        if max_pages is not None and page > max_pages:
            break

        logger.info("Fetching books page %d: %s", page, url)
        response = requests.get(url, timeout=timeout)
        response.encoding = "utf-8"
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.select("article.product_pod")
        if not articles:
            break

        for article in articles:
            title_tag = article.select_one("h3 a")
            price_tag = article.select_one("p.price_color")
            stock_tag = article.select_one("p.instock")
            rating_tag = article.select_one("p.star-rating")

            title = title_tag.get("title") if title_tag else ""
            detail_url = urljoin(url, title_tag.get("href", "")) if title_tag else ""
            price = price_tag.get_text(strip=True) if price_tag else ""
            availability = (
                " ".join(stock_tag.get_text().split()) if stock_tag else ""
            )
            rating = ""
            if rating_tag:
                classes = rating_tag.get("class", [])
                rating = next((c for c in classes if c != "star-rating"), "")

            rows.append(
                {
                    "title": title,
                    "price": price,
                    "availability": availability,
                    "rating": rating,
                    "detail_url": detail_url,
                }
            )

        next_tag = soup.select_one("li.next a")
        url = urljoin(url, next_tag.get("href")) if next_tag else None

    df = pd.DataFrame(rows, columns=["title", "price", "availability", "rating", "detail_url"])
    logger.info("Extracted %d books", len(df))
    return df


def cleaner(df: pd.DataFrame) -> pd.DataFrame:
    data_clean = df.copy()
    data_clean.columns = (
        data_clean.columns.astype(str).str.strip().str.lower()
    )

    for column in ["title", "availability", "rating", "detail_url"]:
        if column in data_clean.columns:
            data_clean[column] = data_clean[column].apply(
                lambda value: " ".join(str(value).split()) if pd.notna(value) else value
            )

    if "rating" in data_clean.columns:
        data_clean["rating"] = data_clean["rating"].apply(
            lambda value: str(value).strip().title() if pd.notna(value) and str(value).strip() else value
        )

    if "price" in data_clean.columns:
        extracted = (
            data_clean["price"]
            .astype(str)
            .str.replace(r"[^0-9.]", "", regex=True)
        )
        data_clean["price"] = pd.to_numeric(extracted, errors="coerce")

    if "title" in data_clean.columns:
        data_clean = data_clean.dropna(subset=["title"], how="all")

    logger.info("Cleaning done: %d rows", len(data_clean))
    return data_clean


def validation(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    
    data_check = df.copy()
    errors = pd.Series("", index=data_check.index, dtype="object")

    def add_error(mask, message: str):
        errors.loc[mask] = errors.loc[mask].apply(
            lambda old: f"{old}; {message}" if old else message
        )

    add_error(
        data_check["title"].isna()
        | (data_check["title"].astype(str).str.strip() == "")
        | (data_check["title"].astype(str) == "nan"),
        "Missing title",
    )
    add_error(data_check["price"].isna(), "Missing price")
    add_error(~data_check["price"].isna() & ~(data_check["price"] > 0), "Invalid price")
    add_error(
        data_check["availability"].isna()
        | (data_check["availability"].astype(str).str.strip() == ""),
        "Missing availability",
    )
    add_error(~data_check["rating"].isin(RATING_VALUES), "Invalid rating")

    rejected = data_check.loc[errors != ""].copy()
    rejected["error_reason"] = errors.loc[errors != ""].values
    valid = data_check.loc[errors == ""].copy()

    logger.info("Validation: valid=%d rejected=%d", len(valid), len(rejected))
    return valid, rejected


def transformat(df: pd.DataFrame) -> pd.DataFrame:
    data_transformed = df.copy()

    data_transformed["rating_number"] = data_transformed["rating"].map(RATING_NUMBERS)

    def price_category(price: float) -> str:
        if pd.isna(price):
            return "Unknown"
        if price < 20:
            return "Cheap"
        if price <= 40:
            return "Moderate"
        return "Expensive"

    data_transformed["price_category"] = data_transformed["price"].apply(price_category)
    data_transformed["in_stock"] = (
        data_transformed["availability"].astype(str).str.contains("In stock", case=False, na=False)
    )
    data_transformed["title_length"] = (
        data_transformed["title"].astype(str).str.len()
    )

    logger.info("Transformation done: %d rows", len(data_transformed))
    return data_transformed


def run_books_pipeline(base_url: str = BASE_URL, max_pages: int | None = 5,
                       output_csv: str | Path = DEFAULT_OUTPUT_CSV) -> pd.DataFrame:
    
    global data

    raw = extract_books(base_url=base_url, max_pages=max_pages)
    cleaned = cleaner(raw)
    valid, rejected = validation(cleaned)
    data = transformat(valid)

    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output_csv, index=False, encoding="utf-8")

    logger.info("Saved %d books to %s (rejected=%d)", len(data), output_csv, len(rejected))
    return data


if __name__ == "__main__":
    data = run_books_pipeline()
    print(data.head())
    print(f"Total books: {len(data)}")
