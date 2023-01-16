import skopt
import warnings
from skopt.space.space import Categorical
from scipy.optimize import OptimizeResult
from enum import Enum
from typing import Callable
from fragments.strategy import Strategy
from fragments.indicators import OHLCV, Indicator


def convert_cell_bounds_skopt(
    cell_bounds: list[tuple[int, int] | list[Enum]]
) -> list[tuple[int, int] | Categorical]:
    converted_bounds = list()
    for bounds in cell_bounds:
        if isinstance(bounds, list):
            converted_bounds.append(Categorical(bounds))
        else:
            converted_bounds.append(bounds)
    return converted_bounds


def optimize(
    strategy: Strategy,
    func: Callable[[Strategy], float],
    ohlcv_list: list[OHLCV],
    **kwargs
) -> OptimizeResult:
    Indicator.enable_precalculation(ohlcv_list)
    strategy.forward_all(ohlcv_list)
    strategy.reset()
    optim_func: Callable[[list[int | Enum]], float] = lambda values: 1 / max(
        1e-8, func(strategy.update_and_forward_all(values, ohlcv_list))
    )
    with warnings.catch_warnings():  # FIXME: should be removed as soon as skopt is updated to no longer use np.int
        warnings.simplefilter("ignore")
        results = skopt.gp_minimize(
            optim_func,
            convert_cell_bounds_skopt(strategy.param_storage.get_cell_bounds()),
            **kwargs
        )
    if results is None:
        raise RuntimeError("skopt.gp_minimize didn't return a result")
    strategy.update_and_forward_all(results.x, ohlcv_list)
    Indicator.disable_precalculation()
    return results
