from fragments.strategy import Strategy


def total_profit(strategy: Strategy) -> float:
    return sum([trade.profit for trade in strategy.trades])
