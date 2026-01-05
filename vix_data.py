import datetime as dt

import pandas as pd
import requests as req
from bs4 import BeautifulSoup as bs
from pandas.tseries.offsets import Day


def return_third_friday(_start_date, _end_date):
    """
    Generates a list of all 3rd fridays within a specified date range.
    """
    all_fridays = pd.date_range(start=_start_date, end=_end_date, freq="W-FRI")
    third_fridays = []
    for date in all_fridays:
        if 15 <= date.day <= 21:
            third_fridays.append(date)
    return pd.Series(third_fridays)


def return_third_wednesday(_start_date, _end_date):
    """
    Finds the third wednesday of each month w/in given date range.

    Args:
        _start_date (str or datetime-like): the start of the date range.
        _end_date (str or datetime-like): the end of the date range.

    Returns:
        pandas.Series: A series containing the third Wednesdays.

    """
    date_range = pd.date_range(start=_start_date, end=_end_date, freq="D")

    # filter these for wednesdays (weekday() returns 2 for wednesday)
    wednesdays = date_range[date_range.weekday == 2]

    # group by month and get the third wednesday for each group (index 2 since 0-indexed)
    # return wednesdays.groupby(wednesdays.to_period("M")).nth(2)
    third_wednesdays = wednesdays.groupby(wednesdays.to_period("M"))
    return third_wednesdays


def get_expiry_date_for_month(curr_date):
    if curr_date.month == 12:
        third_friday_next_month = dt.date(curr_date.year + 1, 1, 15)
    else:
        third_friday_next_month = dt.date(
            curr_date.year, curr_date.month + 1, 15
        )

    one_day = dt.timedelta(days=1)
    thirty_days = dt.timedelta(days=30)
    while third_friday_next_month.weekday() != 4:
        # using += may result in a timedelta object?
        third_friday_next_month += one_day

    return third_friday_next_month - thirty_days


# HEADERS = {
#     "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7339.215 Safari/537.36"
# }

# https://www.cboe.com/us/futures/market_statistics/historical_data
# VX is VIX, VXM is VIX Mini
PRODUCT = "VX"

# NOTE: link only returns csv's with the third friday in the filename:
# f"https://www.cboe.com/us/futures/market_statistics/historical_data/{PRODUCT}/{PRODUCT}_2026-01-21.csv" (3rd friday of the month)


start = "2026-01-01".removesuffix("00:00:00")
end = "2026-12-31".removesuffix("00:00:00")

# returns a series
third_fridays_2026 = return_third_friday(start, end)

# get_df = pd.DataFrame({'event_date': pd.to_datetime(['2026-01-01', '2026-12-31'])})

# returns a df
# third_fridays_df = pd.DataFrame(return_third_friday("2026-01-01", "2026-12-31"))


# URL = f"https://www.cboe.com/us/futures/market_statistics/historical_data/products/{PRODUCT}"
# URL = r"https://www.cboe.com/us/futures/market_statistics/historical_data/products/VX"k
URL = f"https://www.cboe.com/us/futures/market_statistics/historical_data/{PRODUCT}/{PRODUCT}_{third_fridays_2026}"

# page = req.get(URL, headers=HEADERS)

page = req.get(URL)
soup = bs(page.content, "html.parser")
links = [link.get("href") for link in soup.find_all("a")]

cfe_links = [link for link in links if f"products/csv/{PRODUCT}/"]
cfe_futures = pd.DataFrame(
    columns=[
        "Trade Date",
        "Futures",
        "Open",
        "High",
        "Low",
        "Settle",
        "Change",
        "Total Volume",
        "EFP",
        "Open Interest",
        "Expiration Date",
        "Product",
    ]
)

for link in cfe_links:
    expiration_date = list(filter(None, link.split("/")))[-1]

    if expiration_date in cfe_futures["Expiration Date"].values:
        print(f"Skipping {expiration_date} because it already exists")
        continue

    # TODO: use rich console and/or logger
    print(f"Downloading {expiration_date}")

    csv_url = f"https://www.cboe.com/us/futures/market_statistics/historical_data/{link}"
    df = pd.read_csv(csv_url)
    df["Expiration Date"] = expiration_date
    df["Product"] = PRODUCT

    cfe_futures = pd.concat([cfe_futures, df])


cfe_futures.to_pickle(f"{PRODUCT}_futures.pkl")
