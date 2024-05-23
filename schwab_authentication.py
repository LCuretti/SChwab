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

    """
    Schwab API Authentication Class.

    Implements the OAuth 2.0 Authorization Code Grant workflow,
    retrieves and manages access and refresh tokens for authenticated API calls.

    Attributes:
        schwab_config (dict): Configuration dictionary containing client ID,
                              app secret, redirect URI, and username (optional).
        store_refresh_token (bool, optional): Flag to control refresh token
                                              persistence (default: True).
        single_access (bool, optional): Flag to indicate single-use access
                                       token (default: False).
        _tokens (dict): Internal dictionary storing access and refresh tokens
                         along with their expiration times.
        logged_in_state (bool): Flag indicating successful authentication state.
    """

    # time constants (seconds)
    ACCESS_DURATION = 1800
    REFRESH_DURATION = 7776000


    def __init__(self, schwab_config: dict, store_refresh_token: bool  = True,
                 single_access: bool = False):

        """
        Initializes the Schwab authentication session.

        Args:
            schwab_config (dict): Configuration dictionary containing client ID,
                                   app secret, redirect URI, and username (optional).
            store_refresh_token (bool, optional): Flag to control refresh token
                                                   persistence (default: True).
            single_access (bool, optional): Flag to indicate single-use access
                                               token (default: False).
        """

        self._schwab_config = schwab_config
        self._store_refresh_token = store_refresh_token
        self._single_access = single_access
        self._tokens = {
                        'access_token': None,
                        'access_expiration': None,
                        'refresh_token': None,
                        'refresh_expiration': None
                       }

        self.logged_in_state = False
        self._initialize_logging()
        self._initialize_authentication()
        logging.info("Schwab authentication initialized at %s", datetime.now())

    def __repr__(self):
        """
        Defines the string representation of the SchwabAuthentication instance.

        Returns:
            str: String representation indicating logged-in state.
        """
        if self._tokens['access_expiration'] < datetime.now():
            self.logged_in_state = False
        return str(self.logged_in_state)

    def _initialize_logging(self):
        """
        Initializes basic logging configuration for informational messages.
        """
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("Schwab authentication initialized")

    def _initialize_authentication(self):
        """
        Initializes authentication logic, handling refresh token persistence or renewal.
        """
        refresh_token_file = f'./{self._schwab_config["user"]}refreshtoken.pickle'
        if os.path.isfile(refresh_token_file):
            if not self._store_refresh_token or self._single_access:
                os.remove(refresh_token_file)
                self._obtain_refresh_token()
            else:
                with open(refresh_token_file, 'rb') as file:
                    (self._tokens['refresh_token'],
                     self._tokens['refresh_expiration']) = pickle.load(file)

                self._refresh_access_token()
        else:
            self._obtain_refresh_token()


#### OBTAIN ACCESS AND REFRESH TOKEN

    def _obtain_access_code(self) -> str:
        """
        Retrieves an access code for requesting a refresh token.

        Returns:
            str: Access code obtained through user authentication.
        """

        api_key=self._schwab_config['client_id']
        callback_url=self._schwab_config['redirect_uri']

        state = secrets.token_hex(16)[:30]

        # build the URL and store it in a new variable
        auth_url = (
                "https://api.schwabapi.com/v1/oauth/authorize?"
                "response_type=code&client_id=" + api_key + "&"
                "redirect_uri=" + callback_url + "&"
                "state=" + state
                  )

        # aks the user to go to the URL provided, they will be prompted to authenticate themselves.
        print('Please login to your account.')
        webbrowser.open(auth_url)

        # ask the user to take the final URL after authentication and paste here so we can parse.
        redirected_url = input('Paste the redirected full URL here: ').strip()
        parsed_url = up.urlparse(redirected_url)
        query_params = up.parse_qs(parsed_url.query)

        return query_params.get('code', [None])[0]


    def _update_refresh_token(self, token_response: dict):
        """
        Updates the refresh token and its expiration time based on the provided token
        response dictionary.

        Args:
            token_response (dict): Dictionary containing the refresh token and
            its expiration information obtained from the API response.
        """

        self._tokens['refresh_token'] = token_response['refresh_token']
        self._tokens['refresh_expiration'] = (datetime.now() +
                                              timedelta(seconds=self.REFRESH_DURATION))

        if self._store_refresh_token:
            refresh_token_file = f'./{self._schwab_config["user"]}refreshtoken.pickle'
            with open(refresh_token_file, 'wb') as file:
                pickle.dump([self._tokens['refresh_token'],
                             self._tokens['refresh_expiration']], file)


    def _obtain_refresh_token(self):
        """
        Requests a refresh token and access token from the Schwab API by providing an access code,
        client ID, and redirect URI.

        Raises:
            requests.exceptions.RequestException: If an error occurs during the HTTP request.
        """

        url, headers, auth = self._get_request_basic_attributes()

        access_code = self._obtain_access_code()

        # define the payload
        payload = {
                'client_id': self._schwab_config['client_id'],
                'grant_type': 'authorization_code',
                'redirect_uri':self._schwab_config['redirect_uri'],
                'code': access_code
                  }

        try:
            response = requests.post(url, data=payload, headers=headers, auth=auth, timeout=5)
            response.raise_for_status()  # Raise an exception for non-200 status codes
        except requests.exceptions.RequestException as err:
            logging.error('Could not authenticate while getting refresh-token! Error: %s', str(err))
            self.logged_in_state = False
            return

        if response.status_code == 200:
            token_response = response.json()
            self._update_access_token(token_response)
            logging.info(token_response)
            if not self._single_access:
                self._update_refresh_token(token_response)


    def _get_request_basic_attributes(self):
        """
        Returns the basic attributes required for making an HTTP request to the Schwab API.

        Returns:
            tuple: A tuple containing the API URL, request headers,
            and basic authentication credentials.
        """

        url = r'https://api.schwabapi.com/v1/oauth/token'
        headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
                }
        auth = (self._schwab_config['client_id'],self._schwab_config['app_secret'])


        return url, headers, auth


