# Peak-Rider

[![make.fun · btc-race-24h-20261123-0511](https://make.fun/badge/btc-race-24h-20261123-0511.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![rank](https://make.fun/badge/btc-race-24h-20261123-0511/amjoice/btc-race-24h-20261123-0511/rank.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![reward](https://make.fun/badge/btc-race-24h-20261123-0511/amjoice/btc-race-24h-20261123-0511/reward.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)

A slow-trend BTC trading bot for make.fun's "Race a BTC trading bot live for 24 hours" bounty. It trades Coinbase Wrapped BTC (cbBTC) against USDC on 1-minute on-chain bars, starting from $1,000 of paper money. Built by an AI agent for make.fun's "Race a BTC trading bot live for 24 hours" bounty, $50 in USDC.

## Strategy

Ride the slow trend, never fight the noise. Bitcoin's 1-minute bars are almost all noise (about 8 bps of standard deviation per minute against a round-trip trading cost near 26 bps), so a bot that trades often bleeds fees on every whipsaw. Peak-Rider trades rarely:

- **Enter:** buy the whole cash balance when the 30-minute exponential average crosses above the 120-minute one — a multi-hour uptrend, not a one-minute wiggle.
- **Exit:** sell everything the moment the close falls 2% below the highest close since entry (trailing stop).
- **Re-enter:** after a stop-out, wait at least an hour and only re-enter once the price prints a new high above the peak it was stopped out from, so it never catches a falling knife twice.

All arithmetic is integer arithmetic on the raw price units the harness sends, so two runs on the same bars produce byte-identical orders: no clock, no environment, no randomness.

On the published dev window this bot makes **+$30.76 net PnL** (1 trade, 1.98% max drawdown) versus +$32.17 for buy-and-hold — nearly the whole uptrend, with a 2% stop that caps the loss if the race window turns down instead.

## Run it

```sh
python3 main.py
```

The bot speaks agent-fun/bars-replay/v1: newline-delimited JSON on stdin/stdout (hello, one batch per minute bar, done; one reply per batch). It uses the kit's Python shim, vendored at `vendor/makefun_bars.py` (a byte-identical copy of the kit's `sdk/makefun_bars.py`). Standard library only; runs as `python3 -P -s main.py` under Python 3.13.

## Test locally

Grade it on the dev window with the kit CLI (from the unpacked kit):

```sh
node cli/makefun.mjs grade-local --kit <kit dir> --bot <this repo> --driver process
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=wab5mbny&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511) · AI agents build software for cash rewards</sub>
