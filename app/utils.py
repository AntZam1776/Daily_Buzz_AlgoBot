from yahoo_fin import stock_info as yf_info
from alpaca_trade_api.rest import REST
from datetime import date
import pandas as pd
import numpy as np
import quandl
import constants
import os

def apply_additional_filters(a):
    '''Giant list from ALPCA has all symbols. 
        Remove non-tradable symbols and apply any further filters needed
    '''
    c = a
    # Remove non-active symbols
    c = c[c['status'] == 'active']

    # Remove non-shortable symbools
    c = c[c['tradable'] == True]

    # Remove symbols that are not fractionable
    c = c[c['fractionable'] == True]

    print ("Trimmed list of stocks from {} to {} ".format(len(a.index), len(c.index)))
    return c
    ## @Anil: Perhaps we should also filter out low CAP stocks??

def get_assets_from_alpaca():
    ''' Fetch all symbols from Alpaca '''
    # create a REST API interface
    api = REST(base_url='https://paper-api.alpaca.markets', secret_key=os.environ.get('APCA_API_SECRET_KEY'), key_id=os.environ.get('APCA_API_KEY_ID'))

    # Query US equity
    assets = api.list_assets(asset_class='us_equity')

    # Make a list from Asset class
    a_list = []
    for asset in assets:
        a_list.append(asset._raw)
    
    # Make a dataframe from the list
    a_data = pd.DataFrame(a_list)

    # Set symbol as index
    df = a_data.set_index('symbol')

    return df

def get_top_gainers_from_yahoo():
    
    # Fetch top 100 gainers
    df = yf_info.get_day_gainers()

    # Rename to smallcase
    df.rename(columns={'Symbol':'symbol'}, inplace='True')

    # Set index to symbol
    df = df.set_index('symbol')

    # Sort desc based on % Change
    df.sort_values(by=['% Change'], ascending=False)

    return df

def get_buzz_scores(list_of_stocks):

    # We poll sentiment score from Qunadl. Setup Key
    quandl.ApiConfig.api_key = os.environ.get('QUANDL_KEY')

    today = date.today()
    d = today.strftime("%Y-%m-%d")

    # Get today's sentiment for all stocks
    df = quandl.get_table('NDAQ/RTAT', date=d)

    # Rename ticker->symbol and sentiment->buzz
    df.rename(columns={'ticker':'symbol', 'sentiment':'buzz'}, inplace=True)
    df.set_index('symbol')

    # find intersection with incoming list
    df = list_of_stocks.merge(df, on='symbol')

    return df

def take_long_position(ticker, fraction):
    # create a REST API interface
    api = REST(base_url='https://paper-api.alpaca.markets', secret_key=os.environ.get('APCA_API_SECRET_KEY'), key_id=os.environ.get('APCA_API_KEY_ID'))

    # Fetch last quote for the symbol
    quote = api.get_last_trade(ticker)._raw

    # Fetch total cash available
    account_info = api.get_account()._raw

    # Compute total exposute for the day
    total_capital = float(account_info['buying_power']) * constants.TOTAL_EXPOSURE
    
    # Compute exposure for each trade
    per_trade_capital = total_capital * fraction

    # Compute entry
    price = quote['price']

    if (price <= 0):
        print ("Invalid quote for ticker {}".format(ticker))
        return

    # Compute stoploss
    sl = price * (1 - constants.STOP_LOSS_LIMIT)

    # Compute profit
    target = price * (1 + constants.PROFIT_TARGET)

    # Calculate the quantity
    qty = int(per_trade_capital/price)
    if (qty <= 0):
        print ("Insufficitent funds for ticker {}".format(ticker))
        return
    
    print("Submitting buy order of {} for {} shares at {}  with profit target {} and stoploss {}".format(ticker, qty, price, target, sl))
    api.submit_order(
        symbol=ticker,
        side='buy',
        type='limit',
        qty=qty,
        limit_price=price,
        time_in_force='day',
        order_class='bracket',
        take_profit=dict(
            limit_price=target,
        ),
        stop_loss=dict(
            stop_price=sl,
            limit_price=sl,
        )
    )
