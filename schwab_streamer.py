# -*- coding: utf-8 -*-
"""
Created on Mon Sep  2 11:19:59 2019

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

@author: LC
"""
from datetime import datetime
import logging
from schwab_websocket import SchwabWebSocket

if not logging.root.handlers:

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Logging activated at Stremer")
logger = logging.getLogger(__name__)


class SchwabStreamerClient():
    '''
    Schwab API Class.

    Performs subscriptions requests to the Schwab.

    id	service              	command          parameters	                              Response Type
    0	ADMIN	                LOGIN       	 credential, token, version			           response
    1	                        LOGOUT	         None			                               response
    2		                    QOS      	     "qoslevel": "0","1","2","3","4","5"           response
    3	ACCT_ACTIVITY	        SUBS/UNSUBS      "treamkeys		                                   data
    4	ACTIVES_NASDAQ        	SUBS/ADD/UNSUBS  "NASDAQ" - "60","300","600","1800","3600","ALL"   data
    5	ACTIVES_NYSE          	SUBS/ADD/UNSUBS  "NYSE" - "60","300","600","1800","3600","ALL"     data
    6	ACTIVES_OTCBB         	SUBS/ADD/UNSUBS  "OTCBB" - "60","300","600","1800","3600","ALL"    data
    7	ACTIVES_OPTIONS       	SUBS/ADD/UNSUBS  "CALLS*","OPTS*","PUTS*","CALLS-DESC*", 	       data
                                                 "OPTS-DESC*","PUTS-DESC*"(*options)
                                                 - "60","300","600","1800","3600","ALL"
    8	CHART_EQUITY          	SUBS/ADD/UNSUBS  keys = symbols                                    data
    9	CHART_FUTURES         	SUBS/ADD/UNSUBS  keys = future symbol as a product (ie. /ES)       data
    10	CHART_OPTIONS          	SUBS/ADD/UNSUBS  keys = symbols (ie. SPY_111819C300)		       data
    11	QUOTE                	SUBS/ADD/UNSUBS  keys = symbols                                    data
    12	OPTION               	SUBS/ADD/UNSUBS  keys = symbols (ie. SPY_111819C300)               data
    13	LISTED_BOOK          	SUBS/ADD/UNSUBS  keys = symbols	                                   data
    14	NASDAQ_BOOK          	SUBS/ADD/UNSUBS  keys = symbols                                    data
    15	OPTIONS_BOOK         	SUBS/ADD/UNSUBS  keys = symbols (ie. SPY_111819C300)               data
    16	LEVELONE_FUTURES     	SUBS/ADD/UNSUBS  keys = future symbol as a product (ie. /ES)       data
    17	LEVELONE_FOREX       	SUBS/ADD/UNSUBS  keys = FOREX symbols (ie.. EUR/USD)               data
    18	TIMESALE_EQUITY      	SUBS/ADD/UNSUBS  keys = symbols                                    data
    19	TIMESALE_FUTURES	    SUBS/ADD/UNSUBS  keys = future symbol as a product (ie. /ES)       data
    20	TIMESALE_OPTIONS     	SUBS/ADD/UNSUBS  keys = symbols (ie. SPY_111819C300)	           data
    21	NEWS_HEADLINE        	SUBS/ADD/UNSUBS  keys = symbols                                    data
    22	NEWS_HEADLINELIST    	GET              keys = symbols                                snapshot
    23	NEWS_STORY           	GET              story_id (ie. SN20191111010526)               snapshot
    24	CHART_HISTORY_FUTURES	GET              symbols, frequency: "m1","m5","m10","m30",
                                                                      ,"h1","d1","w1","n1",
                                                          perdiod: "d5","w4","n10","y1",
	                                                                   "y10", sT, eT           snapshot
    25	FOREX_BOOK           	SUBS             Service not available or temporary down.
    26	FUTURES_BOOK         	SUBS             Service not available or temporary down.
    27	LEVELONE_FUTURES_OPTIONS SUBS            Service not available or temporary down.
    28	FUTURES_OPTIONS_BOOK	SUBS             Not managed
    29	TIMESALE_FOREX       	SUBS             Not managed
    30	LEVELTWO_FUTURES       	SUBS             Not managed
    31	STREAMER_SERVER	                         Not managed

    '''

    def __init__(self, api, subs_manager = None, data_manager = None):
        '''
            Open API object in order to get credentials, url necessary for streaming login

            schwab_ws: WebSocket Object

        '''


        self._ws = SchwabWebSocket(api, data_manager=data_manager)

        if subs_manager is None:
            self.subs_manager = self._ws.send_subscription_request
        else:
            self.subs_manager = subs_manager

