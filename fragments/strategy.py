from __future__ import annotations
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC
from fragments.optim import ParamCell, ParamStorage
from fragments.indicator import Indicator, OHLCV


class Action(Enum):
    BUY = 1
    SELL = 2
    CANCEL = 3
    PASS = 4


class TradeDirection(Enum):
    LONG = 1
    SHORT = 2


@dataclass
class Trade:
    direction: TradeDirection
    value: float
    profit: float = field(init=False, default=0.0)
    liquidation: bool = field(init=False, default=False)
    _prev_ohlcv: OHLCV | None = field(init=False, default=None)

    def forward(self, ohlcv: OHLCV):
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
                    (self.value + self.profit) * (ohlcv[3] / self._prev_ohlcv[3])
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
    trades: list[Trade]
    _in_trade: bool = False

    def __init__(
        self, param_storage: ParamStorage, previous: Optional[Strategy] = None
    ):
        self.param_storage = param_storage
        self.trades = list()
        if previous is not None:
            self.previous = previous
        else:
            self.previous = None

    def forward(self, ohlcv: OHLCV):
        if self.previous is not None:
            self.previous.forward(ohlcv)

    def _apply_action(self, ohlcv: OHLCV, action: Action):
        if self.previous is not None:
            if self.previous.action == action:
                self.action = action
            elif self.previous.action == Action.CANCEL:
                self.action = Action.CANCEL
        else:
            self.action = action
        match self.action:
            case Action.BUY:
                if (
                    self._in_trade == False
                    or self.trades[-1].direction == TradeDirection.SHORT
                ):
                    self._in_trade = True
                    self.trades.append(Trade(TradeDirection.LONG, 100.0))
            case Action.SELL:
                if (
                    self._in_trade == False
                    or self.trades[-1].direction == TradeDirection.LONG
                ):
                    self._in_trade = True
                    self.trades.append(Trade(TradeDirection.SHORT, 100.0))
            case Action.CANCEL:
                self._in_trade = False
        if self._in_trade:
            self.trades[-1].forward(ohlcv)


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
