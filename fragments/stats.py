from fragments.strategy import Strategy, TradeDirection
from fragments.indicators import OHLCV
import matplotlib.pyplot as plt
import numpy as np


def total_profit(strategy: Strategy) -> float:
    return sum([trade.profit for trade in strategy.trades])


def equity(strategy: Strategy) -> float:
    return strategy.equity


def sqn(strategy: Strategy) -> float:
    profits = np.array([trade.profit for trade in strategy.trades])
    profits = profits[profits != 0]
    if strategy.equity < 0.01 or profits.size == 0 or profits[profits > 0].size == 0:
        return 0
    if profits[profits < 0].size == 0:
        return 1.0
    avg_loss = np.abs(np.average(profits[profits < 0]))
    r_multiples = profits / avg_loss
    r_expectancy = np.average(r_multiples)
    r_multiples_std = np.std(r_multiples)
    n_trades = profits.size
    # if n_trades < 100:
    sqn = (r_expectancy / r_multiples_std) * np.sqrt(n_trades)
    # else:
    #     sqn = (r_expectancy / (r_multiples_std * (n_trades / 100))) * np.sqrt(n_trades)
    return sqn


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

    ax1.set_ylabel("Equity ($)")
    substrategy = strategy
    depth = 0
    while True:
        ax1.plot(
            substrategy.hist_equity, c="0.2", lw=1, alpha=max(0, 1.0 - (0.15 * depth))
        )
        if substrategy.previous is None:
            break
        depth += 1
        substrategy = substrategy.previous

    ax2.set_ylabel("Asset Value ($)")
    ax2.set_xlabel("Iteration")
    ax2.plot(ohlcv[:, 3], c="0.2", lw=1)

    if len(strategy.trades) < 100:
        trades_won = []
        trades_lost = []
        for trade in strategy.trades:
            if trade.profit >= 0:
                trades_won.append(trade.iteration - 1)
            else:
                trades_lost.append(trade.iteration - 1)
        if len(trades_lost) != 0:
            ax2.scatter(
                np.array(trades_lost),
                ohlcv[:, 3][np.array(trades_lost)],
                c="red",
                s=2.5,
                zorder=10,
            )
        if len(trades_won) != 0:
            ax2.scatter(
                np.array(trades_won),
                ohlcv[:, 3][np.array(trades_won)],
                c="lime",
                s=2.5,
                zorder=10,
            )
