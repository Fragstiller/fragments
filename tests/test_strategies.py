import unittest
from fragments.strategy import *
from typing import cast
from fragments.indicators import RSI, ATR, SMA
from fragments.params import ParamStorage


class TestStrategies(unittest.TestCase):
    def test_conditional_strategy_and_actions(self):
        param_storage = ParamStorage()
        strategy = ConditionalStrategy(RSI(param_storage), param_storage)
        strategy.condition_threshold.value = 90
        strategy.condition_type.value = ConditionType.MORE_THAN
        strategy.on_condition.value = Action.BUY

        strategy.forward((0, 0, 0, 1, 0))
        self.assertEqual(len(strategy.trades), 0)
        strategy.forward((0, 0, 0, 1, 0))
        self.assertEqual(len(strategy.trades), 0)
        strategy.forward((0, 0, 0, 1, 0))
        self.assertEqual(len(strategy.trades), 1)
        strategy.forward((0, 0, 0, 1, 0))
        self.assertEqual(len(strategy.trades), 1)

    def test_crossover_strategy(self):
        param_storage = ParamStorage()
        strategy = CrossoverStrategy(
            SMA(param_storage), SMA(param_storage), param_storage
        )
        cast(SMA, strategy.first_indicator).period.value = 2
        cast(SMA, strategy.second_indicator).period.value = 3

        strategy.reset()

        strategy.forward((0, 0, 0, 1, 0))
        self.assertEqual(len(strategy.trades), 0)
        strategy.forward((0, 0, 0, 1, 0))
        self.assertEqual(len(strategy.trades), 0)
        strategy.forward((0, 0, 0, 1, 0))
        self.assertEqual(len(strategy.trades), 0)
        strategy.forward((0, 0, 0, 2, 0))
        self.assertEqual(len(strategy.trades), 1)

    def test_limiter_strategy(self):
        param_storage = ParamStorage()
        strategies = list()

        strategies.append(ConditionalStrategy(RSI(param_storage), param_storage))
        strategies[0].condition_type.value = ConditionType.MORE_THAN
        strategies[0].on_condition.value = Action.BUY
        cast(RSI, strategies[0].indicator).period.value = 2

        strategies.append(
            LimiterStrategy(ATR(param_storage), param_storage, strategies[0])
        )
        strategies[1].limiter_type.value = LimiterType.TAKE_PROFIT

        strategies[1].reset()

        strategies[1].forward((0, 0, 0, 1, 0))
        strategies[1].forward((0, 0, 0, 2, 0))
        strategies[1].forward((0, 0, 0, 1, 0))
        strategies[1].forward((0, 0, 0, 2, 0))
        strategies[1].forward((0, 0, 0, 3, 0))
        strategies[1].forward((0, 0, 0, 0, 0))

        self.assertEqual(strategies[1].trades[-1].profit, 100)

    def test_inverting_strategy(self):
        param_storage = ParamStorage()

        strategies = list()

        strategies.append(ConditionalStrategy(RSI(param_storage), param_storage))
        strategies[0].condition_type.value = ConditionType.MORE_THAN
        strategies[0].on_condition.value = Action.BUY

        strategies.append(
            ConditionalStrategy(RSI(param_storage), param_storage, strategies[0])
        )
        strategies[1].condition_type.value = ConditionType.MORE_THAN
        strategies[1].on_condition.value = Action.BUY
        cast(RSI, strategies[1].indicator).period.value = 15

        strategies.append(InvertingStrategy(param_storage, previous=strategies[1]))

        strategies[2].reset()

        strategies[2].forward((0, 0, 0, 1, 0))
        strategies[2].forward((0, 0, 0, 1, 0))
        strategies[2].forward((0, 0, 0, 1, 0))
        for _ in range(3):
            strategies[2].forward((0, 0, 0, 1, 0))
        for _ in range(13):
            strategies[2].forward((0, 0, 0, 0.5, 0))
        self.assertEqual(strategies[2].action, Action.SELL)

    def test_conditional_strategy_bounds(self):
        param_storage = ParamStorage()
        strategy = ConditionalStrategy(RSI(param_storage), param_storage)

        strategy.forward((0, 0, 0, 1, 0))
        strategy.forward((0, 0, 0, 1, 0))
        strategy.forward((0, 0, 0, 1, 0))
        self.assertEqual(strategy.condition_threshold.bounds, (0, 100))

    def test_strategy_chaining(self):
        param_storage = ParamStorage()

        strategies = list()

        strategies.append(ConditionalStrategy(RSI(param_storage), param_storage))
        strategies[0].condition_type.value = ConditionType.MORE_THAN
        strategies[0].on_condition.value = Action.BUY
        cast(RSI, strategies[0].indicator).period.value = 3

        strategies.append(
            ConditionalStrategy(RSI(param_storage), param_storage, strategies[0])
        )
        strategies[1].condition_type.value = ConditionType.MORE_THAN
        strategies[1].on_condition.value = Action.BUY

        strategies.append(
            ConditionalStrategy(RSI(param_storage), param_storage, strategies[1])
        )
        cast(RSI, strategies[2].indicator).period.value = 4
        strategies[2].condition_type.value = ConditionType.MORE_THAN
        strategies[2].on_condition.value = Action.CANCEL

        strategies.append(
            ConditionalStrategy(RSI(param_storage), param_storage, strategies[2])
        )
        cast(RSI, strategies[3].indicator).period.value = 5
        strategies[3].condition_type.value = ConditionType.MORE_THAN
        strategies[3].on_condition.value = Action.BUY

        strategies[3].reset()

        strategies[3].forward((0, 0, 0, 1, 0))
        strategies[3].forward((0, 0, 0, 1, 0))
        strategies[3].forward((0, 0, 0, 1, 0))
        self.assertEqual(len(strategies[1].trades), 0)
        strategies[3].forward((0, 0, 0, 1, 0))
        self.assertEqual(len(strategies[1].trades), 1)
        strategies[3].forward((0, 0, 0, 1, 0))
        strategies[3].forward((0, 0, 0, 1, 0))
        self.assertEqual(len(strategies[1].trades), 1)
