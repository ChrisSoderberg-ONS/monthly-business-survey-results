from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from mbs_results.calculate_winsorised_weight import calculate_winsorised_weight


@pytest.fixture(scope="class")
def winsorised_weight_test_data():
    return pd.read_csv(
        Path("tests") / "data" / "winsorisation" / "winsorised_weight_data.csv",
        low_memory=False,
        usecols=lambda c: not c.startswith("Unnamed:"),
    )


@pytest.fixture(scope="class")
def winsorised_weight_test_output():
    return pd.read_csv(
        Path("tests") / "data" / "winsorisation" / "winsorised_weight_data_output.csv",
        low_memory=False,
        usecols=lambda c: not c.startswith("Unnamed:"),
    )


class TestWinsorisedWeight:
    def test_winsorised_weight(
        self, winsorised_weight_test_output, winsorised_weight_test_data
    ):
        expected_output = winsorised_weight_test_output[
            [
                "strata",
                "period",
                "aux",
                "sampled",
                "a_weight",
                "g_weight",
                "target_variable",
                "nw_ag_flag",
                "predicted_unit_value",
                "l_values",
                "ratio_estimation_treshold",
                "new_target_variable",
                "outlier_weight",
            ]
        ]
        input_data = winsorised_weight_test_data[
            [
                "strata",
                "period",
                "aux",
                "sampled",
                "a_weight",
                "g_weight",
                "target_variable",
                "nw_ag_flag",
                "predicted_unit_value",
                "l_values",
                "ratio_estimation_treshold",
            ]
        ]

        actual_output = calculate_winsorised_weight(
            input_data,
            "strata",
            "period",
            "aux",
            "sampled",
            "a_weight",
            "g_weight",
            "target_variable",
            "nw_ag_flag",
            "predicted_unit_value",
            "l_values",
            "ratio_estimation_treshold",
        )

        assert_frame_equal(actual_output, expected_output)
