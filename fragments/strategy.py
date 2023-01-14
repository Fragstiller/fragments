from __future__ import annotations
from typing import Optional
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
from abc import ABC
from fragments.params import ParamCell, ParamStorage
from fragments.indicators import Indicator, OHLCV


class Action(Enum):
    BUY = 1
    SELL = 2
    CANCEL = 3
    PASS = 4


class ActionLogic(Enum):
    AND = 1
    OR = 2
    IGNORE = 3


class TradeDirection(Enum):
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

    def _apply_action(self, ohlcv: OHLCV, action: Action, logic_only: bool = False):
        if self.previous is not None and self.action_logic is not None:
            if self.previous.action == action:
                self.action = action
            else:
                self.action = Action.PASS
            match self.action_logic.value:
                case ActionLogic.OR:
                    if action == Action.PASS:
                        self.action = self.previous.action
                case ActionLogic.IGNORE:
                    if action == Action.PASS:
                        self.action = self.previous.action
                    else:
                        self.action = action
        else:
            self.action = action

        if logic_only:
            return

        match self.action:
            case Action.BUY:
                if (
                    self._in_trade == False
                    or self.trades[-1].direction == TradeDirection.SHORT
                ):
                    self._in_trade = True
                    self.trades.append(
                        Trade(TradeDirection.LONG, self.equity, self.iteration)
                    )
            case Action.SELL:
                if (
                    self._in_trade == False
                    or self.trades[-1].direction == TradeDirection.LONG
                ):
                    self._in_trade = True
                    self.trades.append(
                        Trade(TradeDirection.SHORT, self.equity, self.iteration)
                    )
            case Action.CANCEL:
                self._in_trade = False
        if self._in_trade:
            self.trades[-1].forward(ohlcv)
            self.equity = self.trades[-1].value + self.trades[-1].profit
        self.hist_equity.append(self.equity)


class ConditionType(Enum):
    LESS_THAN = 1
    MORE_THAN = 2


class ConditionalStrategy(Strategy):
    indicator: Indicator
    condition_threshold: ParamCell[int]
    condition_type: ParamCell[ConditionType]
    on_condition: ParamCell[Action]

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

    def reset(self):
        super().reset()
        self.indicator.reset()

    def forward(self, ohlcv: OHLCV):
        super().forward(ohlcv)
        action = Action.PASS
        indicator_value = self.indicator.forward(ohlcv)
        if indicator_value is not None:
            assert isinstance(self.condition_threshold.bounds, tuple)
            if int(indicator_value) < self.condition_threshold.bounds[0]:
                self.condition_threshold.bounds = (
                    int(indicator_value),
                    self.condition_threshold.bounds[1],
                )
            elif int(indicator_value) > self.condition_threshold.bounds[1]:
                self.condition_threshold.bounds = (
                    self.condition_threshold.bounds[0],
                    int(indicator_value),
                )
            match self.condition_type.value:
                case ConditionType.LESS_THAN:
                    if indicator_value < self.condition_threshold.value:
                        action = self.on_condition.value
                case ConditionType.MORE_THAN:
                    if indicator_value >= self.condition_threshold.value:
                        action = self.on_condition.value
        self._apply_action(ohlcv, action)


class LimiterType(Enum):
    StopLoss = 1
    TakeProfit = 2


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
        action = Action.PASS
        indicator_value = self.indicator.forward(ohlcv)
        if len(self.trades) != 0:
            if self.trades[-1].profit == 0 and indicator_value is not None:
                self._limiter_threshold = indicator_value * (
                    self.limiter_multiplier.value / 100
                )
            if (
                self.limiter_type.value == LimiterType.StopLoss
                and self.trades[-1].profit <= -self._limiter_threshold
            ):
                action = Action.CANCEL
            elif self.trades[-1].profit > self._limiter_threshold:
                action = Action.CANCEL
        self._apply_action(ohlcv, action)


class CrossoverDirection(Enum):
    UP = 1
    DOWN = 2
    BOTH = 3


class CrossoverHandling(Enum):
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
        action = Action.PASS
        first_value = self.first_indicator.forward(ohlcv)
        second_value = self.second_indicator.forward(ohlcv)
        if first_value is not None and second_value is not None:
            if self._prev_first_value is None or self._prev_second_value is None:
                self._prev_first_value = first_value
                self._prev_second_value = second_value
            elif (
                self._prev_first_value is not None
                and self._prev_second_value is not None
            ):
                if (
                    self._prev_first_value <= self._prev_second_value
                    and first_value > second_value
                    and self.crossover_direction.value
                    in [CrossoverDirection.UP, CrossoverDirection.BOTH]
                ):
                    if self.crossover_handling.value == CrossoverHandling.REGULAR:
                        action = Action.BUY
                    else:
                        action = Action.SELL
                elif (
                    self._prev_first_value >= self._prev_second_value
                    and first_value < second_value
                    and self.crossover_direction.value
                    in [CrossoverDirection.DOWN, CrossoverDirection.BOTH]
                ):
                    if self.crossover_handling.value == CrossoverHandling.REGULAR:
                        action = Action.SELL
                    else:
                        action = Action.BUY
        self._apply_action(ohlcv, action)


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
        self._apply_action(ohlcv, Action.PASS, logic_only=True)
        if self.indicator is not None:
            processed_equity = self.indicator.forward((0, 0, 0, self.equity, 0))
        else:
            processed_equity = self.equity
        if processed_equity is not None:
            if processed_equity > self._peak_equity:
                self._peak_equity = self.equity
                self._drawdown_duration = 0
            else:
                self._drawdown_duration += 1
        if (
            self._drawdown_duration
            > self.invert_drawdown_duration.value * self.duration_multiplier.value
        ):
            self._invert = not self._invert
        action = Action.PASS
        if self._invert:
            if self.action == Action.BUY:
                action = Action.SELL
            elif self.action == Action.SELL:
                action = Action.BUY
        self._apply_action(ohlcv, action)
