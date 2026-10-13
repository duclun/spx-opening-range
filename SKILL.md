---
name: spx-opening-range
description: Monitor SPX opening range breakouts. Use when user wants to be alerted if SPX breaks its high or low from the first N minutes of trading (default 60).
---

# SPX Opening Range Breakout Indicator

Monitor the first hour (or custom timeframe) of trading for SPX and set alerts for breakouts of that range.

## Workflow

1.  **Define Range**: The "Opening Range" starts at market open (9:30 AM EST) and ends after the specified `range_minutes` (default 60).
2.  **Monitor Price**: Check the current SPX price at regular intervals (default 10 mins).
3.  **Alert on Breakout**: If the price moves above the range high or below the range low, send an alert.
4.  **Auto-Stop**: The monitoring stops at a specified time (default 12:00 PM EST).

## Automated Monitoring (Cron)

To set up the monitor, create a cron job that runs the `check_breakout.py` script.

Example Cron Setup:
```json
{
  "name": "SPX Breakout Monitor",
  "schedule": { "kind": "every", "everyMs": 600000 },
  "payload": { 
    "kind": "agentTurn", 
    "message": "Run scripts/check_breakout.py --range 60 --stop 12pm and alert if a breakout is found." 
  },
  "sessionTarget": "isolated"
}
```

## References

-   **Market Open**: 9:30 AM EST
-   **Default Range**: 60 Minutes (closes at 10:30 AM EST)
-   **Default Check Interval**: 10 Minutes
-   **Default Stop Time**: 12:00 PM EST
