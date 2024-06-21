# -*- coding: utf-8 -*-
"""
Created on Thu Jul 29 11:39:44 2021

@author: LC
"""

import time
import json
import logging
from datetime import datetime, timedelta
from threading import Thread
import socket
import websocket #websocket-client


if not logging.root.handlers:
    print("No loggin handler at Websocket")
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)


def is_connected():
    '''
    :return: True if there is internet connection
    :rtype: boolean
    '''
    # check internet connectivity
    try:
        # connect to the host -- tells us if the host is actually
        # reachable
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        return False

class SchwabWebSocket():
    '''
    Handles Schwab websocket connection.
    input parameter:
        keep_alive subscription function to be bind
        data manager function to be bind
    '''


    def __init__(self, api, keep_alive_manager = None, data_manager = None):

        self.api = api
        self._keep_alive_manager = keep_alive_manager or self._resubscribe_all
        self._data_manager = data_manager or self._store_data

        # Define a dictionary that defines response types
        self.response_types = {'notify': [], 'response': [], 'snapshot': [], 'data': []}
        self.current_subscriptions = []
        self.temp_subscriptions = []
        self.stream_delay = 0
        self.download_rate = 0
        self.timeoffset = 0
        self._data_len = 0
        self.total_downloaded_size = 0
        self.logged_in_since = None

        self.ping_time = None
        self.ping = 0
        self._start_time = time.time()


        self.is_logged_in = False
        self._user_logoff  = False
        self._on_close = False
        self._error = False

        self.request_id = -1
        self.streamer_info = None


    def bind_to_keep_alive_manager(self, keep_alive_manager):
        """
        Binds an external function as the keep-alive callback.

        Args:
            keep_alive_manager (callable): The function to call for keep-alive logic.
        """
        logger.info('%s bounded', keep_alive_manager.__name__)
        self._keep_alive_manager = keep_alive_manager


    def bind_to_data_manager(self, data_manager):
        """
        Binds an external function as the data handler.

        Args:
            data_manager (callable): The function to handle received data.
        """

        logger.info('%s bounded', data_manager.__name__)
        self._data_manager = data_manager



    def _reconnect(self):
        """
        Attempts to reconnect after a websocket connection drop.

        Waits for internet connectivity before restarting the streamer.
        """

        logger.info('Recovering connection...')
        # Wait to have internet back in case this was the reason for the interruption
        while not is_connected():
            time.sleep(2)

        # Restart the streamer
        self.connect()
        #time.sleep(2) # Allow time for re-establishment
        # subscribe everything as it was before interruption
        if self.is_logged_in:
            self._keep_alive_manager()


    def _resubscribe_all(self):
        '''
        Subscribe all subscriptions as before the interruption
        It will follow the same sequence of subscriptions and unsubcriptions
        '''

        subscriptions = self.current_subscriptions
        for subs in subscriptions:
            self.send_subscription_request(subs)



    def connect(self):
        '''
        Start websocket connection
        '''
        self._user_logoff  = False
        self._on_close = False
        self._error = False

        if not self.is_logged_in:

            self._open_connection()

            # Create a new thread
            websocket_thread = Thread(
                                    name='websocket_thread',
                                    target = self.websocket.run_forever,
                                    args = (None, None, 30,5),
                                    daemon=True)
            websocket_thread.start()

            waiting = 0
            while (not self.is_logged_in and not self._error
                    and not self._on_close and not self._user_logoff ):
                logger.info('Waiting on "Logged in" message')
                waiting += 1
                time.sleep(2)
                if waiting > 10:
                    self.websocket.close()
                    #break

            if self.is_logged_in:
                logger.info("Streamer started")
                if self.logged_in_since is None:
                    self.logged_in_since = datetime.now()


        else:
            logger.warning("Streamer already started")


    def _open_connection(self):

        response = self.api.get_user_preference()
        self.streamer_info = response['streamerInfo'][0]

        # Turn off seeing the send message.
        websocket.enableTrace(False)

        # Initalize a new websocket object.
        self.websocket = websocket.WebSocketApp(
                              self.streamer_info.get('streamerSocketUrl'),
                              on_message = self._ws_on_message,
                              on_error = self._ws_on_error,
                              on_close = self._ws_on_close,
                              on_pong = self._ws_on_pong)

        # Define what to do on the open, in this case send our login request.
        self.websocket.on_open = self._ws_on_open


    def _ws_on_pong(self, _ws, _msg):

        self.ping_time = datetime.fromtimestamp(self.websocket.last_ping_tm)
        pong_time = datetime.fromtimestamp(self.websocket.last_pong_tm)
        self.ping = (pong_time - self.ping_time).microseconds / 1000


    def _ws_on_open(self, _ws):
        '''
        When connection is open send the logging request
        '''
        self._send_login_request()


    def _ws_on_error(self, _ws, error):

        self._error = True
        error_str = str(error)

        print('-' * 40)
        logger.error(error_str)
