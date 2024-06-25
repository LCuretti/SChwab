#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 23 16:57:30 2024

@author: lccuretti
"""

from enum import Enum

#### ACCOUNT DATA

#### Orders

#### GET
class Status(Enum):
    AWAITING_PARENT_ORDER = 'AWAITING_PARENT_ORDER'
    AWAITING_CONDITION = 'AWAITING_CONDITION'
    AWAITING_STOP_CONDITION = 'AWAITING_STOP_CONDITION'
    AWAITING_MANUAL_REVIEW = 'AWAITING_MANUAL_REVIEW'
    AWAITING_UR_NOT = 'AWAITING_UR_NOT'
    AWAITING_RELEASE_TIME = 'AWAITING_RELEASE_TIME'
    PENDING_ACTIVATION = 'PENDING_ACTIVATION'
    PENDING_CANCEL = 'PENDING_CANCEL'
    PENDING_REPLACE = 'PENDING_REPLACE'
    PENDING_ACKNOWLEDGEMENT = 'PENDING_ACKNOWLEDGEMENT'
    PENDING_RECALL = 'PENDING_RECALL'
    ACCEPTED = 'ACCEPTED'
    QUEUED = 'QUEUED'
    WORKING = 'WORKING'
    REJECTED = 'REJECTED'
    CANCELED = 'CANCELED'
    REPLACED = 'REPLACED'
    FILLED = 'FILLED'
    EXPIRED = 'EXPIRED'
    NEW = 'NEW'
    UNKNOWN = 'UNKNOWN'

#### POST

class Session(Enum):
    NORMAL = 'NORMAL'
    AM = 'AM'
    PM = 'PM'
    SEAMLESS = 'SEAMLESS'

class Duration(Enum):
    DAY = 'DAY'
    GOOD_TILL_CANCEL = 'GOOD_TILL_CANCEL'
    FILL_OR_KILL = 'FILL_OR_KILL'
    IMMEDIATE_OR_CANCEL = 'IMMEDIATE_OR_CANCEL'
    END_OF_WEEK = 'END_OF_WEEK'
    END_OF_MONTH = 'END_OF_MONTH'
    NEXT_END_OF_MONTH = 'NEXT_END_OF_MONTH'
    UNKNOWN = 'UNKNOWN'

class OrderType(Enum):
    MARKET = 'MARKET'
    LIMIT = 'LIMIT'
    STOP = 'STOP'
    STOP_LIMIT = 'STOP_LIMIT'
    TRAILING_STOP = 'TRAILING_STOP'
    MARKET_ON_CLOSE = 'MARKET_ON_CLOSE'
    EXERCISE = 'EXERCISE'
    TRAILING_STOP_LIMIT = 'TRAILING_STOP_LIMIT'
    NET_DEBIT = 'NET_DEBIT'
    NET_CREDIT = 'NET_CREDIT'
    NET_ZERO = 'NET_ZERO'
    CABINET = 'CABINET'
    NON_MARKETABLE = 'NON_MARKETABLE'
    LIMIT_ON_CLOSE = 'LIMIT_ON_CLOSE'

class ComplexOrderStrategyType(Enum):
    NONE = 'NONE'
    COVERED = 'COVERED'
    VERTICAL = 'VERTICAL'
    BACK_RATIO = 'BACK_RATIO'
    CALENDAR = 'CALENDAR'
    DIAGONAL = 'DIAGONAL'
    STRADDLE = 'STRADDLE'
    STRANGLE = 'STRANGLE'
    COLLAR_SYNTHETIC = 'COLLAR_SYNTHETIC'
    BUTTERFLY = 'BUTTERFLY'
    CONDOR = 'CONDOR'
    IRON_CONDOR = 'IRON_CONDOR'
    VERTICAL_ROLL = 'VERTICAL_ROLL'
    COLLAR_WITH_STOCK = 'COLLAR_WITH_STOCK'
    DOUBLE_DIAGONAL = 'DOUBLE_DIAGONAL'
    UNBALANCED_BUTTERFLY = 'UNBALANCED_BUTTERFLY'
    UNBALANCED_CONDOR = 'UNBALANCED_CONDOR'
    UNBALANCED_IRON_CONDOR = 'UNBALANCED_IRON_CONDOR'
    UNBALANCED_VERTICAL_ROLL = 'UNBALANCED_VERTICAL_ROLL'
    MUTUAL_FUND_SWAP = 'MUTUAL_FUND_SWAP'
    CUSTOM = 'CUSTOM'

class PriceLinkBasis(Enum):
    MANUAL = 'MANUAL'
    BASE = 'BASE'
    TRIGGER = 'TRIGGER'
    LAST = 'LAST'
    BID = 'BID'
    ASK = 'ASK'
    ASK_BID = 'ASK_BID'
    MARK = 'MARK'
    AVERAGE = 'AVERAGE'

class PriceLinkType(Enum):
    VALUE = 'VALUE'
    PERCENT = 'PERCENT'
    TICK = 'TICK'

class StopType(Enum):
    STANDARD = 'STANDARD'
    BID = 'BID'
    ASK = 'ASK'
    LAST = 'LAST'
    MARK = 'MARK'

class TaxLotMethod(Enum):
    FIFO = 'FIFO'
    LIFO = 'LIFO'
    HIGH_COST = 'HIGH_COST'
    LOW_COST = 'LOW_COST'
    AVERAGE_COST = 'AVERAGE_COST'
    SPECIFIC_LOT = 'SPECIFIC_LOT'
    LOSS_HARVESTER = 'LOSS_HARVESTER'

class SpecialInstruction(Enum):
    ALL_OR_NONE = 'ALL_OR_NONE'
    DO_NOT_REDUCE = 'DO_NOT_REDUCE'
    ALL_OR_NONE_DO_NOT_REDUCE = 'ALL_OR_NONE_DO_NOT_REDUCE'

class OrderStrategyType(Enum):
    SINGLE = 'SINGLE'
    CANCEL = 'CANCEL'
    RECALL = 'RECALL'
    PAIR = 'PAIR'
    FLATTEN = 'FLATTEN'
    TWO_DAY_SWAP = 'TWO_DAY_SWAP'
    BLAST_ALL = 'BLAST_ALL'
    OCO = 'OCO'
    TRIGGER = 'TRIGGER'

class AssetType(Enum):
    EQUITY = 'EQUITY'
    MUTUAL_FUND = 'MUTUAL_FUND'
    OPTION = 'OPTION'
    FUTURE = 'FUTURE'
    FOREX = 'FOREX'
    INDEX = 'INDEX'
    CASH_EQUIVALENT = 'CASH_EQUIVALENT'
    FIXED_INCOME = 'FIXED_INCOME'
    PRODUCT = 'PRODUCT'
    CURRENCY = 'CURRENCY'
    COLLECTIVE_INVESTMENT = 'COLLECTIVE_INVESTMENT'

class Instruction(Enum):
    BUY = 'BUY'
    SELL = 'SELL'
    BUY_TO_COVER = 'BUY_TO_COVER'
    SELL_SHORT = 'SELL_SHORT'
    BUY_TO_OPEN = 'BUY_TO_OPEN'
    BUY_TO_CLOSE = 'BUY_TO_CLOSE'
    SELL_TO_OPEN = 'SELL_TO_OPEN'
    SELL_TO_CLOSE = 'SELL_TO_CLOSE'
    EXCHANGE = 'EXCHANGE'
    SELL_SHORT_EXEMPT = 'SELL_SHORT_EXEMPT'

class PositionEffect(Enum):
    OPENING = 'OPENING'
    CLOSING = 'CLOSING'
    AUTOMATIC = 'AUTOMATIC'

class AmountIndicator(Enum):
    DOLLARS = 'DOLLARS'
    SHARES = 'SHARES'
    ALL_SHARES = 'ALL_SHARES'
    PERCENTAGE = 'PERCENTAGE'
    UNKNOWN = 'UNKNOWN'

class DivCapGains(Enum):
    REINVEST = 'REINVEST'
    PAYOUT = 'PAYOUT'

class ActivityType(Enum):
    EXECUTION = 'EXECUTION'
    ORDER_ACTION = 'ORDER_ACTION'

#### Transactions

class TransactionType(Enum):
    TRADE = 'TRADE'
    RECEIVE_AND_DELIVER = 'RECEIVE_AND_DELIVER'
    DIVIDEND_OR_INTEREST = 'DIVIDEND_OR_INTEREST'
    ACH_RECEIPT = 'ACH_RECEIPT'
    ACH_DISBURSEMENT = 'ACH_DISBURSEMENT'
    CASH_RECEIPT = 'CASH_RECEIPT'
    CASH_DISBURSEMENT = 'CASH_DISBURSEMENT'
    ELECTRONIC_FUND = 'ELECTRONIC_FUND'
    WIRE_OUT = 'WIRE_OUT'
    WIRE_IN = 'WIRE_IN'
    JOURNAL = 'JOURNAL'
    MEMORANDUM = 'MEMORANDUM'
    MARGIN_CALL = 'ARGIN_CALL'
    MONEY_MARKET = 'MONEY_MARKET'
    SMA_ADJUSTMENT = 'SMA_ADJUSTMENT'
    ALL = 'ALL'

#### MARKET DATA

#### Chain
class ContractType(Enum):  ## Chain
    CALL = 'CALL' #C
    PUT = 'PUT'   #P
    ALL = 'ALL'

class Strategy(Enum):  ## Chain
    SINGLE = 'SINGLE'
    ANALYTICAL = 'ANALYTICAL'
    COVERED = 'COVERED'
    VERTICAL = 'VERTICAL'
    CALENDAR = 'CALENDAR'
    STRANGLE = 'STRANGLE'
    STRADDLE = 'STRADDLE'
    BUTTERFLY = 'BUTTERFLY'
    CONDOR = 'CONDOR'
    DIAGONAL = 'DIAGONAL'
    COLLAR = 'COLLAR'
    ROLL = 'ROLL'

class Range(Enum):  ## Chain
    ITM = 'ITM'
    NTM = 'NTM'
    OTM = 'OTM'
    SAK = 'SAK' #
    SBK = 'SBK' #
    SNK = 'SNK' #
    ALL = 'ALL'

class ExpMonth(Enum): ## Chain
    ALL = 'ALL'
    JAN = 'JAN'
    FEB = 'FEB'
    MAR = 'MAR'
    APR = 'APR'
    MAY = 'MAY'
    JUN = 'JUN'
    JUL = 'JUL'
    AUG = 'AUG'
    SEP = 'SEP'
    OCT = 'OCT'
    NOV = 'NOV'
    DEC = 'DEC'

class OptionType(Enum): #Chain to be berified
    S = 'S'
    NS = 'NS'
    ALL = 'ALL'

class Entitlement(Enum): #Chain
    PN = 'PN'
    NP = 'NP'
    PP = 'PP'

#### Instrument

class Projection(Enum):
    SYMBOL_SEARCH = 'symbol-search'
    SYMBOL_REGEX = 'symbol-regex'
    DESC_SEARCH = 'desc-search'
    DESC_REGEX = 'desc-regex'
    SEARCH = 'search'
    FUNDAMENTAL = 'fundamental'

#### Market hours

class Market(Enum):
    EQUITY = 'equity'
    OPTION = 'option'
    FUTURE = 'future'
    BOND = 'bond'
    FOREX = 'forex'
    ALL = 'all'

#### Movers

class Sort(Enum):
    VOLUME = 'VOLUME'
    TRADES = 'TRADES'
    PERCENT_CHANGE_UP = 'PERCENT_CHANGE_UP'
    PERCENT_CHANGE_DOWN = 'PERCENT_CHANGE_DOWN'

class MoversFrequency(Enum):
    ZERO = 0   #Default
    ONE = 1
    FIVE = 5
    TEN = 10
    THIRTY = 30
    SIXTY = 60

class SymbolId(Enum):
    DJI = '$DJI'
    COMPX = '$COMPX'
    SPX = '$SPX'
    NYSE = 'NYSE'
    NASDAQ = 'NASDAQ'
    OTCBB = 'OTCBB'
    INDEX_ALL = 'INDEX_ALL'
    EQUITY_ALL = 'EQUITY_ALL'
    OPTION_ALL = 'OPTION_ALL'
    OPTION_PUT = 'OPTION_PUT'
    OPTION_CALL = 'OPTION_CALL'

#### PriceHistory

class PeriodType(Enum):
    DAY = 'day'
    MONTH = 'month'
    YEAR = 'year'
    YTD = 'ytd'

class Period(Enum):
    DAY_1 = 1
    DAY_2 = 2
    DAY_3 = 3
    DAY_4 = 4
    DAY_5 = 5
    DAY_10 = 10  #Default
    MONTH_1 = 1  #Default
    MONTH_2 = 2
    MONTH_3 = 3
    MONTH_6 = 6
    YEAR_1 = 1   #Default
    YEAR_2 = 2
    YEAR_3 = 3
    YEAR_5 = 5
    YEAR_10 = 10
    YEAR_15 = 15
    YEAR_20 = 20
    YTD_1 = 1   #Default

class FrequencyType(Enum):
    DAY_MINUTE = 'minute'  #Default
    MONTH_DAILY = 'daily'
    MONTH_WEEKLY = 'weekly' #Default
    YEAR_DAILY = 'daily'
    YEAR_WEEKLY = 'weekly'
    YEAR_MONTHLY = 'monthly' #default
    YTD_DAILY = 'daily'
    YTD_WEEKLY = 'weekly'  #default

class Frequency(Enum):
    MINUTE_1 = 1  #Default
    MINUTE_5 = 5
    MINUTE_10 = 10
    MINUTE_15 = 15
    MINUTE_30 = 30
    DAILY_1 = 1
    WEEKLY_1 = 1
    MONTHLY_1 = 1

#### Quotes
class Fields(Enum):  ##Quotes
    QUOTE = 'quote'
    FUNDAMENTAL = 'fundamental'
    EXTENDED = 'extended'
    REFERENCE = 'reference'
    REGULAR = 'regular'
    ALL = 'all' #default

#### OTHERS

class RequestedDestination(Enum):
    INET = 'INET'
    ECN_ARCA = 'ECN_ARCA'
    CBOE = 'CBOE'
    AMEX = 'AMEX'
    PHLX = 'PHLX'
    ISE = 'ISE'
    BOX = 'BOX'
    NYSE = 'NYSE'
    NASDAQ = 'NASDAQ'
    BATS = 'BATS'
    C2 = 'C2'
    AUTO = 'AUTO'

class SettlementInstruction(Enum):
    REGULAR = 'REGULAR'
    CASH = 'CASH'
    NEXT_DAY = 'NEXT_DAY'
    UNKNOWN = 'UNKNOWN'

class APIRuleAction(Enum):
    ACCEPT = 'ACCEPT'
    ALERT = 'ALERT'
    REJECT = 'REJECT'
    REVIEW = 'REVIEW'
    UNKNOWN = 'UNKNOWN'

class FeeType(Enum):
    COMMISSION = 'COMMISSION'
    SEC_FEE = 'SEC_FEE'
    STR_FEE = 'STR_FEE'
    R_FEE = 'R_FEE'
    CDSC_FEE = 'CDSC_FEE'
    OPT_REG_FEE = 'OPT_REG_FEE'
    ADDITIONAL_FEE = 'ADDITIONAL_FEE'
    MISCELLANEOUS_FEE = 'MISCELLANEOUS_FEE'
    FTT = 'FTT'
    FUTURES_CLEARING_FEE = 'FUTURES_CLEARING_FEE'
    FUTURES_DESK_OFFICE_FEE = 'FUTURES_DESK_OFFICE_FEE'
    FUTURES_EXCHANGE_FEE = 'FUTURES_EXCHANGE_FEE'
    FUTURES_GLOBEX_FEE = 'FUTURES_GLOBEX_FEE'
    FUTURES_NFA_FEE = 'FUTURES_NFA_FEE'
    FUTURES_PIT_BROKERAGE_FEE = 'FUTURES_PIT_BROKERAGE_FEE'
    FUTURES_TRANSACTION_FEE = 'FUTURES_TRANSACTION_FEE'
    LOW_PROCEEDS_COMMISSION = 'LOW_PROCEEDS_COMMISSION'
    BASE_CHARGE = 'BASE_CHARGE'
    GENERAL_CHARGE = 'GENERAL_CHARGE'
    GST_FEE = 'GST_FEE'
    TAF_FEE = 'TAF_FEE'
    INDEX_OPTION_FEE = 'INDEX_OPTION_FEE'
    TEFRA_TAX = 'TEFRA_TAX'
    STATE_TAX = 'STATE_TAX'
    UNKNOWN = 'UNKNOWN'
