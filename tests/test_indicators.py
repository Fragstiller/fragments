import unittest
from fragments.indicators import *
from fragments.params import ParamStorage


class TestIndicators(unittest.TestCase):
    def test_rsi(self):
        rsi = RSI(ParamStorage())
        self.assertEqual(rsi.forward((0, 0, 0, 1, 0)), None)
        self.assertEqual(rsi.forward((0, 0, 0, 2, 0)), None)
        self.assertEqual(rsi.forward((0, 0, 0, 1, 0)), 50.0)

    def test_atr(self):
        atr = ATR(ParamStorage())
        self.assertEqual(atr.forward((0, 0, 0, 1, 0)), None)
        self.assertEqual(atr.forward((0, 0, 0, 2, 0)), 0.5)
        self.assertEqual(atr.forward((0, 0, 0, 1, 0)), 1.25)

    def test_sma(self):
        atr = SMA(ParamStorage())
        self.assertEqual(atr.forward((0, 0, 0, 1, 0)), None)
        self.assertEqual(atr.forward((0, 0, 0, 2, 0)), 1.5)
        self.assertEqual(atr.forward((0, 0, 0, 1, 0)), 1.5)
