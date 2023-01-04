import unittest
from fragments.indicators import *
from fragments.params import ParamStorage


class TestIndicators(unittest.TestCase):
    def test_rsi(self):
        rsi = RSI(ParamStorage())
        self.assertEqual(rsi.forward((0, 0, 0, 1, 0)), None)
        self.assertEqual(rsi.forward((0, 0, 0, 2, 0)), None)
        self.assertEqual(rsi.forward((0, 0, 0, 1, 0)), 50.0)
