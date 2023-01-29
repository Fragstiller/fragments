import unittest
from enum import Enum
from fragments.params import *
from fragments.strategy import ConditionalStrategy
from fragments.indicators import RSI


class TestCategory(Enum):
    FIRST = 1
    SECOND = 2
    THIRD = 3


class TestParamStorage(unittest.TestCase):
    def test_storage_numerical(self):
        param_storage = ParamStorage()
        cells = list()

        cells.append(param_storage.create_cell((30, 100), 50))
        cells.append(param_storage.create_cell((2, 100)))
        cells.append(param_storage.create_default_numerical_cell())
        self.assertEqual([cell.value for cell in cells], [50, 2, 0])

        param_storage.apply_cell_values([20, 30, 40])
        self.assertEqual([cell.value for cell in cells], [20, 30, 40])

        bounds = param_storage.get_cell_bounds()
        self.assertEqual(bounds, [(30, 100), (2, 100), (0, 1)])

    def test_storage_categorical(self):
        param_storage = ParamStorage()
        cells = list()

        cells.append(
            param_storage.create_cell(
                [TestCategory.FIRST, TestCategory.SECOND, TestCategory.THIRD],
                TestCategory.SECOND,
            )
        )
        cells.append(
            param_storage.create_cell(
                [TestCategory.FIRST, TestCategory.SECOND, TestCategory.THIRD]
            )
        )
        cells.append(param_storage.create_default_categorical_cell(TestCategory))
        self.assertEqual(
            [cell.value for cell in cells],
            [TestCategory.SECOND, TestCategory.FIRST, TestCategory.FIRST],
        )

        param_storage.apply_cell_values(
            [TestCategory.FIRST, TestCategory.SECOND, TestCategory.THIRD]
        )
        self.assertEqual(
            [cell.value for cell in cells],
            [TestCategory.FIRST, TestCategory.SECOND, TestCategory.THIRD],
        )

        bounds = param_storage.get_cell_bounds()
        self.assertEqual(
            bounds,
            [
                [TestCategory.FIRST, TestCategory.SECOND, TestCategory.THIRD],
                [TestCategory.FIRST, TestCategory.SECOND, TestCategory.THIRD],
                [TestCategory.FIRST, TestCategory.SECOND, TestCategory.THIRD],
            ],
        )

    def test_storage_mixed(self):
        param_storage = ParamStorage()
        cells = list()

        cells.append(param_storage.create_cell((30, 100)))
        cells.append(param_storage.create_default_categorical_cell(TestCategory))
        self.assertEqual([cell.value for cell in cells], [30, TestCategory.FIRST])

        param_storage.apply_cell_values([50, TestCategory.SECOND])
        self.assertEqual([cell.value for cell in cells], [50, TestCategory.SECOND])

        bounds = param_storage.get_cell_bounds()
        self.assertEqual(
            bounds,
            [(30, 100), [TestCategory.FIRST, TestCategory.SECOND, TestCategory.THIRD]],
        )

    def test_global_storage(self):
        strategy_1 = ConditionalStrategy(RSI())
        self.assertTrue(strategy_1.param_storage is ParamStorage.global_storage)
        self.assertTrue(
            strategy_1.indicator.param_storage is ParamStorage.global_storage
        )
        ParamStorage.new_global()
        strategy_2 = ConditionalStrategy(RSI())
        self.assertTrue(strategy_1.param_storage is not strategy_2.param_storage)
        self.assertTrue(
            strategy_1.indicator.param_storage is not strategy_2.indicator.param_storage
        )
        param_storage = ParamStorage()
        strategy_3 = ConditionalStrategy(
            RSI(param_storage=param_storage), param_storage=param_storage
        )
        self.assertTrue(strategy_3.param_storage is param_storage)
        self.assertTrue(strategy_3.indicator.param_storage is param_storage)
