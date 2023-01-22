import unittest
import pickle as pkl
import os
from fragments.params import ParamStorage
from fragments.strategy import ConditionalStrategy, CrossoverStrategy, LimiterStrategy
from fragments.indicators import RSI, SMA, ATR, Indicator
from fragments.stats import equity
from fragments.optim import *


class TestOptim(unittest.TestCase):
    @unittest.skipIf(os.getenv("TEST_OPTIM") is None, "TEST_OPTIM is not set")
    def test_optim(self):
        param_storage = ParamStorage()

        strategies = list()
        strategies.append(
            CrossoverStrategy(SMA(param_storage), SMA(param_storage), param_storage)
        )
        strategies.append(
            ConditionalStrategy(RSI(param_storage), param_storage, strategies[0])
        )

        with open("./data/GOOG.pkl", "rb") as f:
            ohlcv_list = pkl.load(f)

        self.assertAlmostEqual(
            optimize(strategies[-1], equity, ohlcv_list, random_state=42).fun,
            -152.4914,
            4,
        )

    @unittest.skipIf(os.getenv("TEST_OPTIM") is None, "TEST_OPTIM is not set")
    def test_consistency_after_optim_precalc(self):
        param_storage = ParamStorage()

        with open("./data/GOOG.pkl", "rb") as f:
            ohlcv_list = pkl.load(f)

        Indicator.enable_precalculation(ohlcv_list)

        strategies = list()
        strategies.append(
            CrossoverStrategy(SMA(param_storage), SMA(param_storage), param_storage)
        )
        strategies.append(
            ConditionalStrategy(RSI(param_storage), param_storage, strategies[-1])
        )

        results = optimize(strategies[-1], equity, ohlcv_list, random_state=42)
        first_equity = strategies[-1].equity

        Indicator.disable_precalculation()

        strategies[-1].update_and_forward_all(results.x, ohlcv_list)
        second_equity = strategies[-1].equity

        self.assertEqual(first_equity, second_equity)

    @unittest.skipIf(os.getenv("TEST_OPTIM") is None, "TEST_OPTIM is not set")
    def test_layered_optim(self):
        param_storage = ParamStorage()

        with open("./data/GOOG.pkl", "rb") as f:
            ohlcv_list = pkl.load(f)

        strategies = list()
        strategies.append(
            CrossoverStrategy(SMA(param_storage), SMA(param_storage), param_storage)
        )
        strategies.append(
            ConditionalStrategy(RSI(param_storage), param_storage, strategies[-1])
        )

        _ = optimize(strategies[-1], equity, ohlcv_list, random_state=42)
        first_equity = strategies[-1].equity

        param_storage = ParamStorage()

        strategies.append(
            LimiterStrategy(ATR(param_storage), param_storage, strategies[-1])
        )

        second_results = optimize(strategies[-1], equity, ohlcv_list, random_state=42)
        self.assertAlmostEqual(
            second_results.fun,
            -105.4931,
            4,
        )
        second_equity = strategies[-2].equity

        self.assertEqual(first_equity, second_equity)

    @unittest.skipIf(os.getenv("TEST_OPTIM") is None, "TEST_OPTIM is not set")
    def test_consistency_of_precalc_and_nonprecalc_optim(self):
        param_storage = ParamStorage()

        with open("./data/GOOG.pkl", "rb") as f:
            ohlcv_list = pkl.load(f)

        Indicator.enable_precalculation(ohlcv_list)

        strategies = list()
        strategies.append(
            CrossoverStrategy(SMA(param_storage), SMA(param_storage), param_storage)
        )
        strategies.append(
            ConditionalStrategy(RSI(param_storage), param_storage, strategies[-1])
        )

        first_results = optimize(strategies[-1], equity, ohlcv_list, random_state=42)
        first_equity = strategies[-1].equity

        Indicator.disable_precalculation()

        param_storage = ParamStorage()

        strategies = list()
        strategies.append(
            CrossoverStrategy(SMA(param_storage), SMA(param_storage), param_storage)
        )
        strategies.append(
            ConditionalStrategy(RSI(param_storage), param_storage, strategies[-1])
        )

        second_results = optimize(strategies[-1], equity, ohlcv_list, random_state=42)
        second_equity = strategies[-1].equity

        self.assertEqual(first_results.fun, second_results.fun)
        self.assertEqual(first_results.x, second_results.x)
        self.assertEqual(first_equity, second_equity)
