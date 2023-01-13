import unittest
from fragments.strategy import *


class TestTrade(unittest.TestCase):
    def test_trade_long_pos(self):
        trade = Trade(TradeDirection.LONG, 100.0)
        trade.forward((0, 0, 0, 1, 0))
        trade.forward((0, 0, 0, 0.5, 0))
        trade.forward((0, 0, 0, 1, 0))
        trade.forward((0, 0, 0, 2, 0))
        self.assertEqual(trade.profit, 100.0)

    def test_trade_long_neg(self):
        trade = Trade(TradeDirection.LONG, 100.0)
        trade.forward((0, 0, 0, 1, 0))
        trade.forward((0, 0, 0, 2, 0))
        trade.forward((0, 0, 0, 1, 0))
        trade.forward((0, 0, 0, 0.5, 0))
        self.assertEqual(trade.profit, -50.0)

    def test_trade_short_pos(self):
        trade = Trade(TradeDirection.SHORT, 100.0)
        trade.forward((0, 0, 0, 1, 0))
        trade.forward((0, 0, 0, 1.5, 0))
        trade.forward((0, 0, 0, 1, 0))
        trade.forward((0, 0, 0, 0.5, 0))
        self.assertEqual(trade.profit, 50.0)

    def test_trade_short_neg(self):
        trade = Trade(TradeDirection.SHORT, 100.0)
        trade.forward((0, 0, 0, 1, 0))
        trade.forward((0, 0, 0, 0.5, 0))
        trade.forward((0, 0, 0, 1, 0))
        trade.forward((0, 0, 0, 2, 0))
        self.assertEqual(trade.profit, -100.0)

    def test_trade_long_liq(self):
        trade = Trade(TradeDirection.LONG, 100.0)
        trade.forward((0, 0, 0, 1, 0))
        trade.forward((0, 0, 0, 2, 0))
        trade.forward((0, 0, 0, 1, 0))
        trade.forward((0, 0, 0, 0, 0))
        self.assertEqual(trade.profit, -100.0)
        self.assertEqual(trade.liquidation, True)
        trade.forward((0, 0, 0, -1, 0))
        self.assertEqual(trade.profit, -100.0)

    def test_trade_short_liq(self):
        trade = Trade(TradeDirection.SHORT, 100.0)
        trade.forward((0, 0, 0, 1, 0))
        trade.forward((0, 0, 0, 0.5, 0))
        trade.forward((0, 0, 0, 1, 0))
        trade.forward((0, 0, 0, 2, 0))
        self.assertEqual(trade.profit, -100.0)
        self.assertEqual(trade.liquidation, True)
        trade.forward((0, 0, 0, 5, 0))
        self.assertEqual(trade.profit, -100.0)
