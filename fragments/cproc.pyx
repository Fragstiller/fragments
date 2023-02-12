cpdef enum Action:
    BUY = 1
    SELL = 2
    CANCEL = 3
    PASS = 4


cpdef enum TradeDirection:
    LONG = 1
    SHORT = 2


def apply_strategy_action(self, ohlcv, int action, int logic_only = 0):
    cdef int action_logic, result_action
    cdef int direction_switch = 0

    if self.previous is not None:
        if action == Action.PASS:
            result_action = self.previous.action
        else:
            result_action = action
    else:
        result_action = action
    self.action = result_action

    if logic_only or self.equity < 0.01:
        return

    cdef int in_trade = self._in_trade

    if result_action == Action.BUY:
        if not in_trade:
            self._in_trade = True
            self._new_trade(TradeDirection.LONG)
        elif self._in_trade and self.trades[-1].direction == TradeDirection.SHORT:
            self.trades[-1].forward(ohlcv)
            self.equity = self.hist_equity[self.trades[-1].iteration - 2] + self.trades[-1].profit
            direction_switch = 1
            self._new_trade(TradeDirection.LONG)
    elif result_action == Action.SELL:
        if not in_trade:
            self._in_trade = True
            self._new_trade(TradeDirection.SHORT)
        elif self._in_trade and self.trades[-1].direction == TradeDirection.LONG:
            self.trades[-1].forward(ohlcv)
            self.equity = self.hist_equity[self.trades[-1].iteration - 2] + self.trades[-1].profit
            direction_switch = 1
            self._new_trade(TradeDirection.SHORT)
    elif result_action == Action.CANCEL:
        self._in_trade = False
    if self._in_trade:
        self.trades[-1].forward(ohlcv)
        if direction_switch:
            self.equity = self.hist_equity[self.trades[-1].iteration - 2] + self.trades[-1].profit + self.trades[-2].profit
        else:
            self.equity = self.hist_equity[self.trades[-1].iteration - 2] + self.trades[-1].profit
    self.hist_equity.append(self.equity)


cpdef enum ConditionType:
    LESS_THAN = 1
    MORE_THAN = 2


cpdef enum ConditionLogic:
    AND = 1
    SAMEAND = 2
    IGNORE = 3


def forward_conditional(self, ohlcv, int freeze_bounds):
    cdef int condition_type, condition_logic, action
    cdef float indicator_value
    action = Action.PASS
    indicator_value_unknown = self.indicator.forward(ohlcv)
    if indicator_value_unknown is not None:
        indicator_value = indicator_value_unknown
        if not freeze_bounds:
            if <int>indicator_value < self.condition_threshold.bounds[0]:
                self.condition_threshold.bounds = (
                    <int>indicator_value,
                    self.condition_threshold.bounds[1],
                )
            elif <int>indicator_value > self.condition_threshold.bounds[1]:
                self.condition_threshold.bounds = (
                    self.condition_threshold.bounds[0],
                    <int>indicator_value,
                )
        condition_type = self.condition_type.value
        if condition_type == ConditionType.LESS_THAN:
            if indicator_value < self.condition_threshold.value:
                action = self.on_condition.value
        elif condition_type == ConditionType.MORE_THAN:
            if indicator_value >= self.condition_threshold.value:
                action = self.on_condition.value
    if self.previous is not None and self.condition_logic is not None:
        condition_logic = self.condition_logic.value
        previous_action = self.previous.action
        if condition_logic == ConditionLogic.AND and previous_action != action:
            action = Action.CANCEL
        elif condition_logic == ConditionLogic.SAMEAND and self.on_condition.value == previous_action and previous_action != action:
            action = Action.CANCEL
    apply_strategy_action(self, ohlcv, action)


cpdef enum LimiterType:
    STOP_LOSS = 1
    TAKE_PROFIT = 2


def forward_limiter(self, ohlcv):
    cdef int action
    cdef float trade_profit, limiter_threshold
    action = Action.PASS
    indicator_value = self.indicator.forward(ohlcv)
    if len(self.trades) != 0:
        trade_profit = self.trades[-1].profit
        if trade_profit == 0 and indicator_value is not None:
            limiter_threshold = indicator_value * (
                self.limiter_multiplier.value / 100
            )
            self._limiter_threshold = limiter_threshold
        else:
            limiter_threshold = self._limiter_threshold
        if (
            self.limiter_type.value == LimiterType.STOP_LOSS
            and trade_profit <= -limiter_threshold
        ):
            action = Action.CANCEL
        elif trade_profit > limiter_threshold:
            action = Action.CANCEL
    apply_strategy_action(self, ohlcv, action)


cpdef enum CrossoverHandling:
    REGULAR = 1
    INVERTED = 2


def forward_crossover(self, ohlcv):
    cdef int action
    cdef float first_value, second_value, prev_first_value, prev_second_value
    action = Action.PASS
    first_value_unknown = self.first_indicator.forward(ohlcv)
    second_value_unknown = self.second_indicator.forward(ohlcv)
    if first_value_unknown is not None and second_value_unknown is not None:
        first_value = first_value_unknown
        second_value = second_value_unknown
        if self._prev_first_value is None or self._prev_second_value is None:
            self._prev_first_value = first_value
            self._prev_second_value = second_value
        elif (
            self._prev_first_value is not None
            and self._prev_second_value is not None
        ):
            prev_first_value = self._prev_first_value
            prev_second_value = self._prev_second_value
            if (
                prev_first_value <= prev_second_value
                and first_value > second_value
            ):
                if self.crossover_handling.value == CrossoverHandling.REGULAR:
                    action = Action.BUY
                else:
                    action = Action.SELL
            elif (
                prev_first_value >= prev_second_value
                and first_value < second_value
            ):
                if self.crossover_handling.value == CrossoverHandling.REGULAR:
                    action = Action.SELL
                else:
                    action = Action.BUY
            self._prev_first_value = first_value
            self._prev_second_value = second_value
    apply_strategy_action(self, ohlcv, action)


def forward_inverting(self, ohlcv):
    cdef int action, current_action
    apply_strategy_action(self, ohlcv, Action.PASS, logic_only=True)
    if self.indicator is not None:
        processed_equity = self.indicator.forward((0, 0, 0, self.equity, 0))
    else:
        processed_equity = self.equity
    if processed_equity is not None:
        if processed_equity > self._peak_equity:
            self._peak_equity = processed_equity
            self._drawdown_duration = 0
        else:
            self._drawdown_duration += 1
    if (
        self._drawdown_duration
        > self.invert_drawdown_duration.value * self._duration_multiplier
    ):
        self._invert = not self._invert
        self._peak_equity = processed_equity
        self._drawdown_duration = 0
    action = Action.PASS
    current_action = self.action
    if self._invert:
        if current_action == Action.BUY:
            action = Action.SELL
        elif current_action == Action.SELL:
            action = Action.BUY
    apply_strategy_action(self, ohlcv, action)