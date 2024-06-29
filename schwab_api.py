# -*- coding: utf-8 -*-
"""
Created on Thu Nov  7 08:23:24 2019

@author: LC
"""

from datetime import datetime
import json
from typing import Optional, Dict, Any, Callable, List
import urllib.parse as up
import logging
import requests
from schwab_auth import SchwabAuth
from schwab_enum import (Status, TransactionType, AssetType, Instruction, Session, Duration,
                         OrderType, OrderStrategyType, Projection, Market, SymbolId, Sort,
                         MoversFrequency, Fields, FrequencyType, Frequency, PeriodType, Period)


if not logging.root.handlers:

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    logging.info("Logging activated at API")

logger = logging.getLogger(__name__)

BASE_MARKET_URL = 'https://api.schwabapi.com/marketdata/v1/'
BASE_TRADER_URL = 'https://api.schwabapi.com/trader/v1/'
ADDITIONAL_HEADERS = {'Content-Type':'application/json'}

class SchwabApi():
    '''
	Schwab API Class.

	Performs request to the Schwab API. Response in JSON format.
    '''
    def __init__(self, config):

        '''
        Initialize object with provided account info
        Open Authentication object to have a valid access token for every request.

        The following 2 lines create authentication object and run it.
        It will be use in the headers method to send a valid token.
        '''

        self._auth = SchwabAuth(config)

        #self._auth.authenticate()
        if self._auth:
            self.principals = self.get_user_preference()
            accounts = self.get_account_numbers()
            self.account_hash = accounts[0]['hashValue']

            logger.info("Schwab API Initialized")
        else:
            logger.warning("Could not authenticate")


    def __repr__(self):
        '''
        defines the string representation of our TD Ameritrade Class instance.
        '''

        # define the string representation
        return str(self._auth)

    def _make_request(self, method: Callable, base_url: str, endpoint: str,
                      additional_headers: Optional[Dict[str, str]] = None, **kwargs: Any):

        headers = self._auth.get_headers()
        if additional_headers:
            headers.update(additional_headers)
        url = up.urljoin(base_url, endpoint.lstrip('/'))

        try:
            response = method(url, headers=headers, verify=True, timeout=30, **kwargs)
            response.raise_for_status()
            if response.content:
                return response.json()
            return response

        except requests.exceptions.RequestException as error:
            logger.error("Error: %s, Response: %s", error, response.json())
            return None


    ########## Public services

    @property
    def access_token(self):
        return self._auth.access_token


    #################
    #### ACCOUNT DATA
    #################

    #### User Info & Preferences


    def get_user_preference(self):

        '''
        Get's User Preferences for specific account

        Documentation Link:
        https://developer.tdameritrade.com/user-principal/apis/get/
        accounts/%7BaccountTd%7D/preferences-0

        NAME: account
        DESC: The account number you wish to receive preference data for.
        TYPE: String

        EXAMPLES:
        Object.get_preferences(account = 'MyAccountNumber')
        '''

        endpoint = '/userPreference'

        return self._make_request(requests.get, BASE_TRADER_URL, endpoint)


    #### Account


    def get_account_numbers(self):
        '''
        Returns a mapping from account IDs available to this token to the
        account hash that should be passed whenever referring to that account in
        API calls.
        '''
        endpoint = '/accounts/accountNumbers'

        return self._make_request(requests.get, BASE_TRADER_URL, endpoint)


    def get_accounts(self, *, account_hash: Optional[str] = None, fields: Optional[str] = None):

        '''
        Account balances, positions, and orders for a specific account.
        Account balances, positions, and orders for all linked accounts.

        Serves as the mechanism to make a request to the "Get Accounts" and "Get Account" endpoint.
        If one account is provided a "Get Account" request will be made and if more than one account
        is provided then a "Get Accounts" request will be made.

        Documentation Link: http://developer.tdameritrade.com/
        account-access/apis

        NAME: account
        DESC: The account number you wish to receive data on. Default values is 'all'
              which will return all accounts of the user.
        TYPE: String

        NAME: fields
        DESC: Balances displayed by default, additional field can be added here by
              adding position or orders.
        TYPE = List<String>

        EXAMPLE:
        Object.get_accounts(account = 'all', fields = ['orders'])
        Object.get_accounts(account = 'My AccountNumber', fields = ['orders', 'positions'])
        '''

        params = {}
        if fields:
            params['fields'] = ','.join(fields)


        #if all use '/accounts' else pass through the account number.
        if account_hash:
            endpoint = f'/accounts/{account_hash}'
        else:
            endpoint = '/accounts'

        return self._make_request(requests.get, BASE_TRADER_URL, endpoint, params = params)


    #### Transaction History


    def get_transactions(self, start_date: str, end_date: str, *,
                         account_hash: Optional[str] = None,
                          transaction_type: Optional[str] = TransactionType.NONE ,
                          symbol: Optional[str] = None,
                          transaction_id: Optional[str]= None):

        '''
        Serves to make a request to the "Get Transactions" and "Get Transaction" Endpoint.
        If one 'transaction_id'is provided a "Get Transaction" request will be made and if it is
        not provided then a "Get Transactions"request will be made.

        Documentation Link: https://developer.tdameritrade.com/transaction-history/apis

        account_hash: The account number you wish to recieve transactions for.

        transaction_type: The type of transaction. Only transactions with specified type will
        be returned. Valid values are the following: ALL, TRADE, BUY_ONLY, SELL_ONLY,
                    CASH_INOR_CASH_OUT, CHECKING, DIVIDEND, INTEREST, ITHER, ADVISOR_FEES

        symbol: The symbol in the specified transaction. Only transactions with the specified
              symbol will be returned.

        start_date: Only transactions after the start date (included) will be returned.
        Note: the Max date range is one year. Valid ISO-8601 formats are: yyyy-MM-dd.

        end_date: Only transactions before the End Date (included) will be returned.
        Mote: the max date range is one year. Valid ISO-8601 formats are: yyyy-MM-dd

        transaction_id: The transaction ID you wish to search. If this is specified a
        "Get transaction"request
              is made. Should only be used if you wish to return one transaction.

        EXAMPLES:
        Object.get_transactions(account = 'MyAccountNum', transaction_type = 'ALL',
                                start_date = '2019-01-31', end_date = '2019-04-28')
        Object.get_transactions(account = 'MyAccountNum', transaction_type = 'ALL',
                                start_date = '2019-01-31')
        Object.get_transactions(account = 'MyAccountNum', transaction_type = 'TRADE')
        Object.get_transactions(transaction_id = 'MyTransactionID')
        '''

        account_hash = account_hash or self.account_hash

        if transaction_id:

            endpoint = f'/accounts/{account_hash}/transactions/{transaction_id}'

            return self._make_request(requests.get, BASE_TRADER_URL, endpoint)

        params = {'types':transaction_type.value,
                'symbol':symbol,
                'startDate':start_date,
                'endDate':end_date}

        endpoint = f'/accounts/{account_hash}/transactions'

        return self._make_request(requests.get, BASE_TRADER_URL, endpoint, params = params)


    #### Orders

    def get_orders(self, from_entered_datetime, to_entered_datetime,
                       *, max_results=None, status=Status.NONE):
        '''Orders for all linked accounts. Optionally specify a single status on
        which to filter.

        :param max_results: The maximum number of orders to retrieve.
        :param from_entered_datetime: Specifies that no orders entered before
                                      this time should be returned. Date must
                                      be within 60 days from today's date.
                                      ``toEnteredTime`` must also be set.
        :param to_entered_datetime: Specifies that no orders entered after this
                                    time should be returned. ``fromEnteredTime``
                                    must also be set.
        :param status: Restrict query to orders with this status. See
                       :class:`Order.Status` for options.
        '''
        endpoint = '/orders'
        params = {"maxResults": max_results,
                "fromEnteredTime": from_entered_datetime,
                "toEnteredTime": to_entered_datetime,
                "status": status.value}

        return self._make_request(requests.get, BASE_TRADER_URL, endpoint, params = params)



    def get_account_orders(self, from_entered_time, to_entered_time, *, account_hash = None,
                           max_results = None, status = Status.NONE):

        '''
        Returns the savedorders for a specific account.

        Documentation Link:
        https://developer.tdameritrade.com/account-access/apis/get/accounts/%7BaccountId%7D/orders-0

        NAME: account
        DESC: The account number that you want to query for orders.
        TYPE: String

        NAME: max_results
        DESC: The maximum nymber of orders to receive.
        TYPE: integer

        NAME: from_entered_time
        DESC: Specifies that no orders entered before this time should be returned.
              Valid ISO-8601 formats are : yyyy-MM-dd and yyyy-MM-dd'T'HH:mm:ssz
              Date must be within 60 days from today's date. 'toEnteredTime' must also be set.
        TYPE: string

        NAME: to_entered_time
        DESC: Specifies that no orders entered after this time should be returned.
              Valid ISO-8601 formats are: yyyy-MM-dd and yyyy-MM-dd'T'HH:mm:ssz.
              'fromEnteredTime' must also be set.
        TYPE: String

        NAME: status
        DESC: Specifies that only orders of this status should be returned. Possible values are:

                1. AWAITING_PARENT_ORDER
                2. AWAITING_CONDITION
                3. AWAITING_MANUAL_REVIEW
                4. ACCEPTED
                5. AWAITING_UR_NOT
                6. PENDING_ACTIVATION
                7. QUEUED
                8. WORKING
                9. REJECTED
                10. PENDING_CANCEL
                11. CANCELED
                12. PENDING_REPLACE
                13. REPLACED
                14. FILLED
                15. EXPIRED

        EXAMPLES:

        Object.get_orders_path(account = 'MyAccountID', max_result = 6,
                               from_entered_time = '2019-10-01', to_entered_tme = '2019-10-10)
        Object.get_orders_path(account = 'MyAccountID', max_result = 6, status = 'EXPIRED')
        Object.get_orders_path(account = 'MyAccountID', status ='REJECTED')
        Object.get_orders_path(account = 'MyAccountID')
        '''

        account_hash = account_hash or self.account_hash

        params = {"maxResults": max_results,
                "fromEnteredTime": from_entered_time,
                "toEnteredTime": to_entered_time,
                "status": status.value}

        endpoint = f'/accounts/{account_hash}/orders'

        return self._make_request(requests.get, BASE_TRADER_URL, endpoint, params = params)


    def get_order(self, order_id, account_hash = None):

        '''
        Get a specific order for a specific account.

        Documentation Link: https://developers.tdameritrade.com/account-access/apis/get/orders-a

        NAME: account
        DESC: The accountnumber that you want to queary the order for.
        TYPE: String

        NAME: order_id
        DESC: The order id.
        TYPE: String

        EXA<PLES:
        Session.Object.get_order(account = 'MyAccountID', order_id_ 'MyOrderID')
        '''

        account_hash = account_hash or self.account_hash

        endpoint = f'/accounts/{account_hash}/orders/{order_id}'

        return self._make_request(requests.get, BASE_TRADER_URL, endpoint)


    def cancel_order(self, order_id, account_hash = None):

        '''
        Cancel specific order for a specific account.

        Documentation Link:
        https://developers.tdameritrade.com/account-access/apis/delete/accounts/%7BaccountId%7D/
        orders/%7BporderID%7D-0

        NAME: account
        DESC: The accountnumber that you want to queary the order for.
        TYPE: String

        NAME: order_id
        DESC: The order id.
        TYPE: String

        EXAMPLES:
        Session.Object.cancel_order(account = 'MyAccountID', order_id_ 'MyOrderID')
        '''

        #define the endpoint
        account_hash = account_hash or self.account_hash
        endpoint = f'/accounts/{account_hash}/orders/{order_id}'

        #make the request
        response = self._make_request(requests.delete, BASE_TRADER_URL, endpoint)

        if response and response.status_code == 200:
            logger.info("Order %s was successfully CANCELED.", order_id)
        else:
            logger.error("Failed to cancel order %s.", order_id)



    # Function with type hints
    def place_order(self, symbol: str,
                    quantity: float,
                    instruction: Instruction,
                    asset_type: AssetType, *,
                    price: Optional[float] = None,
                    account_hash: Optional[str] = None,
                    order_type: OrderType = OrderType.MARKET,
                    session: Session = Session.NORMAL,
                    duration: Duration = Duration.DAY,
                    order_strategy_type: OrderStrategyType = OrderStrategyType.SINGLE):

        '''
        Create order. This method does not verify that the symbol or assets type are valid.

        Documentation Link:
        https://developer.tdameritrade.com/account-access/apis/post/accounts/%7BaccountId%7D/
        orders/%7BorderId%7D-0

        NAME: account
        DESC: The account number you wish to create the watchlist for.
        TYPE: String

        NAME: symbol
        DESC: Symbol to operate with.
        TYPE: String

        NAME: price
        DESC: price level for the order. If orderType is Market leave it in None
        TYPE: String

        NAME: quantity
        DESC: amount of shares to operate
        TYPE: String

        NAME: intruction
        DESC: "'BUY' or 'SELL' or 'BUY_TO_COVER' or 'SELL_SHORT' or 'BUY_TO_OPEN' or
               'BUY_TO_CLOSE' or 'SELL_TO_OPEN' or 'SELL_TO_CLOSE' or 'EXCHANGE'"
        TYPE: String

        NAME: assetType
        DESC: "'EQUITY' or 'OPTION' or 'INDEX' or 'MUTUAL_FUND' or 'CASH_EQUIVALENT' or
              'FIXED_INCOME' or 'CURRENCY'"
        TYPE: String

        NAME: orderType
        DESC: "'MARKET' or 'LIMIT' or 'STOP' or 'STOP_LIMIT' or 'TRAILING_STOP' or 'MARKET_ON_CLOSE'
              or 'EXERCISE' or 'TRAILING_STOP_LIMIT' or 'NET_DEBIT' or 'NET_CREDIT' or 'NET_ZERO'"
        TYPE: String

        NAME: session
        DESC: "'NORMAL' or 'AM' or 'PM' or 'SEAMLESS'"
        TYPE: String

        NAME: duration
        DESC: "'DAY' or 'GOOD_TILL_CANCEL' or 'FILL_OR_KILL'"
        TYPE: String

        NAME: orderStrategyType
        DESC: "'SINGLE' or 'OCO' or 'TRIGGER'"
        TYPE: String


        EXAMPLES:
        Object.create_order(account = 'MyaccountNumber' symbol = 'MELI', price = '100.00',
                            quantity = '100', instruction = 'BUY', assetType = 'EQUITY',
                            orderType = 'LIMIT', session = 'NORMAL', duration = 'DAY',
                            orderStrategyType = 'SINGLE')
        '''
        try:

            if not isinstance(instruction, Instruction):
                raise ValueError(
                    f'instruction must be an instance of Instruction Enum, got {type(instruction)}')
            if not isinstance(asset_type, AssetType):
                raise ValueError(
                    f'asset_type must be an instance of AssetType Enum, got {type(asset_type)}')
            if not isinstance(order_type, OrderType):
                raise ValueError(
                    f'order_type must be an instance of OrderType Enum, got {type(order_type)}')
            if not isinstance(session, Session):
                raise ValueError(
                    f'session must be an instance of Session Enum, got {type(session)}')
            if not isinstance(duration, Duration):
                raise ValueError(
                    f'duration must be an instance of Duration Enum, got {type(duration)}')
            if not isinstance(order_strategy_type, OrderStrategyType):
                raise ValueError(
                    f'order_strategy_type must be an instance of OrderStrategyType Enum, '
                    f'got {type(order_strategy_type)}')

            #define the payload
            if order_type.value in ('MARKET','MARKET_ON_CLOSE'):
                price = None

            if order_type.value != 'STOP':
                price_type = 'price'
            else:
                price_type = 'stopPrice'


            payload = {'orderType':order_type.value,
                       'session':session.value,
                       f'{price_type}': price,
                       'duration':duration.value,
                       'orderStrategyType':order_strategy_type.value,
                       'orderLegCollection':[
                                             {'instruction':instruction.value,
                                              'quantity':quantity,
                                              'instrument':{'symbol':symbol,
                                                            'assetType':asset_type.value
                                                           }
                                             }
                                            ]
                  }

            # define the endpoint
            account_hash = account_hash or self.account_hash
            endpoint = f'/accounts/{account_hash}/orders'

            response = self._make_request(requests.post, BASE_TRADER_URL, endpoint,
                                          ADDITIONAL_HEADERS, data = json.dumps(payload))


            if response and response.status_code == 201:
                logger.info("New %s order was successfully created.", symbol)
            else:
                logger.error("Failed to create new order for %s.", symbol)

        except Exception as error:
            logger.exception("An error occurred while replacing the order: %s", str(error))

    def replace_order(self, order_id: str,symbol: str, quantity: float,
                      instruction: Instruction,
                      asset_type: AssetType, *,
                      price: Optional[float] = None,
                      account_hash: Optional[str] = None,
                      order_type: OrderType = OrderType.MARKET,
                      session: Session = Session.NORMAL,
                      duration: Duration = Duration.DAY,
                      order_strategy_type: OrderStrategyType = OrderStrategyType.SINGLE):

        try:
            # Validación de tipos en tiempo de ejecución
            if not isinstance(instruction, Instruction):
                raise ValueError(
                    f'instruction must be an instance of Instruction Enum, got {type(instruction)}')
            if not isinstance(asset_type, AssetType):
                raise ValueError(
                    f'asset_type must be an instance of AssetType Enum, got {type(asset_type)}')
            if not isinstance(order_type, OrderType):
                raise ValueError(
                    f'order_type must be an instance of OrderType Enum, got {type(order_type)}')
            if not isinstance(session, Session):
                raise ValueError(
                    f'session must be an instance of Session Enum, got {type(session)}')
            if not isinstance(duration, Duration):
                raise ValueError(
                    f'duration must be an instance of Duration Enum, got {type(duration)}')
            if not isinstance(order_strategy_type, OrderStrategyType):
                raise ValueError(
                    f'order_strategy_type must be an instance of OrderStrategyType Enum, '
                    f'got {type(order_strategy_type)}')

            #define the payload
            if order_type.value in ('MARKET','MARKET_ON_CLOSE'):
                price = None

            if order_type.value != 'STOP':
                price_type = 'price'
            else:
                price_type = 'stopPrice'

            payload = {
                'orderType': order_type.value,
                'session': session.value,
                f'{price_type}': price,
                'duration': duration.value,
                'orderStrategyType': order_strategy_type.value,
                'orderLegCollection': [
                    {
                        'instruction': instruction.value,
                        'quantity': quantity,
                        'instrument': {
                            'symbol': symbol,
                            'assetType': asset_type.value
                        }
                    }
                ]
            }

            # Define the endpoint
            account_hash = account_hash or self.account_hash
            endpoint = f'/accounts/{account_hash}/orders/{order_id}'

            response = self._make_request(requests.put, BASE_TRADER_URL, endpoint,
                                          ADDITIONAL_HEADERS, data=json.dumps(payload))

            if response and response.status_code == 201:
                logger.info("Order %s was successfully replaced.", order_id)
            else:
                logger.error("Failed to replace order %s.", order_id)

        except Exception as error:
            logger.exception("An error occurred while replacing the order: %s", str(error))




    def preview_order(self, symbol: str, quantity: float,
                      instruction: Instruction,
                      asset_type: AssetType, *,
                      price: Optional[float] = None,
                      account_hash: Optional[str] = None,
                      order_type: OrderType = OrderType.MARKET,
                      session: Session = Session.NORMAL,
                      duration: Duration = Duration.DAY,
                      order_strategy_type: OrderStrategyType = OrderStrategyType.SINGLE):

        try:
            if not isinstance(instruction, Instruction):
                raise ValueError(
                    f'instruction must be an instance of Instruction Enum, got {type(instruction)}')
            if not isinstance(asset_type, AssetType):
                raise ValueError(
                    f'asset_type must be an instance of AssetType Enum, got {type(asset_type)}')
            if not isinstance(order_type, OrderType):
                raise ValueError(
                    f'order_type must be an instance of OrderType Enum, got {type(order_type)}')
            if not isinstance(session, Session):
                raise ValueError(
                    f'session must be an instance of Session Enum, got {type(session)}')
            if not isinstance(duration, Duration):
                raise ValueError(
                    f'duration must be an instance of Duration Enum, got {type(duration)}')
            if not isinstance(order_strategy_type, OrderStrategyType):
                raise ValueError(
                    f'order_strategy_type must be an instance of OrderStrategyType Enum, '
                    f'got {type(order_strategy_type)}')

            #define the payload
            if order_type.value in ('MARKET','MARKET_ON_CLOSE'):
                price = None

            if order_type.value != 'STOP':
                price_type = 'price'
            else:
                price_type = 'stopPrice'


            payload = {'orderType':order_type.value,
                       'session':session.value,
                       f'{price_type}': price,
                       'duration':duration.value,
                       'orderStrategyType':order_strategy_type.value,
                       'orderLegCollection':[
                                             {'instruction':instruction.value,
                                              'quantity':quantity,
                                              'instrument':{'symbol':symbol,
                                                            'assetType':asset_type.value
                                                           }
                                             }
                                            ]
                  }

            account_hash = account_hash or self.account_hash
            endpoint = f'/accounts/{account_hash}/previewOrder'

            response = self._make_request(requests.post, BASE_TRADER_URL, endpoint,
                                          ADDITIONAL_HEADERS, data = json.dumps(payload))

            if response and response.status_code == 201:
                logger.info("New %s preview order was successfully created.", symbol)
            else:
                logger.error("Failed to preview order for %s.", symbol)

        except Exception as error:
            logger.exception("An error occurred while replacing the order: %s", str(error))

    ################
    #### MARKET DATA
    ################

    #### Instruments

    def search_instruments(self, symbol, projection: Projection = Projection.SYMBOL_SEARCH):

        '''
        Search or retrive instrument data, including fundamental data.

        Documentation Link: https://developer.tdameritrade.com/instruments/apis/get/instruments

        NAME: symbol
        DESC: The symbol of the financial instrumen you would like toi search.
        TYPE: string

        NAME: projection
        DESC: Default type of request is "symbol-search". The type of request include the following:

                1. symbol-search
                   Retirve instrument data of a specific symbol or cusip

                2. symbol-regex
                   Retrive instrument data for all symbols matching regex.
                   Example: symbol= XYZ.* will return all symbols beginning with XYZ

                3. desc-search
                   Retrive instrument data for intruments whose description contains
                   the word supplied. Example: symbol = FakeCompany will returnall
                   instruments with FakeCompany in the description

                4. desc-regex
                   Search description with full regex support. Exmapl: symbol=XYZ.[A-C]
                   returns all instruments whose descriptios contains a word begining
                   with XYZ followed by a character A through C

                5. fundamental
                   Returns fundamental data for a single instrument specified by exact symbol.

        TYPE: String

        EAMPLES:
        Object.search_instruments(symbol = 'XYZ', projection = 'symbol-search')
        Object.search_instruments(symbol = 'XYZ', projection = 'symbol-regex')
        Object.search_instruments(symbol = 'FakeCompany', projection = 'desc-search')
        Object.search_instruments(symbol = 'XYZ.[A-C]', projection = 'desc-regex')
        Object.search_instruments(symbol = 'XYZ.[A-C]', projection = 'fundamental')
        Object.search_instruments(symbol = 'XYZ.[A-C]', projection = 'search')
        '''

        # build the params dictionary
        params = {'symbol':symbol,
                'projection':projection.value}

        #define the endpoint
        endpoint = '/instruments'

        # return the response of the get request.
        return self._make_request(requests.get, BASE_MARKET_URL, endpoint, params = params)


    def get_instruments(self, cusip_id):

        '''
        Get an instrument by CUSIP (Committe on Uniform Securities Identification PRocedures) code.

        Documentation Link:
        https://developer.tdameritrade.com/instruments/apis/get/instruments/%7Bcusip%7D

        NAME: cusip
        DESC: The CUSIP code of a given financial instrument.
        TYPE: string

        EXAMPLES:
        Object.get_instruments(cusip = 'SomeCUSIPNumber')
        '''

        #define the endpoint
        endpoint = f'/instruments/{cusip_id}'

        # return the resposne of the get request.
        return self._make_request(requests.get, BASE_MARKET_URL, endpoint)

    ####  Market Hours

    def get_markets_hours(self, markets: List[Market] = None, date = None):

        '''
        Retrieve market hours for specified markets

        Serves to make a request to the "Get Hours for multiple Markets for today or future date"

        Documentation Link: https://developer.tdameritrade.com/market-hours/apis


        EXAMPLES:
        Object.get_market_hours(markets = ['EQUITY', 'OPTION'], date = '2019-11-18')
        '''
         # build the params dictionary
        if Market.ALL in markets:
            markets = [Market.EQUITY, Market.OPTION, Market.FUTURE, Market.BOND, Market.FOREX]


        market_values = ','.join(market.value for market in markets)
        #markets = prepare_parameter_list(markets)

        params = {'markets': market_values,
                'date': date}

        endpoint = '/markets'

        return self._make_request(requests.get, BASE_MARKET_URL, endpoint, params = params)


    def get_market_hours(self, market_id: Market, date = None):

        '''
        Serves as the mechanism to make a request to the
        "Get Hours for simple Markets for today or future date" endpoint."

        Documentation Link: https://developer.tdameritrade.com/market-hours/apis

        NAME: markets
        DESC: The markets for which you're requesting market hours, comma-separated.
              Valid markets are EQUITY, OPTION, FUTURE, BOND, or FOREX.
        TYPE: List<Strings>


        EXAMPLES:
        Object.get_market_hours(market = 'EQUITY')
        '''

        params = {'markets': market_id.value,
                'date': date}

        endpoint = f'/markets/{market_id}'

        return self._make_request(requests.get, BASE_MARKET_URL, endpoint, params = params)


    #### Movers

    def get_movers(self, index: SymbolId, *, sort: Sort = Sort.NONE,
                   frequency: MoversFrequency = MoversFrequency.NONE):

        '''
        Top 10 (up or down) movers by value or percent for a particular index.

        Documentation Link: https://developer.tdameritrade.com/movers/apis/get/marketdata

        NAME: market
        DESC: The index symbol to get movers for. Can be $DJI, $COMPX, or $SPX.X.
        TYPE: String


        EXAMPLES:
        SessionObjec.get_movers(market = $DJI', sort = 'up', frequecy = 'Value')
        SessionObjec.get_movers(market = $COMPX', sort = 'down', frequency = 'percent')

        '''

        params = {'sort': sort.value,
                  'frequency':frequency.value}

        endpoint = f'/movers/{index.value}'

        return self._make_request(requests.get, BASE_MARKET_URL, endpoint, params = params)


    #### Quotes


    def get_quotes(self, symbols: list, fields: Fields = Fields.ALL, indicative: bool = False):

        '''
        Serves as the mechanism to make a request to Get Quotes Endpoint.

        Documentation Link: https://developer.tdameritrade.com/quotes/apis

        NAME: instruments
        DESC: A List of differen financial intruments.
        TYPE: List

        EXAMPLE:
        Object.get_quotes(intruments = ['MSFT'])
        Object.get_quotes(instruments = ['MSFT', 'SQ'])

        fields = quote, fundamental, extended, reference, regular  default = all
        '''

        symbols = ','.join(symbols)

        params = {'symbols': symbols,
                  'fields': fields.value,
                  'indicative': str(indicative).lower()}

        endpoint = '/quotes'

        return self._make_request(requests.get, BASE_MARKET_URL, endpoint, params = params)

    def get_quote(self, symbol_id, fields: Fields = Fields.ALL):


        params = {'fields': fields.value}
        endpoint = f'/{symbol_id}/quotes'

        return self._make_request(requests.get, BASE_MARKET_URL, endpoint, params = params)


    #### Price History

    def get_pricehistory_period(self, symbol,
                                frequency_type: FrequencyType = FrequencyType.DAY_MINUTE,
                                frequency: Frequency = Frequency.MINUTE_1,
                                period_type: PeriodType = PeriodType.DAY,
                                period: Period = Period.DAY_10,
                                need_extendedhours_data: bool = True,
                                need_previousclose_price: bool = True):

        '''
        Get price history for a symbol defining Period. Its provide data up to the last closed day.

        NAME: symbol
        DESC:
        TYPE: String

        NAME: periodType
        DESC: Type of period to show. Valid values are day, month, year, or ytd . Default is day.
        TYPE: String

        NAME: frequencyType
        DESC: The type of frequency with which a new candle is formed.
              Valid frequencyTypes by periodType (defaults marked with an asterisk):
                                                                    day: minute*
                                                                    month: daily, weekly*
                                                                    year: daily, weekly, monthly*
                                                                    ytd: daily, weekly*
        TYPE: String

        NAME: frequency
        DESC: The number of the frequencyType to be included in each candle.
              Valid frequencies by frequencyType (defaults marked with an asterisk):
                                                                    minute: 1*, 5, 10, 15, 30
                                                                    daily: 1*
                                                                    weekly: 1*
                                                                    monthly: 1*
        TYPE: String

        NAME: period
        DESC: The number of periods to show.
              Example: For a 2 day / 1 min chart, the values would be:
                                                                    period: 2
                                                                    periodType: day
                                                                    frequency: 1
                                                                    frequencyType: min

              Valid periods by periodType (defaults marked with an asterisk):
                                                                    day: 1, 2, 3, 4, 5, 10*
                                                                    month: 1*, 2, 3, 6
                                                                    year: 1*, 2, 3, 5, 10, 15, 20
                                                                    ytd: 1*
        TYPE: String

        NAME: needExtendedHoursData
        DESC: true for extended hours data, false for regular market hours only. Default is true
        TYPE: String
        '''

        params = {
                'symbol': symbol,
                'frequencyType': frequency_type.value,
                'frequency': frequency.value,
                'periodType': period_type.value,
                'period': period.value,
                'needExtendedHoursData': str(need_extendedhours_data).lower(),
                'needPreviousClose': str(need_previousclose_price).lower()
                }

        endpoint = '/pricehistory'

        return self._make_request(requests.get, BASE_MARKET_URL, endpoint, params = params)


    def get_pricehistory_dates(self, symbol,
                               frequency_type: FrequencyType,
                               frequency: Frequency,
                               end_date = datetime.now(),
                               start_date = datetime.now(),
                               need_extendedhours_data: bool = True,
                               need_previousclose_price: bool = True):

        '''
        Get price history for symbol defining date Interval. It provides data till the last second.

        NAME: symbol
        DESC:
        TYPE: String

        NAME: endDate
        DESC: End date as milliseconds since epoch. If startDate and endDate are provided,
              period should not be provided. Default is previous trading day.
        Type: DateTime

        NAME: startDate
        DESC: Start date as milliseconds since epoch. If startDate and endDate are provided,
              period should not be provided.
        Type: DateTime

        NAME: needExtendedHoursData
        DESC: true for extended hours data, false for regular market hours only. Default is true
        TYPE: String
        '''
        epoch = datetime.utcfromtimestamp(0)
        end_date = int((end_date - epoch).total_seconds()*1000)
        start_date = int((start_date - epoch).total_seconds()*1000)

        params = {
                'symbol': symbol,
                'frequencyType': frequency_type.value,
                'frequency': frequency.value,
                'endDate': end_date,
                'startDate': start_date,
                'needExtendedHoursData': str(need_extendedhours_data).lower(),
                'needPreviousClose': str(need_previousclose_price).lower()
                }

        # define the endpoint
        endpoint = '/pricehistory'

        return self._make_request(requests.get, BASE_MARKET_URL, endpoint, params = params)


    #### Option Chain


    def get_option_chain(self, option_chain):

        # symbol = None, contractType = None, StrikeCount = None, IncludeQuotes = None,
        # Strategy = None, interval = None, Strike = None, range = None, fromDate = None,
        # toDate = None, volatility = None, underlyingPrice = None, interestRate = None,
        # daysToExpiration = None, expMonth = None, optionType = None

        '''
        Get optionchain for a optionable Symbol.

        Documentation Link:
        https://developer.tdameritrade.com/option-chains/apis/get/marketdata/chains

        NAME: option_chain
        DESC: Represents a single OptionChainObject.
        Type: TDAmeritrade.OptionChainObject

        EXAMPLE:

        OptionChain_1 = {
                        "symbol": "",
                        "contractType": ['CALL', 'PUT', 'ALL'],
                        "strikeCount": '',
                        "includeQuotes":['TRUE','FALSE'],
                        "strategy": ['SINGLE', 'ANALYTICAL', 'COVERED', 'VERTICAL', 'CALENDAR',
                                     'STRANGLE', 'STRADDLE', 'BUTTERFLY', 'CONDOR', 'DIAGONAL',
                                     'COLLAR', 'ROLL'],
                        "interval": '',
                        "strike": "",
                        "range": ['ITM', 'NTM', 'OTM', 'SAK','SBK','SNK','ALL'],
                        "fromDate": "yyyy-MM-dd and yyyy-MM-dd'T'HH:mm:ssz",
                        "toDate": "yyyy-MM-dd and yyyy-MM-dd'T'HH:mm:ssz",
                        "volatility": "",
                        "underlyingPrice": "",
                        "interestRate": "",
                        "daysToExpiration": "",
                        "expMonth":['ALL','JAN','FEB','MAR', 'APR','MAY','JUN', 'JUL','AUG','SEP',
                                    'OCT', 'NOV', 'DEC'],
                        "optionType": ['S', 'NS', 'ALL']
                      }

        Object.get_option_chain( option_chain = option_chain_1)
        '''
        # take JSON representation of the string
        params = option_chain

        #define the endpoint
        endpoint = '/chains'

        return self._make_request(requests.get, BASE_MARKET_URL, endpoint, params = params)

    def get_option_expirationchain(self, symbol):

        params = {'symbol': symbol}

        endpoint = '/expirationchain'

        return self._make_request(requests.get, BASE_MARKET_URL, endpoint, params = params)
