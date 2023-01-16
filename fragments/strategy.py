from __future__ import annotations
from typing import Optional
from dataclasses import dataclass, field
from collections import deque
from enum import Enum, IntEnum
from abc import ABC
from fragments import cproc
from fragments.params import ParamCell, ParamStorage
from fragments.indicators import Indicator, OHLCV


class Action(IntEnum):
    BUY = 1
    SELL = 2
    CANCEL = 3
    PASS = 4


class ActionLogic(IntEnum):
    AND = 1
    OR = 2
    IGNORE = 3


class TradeDirection(IntEnum):
    LONG = 1
    SHORT = 2


@dataclass
class Trade:
    direction: TradeDirection
    value: float
    iteration: int = field(default=0)
    profit: float = field(init=False, default=0.0)
    liquidation: bool = field(init=False, default=False)
    duration: int = field(init=False, default=0)
    _prev_ohlcv: OHLCV | None = field(init=False, default=None)

    def forward(self, ohlcv: OHLCV):
        self.duration += 1
        if self.liquidation:
            return
        if self._prev_ohlcv is None:
            self._prev_ohlcv = ohlcv
            return
        match self.direction:
            case TradeDirection.LONG:
                self.profit = (self.value + self.profit) * (
                    ohlcv[3] / self._prev_ohlcv[3]
                ) - self.value
            case TradeDirection.SHORT:
                self.profit = -(
                    (self.value - self.profit) * (ohlcv[3] / self._prev_ohlcv[3])
                    - self.value
                )
        self._prev_ohlcv = ohlcv
        if self.profit <= -self.value:
            self.liquidation = True
            self.profit = -self.value


class Strategy(ABC):
    param_storage: ParamStorage
    previous: Optional[Strategy]
    action: Action
    action_logic: Optional[ParamCell[ActionLogic]]
    trades: deque[Trade]
    iteration: int = 0
    equity: float = 100.0
    hist_equity: deque[float]
    _in_trade: bool = False

    def __init__(
        self, param_storage: ParamStorage, previous: Optional[Strategy] = None
    ):
        self.param_storage = param_storage
        self.trades = deque()
        self.hist_equity = deque()
        if previous is not None:
            self.previous = previous
            self.action_logic = self.param_storage.create_default_categorical_cell(
                ActionLogic
            )
        else:
            self.previous = None
            self.action_logic = None

    def forward(self, ohlcv: OHLCV):
        self.iteration += 1
        if self.previous is not None:
            self.previous.forward(ohlcv)

    def forward_all(self, ohlcv_list: list[OHLCV]):
        for ohlcv in ohlcv_list:
            self.forward(ohlcv)

    def update_and_forward_all(
        self, values: list[int | Enum], ohlcv_list: list[OHLCV]
    ) -> Strategy:
        self.reset()
        self.param_storage.apply_cell_values(values)
        self.forward_all(ohlcv_list)
        return self

    def reset(self):
        if self.previous is not None:
            self.previous.reset()
        self.trades = deque()
        self.iteration = 0
        self.equity = 100.0
        self.hist_equity = deque()
        self._in_trade = False

    def _new_trade(self, direction: TradeDirection):
        self.trades.append(Trade(direction, self.equity, self.iteration))


class ConditionType(IntEnum):
    LESS_THAN = 1
    MORE_THAN = 2


class ConditionalStrategy(Strategy):
    indicator: Indicator
    condition_threshold: ParamCell[int]
    condition_type: ParamCell[ConditionType]
    on_condition: ParamCell[Action]
    _freeze_bounds: bool

    def __init__(
        self,
        indicator: Indicator,
        param_storage: ParamStorage,
        previous: Optional[Strategy] = None,
    ):
        super().__init__(param_storage, previous)
        self.indicator = indicator
        self.condition_threshold = self.param_storage.create_default_numerical_cell()
        self.condition_type = self.param_storage.create_default_categorical_cell(
            ConditionType
        )
        self.on_condition = self.param_storage.create_default_categorical_cell(Action)
        self._freeze_bounds = False

    def reset(self):
        super().reset()
        self.indicator.reset()

    def forward_all(self, ohlcv_list: list[OHLCV]):
        for ohlcv in ohlcv_list:
            self.forward(ohlcv)
        self._freeze_bounds = True

    def forward(self, ohlcv: OHLCV):
        super().forward(ohlcv)
        cproc.forward_conditional(self, ohlcv, self._freeze_bounds)


