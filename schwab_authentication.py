# -*- coding: utf-8 -*-
"""
Created on Sun Oct 13 13:09:41 2019
@author: LC
"""

import os
import pickle
import webbrowser
import secrets
import urllib.parse as up
import logging
from datetime import datetime, timedelta
import requests

class SchwabAuthentication():

    '''
    Schwab API Class.
    Implements OAuth 2.0 Authorization Code Grant workflow,
    adds token for authenticated calls.
    '''

    # time constants
    ACCESS_DURATION = 1800  # seconds
    REFRESH_DURATION = 7776000  # seconds


    def __init__(self, schwab_config: dict, store_refresh_token: bool  = True,
                 is_single_access: bool = False):

        '''
        Initializes the session with default values and any user-provided overrides.
        '''

        self._schwab_config = schwab_config
        self._store_refresh_token = store_refresh_token
        self._tokens = {
                        'access_token': None,
                        'access_expiration': None,
                        'refresh_token': None,
                        'refresh_expiration': None
                       }
        self._is_single_access = is_single_access
        self.logged_in_state = False

        self._initialize_authentication()
        logging.info("Schwab authentication initialized at %s", datetime.now())
        #print("Schwab Authentication Initialized at:".ljust(50)+str(datetime.now()))

    def __repr__(self):
        '''
        Defines the string representation of our Schwab Class instance.
        '''
        #if never logged in or expired the Log in state is False
        if self._tokens['access_expiration'] < datetime.now():
            self.logged_in_state = False
        return str(self.logged_in_state)

    def _initialize_authentication(self):
        '''
        Initialize authentication logic.
        '''
        refresh_token_file = f'./{self._schwab_config["user"]}refreshtoken.pickle'
        if os.path.isfile(refresh_token_file):
            if not self._store_refresh_token or self._is_single_access:
                os.remove(refresh_token_file)
                self._get_access_token()
            else:
                with open(refresh_token_file, 'rb') as file:
                    (self._tokens['refresh_token'],
                     self._tokens['refresh_expiration']) = pickle.load(file)

                self._refresh_access_token()
        else:
            self._get_access_token()



    def _get_access_code(self) -> str:
        '''
        Get access code which is needed for requesting the refresh token.
        '''

        api_key=self._schwab_config['client_id']
        callback_url=self._schwab_config['redirect_uri']

        state = secrets.token_hex(16)[:30]



        # build the URL and store it in a new variable
        auth_url = str('https://api.schwabapi.com/v1/oauth/authorize?response_type=code&client_id='
               + api_key + '&redirect_uri=' + callback_url +'&state='+ state)

        # aks the user to go to the URL provided, they will be prompted to authenticate themselves.
        print('Please login to your account.')
        webbrowser.open(auth_url)

        # ask the user to take the final URL after authentication and paste here so we can parse.
        redirected_url = input('Paste the redirected full URL here: ').strip()
        parsed_url = up.urlparse(redirected_url)
        query_params = up.parse_qs(parsed_url.query)

        return query_params.get('code', [None])[0]


    def _get_access_token(self):
        '''
        Request the Refresh and Access token providing access code,
        clint_id and redirect_uri.
        '''

        url = 'https://api.schwabapi.com/v1/oauth/token'
        headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
                }

        access_code = self._get_access_code()

        # define the payload
        payload = {
                'grant_type': 'authorization_code',
                'redirect_uri':self._schwab_config['redirect_uri'],
                'client_id': self._schwab_config['client_id'],
                'code': access_code
                  }

        auth = (self._schwab_config['client_id'],self._schwab_config['app_secret'])
        auth_reply = requests.post(url, data=payload, headers=headers, auth=auth, timeout=5)

        if auth_reply.status_code == 200:
            # convert it to dictionary
            token_response = auth_reply.json()
            #print(token_response)
            logging.info(token_response)
            if not self._is_single_access:
                self._update_refresh_token(token_response)

            # grab the access_token
            self._update_access_token(token_response)
        else:
            #print(auth_reply.status_code)
            #print('Could not authenticate while getting access token!')
            logging.error('Could not authenticate while getting access token! Status code: %s',
                          auth_reply.status_code)
            self.logged_in_state = False


    def _update_refresh_token(self, token_response: dict):
        '''
        Update the refresh token and its expiration.
        '''
        self._tokens['refresh_token'] = token_response['refresh_token']
        self._tokens['refresh_expiration'] = (datetime.now() +
                                              timedelta(seconds=self.REFRESH_DURATION))

        if self._store_refresh_token:
            refresh_token_file = f'./{self._schwab_config["user"]}refreshtoken.pickle'
            with open(refresh_token_file, 'wb') as file:
                pickle.dump([self._tokens['refresh_token'],
                             self._tokens['refresh_expiration']], file)


    def _refresh_access_token(self):
        '''
        refresh the access token providing the refreshtoken. It will run each 30 min.
        '''
        if self._tokens['refresh_expiration'] - timedelta(days = 1) < datetime.now():
            logging.warning('Refresh Token is almost expired or expired. Expiration: %s',
                          str(self._tokens['refresh_expiration'])[:22])
            #print("Refresh Token is almost expired or expired. Expiration: "
            #      +str(self._tokens['refresh_expiration'])[:22])
            #print("Renewing Refresh Token")
            self._get_access_token()
        else:
            refresh_response = self._request_refresh_token()

            if refresh_response.status_code != 200:
                logging.error('Could not authenticate while refreshing token! Status code: %s',
                              refresh_response.status_code)
                #print(refresh_response.status_code)
                #print('Could not authenticate while refreshing access token!')
                self.logged_in_state = False
                self._get_access_token()
            else:
                token_response = refresh_response.json()
                self._update_access_token(token_response)


    def _request_refresh_token(self) -> requests.Response:
        '''
        Make the request to refresh the access token.
        '''
        url = r'https://api.schwabapi.com/v1/oauth/token'


        headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
                }

        payload = {
                'grant_type': 'refresh_token',
                'refresh_token': self._tokens['refresh_token'],
                'client_id': self._schwab_config['client_id']
                }

        auth = (self._schwab_config['client_id'],self._schwab_config['app_secret'])
        return requests.post(url, data=payload, headers=headers, auth=auth, timeout=5)


    def _update_access_token(self, token_response: dict):
        '''
        Update the access token and its expiration.
        '''
        self._tokens['access_token'] = token_response['access_token']
        self._tokens['access_expiration'] = datetime.now() + timedelta(seconds=self.ACCESS_DURATION)
        self.logged_in_state = True


    def _authenticate(self):
        '''
        Verify if the access token is valid and update it if neccesarly.
        '''
        # If single access, renew the access token if it's about to expire
        if self._is_single_access and (self._tokens['access_expiration'] -
                                       timedelta(seconds = 180) < datetime.now()):
            self._get_access_token()
        # For non-single access, renew the access token if it's expired or about to expire
        # if the access token is less than 5 sec to expire or expired, then renew it.
        elif self._tokens['access_expiration'] - timedelta(seconds = 5) < datetime.now():
            self._refresh_access_token()


    def headers(self, endpoint: str, content_type: str = None) -> tuple:
        '''
        Returns a dictionary of default HTTP headers for calls to Schwab API,
        in the headers we defined the Authorization and access toke.
        '''
        self._authenticate()

        if self.logged_in_state:
            #Convert relative endpoint (e.g.,  'quotes') to full API endpoint.

            # if they pass through a valid url then, just use that.
            if up.urlparse(endpoint).scheme in ['http', 'https']:
                url = endpoint
            else:
            # otherwise build the URL
                url = up.urljoin('https://api.schwabapi.com/trader/v1/', endpoint.lstrip('/'))

            # create the headers dictionary
            headers ={'Authorization':f'Bearer {self._tokens["access_token"]}'}

            # if mode 'application/json' for request PUT, PATCH and POST
            if content_type == 'application/json':
                headers['Accept'] = 'application/json'

            return url, headers

        logging.error('Wrong authentication')
        #print('Wrong authentication')
        return None, None


    @property
    def access_token(self) -> str:
        ''' Allows you to call variable access_token and it authenticate before
            returning it.
            So there is no more need to call authenticate method. '''

        self._authenticate()
        return self._tokens['access_token'] if self.logged_in_state else False
