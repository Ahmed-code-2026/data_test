import unittest
from pathlib import Path
import pandas as pd

from app.transformation.cleaner import clean_student_data
from app.validation.quality import validate_student_source, validate_api_source
from app.transformation.integration import integrate_data


class PipelineTests(unittest.TestCase):

    def test_csv_loading(self):
        path = Path("data/raw/students.csv")
        data = pd.read_csv(path)
        self.assertGreater(len(data), 0)

    def test_duplicate_removal(self):
        data = pd.read_csv("data/raw/students.csv")
        cleaned = clean_student_data(data)
        self.assertEqual(cleaned["student_id"].duplicated().sum(), 0)

    def test_invalid_student_rejected(self):
        data = pd.read_csv("data/raw/students.csv")
        cleaned = clean_student_data(data)
        valid, rejected = validate_student_source(cleaned)
        self.assertGreater(len(rejected), 0)

    def test_api_validation(self):
        data = pd.DataFrame([
            {"student_id": 1, "gpa": 3.0, "attendance": 90},
            {"student_id": 2, "gpa": 5.0, "attendance": 90},
        ])
        valid, rejected = validate_api_source(data)
        self.assertEqual(len(valid), 1)
        self.assertEqual(len(rejected), 1)

    def test_integration(self):
        csv = pd.DataFrame([{"student_id": 1, "student_name": "A", "age": 20, "major": "CS", "city": "Sanaa"}])
        api = pd.DataFrame([{"student_id": 1, "gpa": 3.5, "attendance": 90, "status": "Active"}])
        db = pd.DataFrame([{"student_id": 1, "course": "Python", "credit_hours": 3, "semester": "2026-1", "score": 90}])
        result = integrate_data(csv, api, db)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["student_id"], 1)


if __name__ == "__main__":
    unittest.main()
