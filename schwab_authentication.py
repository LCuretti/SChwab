# -*- coding: utf-8 -*-
"""
The MIT License

Copyright (c) 2018 Addison Lynch

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

Created on Sun Oct 13 13:09:41 2019
@author: LC
"""

import os
import pickle

import webbrowser
import secrets
import urllib.parse as up

from datetime import datetime, timedelta
import requests

class schwabAuthentication():

    '''
        Schwab API Class.

        Implements OAuth 2.0 Authorization Code Grant workflow,
        adds token for authenticated calls.
    '''
    # time constants
    ACCESS_DURATION = 1800  # seconds
    REFRESH_DURATION = 7776000  # seconds


    def __init__(self, schwab_config, store_refresh_token = True, is_single_access = False):

        '''
            Initializes the session with default values and any user-provided
            overrides.

            The following arguments MUST be specified at runtime or else
            initialization will fail.

            NAME: client_id
            DESC: The Consumer ID assigned to you during the App registration.
                  This can be found at the app registration portal.
                  A must to get the access token

            NAME: redirect_uri
            DESC: This is the redirect URL that you specified when created your
                  Schwab Application. A must in order to get the access token

            NAME: account_id
            DESC: TD Account number. Needed in order to save or retrieve refreshtoken.

            NAME: store_refresh_token
            DESC: If True, RefreshToken will be stored.

            NAME: is_single_access
            DESC: True if there is no need to autorefresh the access token.
                  If after expiration Authentication is call, the complete
                  authentication will be done.
        '''

        self._schwab_config = schwab_config
        self._store_refresh_token = store_refresh_token
        self._tokens = {'access_token': None,
                       'access_expiration': None,
                       'refresh_token': None,
                       'refresh_expiration': None
                       }
        self._is_single_access = is_single_access

        self.logged_in_state = False

        self._initialize_authentication()

        print("Schwab Authentication Initialized at:".ljust(50)+str(datetime.now()))

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

        if os.path.isfile(f'./{self._schwab_config["user"]}refreshtoken.pickle'):
            if not self._store_refresh_token or self._is_single_access:
                os.remove(f'./{self._schwab_config["user"]}refreshtoken.pickle')
                self._get_access_token()
            else:
                with open(f'{self._schwab_config["user"]}refreshtoken.pickle', 'rb') as file:
                    (self._tokens['refresh_token'],
                     self._tokens['refresh_expiration']) = pickle.load(file)

                    self._refresh_access_token()
        else:
            self._get_access_token()



    def _get_access_code(self):
        '''
            Get access code which is needed for requesting the refresh token.

            Need to Authenticate providing User and Password or through the browser.

            This authentication is only necessary each 3 month if the refreshtoken
            is saved (_store_refresh_token=True)
            User may choose to save the refreshtoken that allows to handle most of
            the account but Money Transfers for example or
            Save the account data giving full access, and allowing this authentication
            to be done without any future user interaction.
            The API store the data linked to the account number, so multiple user can
            use it in the same computer.

            The is_single_access make the API to not store anything, not even in memory.
            For the cases you are logging in others computer.
            If that the case will be necessary to go through full authentication each 30 min.

        '''

        api_key=self._schwab_config['client_id']
        callback_url=self._schwab_config['redirect_uri']

        state = state = secrets.token_hex(16)[:30]



        # build the URL and store it in a new variable
        auth_url = str('https://api.schwabapi.com/v1/oauth/authorize?response_type=code&client_id='
               + api_key + '&redirect_uri=' + callback_url +'&state='+ state)

        # aks the user to go to the URL provided, they will be prompted to authenticate themselves.
        print('Please login to your account.')
        webbrowser.open(f"{auth_url}")

        # ask the user to take the final URL after authentication and paste here so we can parse.
        redirected_url = input('Paste the redirected full URL here: ').strip()

        # Parsear la URL
        parsed_url = up.urlparse(redirected_url)

        # Extraer los parámetros de consulta
        query_params = up.parse_qs(parsed_url.query)

        access_code = query_params.get('code', [None])[0]
        #session = query_params.get('session', [None])[0]
        #state = query_params.get('state', [None])[0]

        return access_code


    def _get_access_token(self):
        '''
            Request the Refresh and Access token providing access code,
            clint_id and redirect_uri.
        '''

        # THE AUTHENTICATION ENDPOINT
        #define the endpoint

        url = r'https://api.schwabapi.com/v1/oauth/token'
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}

        access_code = self._get_access_code()

        # define the payload
        payload = {'grant_type': 'authorization_code',
                   'redirect_uri':self._schwab_config['redirect_uri'],
                   'client_id': self._schwab_config['client_id'],
                   'code': access_code
                   }

        auth = (self._schwab_config['client_id'],self._schwab_config['app_secret'])
        auth_reply = requests.post(url = url, data = payload, headers = headers, auth=auth, timeout=5)


        if auth_reply.status_code == 200:
            # convert it to dictionary
            token_response = auth_reply.json()
            print(token_response)
            if not self._is_single_access:
                self._update_refresh_token(token_response)

            # grab the access_token
            self._update_access_token(token_response)
            return

        print(auth_reply.status_code)
        self.logged_in_state = False
        print('Could not authenticate while getting access token!')


    def _update_refresh_token(self, token_response):
        '''
        Update the refresh token and its expiration.
        '''
        self._tokens['refresh_token'] = token_response['refresh_token']
        self._tokens['refresh_expiration'] = (datetime.now() +
                                              timedelta(seconds=self.REFRESH_DURATION))

        # If refresh store_refresh_token is True, store the refresh token and its expiration
        if self._store_refresh_token:
            with open(f'{self._schwab_config["user"]}refreshtoken.pickle', 'wb') as file:
                pickle.dump([self._tokens['refresh_token'],
                             self._tokens['refresh_expiration']], file)


    def _refresh_access_token(self):
        '''
            refresh the access token providing the refreshtoken. It will run each 30 min.
        '''
        if self._tokens['refresh_expiration'] - timedelta(days = 1) < datetime.now():
            print("Refresh Token is almost expired or expired. Expiration: "
                  +str(self._tokens['refresh_expiration'])[:22])
            print("Renewing Refresh Token")
            self._get_access_token()
        else:
            refresh_response = self._request_refresh_token()

            if refresh_response.status_code != 200:
                print(refresh_response.status_code)
                self.logged_in_state = False
                print('Could not authenticate while refreshing access token!')
                self._get_access_token()
            else:
                token_response = refresh_response.json()

                self._update_access_token(token_response)


    def _request_refresh_token(self):
        '''
        Make the request to refresh the access token.
        '''
        auth = (self._schwab_config['client_id'],self._schwab_config['app_secret'])
        url = r'https://api.schwabapi.com/v1/oauth/token'
        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}

        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': self._tokens['refresh_token'],
            'client_id': self._schwab_config['client_id']
        }

        return requests.post(url = url, data = payload, headers = headers, auth=auth, timeout=5)


    def _update_access_token(self, token_response):
        '''
        Update the access token and its expiration.
        '''
        self._tokens['access_token'] = token_response['access_token']
        self._tokens['access_expiration'] = datetime.now() + timedelta(seconds=self.ACCESS_DURATION)
        self.logged_in_state = True


    def _authenticate(self):
        '''
            Verify if the access token is valid and update it if neccesarly.
            Call it before any API request in order to avoid expiration.
            After go through it ensures that the token is still valid
            for requests.
        '''
        # If single access, renew the access token if it's about to expire
        if self._is_single_access and (self._tokens['access_expiration'] -
                                       timedelta(seconds = 30) < datetime.now()):
            self._get_access_token()
        # For non-single access, renew the access token if it's expired or about to expire
        # if the access token is less than 5 sec to expire or expired, then renew it.
        elif self._tokens['access_expiration'] - timedelta(seconds = 5) < datetime.now():
            self._refresh_access_token()


    def headers(self, endpoint, mode = None):
        '''
        Returns a dictionary of default HTTP headers for calls to Schwab API,
        in the headers we defined the Authorization and access toke.

        In the following two line we use the Authentication object to get a valid token.
        You may have a different way to get a valid token for the request.
        '''

        # grab the access token
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
            merged_headers ={'Authorization':f'Bearer {self._tokens["access_token"]}'}

            # if mode 'application/json' for request PUT, PATCH and POST
            if mode == 'application/json':
                merged_headers['Accept'] = 'application/json'

            return url, merged_headers

        print('Wrong authentication')
        return None, None


    @property
    def access_token(self):
        ''' Allows you to call variable access_token and it authenticate before
            returning it.
            So there is no more need to call authenticate method. '''

        self._authenticate()
        if self.logged_in_state:
            return self._tokens['access_token']

        return False
