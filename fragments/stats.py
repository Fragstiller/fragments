from fragments.strategy import Strategy, TradeDirection
from fragments.indicators import OHLCV
from typing import Any
import matplotlib.pyplot as plt
import numpy as np


def total_profit(strategy: Strategy) -> float:
    return sum([trade.profit for trade in strategy.trades])


def equity(strategy: Strategy) -> float:
    return strategy.equity


def plot(strategy: Strategy, ohlcv_list: list[OHLCV]):
    plt.style.use("fast")
    fig, (ax1, ax2) = plt.subplots(
        2, 1, sharex=True, figsize=(15, 7), gridspec_kw={"height_ratios": [1, 2]}
    )
    ohlcv = np.array(ohlcv_list)
    if strategy.iteration != len(ohlcv_list):
        raise RuntimeError(
            f"amount of iterations in strategy must match length of OHLCV list: {strategy.iteration} != {len(ohlcv_list)}"
        )

    ax1.set_ylabel("Equity (%)")
    ax1.plot(strategy.hist_equity, c="0.2", lw=1)

    ax2.set_ylabel("Asset Value ($)")
    ax2.set_xlabel("Iteration")
    ax2.plot(ohlcv[:, 3], c="0.2", lw=1)

    trades_long = []
    trades_short = []
    for trade in strategy.trades:
        match trade.direction:
            case TradeDirection.LONG:
                trades_long.append(trade.iteration - 1)
            case TradeDirection.SHORT:
                trades_short.append(trade.iteration - 1)
        if trade.profit >= 0:
            ax2.plot(
                (i := [trade.iteration - 1, trade.iteration + trade.duration - 2]),
                ohlcv[:, 3][np.array(i)],
                c="limegreen",
                lw=1,
                ls="--",
            )
        else:
            ax2.plot(
                (i := [trade.iteration - 1, trade.iteration + trade.duration - 2]),
                ohlcv[:, 3][np.array(i)],
                c="firebrick",
                lw=1,
                ls="--",
            )
    if len(trades_short) != 0:
        ax2.scatter(
            np.array(trades_short),
            ohlcv[:, 3][np.array(trades_short)],
            c="red",
            s=2.5,
            zorder=10,
        )
    if len(trades_long) != 0:
        ax2.scatter(
            np.array(trades_long),
            ohlcv[:, 3][np.array(trades_long)],
            c="lime",
            s=2.5,
            zorder=10,
        )
