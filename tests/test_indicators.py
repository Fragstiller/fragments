import unittest
import pickle as pkl
from fragments.indicators import *
from fragments.params import ParamStorage


class TestIndicators(unittest.TestCase):
    def test_precalc_toggling(self):
        ohlcv_list = [(0, 0, 0, 1, 0), (0, 0, 0, 2, 0), (0, 0, 0, 1, 0)]

        Indicator.enable_precalculation(ohlcv_list)
        rsi = RSI(ParamStorage())
        self.assertEqual(rsi.forward((0, 0, 0, 1, 0)), None)
        self.assertEqual(rsi.forward((0, 0, 0, 2, 0)), None)
        self.assertEqual(rsi.forward((0, 0, 0, 1, 0)), 50.0)
        Indicator.disable_precalculation()

        rsi.reset()
        self.assertEqual(rsi.forward((0, 0, 0, 1, 0)), None)
        self.assertEqual(rsi.forward((0, 0, 0, 2, 0)), None)
        self.assertEqual(rsi.forward((0, 0, 0, 1, 0)), 50.0)

        Indicator.enable_precalculation(ohlcv_list)
        rsi.reset()
        self.assertEqual(rsi.forward((0, 0, 0, 1, 0)), None)
        self.assertEqual(rsi.forward((0, 0, 0, 2, 0)), None)
        self.assertEqual(rsi.forward((0, 0, 0, 1, 0)), 50.0)
        Indicator.disable_precalculation()

        rsi.reset()
        self.assertEqual(rsi.forward((0, 0, 0, 1, 0)), None)
        self.assertEqual(rsi.forward((0, 0, 0, 2, 0)), None)
        self.assertEqual(rsi.forward((0, 0, 0, 1, 0)), 50.0)

    def test_precalc_rsi(self):
        ohlcv_list = [(0, 0, 0, 1, 0), (0, 0, 0, 2, 0), (0, 0, 0, 1, 0)]
        Indicator.enable_precalculation(ohlcv_list)
        rsi = RSI(ParamStorage())
        self.assertEqual(rsi.forward((0, 0, 0, 1, 0)), None)
        self.assertEqual(rsi.forward((0, 0, 0, 2, 0)), None)
        self.assertEqual(rsi.forward((0, 0, 0, 1, 0)), 50.0)
        Indicator.disable_precalculation()

    def test_rsi(self):
        rsi = RSI(ParamStorage())
        self.assertEqual(rsi.forward((0, 0, 0, 1, 0)), None)
        self.assertEqual(rsi.forward((0, 0, 0, 2, 0)), None)
        self.assertEqual(rsi.forward((0, 0, 0, 1, 0)), 50.0)

    def test_precalc_atr(self):
        with open("./data/GOOG.pkl", "rb") as f:
            ohlcv_list = pkl.load(f)

        Indicator.enable_precalculation(ohlcv_list)
        atr = ATR(ParamStorage())
        atr.period.value = 2
        atr.reset()
        self.assertEqual(atr.forward(ohlcv_list[0]), None)
        self.assertEqual(atr.forward(ohlcv_list[1]), None)
        self.assertAlmostEqual(atr.forward(ohlcv_list[2]), 2.42, 2)  # type: ignore
        Indicator.disable_precalculation()

    # FIXME: why is this so different from TA-Lib's version?
    def test_atr(self):
        with open("./data/GOOG.pkl", "rb") as f:
            ohlcv_list = pkl.load(f)

        atr = ATR(ParamStorage())
        atr.period.value = 2
        atr.reset()
        self.assertEqual(atr.forward(ohlcv_list[0]), None)
        self.assertAlmostEqual(atr.forward(ohlcv_list[1]), 1.87, 2)  # type: ignore
        self.assertAlmostEqual(atr.forward(ohlcv_list[2]), 2.33, 2)  # type: ignore

    def test_precalc_sma(self):
        ohlcv_list = [(0, 0, 0, 1, 0), (0, 0, 0, 2, 0), (0, 0, 0, 1, 0)]
        Indicator.enable_precalculation(ohlcv_list)
        sma = SMA(ParamStorage())
        self.assertEqual(sma.forward((0, 0, 0, 1, 0)), None)
        self.assertEqual(sma.forward((0, 0, 0, 2, 0)), 1.5)
        self.assertEqual(sma.forward((0, 0, 0, 1, 0)), 1.5)
        Indicator.disable_precalculation()

    def test_sma(self):
        sma = SMA(ParamStorage())
        self.assertEqual(sma.forward((0, 0, 0, 1, 0)), None)
        self.assertEqual(sma.forward((0, 0, 0, 2, 0)), 1.5)
        self.assertEqual(sma.forward((0, 0, 0, 1, 0)), 1.5)