class LimiterType(IntEnum):
    STOP_LOSS = 1
    TAKE_PROFIT = 2


class LimiterStrategy(Strategy):
    indicator: Indicator
    limiter_multiplier: ParamCell[int]
    limiter_type: ParamCell[LimiterType]
    _limiter_threshold: float

    def __init__(
        self,
        indicator: Indicator,
        param_storage: ParamStorage,
        previous: Optional[Strategy] = None,
    ):
        super().__init__(param_storage, previous)
        self.indicator = indicator
        self.limiter_multiplier = self.param_storage.create_cell((10, 200), 100)
        self.limiter_type = self.param_storage.create_default_categorical_cell(
            LimiterType
        )
        if self.action_logic is not None:
            self.action_logic.value = ActionLogic.IGNORE
            self.action_logic.bounds = [ActionLogic.IGNORE]

    def reset(self):
        super().reset()
        self.indicator.reset()

    def forward(self, ohlcv: OHLCV):
        super().forward(ohlcv)
        cproc.forward_limiter(self, ohlcv)


class CrossoverDirection(IntEnum):
    UP = 1
    DOWN = 2
    BOTH = 3


class CrossoverHandling(IntEnum):
    REGULAR = 1
    INVERTED = 2


class CrossoverStrategy(Strategy):
    first_indicator: Indicator
    second_indicator: Indicator
    crossover_direction: ParamCell[CrossoverDirection]
    crossover_handling: ParamCell[CrossoverHandling]
    _prev_first_value: float | None = None
    _prev_second_value: float | None = None

    def __init__(
        self,
        first_indicator: Indicator,
        second_indicator: Indicator,
        param_storage: ParamStorage,
        previous: Optional[Strategy] = None,
    ):
        super().__init__(param_storage, previous)
        self.first_indicator = first_indicator
        self.second_indicator = second_indicator
        self.crossover_direction = self.param_storage.create_default_categorical_cell(
            CrossoverDirection
        )
        self.crossover_handling = self.param_storage.create_default_categorical_cell(
            CrossoverHandling
        )

    def reset(self):
        super().reset()
        self._prev_first_value = None
        self._prev_second_value = None
        self.first_indicator.reset()
        self.second_indicator.reset()

    def forward(self, ohlcv: OHLCV):
        super().forward(ohlcv)
        cproc.forward_crossover(self, ohlcv)


class InvertingStrategy(Strategy):
    indicator: Optional[Indicator] = None
    invert_drawdown_duration: ParamCell[int]
    duration_multiplier: ParamCell[int]
    _peak_equity: float = 0
    _drawdown_duration: int = 0
    _invert: bool = False

    def __init__(
        self,
        param_storage: ParamStorage,
        indicator: Optional[Indicator] = None,
        previous: Optional[Strategy] = None,
    ):
        super().__init__(param_storage, previous)
        if indicator is not None:
            self.indicator = indicator
        self.invert_drawdown_duration = self.param_storage.create_cell((7, 90))
        self.duration_multiplier = self.param_storage.create_cell((1, 1440))
        if self.action_logic is not None:
            self.action_logic.value = ActionLogic.IGNORE
            self.action_logic.bounds = [ActionLogic.IGNORE]

    def reset(self):
        super().reset()
        self._peak_equity = 0
        self._drawdown_duration = 0
        if self.indicator is not None:
            self.indicator.reset()

    def forward(self, ohlcv: OHLCV):
        super().forward(ohlcv)
        cproc.forward_inverting(self, ohlcv)
