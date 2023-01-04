import unittest
from fragments.params import ParamStorage
from fragments.strategy import ConditionalStrategy, ConditionType, Action
from fragments.indicators import RSI
from fragments.stats import total_profit


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
