# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import time
import logging
import os
from datetime import datetime, timedelta
import json
import pytz

# Crear la carpeta /logs si no existe
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

if not logging.root.handlers:
    # Configurar el logger
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # Crear un manejador para escribir en un archivo con fecha y hora
    log_filename = 'test_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.log'
    log_path = os.path.join(log_dir, log_filename)
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)

    # Crear un formato común para ambos manejadores
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Añadir los manejadores al logger root
    logging.root.addHandler(file_handler)

logger = logging.getLogger(__name__)
logger.info('Logger configurado en el módulo principal.')

def read_json_file(file_path):
    '''
    Reads and loads JSON data from the specified file.

    Parameters:
        file_path (str): Path to the JSON file.

    Returns:
        list: Loaded JSON data.
    '''
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error(f'File not found: {file_path}')
        return []

config = read_json_file('schwab_config.json')

#### API TEST
from schwab_api import SchwabApi

logger.info('Starting API session')
api = SchwabApi(config)

#### ACCOUNT DATA
logger.info('Testing "ACCOUNT DATA" endpoints')
logger.info('Account Hash: [PROTECTED]')

logger.info('Testing "GET_ACCOUNTS" endpoint')
account = api.get_accounts(fields=['positions'])
logger.info('Account Balances: %s', json.dumps(account[0]['securitiesAccount']['currentBalances'], indent=1))

logger.info('Testing "GET_USER_PREFERENCES" endpoint')
user_preferences = api.get_user_preference()
logger.info('User Preferences: %s', json.dumps(user_preferences, indent=1))

logger.info('Testing "GET_ACCOUNT_NUMBERS" endpoint')
account_num = api.get_account_numbers()
logger.info('Accounts numbers: [PROTECTED]')

def format_dateTime(dateTime):
    original_date = datetime.fromisoformat(dateTime)
    utc_date = original_date.astimezone(pytz.UTC)
    formatted_date_str = utc_date.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    return formatted_date_str

logger.info('Testing "GET_TRANSACTIONS" endpoint')
end_date = datetime.now()
start_date = end_date - timedelta(days=180)
end_date_str = format_dateTime(str(end_date))
start_date_str = format_dateTime(str(start_date))

transactions = api.get_transactions(start_date_str, end_date_str)
logger.info('Transactions Numbers: %s', len(transactions))
logger.info('Transactions: %s', json.dumps(transactions[0], indent=1))

logger.info('Testing "GET_ORDERS" endpoint')
start_date = end_date - timedelta(days=60)
start_date_str = format_dateTime(str(start_date))

orders = api.get_orders(start_date_str, end_date_str)
logger.info('Orders Numbers: %s', len(orders))
logger.info('Orders: %s', json.dumps(orders[0], indent=1))

logger.info('Testing "PLACE_ORDER" endpoint')
api.place_order('AAPL', '1', 'BUY', 'EQUITY', price='150', order_type='LIMIT')
time.sleep(2)

logger.info('Testing "GET_ACCOUNT_ORDERS" endpoint')
end_date = datetime.now()
end_date_str = format_dateTime(str(end_date))
start_date_str = format_dateTime(str(start_date))

orders_account = api.get_account_orders(start_date_str, end_date_str)

for order in orders_account:
    if (order['quantity'] == 1.0 and
        order['price'] == 150.0 and
        order['orderLegCollection'][0]['instrument']['symbol'] == 'AAPL'):
        order_id = order['orderId']
        break

placed_order = api.get_order(order_id)
logger.info('Order: %s', json.dumps(placed_order, indent=1))

logger.info('Testing "REPLACE_ORDER" endpoint')
api.replace_order(str(order_id), 'AAPL', '2', 'BUY', 'EQUITY', price='170', order_type='LIMIT')
time.sleep(2)

logger.info('Testing "CANCEL_ORDER" endpoint')
logger.info('Cancelling the order just got replaced in order to see the error handling')
api.cancel_order(str(order_id))

end_date = datetime.now()
end_date_str = format_dateTime(str(end_date))

orders_account = api.get_account_orders(start_date_str, end_date_str)

for order in orders_account:
    if (order['quantity'] == 2.0 and
        order['price'] == 170.0 and
        order['orderLegCollection'][0]['instrument']['symbol'] == 'AAPL'):
        order_id = order['orderId']
        break

logger.info('Cancel the replaced Order')
api.cancel_order(order_id)

#### MARKET DATA
logger.info('Testing "MARKET DATA" endpoints')
logger.info('Testing "SEARCH_INSTRUMENTS" endpoint')
instruments = api.search_instruments('AAPL')
cusip = instruments['instruments'][0]['cusip']
logger.info('Cusip: %s', cusip)

logger.info('Testing "GET_INSTRUMENTS" endpoint')
instrument = api.get_instruments(cusip)
logger.info('Instrument: %s', json.dumps(instrument, indent=1))

logger.info('Testing "GET_MARKETS_HOURS" endpoint')
markets_hours = api.get_markets_hours()
logger.info('Markets hours: %s', json.dumps(markets_hours['bond'], indent=1))