# =============================================================================
#         if error_str == 'ping/pong timed out':
#             self._reconnect()
# =============================================================================


    def _ws_on_close(self, _ws, close_status_code = None, close_msg = None):

        logger.info(close_status_code)
        logger.info(close_msg)

        # No longer Logged In
        self.is_logged_in = False
        self._on_close = True
        print('-' * 40)
        logger.info('Websocket is Closed.')

        # objgraph.show_refs([self], filename='sample-graph.png')

        if not self._user_logoff : #if user logged off
            self._reconnect()


    def _ws_on_message(self, _ws, message):
        '''
        Handle the messages it receives
        '''

        self._data_len += len(message)
        self.total_downloaded_size += len(message)

        now = time.time()
        diff = now - self._start_time
        if diff >= 1:
            self.download_rate = round(self._data_len/diff,2)
            self._start_time = now
            #self.download_rate = copy.copy(self._data_len)
            self._data_len = 0

        # Load the message
        message = json.loads(message, strict = False)

        if 'notify' in message:
            self._handle_notify_message(message)
        elif 'response' in message:
            self._handle_response_message(message)
        elif 'snapshot' in message:
            self._handle_snapshot_message(message)
        elif 'data' in message:
            self._handle_data_message(message)


    def _handle_notify_message(self, content):

        self.response_types['notify'].append(content)

        if 'heartbeat' in content['notify'][0]:
            logger.info("Heartbeat")
            self._delay_test(int(content['notify'][0]['heartbeat']))
        else:
            logger.info(content)

    def _handle_response_message(self, content):
        '''
        The first response is the login answer, if it ok set the LoggedIn to True
        '''

        response_time = datetime.fromtimestamp(int(content['response'][0]['timestamp'])/1000)

        if ((content['response'][0]['command'] == 'LOGIN') and
            (content['response'][0]['content']['code'] == 0)):
            self.is_logged_in = True

            now = datetime.now()

            time_diff = now - response_time

            self.timeoffset = ((time_diff.microseconds + 90000) if time_diff.days < 0
                              else (90000 - time_diff.microseconds))

            if abs(self.timeoffset) > 1000000:
                logger.warning("Your system clock is off by more than 1 sec. Please synchronize it")
            logger.info('System clock offset: %d microseconds', self.timeoffset)
            logger.info('Logged in')

        else:
            logger.info("%s %s", content['response'][0]['content']['msg'],
                        content['response'][0]['service'])
            #logger.info('%-50s %s', response, response_time)

            service = content['response'][0]['service']
            command = content['response'][0]['command']

            matching_temp_subscription = next((sub for sub in self.temp_subscriptions
                                               if sub[0] == service), None)

            if content['response'][0]['content']['msg'][-17:] == "command succeeded":


                matching_current_subscription = next((sub for sub in self.current_subscriptions
                                                      if sub[0] == service), None)



                if command == "SUBS" and not matching_current_subscription:
                    self.current_subscriptions.append(matching_temp_subscription)

                elif command == "UNSUBS" and matching_current_subscription:
                    self.current_subscriptions.remove(matching_current_subscription)

                elif command == "ADD":
                    self.current_subscriptions.append(matching_temp_subscription)

            self.temp_subscriptions.remove(matching_temp_subscription)

        self.response_types['response'].append(content)


    def _handle_snapshot_message(self, content):
        '''
        snapshot from Get services
        '''
        self.response_types['snapshot'].append(content)


    def _handle_data_message(self, content):
        self._delay_test(content['data'][-1]['timestamp'])
        self._data_manager(content)

    def _store_data(self, content):
        self.response_types['data'].append(content)


    def _delay_test(self,timestamp):

        now = datetime.now()
        datatime = datetime.fromtimestamp(timestamp/1000)
        self.stream_delay = (now - datatime) + timedelta(microseconds = self.timeoffset)
        # self.stream_delay = (now - datatime).microseconds / 1000


    def _send_login_request(self):
        '''
        When WebSocket connection is opened, the first command
        to the Streamer Server must be a LOGIN command.
        '''
        parameters = {
            "Authorization": self.api.auth.access_token,
            "SchwabClientChannel": self.streamer_info.get("schwabClientChannel"),
            "SchwabClientFunctionId": self.streamer_info.get("schwabClientFunctionId")
        }

        login_request = {"service": "ADMIN",
                         "requestid": "0",
                         "command": "LOGIN",
                         "SchwabClientCustomerId": self.streamer_info.get("schwabClientCustomerId"),
                         "SchwabClientCorrelId": self.streamer_info.get("schwabClientCorrelId"),
                         "parameters": parameters
                        }


        ### Here is when we actually find out if the connection is granted or not.
        # For example if the uri is wrong you will not be able to log in then
        # connectipon started is False.

        self.websocket.send(json.dumps(login_request))


    def send_logout_request(self):
        '''
        Logout closes the WebSocket Session and cleans up
        all subscriptions for the client session.
        It’s a good practice to logout when closing the client tool.
        '''
        self._user_logoff = True

        if self.is_logged_in:

            self.is_logged_in = False
            self.current_subscriptions = []

            logout_request = {
                "service": "ADMIN",
                "requestid": "1",
                "command": "LOGOUT",
                "SchwabClientCustomerId": self.streamer_info.get("schwabClientCustomerId"),
                "SchwabClientCorrelId": self.streamer_info.get("schwabClientCorrelId")
                }

            self.websocket.send(json.dumps(logout_request))
            logger.info('Client is logged out.')
            self.websocket.close()

        else:
            logger.warning('Client is already logged out.')



    def send_qos_request(self, qoslevel = '0'):
        '''
        Quality of Service provides the different rates of data updates per protocol
        (binary, websocket etc), or per user based.

        0 = Express (500 ms)
        1 = Real-Time (750 ms) ß default value for http binary protocol
        2 = Fast (1,000 ms)  ßdefault value for websocket and http asynchronous protocol
        3 = Moderate (1,500 ms)
        4 = Slow (3,000 ms)
        5 = Delayed (5,000 ms)
        '''

        qos_request = {"service": "ADMIN",
                       "requestid": "2",
                       "command": "QOS",
                       "parameters": {"qoslevel": qoslevel}}

        self.send_request(qos_request)


    def send_request(self, request):
        '''
        Method for request handler. This method is the one that make requests to WebSocket
        :param data_request: DESCRIPTION
        :type data_request: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        '''

        request["SchwabClientCustomerId"] = self.streamer_info.get("schwabClientCustomerId")
        request["SchwabClientCorrelId"] = self.streamer_info.get("schwabClientCorrelId")


        if self.is_logged_in:
            self.websocket.send(json.dumps(request))

        else:
            logger.warning('''No websocket conection opened.
                  Please run connect method in order to be logged in.''')


    def send_subscription_request(self, subscription):
        '''
        Method for subscription handler
        '''
        self.temp_subscriptions.append(subscription)

        subs_request= {
                       "service": subscription[0],
                       "requestid": subscription[1],
                       "command": subscription[2],
                       "parameters": {
                                      "keys": subscription[3],
                                      "fields": subscription[4]
                                     }
                     }


        self.send_request(subs_request)
