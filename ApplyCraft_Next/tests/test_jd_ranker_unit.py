import unittest
from unittest.mock import patch

from core.jd_ranker import BulletScore, compute_fit_score, generate_match_recommendations


class TestJDRankerRecommendations(unittest.TestCase):
    def test_fit_score_in_range(self):
        ranked = [
            BulletScore("Role A", "Built SQL pipelines and dashboards", 0.72, ["sql", "dashboards"]),
            BulletScore("Role B", "Automated ETL jobs in Python", 0.64, ["python", "etl"]),
            BulletScore("Role C", "Worked with stakeholders", 0.31, ["stakeholders"]),
        ]
        fit = compute_fit_score(
            "Need Python SQL ETL dashboards and stakeholder communication",
            ranked,
        )
        self.assertGreaterEqual(fit["fit_score"], 0.0)
        self.assertLessEqual(fit["fit_score"], 1.0)

    def test_recommendations_require_local_llm(self):
        ranked = [
            BulletScore("Role A", "Built SQL pipelines", 0.51, ["sql"]),
            BulletScore("Role B", "Maintained reports", 0.34, ["reports"]),
            BulletScore("Role C", "Collaborated with teams", 0.28, []),
        ]
        with self.assertRaises(RuntimeError):
            generate_match_recommendations(
                "Looking for Python, ETL, stakeholder management, and experimentation",
                ranked,
                max_items=3,
            )

    def test_recommendations_return_when_local_llm_available(self):
        ranked = [
            BulletScore("Role A", "Built SQL pipelines", 0.71, ["sql"]),
            BulletScore("Role B", "Automated ETL in Python", 0.66, ["python", "etl"]),
        ]
        with patch("core.jd_ranker._ollama_generate_recommendations", return_value=["Add Python KPI bullet", "Quantify ETL impact"]):
            result = generate_match_recommendations(
                "Need Python, ETL, and KPI reporting",
                ranked,
                max_items=2,
            )
        self.assertIn("local-llm (ollama:", result["source"])
        self.assertEqual(len(result["recommendations"]), 2)


if __name__ == "__main__":
    unittest.main()