# =============================================================================
#     def __repr__(self):
#         '''
#             defines the string representation of our Schwab Class instance.
#         '''
#         # define the string representation
#         return f'<Schwab Streaming API - Connected = {self.is_logged_in}>'
# =============================================================================

    def bind_to_subs_manager(self, subs_manager):
        '''
        Serves to bing external function as callback function

        :param callback: callback function
        :type callback: function or method

        '''
        logger.info('%s bounded', subs_manager.__name__)
        self.subs_manager = subs_manager


    def connect(self):
        """
        Connect to websocket
        """
        self._ws.connect()

    def logout(self):
        """
        Disconnect the WebSocket
        """
        self._ws.send_logout_request()





    #### SUBSCRIPTION REQUESTS ##################

    # You may do the subscription request with subs_request but then need to handle the ID
    # asignation in order to add or unsunbscribe or not to or to avoid requesting different
    # data in same ID. In order to let the streamer handle them use followings methods


    def subs_request_account_activity(self, command = "SUBS",
                                      fields = '0,1,2,3', store_flag = True):
        '''
        This service is used to request streaming updates for one or
        more accounts associated with the logged in User ID.
        Common usage would involve issuing the OrderStatus API request
        to get all transactions for an account, and subscribing
        to ACCT_ACTIVITY to get any updates.

        NAME: command
        DESC: chose between "SUBS"= subscribe, "UNSUBS"= unsubscribe
        TYPE: String

        NAME: fields
        DESC: select streaming fields.:
        Field   Field Name          Type        Field Description
        key     Subscription Key    str         Subscription Key
        seq     Sequence            int         Ticker sequence number
        1       Account #           str         Account Number
        2       Message Type        str         Message Type
        3       Acttivity (xml)     str         Acttivity detail in XML format
        TYPE: String

        EXAMPLES:
        SessionObject.data_request_account_activity(command = "SUBS", fields = '0,1')

        '''
        subs_request = ["ACCT_ACTIVITY", "3", command,
                        self._ws.streamer_info.get("schwabClientCorrelId"),
                        fields, store_flag]

        self.subs_manager(subs_request)

    def subs_request_actives_nasdaq(self, command = "SUBS", keys = 'NASDAQ-60',
                                    fields = '0,1', store_flag = True):

        '''
        Actives shows the day’s top most traded symbols in the four exchanges.
        Different duration can be selected.

        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Shoud be formed as: "Venue"-"Duration"
              Venue:
                      NASDAQ
              Duration:
                      ALL= all day
                      3600 = 60 min
                      1800 = 30 min
                      600 = 10 min
                      300 = 5 min
                      60 = 1 min
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:
                                        0 = Subscription Key
                                        1 = Actives Data
        TYPE: String

        EXAMPLES:
        SessionObject.data_request_actives_nasdaq(command = "SUBS", keys = 'NASDAQ-60',
                                                  fields = '0,1')
        '''

        subs_request = ["ACTIVES_NASDAQ", "4", command, keys, fields, store_flag]

        self.subs_manager(subs_request)


    def subs_request_actives_nyse(self, command = "SUBS", keys = 'NYSE-60',
                                  fields = '0,1', store_flag = True):

        '''
        Actives shows the day’s top most traded symbols in the four exchanges.
        Different duration can be selected.

        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Shoud be formed as: "Venue"-"Duration"
              Venue:
                      NYSE

              Duration:
                      ALL= all day
                      3600 = 60 min
                      1800 = 30 min
                      600 = 10 min
                      300 = 5 min
                      60 = 1 min
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:
                                        0 = Subscription Key
                                        1 = Actives Data
        TYPE: String

        EXAMPLES:
        SessionObject.data_request_actives_nyse(command = "SUBS", keys = 'NYSE-60',
                                                fields = '0,1')
        '''

        subs_request = ["ACTIVES_NYSE", "5", command, keys, fields, store_flag]

        self.subs_manager(subs_request)


    def subs_request_actives_otcbb(self, command = "SUBS", keys = 'OTCBB-60',
                                   fields = '0,1', store_flag = True):

        '''
        Actives shows the day’s top most traded symbols in the four exchanges.
        Different duration can be selected.

        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Shoud be formed as: "Venue"-"Duration"
              Venue:
                      OTCBB

              Duration:
                      ALL= all day
                      3600 = 60 min
                      1800 = 30 min
                      600 = 10 min
                      300 = 5 min
                      60 = 1 min
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:
                                        0 = Subscription Key
                                        1 = Actives Data
        TYPE: String

        EXAMPLES:
        SessionObject.data_request_actives_otcbb(command = "SUBS", keys = 'OTCBB-60',
                                                 fields = '0,1')
        '''

        subs_request = ["ACTIVES_OTCBB", "6", command, keys, fields, store_flag]

        self.subs_manager(subs_request)


    def subs_request_actives_options(self, command = "SUBS", keys = 'OPTS-DESC-60',
                                     fields = '0,1', store_flag = True):

        '''
        Actives shows the day’s top most traded symbols in the four exchanges.
        Different duration can be selected.

        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Shoud be formed as: "Venue"-"Duration"
              Venue:
                      CALLS*
                      OPTS*
                      PUTS*
                      CALLS-DESC*
                      OPTS-DESC*
                      PUTS-DESC*
                      (*options)
              Duration:
                      ALL= all day
                      3600 = 60 min
                      1800 = 30 min
                      600 = 10 min
                      300 = 5 min
                      60 = 1 min
        TYPE: String

        NAME: fields
        DESC: select streaming fields.:
                                        0 = Subscription Key
                                        1 = Actives Data
        TYPE: String

        EXAMPLES:
        SessionObject.data_request_actives_options(command = "SUBS", keys = 'OPTS-DESC-ALL',
                                                   -fields = '0,1')
        '''

        subs_request = ["ACTIVES_OPTIONS", "7", command, keys, fields, store_flag]

        self.subs_manager(subs_request)


    def subs_request_chart_equity(self, command = "SUBS", keys = 'SPY, AAPL',
                                  fields = '0,1,2,3,4,5,6,7,8', store_flag = True):

        '''
        Chart provides  streaming one minute OHLCV (Open/High/Low/Close/Volume)
        for a one minute period .
        The one minute bar falls on the 0 second slot (ie. 9:30:00) and includes
        data from 0 second to 59 seconds.
        For example, a 9:30 bar includes data from 9:30:00 through 9:30:59.

        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:
        Field   Field Name          Type        Field Description
        key     Subscription Key    String      Ticker symbol in upper case
        seq     Sequence            int         Ticker sequence number
        1       Open Price          double      Opening price for the minute
        2       High Price          double      Highest price for the minute
        3       Low Price           double      Chart’s lowest price for the minute
        4       Close Price         double      Closing price for the minute
        5       Volume              double      Total volume for the minute
        6       Sequence            long        Identifies the candle minute
        7       Chart Time          long        Milliseconds since Epoch
        8       Chart Day           int         Not Useful
        TYPE: String

        EXAMPLES:
        SessionObject.data_request_chart_equity(command = "SUBS", keys = 'SPY, AAPL',
                                                fields = '0,1,2,3,4,5,6,7,8')
        '''

        subs_request = ["CHART_EQUITY", "8", command, keys, fields, store_flag]

        self.subs_manager(subs_request)


    def subs_request_chart_futures(self, command = "SUBS", keys = '/ES',
                                   fields = '0,1,2,3,4,5,6', store_flag = True):

        '''
        Chart provides  streaming one minute OHLCV (Open/High/Low/Close/Volume)
        for a one minute period .
        The one minute bar falls on the 0 second slot (ie. 9:30:00) and includes data
        from 0 second to 59 seconds.
        For example, a 9:30 bar includes data from 9:30:00 through 9:30:59.

        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:
        Field   Field Name          Type        Field Description
        key     Subscription Key    String      Ticker symbol in upper case
        1       ChartTime           long        Milliseconds since Epoch
        2       Open Price          double      Opening price for the minute
        3       High Price          double      Highest price for the minute
        4       Low Price           double      Chart’s lowest price for the minute
        5       Close Price         double      Closing price for the minute
        6       Volume              double      Total volume for the minute
        TYPE: String

        EXAMPLES:
        SessionObject.data_request_chart_futures(command = "SUBS", keys = '/ES',
                                                 fields = '0,1,2,3,4,5,6')
        '''

        subs_request = ["CHART_FUTURES", "9", command, keys, fields, store_flag]

        self.subs_manager(subs_request)

    def subs_request_chart_options(self, keys, command = "SUBS",
                                   fields = '0,1,2,3,4,5,6', store_flag = True):

        '''
        Chart provides  streaming one minute OHLCV (Open/High/Low/Close/Volume)
        for a one minute period .
        The one minute bar falls on the 0 second slot (ie. 9:30:00) and includes data
        from 0 second to 59 seconds.
        For example, a 9:30 bar includes data from 9:30:00 through 9:30:59.

        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:
        Field   Field Name          Type        Field Description
        key     Subscription Key    String      Ticker symbol in upper case
        seq     Sequence            int         Ticker sequence number
        1       ChartTime           long        Milliseconds since Epoch
        2       Open Price          double      Opening price for the minute
        3       High Price          double      Highest price for the minute
        4       Low Price           double      Chart’s lowest price for the minute
        5       Close Price         double      Closing price for the minute
        6       Volume              double      Total volume for the minute
        TYPE: String

        EXAMPLES:
        SessionObject.data_request_chart_options(command = "SUBS", keys = 'SPY_112219C300',
                                                 fields = '0,1,2,3,4,5,6')
        '''

        subs_request = ["CHART_OPTIONS", "10", command, keys, fields, store_flag]

        self.subs_manager(subs_request)

    def subs_request_quote(self, command = "SUBS", keys = 'SPY, AAPL',
                           fields = '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,22,23,24,\
                               25,26,27,28,29,30,31,32,33,34,37,38,39,40,41,42,43,44,45,46,47,\
                                   48,49,50,51,52', store_flag = True):

        '''
        Listed (NYSE, AMEX, Pacific Quotes and Trades)
        NASDAQ (Quotes and Trades)
        OTCBB (Quotes and Trades)
        Pinks (Quotes only)
        Mutual Fund (No quotes)
        Indices (Trades only)
        Indicators

        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previous subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:

        Fields	Field Name                       Type	   Field Description
        key	     Symbol	                         String	   Ticker symbol in upper case.
        delayed                                  boolean
        assetMainType                            String
        cusip                                    String
        1	     Bid Price	                     float	   Current Best Bid Price
        2	     Ask Price	                     float	   Current Best Ask Price
        3	     Last Price	                     float	   Price at which the last trade was matched
        4	     Bid Size	                     float	   Number of shares for bid
        5	     Ask Size	                     float	   Number of shares for ask
        6	     Ask ID	                         char	   Exchange with the best ask
        7	     Bid ID	                         char	   Exchange with the best bid
        8	     Total Volume	                 long	   Aggregated shares traded throughout
                                                           the day, including pre/post market hours.
        9	     Last Size	                     float	   Number of shares traded with last trade
        10	     Trade Time	                     int	   Trade time of the last trade
        11	     Quote Time	                     int	   Trade time of the last quote
        12	     High Price	                     float	   Day’s high trade price
        13	     Low Price	                     float	   Day’s low trade price
        14	     Bid Tick	                     char	   Indicates Up or Downtick
                                                           (NASDAQ NMS & Small Cap)
        15	     Close Price	                 float	   Previous day’s closing price
        16	     Exchange ID	                 char	   Primary "listing" Exchange
        17	     Marginable	                     boolean   Stock approved by the Federal
                                                           Reserve and an investor's broker
                                                           as being suitable for providing
                                                           collateral for margin debt.
        18	     Shortable	                     boolean   Stock can be sold short.
        19	     Island Bid	                     float	   No longer used
        20	     Island Ask	                     float	   No longer used
        21	     Island Volume	                 Int	   No longer used
        22	     Quote Day	                     Int	   Day of the quote
        23	     Trade Day	                     Int	   Day of the trade
        24	     Volatility	                     float	   Option Risk/Volatility Measurement
        25	     Description	                 String	   A company, index or fund name
        26	     Last ID	                     char	   Exchange where last trade was executed
        27	     Digits	                         int	   Valid decimal points
        28	     Open Price	                     float	   Day's Open Price
        29	     Net Change	                     float	   Current Last-Prev Close
        30	     52  Week High	                 float	   Higest price traded in the past
                                                           12 months, or 52 weeks
        31	     52 Week Low	                 float	   Lowest price traded in the past
                                                           12 months, or 52 weeks
        32	     PE Ratio	                     float
        33	     Dividend Amount	             float	   Earnings Per Share
        34	     Dividend Yield	                 float	   Dividend Yield
        35	     Island Bid Size	             Int	   No longer used
        36	     Island Ask Size	             Int	   No longer used
        37	     NAV	                         float	   Mutual Fund Net Asset Value
        38	     Fund Price	                     float
        39	     Exchange Name	                 String	   Display name of exchange
        40	     Dividend Date	                 String
        41	     Regular Market Quote	         boolean
        42	     Regular Market Trade	         boolean
        43	     Regular Market Last Price   	 float
        44	     Regular Market Last Size	     float
        45	     Regular Market Trade Time	     int
        46	     Regular Market Trade Day	     int
        47	     Regular Market Net Change	     float
        48	     Security Status	             String
        49	     Mark	                         double	   Mark Price
        50	     Quote Time in  	             Long	   Last quote time in millisec since Epoch
        51	     Trade Time in  	             Long	   Last trade time in millisec since Epoch
        52	     Regular Market Trade Time in    Long	   Regular market trade time in
                                                           millisec since Epoch
        TYPE: String

        EXAMPLES:
        SessionObject.data_request_chart_quote(command = "SUBS", keys = 'SPY, AAPL',
                                               fields = '0,1,2,3,4,5,6')
        '''

        subs_request = ["QUOTE", "11", command, keys, fields, store_flag]

        self.subs_manager(subs_request)

    def subs_request_option(self, keys, command = "SUBS",
                            fields = '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,\
                                22,23,24,25,26,27,28,29,30,31,32,33,343,35,36,37,38,39,40,41',
                                store_flag = True):

        '''
        Level one option quote and trade

        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:
        Field   Field Name          Type        Field Description
        key	    Symbol            	String	Ticker symbol in upper case.
        1	    Description       	String	A company, index or fund name
        2	    Bid Price         	float	Current Best Bid Price
        3	    Ask Price         	float	Current Best Ask Price
        4   	Last Price         	float	Price at which the last trade was matched
        5   	High Price         	float	Day’s high trade price
        6   	Low Price          	float	Day’s low trade price
        7   	Close Price        	float	Previous day’s closing price
        8   	Total Volume       	long	Aggregated shares traded throughout the day, including
                                            pre/post market hours.
        9   	Open Interest      	int
        10  	Volatility         	float	Option Risk/Volatility Measurement
        11  	Quote Time         	long	Trade time of the last quote
        12  	Trade Time         	long	Trade time of the last trade
        13  	Money Intrinsic Value	float
        14  	Quote Day	        Int	Day of the quote
        15  	Trade Day          	Int	Day of the trade
        16  	Expiration Year    	int
        17  	Multiplier         	float
        18  	Digits             	int	Valid decimal points
        19  	Open Price         	float	Day's Open Price
        20  	Bid Size           	float	Number of shares for bid
        21  	Ask Size           	float	Number of shares for ask
        22  	Last Size          	float	Number of shares traded with last trade
        23  	Net Change         	float	Current Last-Prev Close
        24  	Strike Price       	float
        25  	Contract Type      	char
        26  	Underlying         	String
        27  	Expiration Month	int
        28  	Deliverables       	String
        29  	Time Value         	float
        30  	Expiration Day     	int
        31  	Days to Expiration	int
        32  	Delta              	float
        33  	Gamma              	float
        34  	Theta              	float
        35  	Vega               	float
        36  	Rho                	float
        37  	Security Status    	String
        38  	Theoretical Option Value	float
        39  	Underlying Price	double
        40  	UV Expiration Type	char
        41  	Mark               	double	Mark Price
        TYPE: String

        EXAMPLES:
        SessionObject.data_request_option(command = "SUBS", keys = 'SPY_112219C300',
                                          fields = '0,1,2,3,4,5,6,7,8,9,10')
        '''

        subs_request = ["OPTION", "12", command, keys, fields, store_flag]

        self.subs_manager(subs_request)

    def subs_request_futures_book(self, command = "SUBS", keys = 'SPY, AAPL',
                                 fields = '0,1,2,3', store_flag = True):

        '''
        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:

        Field   Field Name          Type        Field Description
        key     Symbol            	String	    Ticker symbol in upper case.
        1       Level2 Time         int         Level2 time in milliseconds since epoch
        2       Bid Book            list        List of Bid prices and theirs volumes
        3       Ask Book            list        List of Ask prices and theirs volumes
        TYPE: String

        EXAMPLES:
        SessionObject.data_request_listed_book(command = "SUBS", keys = 'SPY, AAPL',
                                               fields = '0,1,2,3')
        '''

        subs_request = ["FUTURES_BOOK", "13", command, keys, fields, store_flag]

        self.subs_manager(subs_request)

    def subs_request_futures_options_book(self, command = "SUBS", keys = 'SPY, AAPL',
                                 fields = '0,1,2,3', store_flag = True):

        '''
        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:

        Field   Field Name          Type        Field Description
        key     Symbol            	String	    Ticker symbol in upper case.
        1       Level2 Time         int         Level2 time in milliseconds since epoch
        2       Bid Book            list        List of Bid prices and theirs volumes
        3       Ask Book            list        List of Ask prices and theirs volumes
        TYPE: String

        EXAMPLES:
        SessionObject.data_request_listed_book(command = "SUBS", keys = 'SPY, AAPL',
                                               fields = '0,1,2,3')
        '''

        subs_request = ["FUTURES_OPTIONS_BOOK", "14", command, keys, fields, store_flag]

        self.subs_manager(subs_request)


    def subs_request_forex_book(self, command = "SUBS", keys = 'SPY, AAPL',
                                 fields = '0,1,2,3', store_flag = True):

        '''
        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:

        Field   Field Name          Type        Field Description
        key     Symbol            	String	    Ticker symbol in upper case.
        1       Level2 Time         int         Level2 time in milliseconds since epoch
        2       Bid Book            list        List of Bid prices and theirs volumes
        3       Ask Book            list        List of Ask prices and theirs volumes
        TYPE: String

        EXAMPLES:
        SessionObject.data_request_listed_book(command = "SUBS", keys = 'SPY, AAPL',
                                               fields = '0,1,2,3')
        '''

        subs_request = ["FOREX_BOOK", "15", command, keys, fields, store_flag]

        self.subs_manager(subs_request)

    def subs_request_listed_book(self, command = "SUBS", keys = 'SPY, AAPL',
                                 fields = '0,1,2,3', store_flag = True):

        '''
        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:

        Field   Field Name          Type        Field Description
        key     Symbol            	String	    Ticker symbol in upper case.
        1       Level2 Time         int         Level2 time in milliseconds since epoch
        2       Bid Book            list        List of Bid prices and theirs volumes
        3       Ask Book            list        List of Ask prices and theirs volumes
        TYPE: String

        EXAMPLES:
        SessionObject.data_request_listed_book(command = "SUBS", keys = 'SPY, AAPL',
                                               fields = '0,1,2,3')
        '''

        subs_request = ["LISTED_BOOK", "16", command, keys, fields, store_flag]

        self.subs_manager(subs_request)

    def subs_request_nyse_book(self, command = "SUBS", keys = 'SPY, AAPL',
                                 fields = '0,1,2,3', store_flag = True):

        '''
        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:

        Field   Field Name          Type        Field Description
        key     Symbol            	String	    Ticker symbol in upper case.
        1       Level2 Time         int         Level2 time in milliseconds since epoch
        2       Bid Book            list        List of Bid prices and theirs volumes
        3       Ask Book            list        List of Ask prices and theirs volumes
        TYPE: String

        EXAMPLES:
        SessionObject.data_request_listed_book(command = "SUBS", keys = 'SPY, AAPL',
                                               fields = '0,1,2,3')
        '''

        subs_request = ["NYSE_BOOK", "17", command, keys, fields, store_flag]

        self.subs_manager(subs_request)


    def subs_request_nasdaq_book(self, command = "SUBS", keys = 'SPY, AAPL',
                                 fields = '0,1,2,3', store_flag = True):

        '''
        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:
        Field   Field Name          Type        Field Description
        key     Symbol            	String	    Ticker symbol in upper case.
        1       Level2 Time         int         Level2 time in milliseconds since epoch
        2       Bid Book            list        List of Bid prices and theirs volumes
        3       Ask Book            list        List of Ask prices and theirs volumes

        TYPE: String

        EXAMPLES:
        SessionObject.data_request_nasdaq_book(command = "SUBS", keys = 'SPY, AAPL',
                                               fields = '0,1,2,3')
        '''

        subs_request = ["NASDAQ_BOOK", "18", command, keys, fields, store_flag]

        self.subs_manager(subs_request)

    def subs_request_options_book(self, keys, command = "SUBS",
                                  fields = '0,1,2,3', store_flag = True):

        '''
        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:
        Field   Field Name          Type        Field Description
        key     Symbol            	String	    Ticker symbol in upper case.
        1       Level2 Time         int         Level2 time in milliseconds since epoch
        2       Bid Book            list        List of Bid prices and theirs volumes
        3       Ask Book            list        List of Ask prices and theirs volumes

        TYPE: String

        EXAMPLES:
        SessionObject.data_request_options_book(command = "SUBS", keys = 'SPY_112219C300',
                                                fields = '0,1,2,3')
        '''


        subs_request = ["OPTIONS_BOOK", "19", command, keys, fields, store_flag]

        self.subs_manager(subs_request)

    def subs_request_screener_equity(self, keys = 'AAPL', command = "SUBS",
                                  fields = '0,1,2,3', store_flag = True):

        '''
        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:
        Field   Field Name          Type        Field Description
        key     Symbol            	String	    Ticker symbol in upper case.
        1       Level2 Time         int         Level2 time in milliseconds since epoch
        2       Bid Book            list        List of Bid prices and theirs volumes
        3       Ask Book            list        List of Ask prices and theirs volumes

        TYPE: String

        EXAMPLES:
        SessionObject.data_request_options_book(command = "SUBS", keys = 'SPY_112219C300',
                                                fields = '0,1,2,3')
        '''


        subs_request = ["SCREENER_EQUITY", "20", command, keys, fields, store_flag]

        self.subs_manager(subs_request)

    def subs_request_screener_option(self, keys, command = "SUBS",
                                  fields = '0,1,2,3', store_flag = True):

        '''
        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:
        Field   Field Name          Type        Field Description
        key     Symbol            	String	    Ticker symbol in upper case.
        1       Level2 Time         int         Level2 time in milliseconds since epoch
        2       Bid Book            list        List of Bid prices and theirs volumes
        3       Ask Book            list        List of Ask prices and theirs volumes

        TYPE: String

        EXAMPLES:
        SessionObject.data_request_options_book(command = "SUBS", keys = 'SPY_112219C300',
                                                fields = '0,1,2,3')
        '''


        subs_request = ["SCREENER_OPTION", "21", command, keys, fields, store_flag]

        self.subs_manager(subs_request)

    ### ver si no es quotes
    def subs_request_levelone_equity(self, command = "SUBS", keys = 'AAPL',
                                      fields = '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,\
                                          17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,\
                                              33,34,35', store_flag = True):

        '''
        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Futures symbol as a product or active symbol (ie. /ES or /ESM4)
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:

        Fields	  Field Name	              Type	    Field Description
        key	      Symbol	                  String	Ticker symbol in upper case.
        1	      Bid Price	                  double	Current Best Bid Price
        2	      Ask Price	                  double	Current Best Ask Price
        3	      Last Price	              double	Price at which the last trade was matched
        4	      Bid Size	                  long	    Number of shares for bid
        5	      Ask Size	                  long	    Number of shares for ask
        6	      Ask ID	                  char	    Exchange with the best ask
        7	      Bid ID	                  char	    Exchange with the best bid
        8	      Total Volume	              double	Aggregated shares traded throughout the day,
                                                        including pre/post market hours.
        9	      Last Size	                  long	    Number of shares traded with last trade
        10	      Quote Time	              long	    Trade time of the last quote in
                                                        millisec since epoch
        11	      Trade Time	              long	    Trade time of the last trade in
                                                        millisec since epoch
        12	      High Price	              double	Day’s high trade price
        13	      Low Price	                  double	Day’s low trade price
        14	      Close Price	              double	Previous day’s closing price
        15	      Exchange ID	              char	    Primary "listing" Exchange
        16	      Description	              String	Description of the product
        17	      Last ID	                  char	    Exchange where last trade was executed
        18	      Open Price	              double	Day's Open Price
        19	      Net Change	              double	Current Last-Prev Close
        20	      Future Percent Change	      double	Current percent change
        21	      Exhange Name	           	  String    Name of exchange
        22	      Security Status	          String	Trading status of the symbol
        23	      Open Interest	              int	    The total number of futures ontracts that
                                                        are not closed or delivered on a
                                                        particular day
        24	      Mark	                      double	Mark-to-Market value is calculated daily
                                                        using current prices to determine
                                                        profit/loss
        25	      Tick	                      double	Minimum price movement
        26	      Tick Amount	              double	Minimum amount that the price of the
                                                        market can change
        27	      Product	                  String	Futures product
        28	      Future Price Format	      String	Display in fraction or decimal format.
        29	      Future Trading Hours	      String	Trading hours
        30	      Future Is Tradable	      boolean	Flag to indicate if this future contract
                                                        is tradable
        31	      Future Multiplier	          double	Point value
        32	      Future Is Active	          boolean	Indicates if this contract is active
        33	      Future Settlement Price	  double	Closing price
        34	      Future Active Symbol	      String	Symbol of the active contract
        35	      Future Expiration Date	  long	    Expiration date of this contract
        TYPE: String

        EXAMPLES:
        SessionObject.data_request_chart_levelone_futures(command = "SUBS", keys = '/ES',
                                                          fields = '0,1,2,3,4,5,6')
        '''

        subs_request = ["LEVELONE_EQUITIES", "22", command, keys, fields, store_flag]

        self.subs_manager(subs_request)

    def subs_request_levelone_futures(self, command = "SUBS", keys = '/ES',
                                      fields = '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,\
                                          17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,\
                                              33,34,35', store_flag = True):

        '''
        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Futures symbol as a product or active symbol (ie. /ES or /ESM4)
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:

        Fields	  Field Name	              Type	    Field Description
        key	      Symbol	                  String	Ticker symbol in upper case.
        1	      Bid Price	                  double	Current Best Bid Price
        2	      Ask Price	                  double	Current Best Ask Price
        3	      Last Price	              double	Price at which the last trade was matched
        4	      Bid Size	                  long	    Number of shares for bid
        5	      Ask Size	                  long	    Number of shares for ask
        6	      Ask ID	                  char	    Exchange with the best ask
        7	      Bid ID	                  char	    Exchange with the best bid
        8	      Total Volume	              double	Aggregated shares traded throughout the day,
                                                        including pre/post market hours.
        9	      Last Size	                  long	    Number of shares traded with last trade
        10	      Quote Time	              long	    Trade time of the last quote in
                                                        millisec since epoch
        11	      Trade Time	              long	    Trade time of the last trade in
                                                        millisec since epoch
        12	      High Price	              double	Day’s high trade price
        13	      Low Price	                  double	Day’s low trade price
        14	      Close Price	              double	Previous day’s closing price
        15	      Exchange ID	              char	    Primary "listing" Exchange
        16	      Description	              String	Description of the product
        17	      Last ID	                  char	    Exchange where last trade was executed
        18	      Open Price	              double	Day's Open Price
        19	      Net Change	              double	Current Last-Prev Close
        20	      Future Percent Change	      double	Current percent change
        21	      Exhange Name	           	  String    Name of exchange
        22	      Security Status	          String	Trading status of the symbol
        23	      Open Interest	              int	    The total number of futures ontracts that
                                                        are not closed or delivered on a
                                                        particular day
        24	      Mark	                      double	Mark-to-Market value is calculated daily
                                                        using current prices to determine
                                                        profit/loss
        25	      Tick	                      double	Minimum price movement
        26	      Tick Amount	              double	Minimum amount that the price of the
                                                        market can change
        27	      Product	                  String	Futures product
        28	      Future Price Format	      String	Display in fraction or decimal format.
        29	      Future Trading Hours	      String	Trading hours
        30	      Future Is Tradable	      boolean	Flag to indicate if this future contract
                                                        is tradable
        31	      Future Multiplier	          double	Point value
        32	      Future Is Active	          boolean	Indicates if this contract is active
        33	      Future Settlement Price	  double	Closing price
        34	      Future Active Symbol	      String	Symbol of the active contract
        35	      Future Expiration Date	  long	    Expiration date of this contract
        TYPE: String

        EXAMPLES:
        SessionObject.data_request_chart_levelone_futures(command = "SUBS", keys = '/ES',
                                                          fields = '0,1,2,3,4,5,6')
        '''

        subs_request = ["LEVELONE_FUTURES", "23", command, keys, fields, store_flag]

        self.subs_manager(subs_request)

    def subs_request_levelone_forex(self, command = "SUBS", keys = 'EUR/USD',
                                    fields = '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,\
                                        19,20,21,22,23,24,25,26,27,28', store_flag = True):

        '''
        Level one option quote and trade

        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas (FOREX symbols (ie.. EUR/USD,
                                                                            GBP/USD, EUR/JPY,
                                                                            USD/JPY, GBP/JPY,
                                                                            AUD/USD))
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:

        Field   Field Name          Type        Field Description
        key   	Symbol	            String	Ticker symbol in upper case.
        1   	Bid Price	        double	Current Best Bid Price
        2   	Ask Price          	double	Current Best Ask Price
        3   	Last Price         	double	Price at which the last trade was matched
        4   	Bid Size           	long	Number of shares for bid
        5   	Ask Size           	long	Number of shares for ask
        6   	Total Volume       	double	Aggregated shares traded throughout the day, including
                                            pre/post market hours.
        7   	Last Size          	long	Number of shares traded with last trade
        8   	Quote Time	        long	Trade time of the last quote in milliseconds since epoch
        9   	Trade Time         	long	Trade time of the last trade in milliseconds since epoch
        10  	High Price         	double	Day’s high trade price
        11	    Low Price        	double	Day’s low trade price
        12  	Close Price        	double	Previous day’s closing price
        13  	Exchange ID        	char	Primary "listing" Exchange
        14  	Description         String	Description of the product
        15  	Open Price         	double	Day's Open Price
        16  	Net Change         	double	Current Last-Prev Close
        17  	Percent Change     	double	Current percent change
        18  	Exchange Name      	String	Name of exchange
        19  	Digits             	Int	    Valid decimal points
        20  	Security Status    	String	Trading status of the symbol
        21  	Tick               	double	Minimum price movement
        22  	Tick Amount        	double	Minimum amount that the price of the market can change
        23  	Product            	String	Product name
        23  	Trading Hours      	String	Trading hours
        24  	Is Tradable        	boolean	Flag to indicate if this forex is tradable
        25  	Market Maker       	String
        26  	52 Week High       	double	Higest price traded in the past 12 months, or 52 weeks
        27  	52 Week Low        	double	Lowest price traded in the past 12 months, or 52 weeks
        28  	Mark               	double	Mark-to-Market value is calculated daily using current
                                            prices to determine profit/loss

        TYPE: String

        EXAMPLES:
        SessionObject.data_request_levelone_forex(command = "SUBS", keys = 'EUR/USD',
                                                  fields = '0,1,2,3,4,5,6,7,8,9,10')
        '''

        subs_request = ["LEVELONE_FOREX", "24", command, keys, fields, store_flag]

        self.subs_manager(subs_request)


    ### Ver si no es options
    def subs_request_levelone_options(self, keys, command = "SUBS",
                                    fields = '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,\
                                        19,20,21,22,23,24,25,26,27,28', store_flag = True):

        '''
        Level one option quote and trade

        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas (FOREX symbols (ie.. EUR/USD,
                                                                            GBP/USD, EUR/JPY,
                                                                            USD/JPY, GBP/JPY,
                                                                            AUD/USD))
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:

        Field   Field Name          Type        Field Description
        key   	Symbol	            String	Ticker symbol in upper case.
        1   	Bid Price	        double	Current Best Bid Price
        2   	Ask Price          	double	Current Best Ask Price
        3   	Last Price         	double	Price at which the last trade was matched
        4   	Bid Size           	long	Number of shares for bid
        5   	Ask Size           	long	Number of shares for ask
        6   	Total Volume       	double	Aggregated shares traded throughout the day, including
                                            pre/post market hours.
        7   	Last Size          	long	Number of shares traded with last trade
        8   	Quote Time	        long	Trade time of the last quote in milliseconds since epoch
        9   	Trade Time         	long	Trade time of the last trade in milliseconds since epoch
        10  	High Price         	double	Day’s high trade price
        11	    Low Price        	double	Day’s low trade price
        12  	Close Price        	double	Previous day’s closing price
        13  	Exchange ID        	char	Primary "listing" Exchange
        14  	Description         String	Description of the product
        15  	Open Price         	double	Day's Open Price
        16  	Net Change         	double	Current Last-Prev Close
        17  	Percent Change     	double	Current percent change
        18  	Exchange Name      	String	Name of exchange
        19  	Digits             	Int	    Valid decimal points
        20  	Security Status    	String	Trading status of the symbol
        21  	Tick               	double	Minimum price movement
        22  	Tick Amount        	double	Minimum amount that the price of the market can change
        23  	Product            	String	Product name
        23  	Trading Hours      	String	Trading hours
        24  	Is Tradable        	boolean	Flag to indicate if this forex is tradable
        25  	Market Maker       	String
        26  	52 Week High       	double	Higest price traded in the past 12 months, or 52 weeks
        27  	52 Week Low        	double	Lowest price traded in the past 12 months, or 52 weeks
        28  	Mark               	double	Mark-to-Market value is calculated daily using current
                                            prices to determine profit/loss

        TYPE: String

        EXAMPLES:
        SessionObject.data_request_levelone_forex(command = "SUBS", keys = 'EUR/USD',
                                                  fields = '0,1,2,3,4,5,6,7,8,9,10')
        '''

        subs_request = ["LEVELONE_OPTIONS", "25", command, keys, fields, store_flag]

        self.subs_manager(subs_request)

    def subs_request_levelone_future_options(self, keys, command = "SUBS",
                                    fields = '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,\
                                        19,20,21,22,23,24,25,26,27,28', store_flag = True):

        '''
        Level one option quote and trade

        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas (FOREX symbols (ie.. EUR/USD,
                                                                            GBP/USD, EUR/JPY,
                                                                            USD/JPY, GBP/JPY,
                                                                            AUD/USD))
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:

        Field   Field Name          Type        Field Description
        key   	Symbol	            String	Ticker symbol in upper case.
        1   	Bid Price	        double	Current Best Bid Price
        2   	Ask Price          	double	Current Best Ask Price
        3   	Last Price         	double	Price at which the last trade was matched
        4   	Bid Size           	long	Number of shares for bid
        5   	Ask Size           	long	Number of shares for ask
        6   	Total Volume       	double	Aggregated shares traded throughout the day, including
                                            pre/post market hours.
        7   	Last Size          	long	Number of shares traded with last trade
        8   	Quote Time	        long	Trade time of the last quote in milliseconds since epoch
        9   	Trade Time         	long	Trade time of the last trade in milliseconds since epoch
        10  	High Price         	double	Day’s high trade price
        11	    Low Price        	double	Day’s low trade price
        12  	Close Price        	double	Previous day’s closing price
        13  	Exchange ID        	char	Primary "listing" Exchange
        14  	Description         String	Description of the product
        15  	Open Price         	double	Day's Open Price
        16  	Net Change         	double	Current Last-Prev Close
        17  	Percent Change     	double	Current percent change
        18  	Exchange Name      	String	Name of exchange
        19  	Digits             	Int	    Valid decimal points
        20  	Security Status    	String	Trading status of the symbol
        21  	Tick               	double	Minimum price movement
        22  	Tick Amount        	double	Minimum amount that the price of the market can change
        23  	Product            	String	Product name
        23  	Trading Hours      	String	Trading hours
        24  	Is Tradable        	boolean	Flag to indicate if this forex is tradable
        25  	Market Maker       	String
        26  	52 Week High       	double	Higest price traded in the past 12 months, or 52 weeks
        27  	52 Week Low        	double	Lowest price traded in the past 12 months, or 52 weeks
        28  	Mark               	double	Mark-to-Market value is calculated daily using current
                                            prices to determine profit/loss

        TYPE: String

        EXAMPLES:
        SessionObject.data_request_levelone_forex(command = "SUBS", keys = 'EUR/USD',
                                                  fields = '0,1,2,3,4,5,6,7,8,9,10')
        '''

        subs_request = ["LEVELONE_FUTURES_OPTIONS", "26", command, keys, fields, store_flag]

        self.subs_manager(subs_request)

    def subs_request_timesale_equity(self, command = "SUBS", keys = 'SPY, AAPL',
                                     fields = '0,1,2,3,4', store_flag = True):

        '''
        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:
        Field   Field Name          Type        Field Description
        key     Symbol              String      Ticker symbol in upper case.
        seq     Sequence            int         Ticker sequence number
        1       Trade Time          long        Trade time of the last trade in millisec since epoch
        2       Last Price          double      Price at which the last trade was matched
        3       Last Size           double      Number of shares traded with last trade
        4       Last Sequence       long        Number of shares for bid

        TYPE: String

        EXAMPLES:
        SessionObject.data_request_timesale_equity(command = "SUBS", keys = 'SPY, AAPL',
                                                   fields = '0,1,2,3,4,5,6')
        '''

        subs_request = ["TIMESALE_EQUITY", "27", command, keys, fields, store_flag]

        self.subs_manager(subs_request)

    def subs_request_timesale_futures(self, command = "SUBS", keys = '/ES',
                                      fields = '0,1,2,3,4', store_flag = True):

        '''
        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:
        Field   Field Name          Type        Field Description
        key     Symbol              String      Ticker symbol in upper case.
        seq     Sequence            int         Ticker sequence number
        1       Trade Time          long        Trade time of the last trade in millisec since epoch
        2       Last Price          double      Price at which the last trade was matched
        3       Last Size           double      Number of shares traded with last trade
        4       Last Sequence       long        Number of shares for bid

        TYPE: String

        EXAMPLES:
        SessionObject.data_request_timesale_futures(command = "SUBS", keys = '/ES',
                                                    fields = '0,1,2,3,4,5,6')
        '''

        subs_request = ["TIMESALE_FUTURES", "28", command, keys, fields, store_flag]

        self.subs_manager(subs_request)

    def subs_request_timesale_options(self, keys, command = "SUBS",
                                      fields = '0,1,2,3,4', store_flag = True):

        '''
        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:
        Field   Field Name          Type        Field Description
        key     Symbol              String      Ticker symbol in upper case.
        1       Trade Time          long        Trade time of the last trade in mseconds since epoch
        2       Last Price          double      Price at which the last trade was matched
        3       Last Size           double      Number of shares traded with last trade
        4       Last Sequence       long        Number of shares for bid

        TYPE: String

        EXAMPLES:
        SessionObject.data_request_timesale_options(command = "SUBS", keys = 'SPY_112219C300',
                                                    fields = '0,1,2,3,4,5,6')
        '''

        subs_request = ["TIMESALE_OPTIONS", "29", command, keys, fields, store_flag]

        self.subs_manager(subs_request)

    def subs_request_timesale_forex(self, keys, command = "SUBS",
                                      fields = '0,1,2,3,4', store_flag = True):

        '''
        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:
        Field   Field Name          Type        Field Description
        key     Symbol              String      Ticker symbol in upper case.
        1       Trade Time          long        Trade time of the last trade in mseconds since epoch
        2       Last Price          double      Price at which the last trade was matched
        3       Last Size           double      Number of shares traded with last trade
        4       Last Sequence       long        Number of shares for bid

        TYPE: String

        EXAMPLES:
        SessionObject.data_request_timesale_options(command = "SUBS", keys = 'SPY_112219C300',
                                                    fields = '0,1,2,3,4,5,6')
        '''

        subs_request = ["TIMESALE_FOREX", "30", command, keys, fields, store_flag]

        self.subs_manager(subs_request)

    def subs_request_news_headline(self, command = "SUBS", keys = 'SPY, AAPL',
                                   fields = '0,1,2,3,4,5,6,7,8,9,10', store_flag = True):

        '''
        NAME: command
        DESC: chose between "SUBS": subscribe or replace previous subscription.
                            "UNSUBS": unsubscribe
                            "ADD": subscribe or ADD to the previos subscription.
        TYPE: String

        NAME: keys
        DESC: Symbols in upper case and separated by commas
        TYPE: String

        MAME: fields
        DESC: select streaming fields.:

        Field   Field Name          Type        Field Description
        key     Symbol              String      Ticker symbol in upper case.
        1       Error Code          double      Specifies if there is any error.
        2       Story Datetime      long        Headline’s datetime in millisec since epoch
        3       Headline ID         String      Unique ID for the headline
        4       Status              char
        5       Headline            String      News headline
        6       Story ID            String
        7       Count for Keyword   integer
        8       Keyword Array       String
        9       Is Hot              boolean
        10      Story Source        char

        TYPE: String

        EXAMPLES:
        SessionObject.data_request_news_headline(command = "SUBS", keys = 'SPY, AAPL',
                                                 fields = '0,1,2,3,4,5,6,7,8,9,10')
        '''

        subs_request = ["NEWS_HEADLINE", "31", command, keys, fields, store_flag]

        self.subs_manager(subs_request)

    #### GET REQUEST ##########################

    def data_request_news_headlinelist(self, keys = 'SPY, AAPL'):

        '''
        NAME: keys
        DESC: Symbols in upper case and separated by commas
        TYPE: String

        Snapshot fields:
                        1	??
                        2	list amount
                        3	list
                        key	symbol

        EXAMPLES:
        SessionObject.data_request_news_headlinelist(keys = 'SPY')
        '''

        data_request= {
                       "service": "NEWS_HEADLINELIST",
                       "requestid": "32",
                       "command": 'GET',
                       "parameters": {
                                     "keys": keys,
                                     }
                       }
        self._ws.send_request(data_request)

    def data_request_news_story(self, keys):

        '''
        NAME: keys
        DESC: StoryID
        TYPE: String

        Snapshot fields:
                        1	??
                        2	timestamp
                        3	story_id
                        4	??
                        5	story_id
                        6	Story
                        7	source
                        keys	story_id

        EXAMPLES:
        SessionObject.data_request_news_story(keys = 'SN20191111010526')
        '''

        data_request= {
                       "service": "NEWS_STORY",
                       "requestid": "33",
                       "command": 'GET',
                       "parameters": {
                                     "keys": keys,
                                     }
                       }

        self._ws.send_request(data_request)

    def data_request_chart_history_futures(self, symbol = '/ES',
                                           frequency = 'm5', period = 'd5',
                                           start_time = None, end_time = None):

        '''
        Chart history for equities is available via requests to the MDMS services.
        Only Futures chart history is available via Streamer Server.

        NAME: symbol
        DESC: Symbols in upper case and separated by commas
        TYPE: String

        NAME: frequency
        DESC: Sample Size of the candle: Fixed frequency choices:
                                                    m1, m5, m10, m30, h1, d1, w1, n1
                                                    (m=minute, h=hour, d=day, w=week, n=month)
        TYPE: String

        NAME: period
        DESC: Period (not required if START_TIME & END_TIME are sent).
              The number of periods to show.Flexible time period examples:
                                                                d5, w4, n10, y1, y10
                                                                (d=day, w=week, n=month, y=year)
        TYPE: String

        NAME: start_Time
        DESC: Start time
        TYPE: String

        NAME: end_Time
        DESC: End time
        TYPE: String

        Snapshot fields:
        Field   Field Name          Type        Field Description
        0   	key                	String     	Ticker symbol in upper case.
        1   	Chart Time         	long       	Milliseconds since Epoch
        2   	Open Price         	double     	Opening price for the minute
        3    	High Price        	double     	Highest price for the minute
        4   	Low Price          	double     	Chart’s lowest price for the minute
        5   	Close Price        	double     	Closing price for the minute
        6   	Volume             	doulbe     	Total volume for the minute


        TYPE: String

        EXAMPLES:
        SessionObject.data_request_chart_history_futures(keys = '/ES', frequecy = 'm5',
                                                         period = 'd5')
        '''

        if end_time is not None and start_time is not None:

            epoch = datetime.utcfromtimestamp(0)
            end_date = int((end_time - epoch).total_seconds()*1000)
            start_date = int((start_time - epoch).total_seconds()*1000)

        else:
            end_date = None
            start_date = None

        data_request= {
                      "service": "CHART_HISTORY_FUTURES",
                      "requestid": "34",
                      "command": 'GET',
                      "parameters": {
                                     "symbol": symbol,
                                     "frequency": frequency,
                                     "period": period,
                                     "END_TIME": end_date,
                                     "START_TIME": start_date,
                                    }
                    }
        self._ws.send_request(data_request)
