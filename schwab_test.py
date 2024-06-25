# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import time
import logging
import os
from datetime import datetime, timedelta


# Crear la carpeta /logs si no existe
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

if not logging.root.handlers:
    # Configurar el logger
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # Crear un manejador para escribir en un archivo con fecha y hora
    log_filename = datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.log'
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


import json

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
        print(f'File not found: {file_path}')
        return []


config = read_json_file('schwab_config.json')

#### API TEST
from schwab_api import SchwabApi
#from schwab_api_enum import AssetType, Instruction, Session, Duration, OrderType, FrequencyType, PeriodType

api = SchwabApi(config)


#### ACCOUNT DATA

api.account_hash

account = api.get_accounts(fields = ['positions'])
user_preferences = api.get_user_preference() #Already test when initialize API
account_num = api.get_account_numbers() #Already test when initialize API


import pytz
def format_dateTime(dateTime):

    # Parsear la cadena de fecha y hora a un objeto datetime
    original_date = datetime.fromisoformat(dateTime)

    # Convertir la fecha y hora a UTC
    utc_date = original_date.astimezone(pytz.UTC)

    # Formatear la fecha y hora en el formato deseado
    formatted_date_str = utc_date.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    return formatted_date_str

end_date = datetime.now()
start_date = end_date - timedelta(days=180)  # 3 meses
end_date_str = format_dateTime(str(end_date))
start_date_str = format_dateTime(str(start_date))

transactions = api.get_transactions(start_date_str, end_date_str)

account_hash = api.account_hash

start_date = datetime.now()

api.place_order('AAPL', '1', 'BUY', 'EQUITY', price='150', order_type = 'LIMIT')
time.sleep(2)

end_date = datetime.now()

end_date_str = format_dateTime(str(end_date))
start_date_str = format_dateTime(str(start_date))

orders = api.get_orders(start_date_str, end_date_str)

orders_account = api.get_account_orders(start_date_str, end_date_str)

for order in orders_account:
    if (order['quantity'] == 1.0 and
        order['price'] == 150.0 and
        order['orderLegCollection'][0]['instrument']['symbol'] == 'AAPL'):
            order_id = order['orderId']
            break

order = api.get_order(order_id)

api.replace_order(str(order_id), 'AAPL', '2', 'BUY', 'EQUITY', price='170', order_type = 'LIMIT')
time.sleep(2)


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

api.cancel_order(order_id)


#### MARKET DATA


instruments = api.search_instruments('AAPL')
cusip = instruments['instruments'][0]['cusip']
instrument = api.get_instruments(cusip)

print(instrument['instruments'][0]['description'])


markets_hours = api.get_markets_hours()

market_hours = api.get_market_hours('bond')

movers = api.get_movers('$DJI')

pricehistory_date = api.get_pricehistory_dates(symbol = 'SPY',
                                                 frequency_type = 'minute', frequency = '30',
                                                 end_date = end_date,
                                                 start_date = start_date,
                                                 need_extendedhours_data = 'false')

pricehistory_period = api.get_pricehistory_period('AAPL', 'minute', '15', 'day', '2')

quote = api.get_quote('AAPL', 'quote')

quotes = api.get_quotes(['AAPL', 'NVDA'], 'all')


OptionChain_1 = {
                "symbol": "AAPL",
                "contractType": ['ALL'],
                "strikeCount": '',
                "includeQuotes":['TRUE'],
                "strategy": ['SINGLE'],
                "interval": '',
                "strike": "",
                "range": ['ALL'],
                "fromDate": "2024-06-24",
                "toDate": "2024-07-30",
                "volatility": "",
                "underlyingPrice": "",
                "interestRate": "",
                "daysToExpiration": "",
                "expMonth":['ALL'],
                "optionType": ['ALL']
              }

option_chains = api.get_option_chain(OptionChain_1)

expiration_option_chain = api.get_option_expirationchain('AAPL')


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
streamer.subs_request_levelone_options(keys = 'AAPL  240628C00100000')
streamer.subs_request_levelone_future_options(keys = 'AAPL  240628C00100000')

streamer.subs_request_nasdaq_book(keys = equities)
streamer.subs_request_options_book(keys = 'AAPL  240628C00100000')


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