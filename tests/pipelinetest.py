"""استدعاء واختبار خط الكتب (database/read_dataset_html.py).

التشغيل المباشر:
    python tests/pipelinetest.py

التشغيل عبر unittest:
    python -m unittest tests.pipelinetest -v
"""

import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.read_dataset_html import (
    cleaner,
    extract_books,
    run_books_pipeline,
    transformat,
    validation,
)


class BooksPipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # استخراج حقيقي محدود (صفحتين = ~40 كتاب) حتى يبقى الاختبار سريعًا.
        cls.raw = extract_books(max_pages=2)
        cls.cleaned = cleaner(cls.raw)
        cls.valid, cls.rejected = validation(cls.cleaned)
        cls.data = transformat(cls.valid)

    def test_extract_returns_books(self):
        self.assertGreater(len(self.raw), 0)
        for column in ["title", "price", "availability", "rating"]:
            self.assertIn(column, self.raw.columns)

    def test_cleaner_parses_price(self):
        self.assertTrue(pd.api.types.is_numeric_dtype(self.cleaned["price"]))
        self.assertGreater(self.cleaned["price"].dropna().min(), 0)

    def test_validation_splits_valid_rejected(self):
        # بيانات صحيحة تمر، وبيانات فاسدة تُرفَض مع سبب.
        bad = pd.DataFrame(
            [
                {"title": "", "price": -5, "availability": "", "rating": "Wrong", "detail_url": ""},
                {"title": "Good Book", "price": 25.0, "availability": "In stock", "rating": "Three", "detail_url": ""},
            ]
        )
        valid, rejected = validation(bad)
        self.assertEqual(len(valid), 1)
        self.assertEqual(len(rejected), 1)
        self.assertIn("error_reason", rejected.columns)

    def test_transformat_adds_columns(self):
        for column in ["rating_number", "price_category", "in_stock", "title_length"]:
            self.assertIn(column, self.data.columns)
        self.assertTrue(self.data["rating_number"].between(1, 5).all())

    def test_full_pipeline_saves_csv(self):
        # الاستدعاء الكامل للخط وتخزين الناتج في متغير data وحفظه CSV.
        # يُحفَظ في ملف مؤقت حتى لا يمسح الناتج الكامل.
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "books_test.csv"
            data = run_books_pipeline(max_pages=2, output_csv=out)
            self.assertGreater(len(data), 0)
            self.assertTrue(out.exists())


def main():
    """نقطة الاستدعاء المباشرة: تشغيل الخط وتخزين الناتج في data."""
    data = run_books_pipeline(max_pages=5)
    print(f"Extracted & saved books: {len(data)}")
    print(data.head().to_string(index=False))
    return data


if __name__ == "__main__":
    # تشغيل الخط أولًا ثم الاختبارات.
    data = main()
    unittest.main(argv=[sys.argv[0]], verbosity=2)