logger.info('Testing "GET_MARKET_HOURS" endpoint')
market_hours = api.get_market_hours('bond')
logger.info('Market hours: %s', json.dumps(market_hours, indent=1))

logger.info('Testing "GET_MOVERS" endpoint')
movers = api.get_movers('$DJI')
logger.info('Movers: %s', json.dumps(movers['screeners'][0], indent=1))

logger.info('Testing "GET_PRICEHISTORY_DATES" endpoint')
pricehistory_date = api.get_pricehistory_dates(symbol='SPY',
                                              frequency_type='minute', frequency='30',
                                              end_date=end_date,
                                              start_date=start_date,
                                              need_extendedhours_data='false')
logger.info('Pricehistory: %s', json.dumps(pricehistory_date['candles'][0], indent=1))

logger.info('Testing "GET_PRICEHISTORY_PERIOD" endpoint')
pricehistory_period = api.get_pricehistory_period('AAPL', 'minute', '15', 'day', '2')
logger.info('Pricehistory: %s', json.dumps(pricehistory_period['candles'][0], indent=1))

logger.info('Testing "GET_QUOTE" endpoint')
quote = api.get_quote('AAPL', 'quote')
logger.info('Quote: %s', json.dumps(quote, indent=1))

logger.info('Testing "GET_QUOTES" endpoint')
quotes = api.get_quotes(['AAPL', 'NVDA'], 'all')
logger.info('Quotes: %s', json.dumps(quotes['AAPL'], indent=1))

logger.info('Testing "GET_OPTION_EXPIRATIONCHAIN" endpoint')
option_expirationchain = api.get_option_expirationchain('AAPL')
logger.info('Expiration chain: %s', json.dumps(option_expirationchain['expirationList'][0], indent=1))

logger.info('Testing "GET_OPTION_CHAIN" endpoint')
start_date = datetime.now() + timedelta(days=1)
end_date = start_date + timedelta(days=30)
end_date_str = format_dateTime(str(end_date))[:10]
start_date_str = format_dateTime(str(start_date))[:10]

OptionChain_1 = {
    "symbol": "AAPL",
    "contractType": ['ALL'],
    "strikeCount": '',
    "includeQuotes": ['TRUE'],
    "strategy": ['SINGLE'],
    "interval": '',
    "strike": "",
    "range": ['ALL'],
    "fromDate": start_date_str,
    "toDate": end_date_str,
    "volatility": "",
    "underlyingPrice": "",
    "interestRate": "",
    "daysToExpiration": "",
    "expMonth": ['ALL'],
    "optionType": ['ALL']
}

option_chain = api.get_option_chain(OptionChain_1)
logger.info('Option chain number of contract: %s', json.dumps(option_chain['numberOfContracts'], indent=1))
first_key = next(iter(option_chain['callExpDateMap']))
first_record_key = next(iter(option_chain['callExpDateMap'][first_key]))
first_record = option_chain['callExpDateMap'][first_key][first_record_key][0]
logger.info('Option chain CALL: %s', json.dumps(first_record, indent=1))
option_symbol = first_record['symbol']


#### STREAMER

from schwab_streamer import SchwabStreamerClient

streamer = SchwabStreamerClient(api)

streamer.connect()


subs = streamer._ws.current_subscriptions
su = streamer._ws.temp_subscriptions


indicators = '$DJI, $TICK'
equities = 'SPY, AAPL, MELI, GOOG, AMZN, NFLX, TSLA, NVDA, SLB, C, META, MSFT, KO, DIS, ADBE, QQQ KO'
futures = '/ES, /CL, /BTC'

equities = equities +str(', ')+ indicators

streamer.subs_request_account_activity()
#streamer.subs_request_account_activity(command="UNSUBS")

streamer.subs_request_chart_equity(keys = equities)
streamer.subs_request_chart_futures(keys = futures)

streamer.subs_request_levelone_equity(keys = equities)
streamer.subs_request_levelone_futures(keys = futures)
streamer.subs_request_levelone_forex(keys = 'EUR/USD')
streamer.subs_request_levelone_options(keys = option_symbol)
streamer.subs_request_levelone_future_options(keys = option_symbol)

streamer.subs_request_nasdaq_book(keys = equities)
streamer.subs_request_options_book(keys = option_symbol)


#streamer._ws.send_qos_request('0')

#streamer.subs_request_timesale_equity(keys = equities) #not available
#streamer.subs_request_timesale_futures(keys = futures) #not available
#streamer.subs_request_timesale_options(keys = 'AAPL  240628C00100000') #not available
#streamer.subs_request_timesale_forex(keys = 'EUR/USD') #not available bad command formatting

#streamer.subs_request_quote(keys = equities) #not available
#streamer.subs_request_news_headline(keys = equities) #not available

#streamer.subs_request_actives_nasdaq() #not available
#streamer.subs_request_actives_nyse() #not available
#streamer.subs_request_actives_otcbb() #not available
#streamer.subs_request_actives_options() #not available

#streamer.logout()