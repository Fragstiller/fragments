import unittest
import pickle as pkl
from fragments.params import ParamStorage
from fragments.strategy import ConditionalStrategy
from fragments.indicators import RSI
from fragments.stats import total_profit
from fragments.optim import *


class TestOptim(unittest.TestCase):
    def test_optim(self):
        param_storage = ParamStorage()

        strategies = list()
        strategies.append(ConditionalStrategy(RSI(param_storage), param_storage))
        strategies.append(
            ConditionalStrategy(RSI(param_storage), param_storage, strategies[0])
        )

        with open("./data/GOOG.pkl", "rb") as f:
            ohlcv_list = pkl.load(f)

        self.assertAlmostEqual(
            optimize(strategies[-1], total_profit, ohlcv_list, 42).fun, 0.0330, 4
        )
