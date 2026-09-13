from __future__ import annotations

import unittest

import pandas as pd

from runtime.shared.scripts.rba_cash_rate_tri_local import apply_date_filter, extract_tri_frame


class RbaCashRateTriTests(unittest.TestCase):
    def test_extract_tri_frame_builds_risk_free_return(self):
        csv_text = "\n".join([
            "Title,Other,Total Return Index",
            "Publication date,,11-Sep-2026",
            "01-Jan-2020,,100.0",
            "02-Jan-2020,,100.1",
        ])
        frame = extract_tri_frame(csv_text)
        self.assertEqual(len(frame), 2)
        self.assertTrue(pd.isna(frame.loc[0, "risk_free_return"]))
        self.assertAlmostEqual(frame.loc[1, "risk_free_return"], 0.001)

    def test_apply_date_filter_is_inclusive(self):
        frame = pd.DataFrame({
            "trade_date": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
            "rba_cash_rate_tri": [100.0, 100.1, 100.2],
            "risk_free_return": [float("nan"), 0.001, 0.001],
            "publication_date": ["", "", ""],
            "source": ["RBA statistical table F1"] * 3,
            "source_url": ["x"] * 3,
        })
        filtered = apply_date_filter(frame, "2020-01-02", "2020-01-03")
        self.assertEqual(filtered["trade_date"].dt.strftime("%Y-%m-%d").tolist(), ["2020-01-02", "2020-01-03"])


if __name__ == "__main__":
    unittest.main()
