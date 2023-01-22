from typing import Optional
from abc import ABC, abstractmethod
import talipp.indicators
from talipp.ohlcv import OHLCVFactory
from collections import deque
from math import isnan
import numpy as np
import talib
from fragments.params import ParamCell, ParamStorage


OHLCV = tuple[float, float, float, float, float]


class Indicator(ABC):
    param_storage: ParamStorage
    _active: bool
    _precalc: bool = False
    _precalc_iteraion: int
    _precalc_ohlcv: np.ndarray
    _precalc_result: np.ndarray

    def __init__(self, param_storage: ParamStorage):
        self.param_storage = param_storage
        if self._precalc:
            self._precalc_iteraion = 0
        self._active = False

    @classmethod
    def enable_precalculation(cls, ohlcv_list: list[OHLCV]):
        cls._precalc = True
        cls._precalc_ohlcv = np.asarray(ohlcv_list, dtype=np.float64)

    @classmethod
    def disable_precalculation(cls):
        cls._precalc = False
        cls._precalc_ohlcv = None  # type: ignore

    def disable_precalculation_for_self(self):
        self._precalc = False
        cls._precalc_ohlcv = None  # type: ignore

    @abstractmethod
    def reset(self):
        if self._precalc:
            self._precalc_iteraion = 0
        self._active = False

    @abstractmethod
    def forward(self, ohlcv: OHLCV) -> Optional[float]:
        pass


class RSI(Indicator):
    period: ParamCell[int]
    wrapped_indicator: talipp.indicators.RSI
    ohlcv_deque: deque[OHLCV]

    def __init__(self, param_storage: ParamStorage):
        super().__init__(param_storage)
        self.period = self.param_storage.create_cell((2, 20))
        self.reset()

    def reset(self):
        super().reset()
        if self._precalc:
            self._precalc_result = talib.RSI(  # type: ignore
                self._precalc_ohlcv[:, 3], self.period.value
            )
        else:
            self.wrapped_indicator = talipp.indicators.RSI(self.period.value)

    def forward(self, ohlcv: OHLCV) -> Optional[float]:
        if self._precalc:
            if not self._active:
                val = (
                    v
                    if not isnan(v := self._precalc_result[self._precalc_iteraion])
                    else None
                )
                if val is not None:
                    self._active = True
                self._precalc_iteraion += 1
                return val
            self._precalc_iteraion += 1
            return self._precalc_result[self._precalc_iteraion - 1]

        self.wrapped_indicator.add_input_value(ohlcv[3])
        if not self._active:
            if len(self.wrapped_indicator) == 0:
                return None
            else:
                self._active = True
        return self.wrapped_indicator[-1]


class ATR(Indicator):
    period: ParamCell[int]
    wrapped_indicator: talipp.indicators.ATR

    def __init__(self, param_storage: ParamStorage):
        super().__init__(param_storage)
        self.period = self.param_storage.create_cell((5, 50))
        self.reset()

    def reset(self):
        super().reset()
        if self._precalc:
            self._precalc_result = talib.ATR(  # type: ignore
                self._precalc_ohlcv[:, 1],
                self._precalc_ohlcv[:, 2],
                self._precalc_ohlcv[:, 3],
                self.period.value,
            )
        else:
            self.wrapped_indicator = talipp.indicators.ATR(self.period.value)

    def forward(self, ohlcv: OHLCV) -> Optional[float]:
        if self._precalc:
            if not self._active:
                val = (
                    v
                    if not isnan(v := self._precalc_result[self._precalc_iteraion])
                    else None
                )
                if val is not None:
                    self._active = True
                self._precalc_iteraion += 1
                return val
            self._precalc_iteraion += 1
            return self._precalc_result[self._precalc_iteraion - 1]

        self.wrapped_indicator.add_input_value(OHLCVFactory.from_matrix([list(ohlcv)]))
        if not self._active:
            if len(self.wrapped_indicator) == 0:
                return None
            else:
                self._active = True
        return self.wrapped_indicator[-1]


class SMA(Indicator):
    period: ParamCell[int]
    wrapped_indicator: talipp.indicators.SMA

    def __init__(self, param_storage: ParamStorage):
        super().__init__(param_storage)
        self.period = self.param_storage.create_cell((2, 120))
        self.reset()

    def reset(self):
        super().reset()
        if self._precalc:
            self._precalc_result = talib.SMA(  # type: ignore
                self._precalc_ohlcv[:, 3], self.period.value
            )
        else:
            self.wrapped_indicator = talipp.indicators.SMA(self.period.value)

    def forward(self, ohlcv: OHLCV) -> Optional[float]:
        if self._precalc:
            if not self._active:
                val = (
                    v
                    if not isnan(v := self._precalc_result[self._precalc_iteraion])
                    else None
                )
                if val is not None:
                    self._active = True
                self._precalc_iteraion += 1
                return val
            self._precalc_iteraion += 1
            return self._precalc_result[self._precalc_iteraion - 1]

        self.wrapped_indicator.add_input_value(ohlcv[3])
        if not self._active:
            if len(self.wrapped_indicator) == 0:
                return None
            else:
                self._active = True
        return self.wrapped_indicator[-1]
