import unittest
from collections import deque
from fragments.params import ParamStorage
from fragments.strategy import (
    Strategy,
    ConditionalStrategy,
    ConditionType,
    Action,
    Trade,
    TradeDirection,
)
from fragments.indicators import RSI
from fragments.stats import *


class TestStats(unittest.TestCase):
    def test_total_profit(self):
        param_storage = ParamStorage()
        strategy = ConditionalStrategy(RSI(param_storage), param_storage)
        strategy.condition_threshold.value = 90
        strategy.condition_type.value = ConditionType.MORE_THAN
        strategy.on_condition.value = Action.BUY

        strategy.forward((0, 0, 0, 1, 0))
        strategy.forward((0, 0, 0, 1, 0))
        strategy.forward((0, 0, 0, 1, 0))
        strategy.forward((0, 0, 0, 2, 0))
        self.assertEqual(total_profit(strategy), 100.0)

    def test_sqn(self):
        param_storage = ParamStorage()
        strategy = Strategy(param_storage)

        def create_trades(*args):
            trades = deque()
            for profit in args:
                trade = Trade(TradeDirection.LONG, 100)
                trade.profit = profit
                trades.append(trade)
            return trades

        strategy.trades = create_trades(100, 50, -100, -50, 100, 150, 50)
        self.assertAlmostEqual(sqn(strategy), 1.38, 2)
