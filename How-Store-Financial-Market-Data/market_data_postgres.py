import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
import exchange_calendars as xcals
from openbb import obb
obb.user.preferences.output_type = "dataframe"

# this function creates a database to store market data if one does not exist
def create_database_and_get_engine(db_name, base_engine):
    conn = base_engine.connect()
    conn = conn.execution_options(
        isolation_level="AUTOCOMMIT")
    try:
        conn.execute(text(f"CREATE DATABASE{db_name};"))   
    except ProgrammingError:
        pass
    finally:
        conn.close()
    conn_str = base_engine.url.set(database=db_name)
    return create_engine(conn_str)

def get_stock_data(symbol, start_date=None, end_date=None):
    data = obb.equity.price.historical(
        symbol,
        start_date=start_date,
        end_date=end_date,
        provider="yfinance",
    )
    data.reset_index(inplace=True)
    data['symbol'] = symbol
    return data

def save_data_range(symbol, engine, start_date=None, end_date=None):
    data = get_stock_data(symbol, start_date,end_date)
    data.to_sql(
        "stock_data",
        engine,
        if_exists="append",
        index=False
    )

def save_last_trading_session(symbol, engine, today):
    data = get_stock_data(symbol, today, today)
    data.to_sql(
        "stock_data",
        engine,
        if_exists="append",
        index=False
    )

# The database connection and calls our code to download and save the data
if __name__ == "__main__":
    username = "postgres"
    password = "Kj4*spahxBPuZ!J"
    host = "127.0.0.1"
    port = "5432"
    database = "market_data"
    DATABASE_URL = f"postgresql://{username}:{password}@{host}:{port}/postgres"
    base_engine = create_engine(DATABASE_URL)
    engine = create_database_and_get_engine(
        "stock_data", base_engine)
    if argv[1] == "bulk":
        symbol = argv[2]
        start_date = argv[3]
        start_date = argv[4]
        save_data_range(symbol, engine, start_date=None, end_date=None)
        print(f"{symbol} saved between {start_date} and {end_date}")
    elif argv[1] == "last":
        symbol = argv[2]
        calendar = argv[3]
        cal = xcals.get_calendar(calendar)
        today = pd.Timestamp.today().date()
        if cal.is_session(today):
            save_last_trading_session(symbol, engine, today)
            print(f"{symbol} saved")
        else:
            print(f"{today} is not a trading day. Do nothing.")


