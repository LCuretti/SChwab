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


config = read_json_file('./Schwab_config.json')


from schwab_api import SchwabApi

api = SchwabApi(config)
account = api.get_accounts(fields = ['positions'])

from schwab_streamer import SchwabStreamerClient

streamer = SchwabStreamerClient(api)

streamer.connect()


subs = streamer.ws.current_subscriptions
su = streamer.ws.temp_subscriptions


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


streamer.subs_request_levelone_options(keys = '')
streamer.subs_request_levelone_future_options(keys = '')


streamer.subs_request_nasdaq_book(keys = equities)


#streamer.schwab_ws.send_qos_request('0')

#streamer.subs_request_timesale_equity(keys = equities) #not available
#streamer.subs_request_timesale_futures(keys = futures) #not available
#streamer.subs_request_timesale_options(keys = futures) #not available
#streamer.subs_request_timesale_forex(keys = futures) #not available bad command formatting


#streamer.subs_request_quote(keys = equities) #not available
#streamer.subs_request_news_headline(keys = equities) #not available




#streamer.subs_request_actives_nasdaq() #not available
#streamer.subs_request_actives_nyse() #not available
#streamer.subs_request_actives_otcbb() #not available
#streamer.subs_request_actives_options() #not available

#streamer.logout()