#### OBTAIN ACCESS TOKEN

    def _obtain_access_token(self) -> requests.Response:
        """
        Makes a request to refresh the access token using the current refresh token.

        Returns:
            requests.Response: The response object containing
            the refreshed access token information.
        """

        url, headers, auth = self._get_request_basic_attributes()

        payload = {
                'client_id': self._schwab_config['client_id'],
                'grant_type': 'refresh_token',
                'refresh_token': self._tokens['refresh_token']
                }

        response = requests.post(url, data=payload, headers=headers, auth=auth, timeout=5)

        if response.status_code == 200:
            token_response = response.json()
            self._update_access_token(token_response)
        else:
            logging.error('Could not authenticate while refreshing token! Status code: %s',
                          response.status_code)
            self.logged_in_state = False
            self._obtain_refresh_token()


    def _refresh_access_token(self):
        """
        Refreshes the access token if it is nearing expiration.

        This method checks the expiration time of the refresh token. If the refresh token
        is within one day of expiring, a warning message is logged. Additionally, if the
        access token itself is about to expire (within 5 seconds), this method will
        attempt to refresh the access token using the refresh token.

        **Note:** This method is typically called periodically (e.g., every 30 minutes)
        to ensure a valid access token is available for API calls.
        """
        if self._tokens['refresh_expiration'] - timedelta(days = 1) < datetime.now():
            logging.warning('Refresh Token is almost expired or expired. Expiration: %s',
                          str(self._tokens['refresh_expiration'])[:22])
            self._obtain_refresh_token()
        else:
            self._obtain_access_token()


    def _update_access_token(self, token_response: dict):
        """
        Updates the access token and its expiration time based on
        the provided token response dictionary.

        This method is called after a successful refresh token exchange or initial
        access token retrieval. It extracts the access token and its expiration time from
        the `token_response` dictionary and updates the internal state of the object.

        **Arguments:**

        * token_response (dict): A dictionary containing the access token information
          returned by the Schwab API. This dictionary typically includes keys like
          'access_token' and 'expires_in'.

        **Internal Updates:**

        * `_tokens['access_token']`: Stores the updated access token.
        * `_tokens['access_expiration']`: Sets the expiration time for the access token
          based on the current time and the `ACCESS_DURATION` class attribute (assumed to
          be in seconds).
        * `logged_in_state`: Sets the `logged_in_state` flag to `True` to indicate successful
          authentication.
        """

        self._tokens['access_token'] = token_response['access_token']
        self._tokens['access_expiration'] = datetime.now() + timedelta(seconds=self.ACCESS_DURATION)
        self.logged_in_state = True


#### AUTHENTICATE

    def _authenticate(self):
        """
        Verifies the validity of the access token and refreshes it if necessary.

        This method checks the type of access granted (`_single_access` flag).

        * **Single Access:** If single access is enabled and the access token is about to expire
          (within 180 seconds), the method attempts to refresh the access token using the
          refresh token.
        * **Non-Single Access:** If single access is not enabled, the method checks if the
          access token is expired or about to expire (within 5 seconds). If so, it attempts
          to refresh the access token.

        This method is typically called before making API calls
        to ensure a valid access token is available.
        """

        if self._single_access and (self._tokens['access_expiration'] -
                                       timedelta(seconds = 180) < datetime.now()):
            self._obtain_refresh_token()

        elif self._tokens['access_expiration'] - timedelta(seconds = 5) < datetime.now():
            self._refresh_access_token()

#### PUBLIC SERVICES

    def get_url_and_headers(self, endpoint: str, content_type: str = None) -> tuple:
        """
        Provides the URL and headers required for making authenticated API calls to Schwab.

        This method first calls the `_authenticate` method to ensure a valid access token
        is available. If authentication is successful, it constructs the full API URL based
        on the provided endpoint (either a relative path or a full URL).

        **Arguments:**

        * endpoint (str): The API endpoint to access. It can be a relative path (e.g.,
          'quotes') or a full URL.
        * content_type (str, optional): The content type for the request. Defaults to
          `None`. If set to `'application/json'`, the `Accept` header is also set to
          `'application/json'`.

        **Returns:**

        * tuple: A tuple containing two elements:
            * url (str): The complete URL for the API call.
            * headers (dict): A dictionary containing the required HTTP headers for the request,
              including the `Authorization` header with the access token.

        **Raises:**

        * None: This method doesn't raise any exceptions directly. However, if
          authentication fails (`self.logged_in_state` is False), it logs an error message
          and returns `None, None`.
        """

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
        return None, None


    @property
    def access_token(self) -> str:
        """
        Provides a property to access the access token after automatic authentication.

        This property calls the `_authenticate` method to ensure a valid access token
        is available before returning it. If authentication fails, the property returns `False`.
        """

        self._authenticate()
        return self._tokens['access_token'] if self.logged_in_state else False
