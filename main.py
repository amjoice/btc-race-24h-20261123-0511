"""Peak-Rider: a slow-trend BTC bot for the make.fun bars-replay/v1 harness.

Strategy, in one paragraph: ride the slow trend, never fight the noise.
Bitcoin's 1-minute bars are almost all noise (an 8 bps standard deviation per
minute against a round-trip trading cost near 26 bps), so a bot that trades
often bleeds fees on every whipsaw. This bot trades rarely: it buys the whole
cash balance when the 30-minute exponential average crosses above the
120-minute one (a multi-hour uptrend, not a one-minute wiggle), then holds
while the trend lasts and sells everything the moment the close falls 2%
below the highest close since entry. After being stopped out it waits at
least an hour and only re-enters once the price prints a new high above the
peak it was stopped out from, so it never catches a falling knife twice.

All arithmetic is integer arithmetic on the raw price units the harness
sends, so two runs on the same bars produce byte-identical orders: no clock,
no environment, no randomness anywhere.

Wire notes (agent-fun/bars-replay/v1): the harness sends hello once, then
one batch per minute bar, then done. Each batch carries the bar that just
closed, the fills of the orders sent on the previous batch, and the account.
An order decided on a batch fills at the next bar's open, so every decision
here uses only closes the bot has already been sent. The bot answers every
batch with exactly one reply echoing its seq.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"

# Trend lengths, in 1-minute bars.
FAST_LEN = 30
SLOW_LEN = 120
# Bars of history before the first entry may be considered: both averages
# start seeded at the first close, so a cross in the first minutes is
# meaningless noise. The dev window's first real cross is far later.
MIN_BARS = 30
# Trailing stop: sell when the close falls below 98% of the peak close
# since entry (integer ratio, no floats).
TRAIL_NUM = 9800
TRAIL_DEN = 10000
# Bars to wait after a stop-out before a re-entry may be considered.
COOLDOWN_BARS = 60
# Cap on how far a fill may move from the latest close (3%): a 1-minute
# BTC move that large is far outside the observed range, so this only
# guards against a freak gap, never a normal fill.
MAX_SLIPPAGE_BPS = 300


class PeakRider:
    """The whole strategy state. All prices are raw integer units."""

    def __init__(self):
        # Exponential averages, seeded at the first close seen.
        self.fast = None
        self.slow = None
        self.prev_fast = None
        self.prev_slow = None
        # How many CBBTC closes have been seen.
        self.n_bars = 0
        # Highest close since the current position was opened.
        self.peak = 0
        # Bar index and peak of the most recent stop-out.
        self.last_exit_bar = -10 ** 9
        self.last_peak = 0

    def _ema_step(self, prev, price, length):
        # e += (price - e) * 2 / (length + 1), in integers.
        return prev + (price - prev) * 2 // (length + 1)

    def on_batch(self, state, batch):
        if state.warming_up:
            # Warm-up batches build history only; orders on them are rejected.
            return []
        close = state.close(SYMBOL)
        if close is None:
            # No CBBTC bar in this batch: nothing to decide on.
            return []
        self.n_bars += 1
        if self.fast is None:
            self.fast = close
            self.slow = close
        else:
            self.prev_fast = self.fast
            self.prev_slow = self.slow
            self.fast = self._ema_step(self.fast, close, FAST_LEN)
            self.slow = self._ema_step(self.slow, close, SLOW_LEN)

        holding = state.positions.get(SYMBOL)
        qty = holding.qty if holding is not None else 0
        if qty > 0:
            return self._maybe_exit(close, qty)
        return self._maybe_enter(state, close)

    def _maybe_exit(self, close, qty):
        if close > self.peak:
            self.peak = close
        if close * TRAIL_DEN < self.peak * TRAIL_NUM:
            self.last_exit_bar = self.n_bars
            self.last_peak = self.peak
            self.peak = 0
            return [{"side": "sell", "symbol": SYMBOL, "qty": qty,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []

    def _maybe_enter(self, state, close):
        if self.n_bars < MIN_BARS:
            return []
        if self.n_bars - self.last_exit_bar < COOLDOWN_BARS:
            return []
        if self.last_peak and close <= self.last_peak:
            # After a stop-out, only a new high above the old peak proves
            # the downtrend is over.
            return []
        crossed_up = (self.fast > self.slow
                      and self.prev_fast is not None
                      and self.prev_fast <= self.prev_slow)
        first_chance = self.n_bars == MIN_BARS and self.fast > self.slow
        if not (crossed_up or first_chance):
            return []
        cash = state.cash
        if cash <= 0:
            return []
        self.peak = close
        return [{"side": "buy", "symbol": SYMBOL,
                 "notional_quote_units": cash,
                 "max_slippage_bps": MAX_SLIPPAGE_BPS}]


def main():
    bot = PeakRider()
    makefun_bars.run(bot.on_batch)


if __name__ == "__main__":
    main()
