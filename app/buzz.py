from utils import *

# get alpaca asset list
alpaca_assets_list = get_assets_from_alpaca()

# get top gainers for the day from yahoo
yahoo_gainers = get_top_gainers_from_yahoo()

# merge both DF (join:inner) on symbol
list_for_today = alpaca_assets_list.merge(yahoo_gainers, on='symbol')

# Apply additional filters
filtered_list = apply_additional_filters(list_for_today)

# Get BUZZ score for the list
buzz_scores = get_buzz_scores(filtered_list)

# Take Top 5 of stocks ordered by buzz
final_tickers_for_the_day = buzz_scores.sort_values(by=['buzz'], ascending=False).head()

# Compute total number of positions for the day
number_of_positions = len(final_tickers_for_the_day.index)

for ticker in final_tickers_for_the_day.index.tolist():
    # Take long position on each one of them.
    take_long_position(ticker, 1/number_of_positions)