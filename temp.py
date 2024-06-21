# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import json
import logging

if not logging.root.handlers:
    # Configurar el logger
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # Crear un manejador para escribir en un archivo
    file_handler = logging.FileHandler('schwab_streamer.log')
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
        print(f'File not found: {file_path}')
        return []

CONFIG_FILE = 'Schwab_config.json'


from schwab_api import SchwabApi

user_data = read_json_file(CONFIG_FILE)
schwab_api = SchwabApi(user_data)
account = schwab_api.get_accounts(fields = ['positions'])
from schwab_websocket import SchwabStreamerWebSocket

schwab_websocket = SchwabStreamerWebSocket(schwab_api)

from schwab_stream_subscription import SchwabStreamerClient

schwab_streamer = SchwabStreamerClient(schwab_websocket)

schwab_websocket.connect()


subs = schwab_websocket.current_subscriptions
su = schwab_websocket.temp_subscriptions


indicators = '$DJI, $TICK'
equities = 'SPY, AAPL, MELI, GOOG, AMZN, NFLX, TSLA, NVDA, SLB, C, META, MSFT, KO, DIS, ADBE, QQQ KO'
futures = '/ES, /CL, /BTC'

equities = equities +str(', ')+ indicators

schwab_streamer.subs_request_account_activity()
#schwab_streamer.subs_request_account_activity(command="UNSUBS")

schwab_streamer.subs_request_chart_equity(keys = equities)
schwab_streamer.subs_request_chart_futures(keys = futures)


schwab_streamer.subs_request_levelone_equity(keys = equities)
schwab_streamer.subs_request_levelone_futures(keys = futures)
schwab_streamer.subs_request_levelone_forex(keys = 'EUR/USD')


schwab_streamer.subs_request_levelone_options(keys = '')
schwab_streamer.subs_request_levelone_future_options(keys = '')


schwab_streamer.subs_request_nasdaq_book(keys = equities)


#schwab_streamer.schwab_ws.send_qos_request('0')

#schwab_streamer.subs_request_timesale_equity(keys = equities) #not available
#schwab_streamer.subs_request_timesale_futures(keys = futures) #not available
#schwab_streamer.subs_request_timesale_options(keys = futures) #not available
#schwab_streamer.subs_request_timesale_forex(keys = futures) #not available bad command formatting


#schwab_streamer.subs_request_quote(keys = equities) #not available
#schwab_streamer.subs_request_news_headline(keys = equities) #not available




#schwab_streamer.subs_request_actives_nasdaq() #not available
#schwab_streamer.subs_request_actives_nyse() #not available
#schwab_streamer.subs_request_actives_otcbb() #not available
#schwab_streamer.subs_request_actives_options() #not available

#schwab_websocket.send_logout_request()