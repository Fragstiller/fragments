from typing import Optional
from abc import ABC, abstractmethod
import talipp.indicators
from talipp.ohlcv import OHLCVFactory
from fragments.params import ParamCell, ParamStorage


OHLCV = tuple[float, float, float, float, float]


class Indicator(ABC):
    param_storage: ParamStorage

    def __init__(self, param_storage: ParamStorage):
        self.param_storage = param_storage

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def forward(self, ohlcv: OHLCV) -> Optional[float]:
        pass


class RSI(Indicator):
    period: ParamCell[int]
    wrapped_indicator: talipp.indicators.RSI

    def __init__(self, param_storage: ParamStorage):
        super().__init__(param_storage)
        self.period = self.param_storage.create_cell((2, 240))
        self.wrapped_indicator = talipp.indicators.RSI(self.period.value)

    def reset(self):
        self.wrapped_indicator = talipp.indicators.RSI(self.period.value)

    def forward(self, ohlcv: OHLCV) -> Optional[float]:
        if self.period.value != self.wrapped_indicator.period:
            self.wrapped_indicator = talipp.indicators.RSI(self.period.value)
        self.wrapped_indicator.add_input_value(ohlcv[3])
        if len(self.wrapped_indicator) == 0:
            return None
        return self.wrapped_indicator[-1]


class ATR(Indicator):
    period: ParamCell[int]
    wrapped_indicator: talipp.indicators.ATR

    def __init__(self, param_storage: ParamStorage):
        super().__init__(param_storage)
        self.period = self.param_storage.create_cell((2, 240))
        self.wrapped_indicator = talipp.indicators.ATR(self.period.value)

    def reset(self):
        self.wrapped_indicator = talipp.indicators.ATR(self.period.value)

    def forward(self, ohlcv: OHLCV) -> Optional[float]:
        if self.period.value != self.wrapped_indicator.period:
            self.wrapped_indicator = talipp.indicators.ATR(self.period.value)
        self.wrapped_indicator.add_input_value(OHLCVFactory.from_matrix([list(ohlcv)]))
        if len(self.wrapped_indicator) == 0:
            return None
        return self.wrapped_indicator[-1]


class SMA(Indicator):
    period: ParamCell[int]
    wrapped_indicator: talipp.indicators.SMA

    def __init__(self, param_storage: ParamStorage):
        super().__init__(param_storage)
        self.period = self.param_storage.create_cell((2, 240))
        self.wrapped_indicator = talipp.indicators.SMA(self.period.value)

    def reset(self):
        self.wrapped_indicator = talipp.indicators.SMA(self.period.value)

    def forward(self, ohlcv: OHLCV) -> Optional[float]:
        if self.period.value != self.wrapped_indicator.period:
            self.wrapped_indicator = talipp.indicators.SMA(self.period.value)
        self.wrapped_indicator.add_input_value(ohlcv[3])
        if len(self.wrapped_indicator) == 0:
            return None
        return self.wrapped_indicator[-1]
