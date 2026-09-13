from __future__ import annotations

import unittest

import pandas as pd

from runtime.shared.scripts.stw_benchmark_local import normalize_downloaded_history, resolve_date_window


class STWBenchmarkTests(unittest.TestCase):
    def test_resolve_date_window_from_panel(self):
        panel = pd.DataFrame({"trade_date": pd.to_datetime(["2020-01-02", "2020-01-06"])})
        self.assertEqual(resolve_date_window(panel), ("2020-01-02", "2020-01-06"))

    def test_normalize_downloaded_history_builds_benchmark_return(self):
        downloaded = pd.DataFrame(
            {
                "Open": [10.0, 10.5],
                "High": [10.2, 10.7],
                "Low": [9.9, 10.4],
                "Close": [10.1, 10.6],
                "Adj Close": [10.0, 10.5],
                "Volume": [1000, 1200],
            },
            index=pd.to_datetime(["2020-01-02", "2020-01-03"]),
        )
        downloaded.index.name = "Date"
        frame = normalize_downloaded_history(downloaded)
        self.assertEqual(frame["vendor_symbol"].unique().tolist(), ["STW.AX"])
        self.assertTrue(pd.isna(frame.loc[0, "benchmark_return"]))
        self.assertAlmostEqual(frame.loc[1, "benchmark_return"], 0.05)


if __name__ == "__main__":
    unittest.main()
