# SPX Opening Range Breakout Monitor

Monitors the SPX (S&P 500) opening range during the first N minutes of trading (default: 60 minutes) and alerts on breakouts above the range high or below the range low.

## Overview

The "Opening Range" is a classic day trading concept where the high/low established during the first period of trading (typically 9:30–10:30 AM EST) often acts as significant support/resistance for the rest of the session. This tool:

1. **Defines the range** from market open (9:30 AM EST) for a configurable duration
2. **Monitors price** at regular intervals via cron
3. **Alerts on breakouts** when price moves above range high or below range low
4. **Persists alerts** to SQLite with semantic descriptions for vector search
4. **Auto-stops** monitoring at a configurable end time (default: 12:00 PM EST)

## Installation

```bash
git clone https://github.com/duclun/spx-opening-range.git
cd spx-opening-range
pip install -r requirements.txt
```

## Usage

### CLI

```bash
# Default: SPX (^GSPC), 60-minute range, stop at 12:00 PM EST
python scripts/check_breakout.py

# Custom ticker, 30-minute range, stop at 11:00 AM
python scripts/check_breakout.py --ticker SPY --range 30 --stop 11:00am

# Custom ticker with different stop time
python scripts/check_breakout.py --ticker "^GSPC" --range 60 --stop 12:30pm
```

### Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--ticker` | `^GSPC` | Yahoo Finance ticker symbol (SPX = `^GSPC`, SPY ETF = `SPY`) |
| `--range` | `60` | Opening range duration in minutes |
| `--stop` | `12:00pm` | Stop monitoring at this time (EST) |

### Output Examples

**Breakout UP:**
```
🚨 **ORB BREAKOUT UP**
Ticker: ^GSPC
Current: 4523.45
Range High: 4520.10
Range Low: 4505.30
```

**Breakout DOWN:**
```
🚨 **ORB BREAKOUT DOWN**
Ticker: ^GSPC
Current: 4500.20
Range Low: 4505.30
Range High: 4520.10
```

**No breakout:**
```
No breakout. ^GSPC at 4515.00 (Range: 4505.30 - 4520.10)
```

## Automated Monitoring (Cron)

Set up a cron job to run every 10 minutes during market hours:

```bash
# Runs every 10 minutes, Mon-Fri, 9:30 AM - 12:00 PM EST
*/10 9-11 * * 1-5 /usr/bin/python3 /path/to/scripts/check_breakout.py --range 60 --stop 12:00pm
```

Or via Hermes Agent (as currently configured):
- Cron job ID: `200468ea9e7a` ("ORB Breakout Alerts")
- Runs every 10 minutes during market hours
- Delivers alerts to Telegram

## Data Persistence

Breakouts are logged to SQLite at `~/.openclaw/workspace-manager/market_data.db` in the `orb_breakouts` table:

```sql
CREATE TABLE orb_breakouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ticker TEXT,
    price REAL,
    range_high REAL,
    range_low REAL,
    direction TEXT,  -- "UP" or "DOWN"
    event_description TEXT,  -- Human-readable for embedding/search
    embedding BLOB  -- For vector similarity search
);
```

Each breakout also triggers a vector sync via `sync_vectors.py` for semantic search.

## Dependencies

- `yfinance` - Market data from Yahoo Finance
- `pandas` - Data manipulation
- `pytz` - Timezone handling (EST/EDT)
- `sqlite3` - Built-in, local persistence

## License

MIT