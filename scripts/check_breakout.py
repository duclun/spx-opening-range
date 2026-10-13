import sys
import argparse
import os
from datetime import datetime, timedelta
import pytz
import yfinance as yf
import pandas as pd
import sqlite3
import json
import subprocess

def has_already_broken_out(ticker):
    """Check if a breakout has already been logged for this ticker today."""
    db_path = "/home/dlun/.openclaw/workspace-manager/market_data.db"
    if not os.path.exists(db_path):
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orb_breakouts'")
        if not cursor.fetchone():
            conn.close()
            return False

        # Get today's date in YYYY-MM-DD (using EST for market hours consistency)
        est = pytz.timezone('US/Eastern')
        today = datetime.now(est).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT id FROM orb_breakouts 
            WHERE ticker = ? AND date(timestamp, 'localtime') = ?
            LIMIT 1
        ''', (ticker, today))
        
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        print(f"Error checking previous breakouts: {e}")
        return False

def get_opening_range(ticker, range_minutes):
    """Fetch the high and low of the opening range from 9:30 AM EST."""
    est = pytz.timezone('US/Eastern')
    now = datetime.now(est)
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    
    # Use period='1d' to get today's data and filter
    data = yf.download(ticker, period='1d', interval="1m", progress=False)
    
    if data.empty:
        return None, None
        
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # Convert index to EST to filter properly
    data.index = data.index.tz_convert(est)

    # Filter for the opening range
    range_end = market_open + timedelta(minutes=range_minutes)
    range_data = data[(data.index >= market_open) & (data.index < range_end)]
    
    if range_data.empty:
        return None, None

    range_high = range_data['High'].max()
    range_low = range_data['Low'].min()
    return range_high, range_low

def log_breakout(ticker, price, high, low, direction):
    """Persist breakout data to SQLite with semantic description."""
    db_path = "/home/dlun/.openclaw/workspace-manager/market_data.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table if not exists with embedding support (BLOB)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orb_breakouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ticker TEXT,
            price REAL,
            range_high REAL,
            range_low REAL,
            direction TEXT,
            event_description TEXT,
            embedding BLOB
        )
    ''')
    
    description = f"At {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, {ticker} triggered an ORB breakout {direction} at {price:.2f}. The opening range high was {high:.2f} and low was {low:.2f}."
    
    cursor.execute('''
        INSERT INTO orb_breakouts (ticker, price, range_high, range_low, direction, event_description)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (ticker, price, high, low, direction, description))
    
    conn.commit()
    conn.close()
    
    # Trigger vector sync
    try:
        subprocess.run(["python3", "/home/dlun/.openclaw/workspace-manager/sync_vectors.py"], capture_output=True)
    except:
        pass
        
    print(f"Logged {direction} breakout to database.")


def check_breakout(ticker, range_minutes, end_time_str):
    est = pytz.timezone('US/Eastern')
    now = datetime.now(est)
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    
    if has_already_broken_out(ticker):
        return "ALREADY_LOGGED"
    
    if now < market_open:
        return "Market is not open yet."

    range_end = market_open + timedelta(minutes=range_minutes)
    
    if now < range_end:
        return f"Still within opening range. Range ends at {range_end.strftime('%H:%M')} EST."

    # Parse end time
    try:
        if ':' in end_time_str:
            h_str, m_str = end_time_str.replace('pm', '').replace('am', '').split(':')
            end_hour, end_minute = int(h_str), int(m_str)
        else:
            end_hour, end_minute = int(end_time_str.replace('pm', '').replace('am', '')), 0
            
        if 'pm' in end_time_str.lower() and end_hour < 12:
            end_hour += 12
    except:
        end_hour, end_minute = 12, 0 # Default 12pm
    
    stop_time = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
    
    if now > stop_time:
        return "STOP"

    # Fetch Range
    range_high, range_low = get_opening_range(ticker, range_minutes)
    if range_high is None:
        return "Error fetching range data."

    # Fetch current price
    ticker_obj = yf.Ticker(ticker)
    current_price = ticker_obj.fast_info['last_price']

    if current_price > range_high:
        log_breakout(ticker, current_price, range_high, range_low, "UP")
        return f"🚨 **ORB BREAKOUT UP**\nTicker: {ticker}\nCurrent: {current_price:.2f}\nRange High: {range_high:.2f}\nRange Low: {range_low:.2f}"
    elif current_price < range_low:
        log_breakout(ticker, current_price, range_high, range_low, "DOWN")
        return f"🚨 **ORB BREAKOUT DOWN**\nTicker: {ticker}\nCurrent: {current_price:.2f}\nRange Low: {range_low:.2f}\nRange High: {range_high:.2f}"
    
    return f"No breakout. {ticker} at {current_price:.2f} (Range: {range_low:.2f} - {range_high:.2f})"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="^GSPC")
    parser.add_argument("--range", type=int, default=60)
    parser.add_argument("--stop", default="12:00pm")
    args = parser.parse_args()
    
    result = check_breakout(args.ticker, args.range, args.stop)
    print(result)
