from dataclasses import asdict
from functools import partial
from unittest import TestCase, main as unittest_main

import numpy as np

from gbstats.frequentist.tests import (
    FrequentistConfig,
    SequentialTwoSidedTTest,
    TwoSidedTTest,
)
from gbstats.shared.models import (
    FrequentistTestResult,
    ProportionStatistic,
    SampleMeanStatistic,
    Uplift,
)

DECIMALS = 5
round_ = partial(np.round, decimals=DECIMALS)


def _round_result_dict(result_dict):
    for k, v in result_dict.items():
        if k == "uplift":
            v = {
                kk: round_(vv) if isinstance(vv, float) else vv for kk, vv in v.items()
            }
        else:
            v = [round_(x) for x in v] if isinstance(v, list) else round_(v)
        result_dict[k] = v
    return result_dict


class TestTwoSidedTTest(TestCase):
    def test_two_sided_ttest(self):
        stat_a = SampleMeanStatistic(sum=1396.87, sum_squares=52377.9767, n=3407)
        stat_b = SampleMeanStatistic(sum=2422.7, sum_squares=134698.29, n=3461)
        result_dict = asdict(TwoSidedTTest(stat_a, stat_b).compute_result())
        expected_rounded_dict = asdict(
            FrequentistTestResult(
                expected=round_((0.7 - 0.41) / 0.41),
                ci=[-0.03526, 1.44989],
                uplift=Uplift("normal", 0.70732, 0.37879),
                p_value=0.06191,
            )
        )

        self.assertDictEqual(_round_result_dict(result_dict), expected_rounded_dict)

    def test_two_sided_ttest_binom(self):
        stat_a = ProportionStatistic(sum=14, n=28)
        stat_b = ProportionStatistic(sum=16, n=30)
        result_dict = asdict(TwoSidedTTest(stat_a, stat_b).compute_result())
        expected_rounded_dict = asdict(
            FrequentistTestResult(
                expected=round_((16 / 30 - 0.5) / 0.5),
                ci=[-0.47767, 0.61101],
                uplift=Uplift("normal", 0.06667, 0.2717),
                p_value=0.80707,
            )
        )

        self.assertDictEqual(_round_result_dict(result_dict), expected_rounded_dict)

    def test_two_sided_ttest_missing_variance(self):
        stat_a = SampleMeanStatistic(sum=1396.87, sum_squares=52377.9767, n=2)
        stat_b = SampleMeanStatistic(sum=2422.7, sum_squares=134698.29, n=3461)
        default_output = TwoSidedTTest(stat_a, stat_b)._default_output()
        result_output = TwoSidedTTest(stat_a, stat_b).compute_result()

        self.assertEqual(default_output, result_output)


class TestSequentialTTest(TestCase):
    def test_sequential_test_runs(self):
        stat_a = SampleMeanStatistic(sum=1396.87, sum_squares=52377.9767, n=3000)
        stat_b = SampleMeanStatistic(sum=2422.7, sum_squares=134698.29, n=3461)
        config = FrequentistConfig(sequential_tuning_parameter=1000)
        result_dict = asdict(
            SequentialTwoSidedTTest(stat_a, stat_b, config).compute_result()
        )
        expected_dict = asdict(
            FrequentistTestResult(
                expected=0.50336,
                ci=[-0.85121, 1.85793],
                uplift=Uplift("normal", 0.50336, 0.33341),
                p_value=1,
            )
        )

        self.assertEqual(_round_result_dict(result_dict), expected_dict)

    def test_sequential_test_tuning_as_expected(self):
        stat_a = SampleMeanStatistic(sum=1396.87, sum_squares=52377.9767, n=3000)
        stat_b = SampleMeanStatistic(sum=2422.7, sum_squares=134698.29, n=3461)
        config_below_n = FrequentistConfig(sequential_tuning_parameter=10)
        result_below = SequentialTwoSidedTTest(
            stat_a, stat_b, config_below_n
        ).compute_result()


        config_above_n = FrequentistConfig(sequential_tuning_parameter=10000)
        result_above = SequentialTwoSidedTTest(
            stat_a, stat_b, config_above_n
        ).compute_result()

        # Way underestimating should be worse here
        self.assertTrue((result_below.ci[0] < result_above.ci[0]) and (result_below.ci[1] > result_above.ci[1]))


if __name__ == "__main__":
    unittest_main()
