# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 10:54:45 2023

@author: pc
"""

from datetime import datetime, timedelta
import copy
import logging
import json
import os
from dateutil.relativedelta import relativedelta
import pandas as pd
import pytz

#### Auxilian Functions

def parse_date_time(time_to_format):
    '''
    Reformats the input time string by replacing 'T' with ' '.

    Parameters:
        time_to_format (str): Time string to be reformatted.

    Returns:
        str: Reformatted time string.

    '''

    if len(time_to_format) > 25:
        time_to_format = datetime.strptime(time_to_format,'%Y-%m-%dT%H:%M:%S.%f%z')
    else:
        time_to_format = datetime.strptime(time_to_format,'%Y-%m-%dT%H:%M:%S%z')

    return str(time_to_format.astimezone())


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


def write_json_file(data, file_path):

    '''
    Writes data to a JSON file.

    Parameters:
        data: Data to be written.
        file_path (str): Path to the JSON file.
    '''

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file)


#### Position and Balances

class Position:
    '''
    Represents a financial position with associated holdings and transactions.

    Attributes:
        symbol (str): Symbol associated with the position.
        quantity (float): Quantity of the position.
        fifo (dict): First-in-First-Out method data for holdings and allocation.
        lifo (dict): Last-in-First-Out method data for holdings and allocation.
        orders (list): List of orders associated with the position.
        transactions (list): List of transactions associated with the position.

    Methods:
        update_positions_and_holdings(self, transaction, results): Updates positions and
                                                                    transaction records.
        add_holding(self, quantity, price_with_fees, date_time): Adds a new holding to the
                                                                    list of positions.
        remove_holding(self, quantity, price_with_fees, date_time, results): Removes a
                                                        holding from the list of positions.

    '''

    def __init__(self, symbol):
        self.symbol = symbol
        self.quantity = 0.0
        self.fifo = {'holdings': [], 'allocated': 0.00, 'avg_price': 0.00}
        self.lifo = {'holdings': [], 'allocated': 0.00, 'avg_price': 0.00}
        self.orders = []
        self.transactions = []


    def update_positions_and_holdings(self, transaction, results):

        '''
        Updates positions and transaction records based on the given transaction.

        Parameters:
            transaction (dict): Information about the current transaction.
            results (dict): Dictionary to track gains.

        Returns:
            None
        '''

        transaction_item = transaction['transactionItem']

        instruction = transaction['instruction']

        amount = transaction_item['amount']
        quantity = amount if instruction == 'BUY' else -amount
        price_with_fees = -transaction['netAmount'] / quantity

        date_time = parse_date_time(transaction['transactionDate'])[:19]

        if ((instruction == 'BUY' and self.quantity >= 0) or
            (instruction != 'BUY' and self.quantity <= 0)):

            self._add_holding(quantity, price_with_fees, date_time)

            if not transaction['opening transaction']:
                #logger.error('Transaction Sub type mismatch: %s',transaction)
                print('\nERROR - Transaction came with wrong Label/Description', transaction)
                if 'positionEffect' in transaction_item:
                    transaction_item['positionEffect'] += ' - ERROR, MISMATCH could not be solved'
                else:
                    transaction_item['positionEffect'] = 'Transaction Sub type MISMATCH'
                #transaction['description'] += ' - Transaction Sub type MISMATCH'

        else:

            self._remove_holding(quantity, price_with_fees, date_time, results)

            if transaction['opening transaction']:
                #logger.error('Transaction Sub type mismatch: %s',transaction)
                print('\nERROR - Transaction came with wrong Label/Description', transaction)
                if 'positionEffect' in transaction_item:
                    transaction_item['positionEffect'] += ' - ERROR, MISMATCH could not be solved'
                else:
                    transaction_item['positionEffect'] = 'Transaction Sub type MISMATCH'
                #transaction['description'] += ' - Transaction Sub type MISMATCH'
            if results['reverse']:
                #transaction['description'] += ' - REVERSE'
                if 'positionEffect' in transaction_item:
                    transaction_item['positionEffect'] += ' - ERROR REVERSE'
                else:
                    transaction_item['positionEffect'] = 'REVERSE'
                #logger.error('REVERSE: %s, %s', self.symbol, date_time)
                print('\nERROR - REVERSE', transaction)


        self.fifo['allocated'] += -transaction['netAmount'] + results['fifo']['gain']
        self.lifo['allocated'] += -transaction['netAmount'] + results['lifo']['gain']

        self.fifo['allocated'] = round(self.fifo['allocated'],2)
        self.lifo['allocated'] = round(self.lifo['allocated'],2)

        if self.quantity != 0:
            self.fifo['avg_price'] = round(self.fifo['allocated']/self.quantity,2)
            self.lifo['avg_price'] = round(self.lifo['allocated']/self.quantity,2)
        else:
            self.fifo['avg_price'] = 0
            self.lifo['avg_price'] = 0


    def split_holding(self, transaction):
        #find split ratio
        original_quantity = self.quantity
        extra_quantity = transaction['transactionItem']['amount']
        new_quantity = original_quantity + extra_quantity

        split_ratio = new_quantity / original_quantity

        self.quantity = new_quantity
        for method in ('fifo', 'lifo'):
            holdings = getattr(self, method)['holdings']

            for holding in holdings:
                holding['quantity'] = holding['quantity'] * split_ratio
                holding['price_with_fees'] = holding['price_with_fees'] / split_ratio


    def _add_holding(self, quantity, price_with_fees, date_time):
        '''
        Adds a new holding to the list of positions.

        Parameters:
            quantity (float): Quantity of the position.
            price_with_fees (float): Price with fees.
            date_time (str): Date and time of the transaction.

        Returns:
            None
        '''

        new_holding = {'quantity': quantity,
                       'price_with_fees': price_with_fees,
                       'date_time': date_time}

        self.fifo['holdings'].append(copy.deepcopy(new_holding))
        self.lifo['holdings'].insert(0, new_holding)
        self.quantity += quantity


    def _remove_holding(self, quantity, price_with_fees, date_time, results):
        '''
        Removes a holding from the list of positions.

        Parameters:
            quantity (float): Quantity of the position.
            price_with_fees (float): Price with fees.
            date_time (str): Date and time of the transaction.
            results (dict): Dictionary to track gains.

        Returns:
            None
        '''

        transaction_date = datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')

        for method in ('fifo', 'lifo'):

            transaction_quantity = quantity

            result = results[method]
            holdings = getattr(self, method)['holdings']

            transaction_fully_accounted_for = False

            while holdings and not transaction_fully_accounted_for:
                # Check if there are enough in first holding
                # if exactly enough, remove first holding & done w/ removing holdings

                holding_basis = holdings[0]['price_with_fees']

                holding_date = datetime.strptime(holdings[0]['date_time'], '%Y-%m-%d %H:%M:%S')

                holding_duration = transaction_date - holding_date

                if holding_duration > result['duration']:
                    result['duration'] = holding_duration

                if holdings[0]['quantity'] == -transaction_quantity:
                    result['gain'] += holdings[0]['quantity'] * (price_with_fees - holding_basis)

                    holdings.pop(0)
                    transaction_fully_accounted_for = True # Done with removing.

                elif abs(transaction_quantity) < abs(holdings[0]['quantity']):
                    result['gain'] += -transaction_quantity * (price_with_fees - holding_basis)

                    holdings[0]['quantity'] += transaction_quantity
                    transaction_fully_accounted_for = True # Done with removing.

                else: # Quantity sold exceeds value of the first remaining holding
                    result['gain'] += holdings[0]['quantity'] * (price_with_fees - holding_basis)

                    transaction_quantity += holdings[0]['quantity']
                    holdings.pop(0)
                    # Not done with removing. Continue.

            result['gain'] = round(result['gain'],2)

            if not holdings and not transaction_fully_accounted_for:
                results['reverse'] = True

        if results['reverse']:
            self.quantity = 0
            self._add_holding(transaction_quantity, price_with_fees, date_time)
        else:
            self.quantity += quantity


class Balances:
    '''
    Represents financial balances, including cash, margin, and positions.

    Attributes:
        cash_sweep_vehicle (float): Balance in the cash sweep vehicle.
        cash_balance (float): Cash balance.
        margin_balance (float): Margin balance.
        short_balance (float): Short balance.
        account_value (float): Total account value.
        fifo_allocated (float): Allocated amount using FIFO method.
        lifo_allocated (float): Allocated amount using LIFO method.
        positions (dict): Dictionary of positions.
        positions_resume (str): Summary of positions.

    Methods:
        process_transaction(self, transaction): Processes a transaction and updates the
                                                corresponding balances and records.
        process_transaction_balances(self, transaction): Updates balance information based
        on the given transaction.

    '''

    def __init__(self):

        self.cash_related_balances = {'cash balance': 0.00,
                                      'cash alternatives': 0.00,
                                      'margin balance':0.00,
                                      'short balance': 0.00}

        self.cash_sweep_vehicle = 0.00

        self.account_value = 0.00

        self.fifo = {'allocated':0.00,
                     'breakeven value': 0.00}

        self.lifo = {'allocated':0.00,
                     'breakeven value': 0.00}

        self.positions = {}

        self.incorrect_sequence_list = []

        self.processed_transactions = []

        self.positions_resume = ''


    def get_positions_quantities(self):
        '''
        Extracts position quantities and FIFO allocated values from the internal
        positions dictionary.

        Returns:
        dict: A dictionary where symbols are keys, and values are dictionaries with
        'quantity' and 'fifo_allocated'.
        '''

        positions_dict = {}
        for symbol, position in self.positions.items():
            positions_dict[symbol] = {'quantity': position.quantity,
                                      'fifo_allocated': round(position.fifo['allocated'],2),
                                      }

        return positions_dict


    def process_transaction(self, transaction):
        '''
        Processes a transaction and updates the corresponding balances and records.

        Parameters:
            transaction (dict): Information about the current transaction.

        Returns:
            None
        '''


        if transaction['position affected']:

            if transaction['instruction'] == 'SPLIT':
                symbol = transaction['transactionItem']['instrument']['symbol']
                self.positions[symbol].split_holding(transaction)
                results = {'reverse': False,
                            'fifo':{'gain' : 0.00, 'duration': timedelta()},
                            'lifo':{'gain' : 0.00, 'duration': timedelta()}
                          }
                self._update_transaction_data(transaction, results)

            elif self.incorrect_sequence_list: #There is a ongoing sequence fix

                if self.incorrect_sequence_list[0]['transactionDate'] == transaction['transactionDate']:
                #As the ongoing transaction has the same time as the one detected as wrong sequence
                #We add to teh queue to reoder in apropiate sequence whenever we have all of them
                    transaction['transactionItem']['positionEffect'] = 'sorted'
                    self.incorrect_sequence_list.append(transaction)

                else:
                    self._process_incorrect_sequence()
                    if self._transaction_wrong_sequence_detected(transaction):
                        self.incorrect_sequence_list.append(transaction)
                    else:
                        self._update_position_balances(transaction)

            elif self._transaction_wrong_sequence_detected(transaction):
                self.incorrect_sequence_list.append(transaction)
            else:
                self._update_position_balances(transaction)


        else:
            results = {'reverse': False,
                        'fifo':{'gain' : 0.00, 'duration': timedelta()},
                        'lifo':{'gain' : 0.00, 'duration': timedelta()}
                      }
            self._update_transaction_data(transaction, results)


    def is_less_than_3_min_diff(self, d1, d2):
        date1 = datetime.strptime(d1, "%Y-%m-%dT%H:%M:%S%z")
        date2 = datetime.strptime(d2, "%Y-%m-%dT%H:%M:%S%z")

        # Calcular la diferencia en minutos
        difference_in_minutes = abs((date2 - date1).total_seconds() / 60)

        if difference_in_minutes < 3:
            return True
        return False


    def _process_incorrect_sequence(self):

        first_flag = self.incorrect_sequence_list[0]['opening transaction']
        ordered_transactions = sorted(self.incorrect_sequence_list, key=lambda x:
                                      x['opening transaction'] == first_flag)

        for tran in ordered_transactions:
            self._update_position_balances(tran)
        self.incorrect_sequence_list = []


    def _transaction_wrong_sequence_detected(self, transaction):
        """
        Checks for a mismatch in transaction sequence.

        Parameters:
            transaction (dict): Information about the current transaction.

        Returns:
            bool: True if there is a sequence mismatch, False otherwise.
        """

        instruction = transaction['instruction']
        wrong_sequence = False

        position_quantity = 0
        symbol = transaction['transactionItem']['instrument']['symbol']
        transaction_item = transaction['transactionItem']

        if symbol in self.positions:
            position_quantity = self.positions[symbol].quantity

        if ((instruction == 'BUY' and position_quantity >= 0) or
            (instruction != 'BUY' and position_quantity <= 0)):

            if not transaction['opening transaction']:
                wrong_sequence = True
                #logger.warning('Transaction Sub type mismatch: %s',transaction)
        else:
            if transaction['opening transaction']:
                wrong_sequence = True
                #logger.warning('Transaction Sub type mismatch: %s',transaction)

        if wrong_sequence:
            print('\nWARNING - transaction came in the wrong sequence', transaction)
            if 'positionEffect' in transaction_item:
                transaction_item['positionEffect'] += ' - Warning, Transaction Sub type MISMATCH'
            else:
                transaction_item['positionEffect'] = 'Warning, Transaction Sub type MISMATCH'

        return wrong_sequence


    def _update_position_balances(self, transaction):
        '''
        Updates position-related balances based on the given transaction.

        Parameters:
            transaction (dict): Information about the current transaction.

        Returns:
            None
        '''

        symbol = transaction['transactionItem']['instrument']['symbol']

        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol)

        results = {'reverse': False,
                    'fifo':{'gain' : 0.00, 'duration': timedelta()},
                    'lifo':{'gain' : 0.00, 'duration': timedelta()}
                  }

        self.positions[symbol].update_positions_and_holdings(transaction, results)

        self.fifo['allocated'] += -transaction['netAmount'] + results['fifo']['gain']
        self.lifo['allocated'] += -transaction['netAmount'] + results['lifo']['gain']

        self.fifo['allocated'] = round(self.fifo['allocated'],2)
        self.lifo['allocated'] = round(self.lifo['allocated'],2)

        self._update_transaction_data(transaction,results)


    def _update_cash_balances(self, transaction):
        '''
        Updates cash-related balances based on the given transaction.

        Parameters:
            transaction (dict): Transaction information.

        Returns:
            None
        '''

        description = transaction['description']
        transaction_type = transaction['type']
        transaction_subaccount = transaction['subAccount']
        net_amount = transaction['netAmount']
        cash = self.cash_related_balances

        # Update cash alternatives balance
        if transaction_type == 'RECEIVE_AND_DELIVER':
            amount = transaction['transactionItem']['amount']
            if description in ('CASH ALTERNATIVES PURCHASE', 'CASH ALTERNATIVES INTEREST'):
                cash['cash alternatives'] = round(cash['cash alternatives'] + amount,2)
            elif description == 'CASH ALTERNATIVES REDEMPTION':
                cash['cash alternatives'] = round(cash['cash alternatives'] - amount,2)

        # Update short balance
        elif (description in ('SHORT SALE', 'CLOSE SHORT POSITION') or
              (description == 'MARK TO THE MARKET' and transaction_subaccount == '4')):

            cash['short balance'] = round(cash['short balance'] + net_amount,2)


        # Update cash balance and margin balance
        else:
            margin = round(cash['cash balance'] +
                           cash['margin balance'] +
                           net_amount,2)

            if margin >0:
                cash['cash balance'] = margin
                cash['margin balance'] = 0.00
            else:
                cash['margin balance'] = margin
                cash['cash balance'] = 0.00


    def _update_transaction_data(self, transaction, results):

        self._update_cash_balances(transaction)

        description = transaction['description']
        net_amount = transaction['netAmount']
        cash = self.cash_related_balances
        quantity = ''

        # Update cash sweep vehicle balance when no intra account transfer
        if description not in ('CASH ALTERNATIVES PURCHASE', 'CASH ALTERNATIVES REDEMPTION',
                               'INTRA-ACCOUNT TRANSFER', 'MARK TO THE MARKET'):
            #Those above are inter account transfers so total cash does not change.

            self.cash_sweep_vehicle = round(cash['margin balance'] +
                                      cash['cash balance'] +
                                      cash['short balance'] +
                                      cash['cash alternatives'],2)


            #Add gains when no position affected transaction and no intraccount transfer
            if not transaction['position affected']:
                if description == 'CASH ALTERNATIVES INTEREST':
                    transaction_result = transaction['transactionItem']['amount']
                else:
                    transaction_result = net_amount
                results['fifo']['gain'] = transaction_result
                results['lifo']['gain'] = transaction_result
            else: #If position affected transaction, gain already accounted.
                symbol = transaction['transactionItem']['instrument']['symbol']

                quantity = self.positions[symbol].quantity

        self.positions_resume = ''
        for symbol in list(self.positions.keys()):
            position = self.positions[symbol]
            self.positions_resume += f"{symbol}: {position.quantity}, "
            if  self.positions[symbol].quantity == 0: #no borrar si es today
                del self.positions[symbol]


        # Create transaction row
        row = self._create_transaction_row(transaction, results, quantity)
        self.processed_transactions.append(row)


    def _create_transaction_row(self, transaction, results, quantity):
        '''
        Creates a row of transaction data for the DataFrame.

        Parameters:
            balances (dict): Balance information.
            transaction (dict): Transaction information.
            results (dict): Dictionary to track gains and durations.
            quantity (float): Transaction quantity.

        Returns:
            list: List representing a row of transaction data.
        '''

        transaction['transactionDate'] = parse_date_time(transaction['transactionDate'])

        instrument = transaction['transactionItem'].get('instrument', {})
        asset_type = instrument.get('assetType', '')
        description = transaction['description']
        if asset_type == 'OPTION':
            description += f" {instrument.get('description', '')}"

        return [
            datetime.strptime(transaction['transactionDate'][:10], '%Y-%m-%d').date(),
            datetime.strptime(transaction['transactionDate'][11:19], '%H:%M:%S').time(),
            transaction['type'],
            transaction.get('transactionSubType', ''),
            transaction.get('transactionId', transaction.get('orderId', '')),
            description,
            transaction['subAccount'],
            transaction['fees']['regFee'],
            transaction['fees']['commission'],
            transaction['netAmount'],
            transaction['transactionItem'].get('amount', ''),

            self.cash_related_balances['cash balance'],
            self.cash_related_balances['cash alternatives'],
            self.cash_related_balances['margin balance'],
            self.cash_related_balances['short balance'],
            self.cash_sweep_vehicle,

            asset_type,
            instrument.get('symbol', ''),
            transaction.get('orderId', ''),
            transaction['transactionItem'].get('instruction', ''),
            transaction['transactionItem'].get('price', ''),
            transaction['transactionItem'].get('positionEffect', ''),
            instrument.get('underlyingSymbol', ''),

            results['fifo']['gain'],
            results['lifo']['gain'],
            results['fifo']['duration'],
            results['lifo']['duration'],

            quantity,
            self.positions_resume,

            self.fifo['allocated'],
            self.lifo['allocated'],

            self.cash_sweep_vehicle + self.fifo['allocated'],
            self.cash_sweep_vehicle + self.lifo['allocated']
            ]


    def transaction_interpretation_schwab(self, transaction):
        '''
        Interprets and annotates transaction information.

        Parameters:
            transaction (dict): Information about the transaction.

        Returns:
            None
        '''

        ## Position affected ?
        relevant_transaction_types = ('TRADE', 'RECEIVE_AND_DELIVER')
        irrelevant_transaction_descriptions = ('CASH ALTERNATIVES PURCHASE',
                                   'CASH ALTERNATIVES REDEMPTION',
                                   'CASH ALTERNATIVES INTEREST',
                                   'INTERNAL TRANSFER BETWEEN ACCOUNTS OR ACCOUNT TYPES')


        transaction['position affected'] = (transaction['type'] in relevant_transaction_types and
                                            transaction['description'] not in
                                            irrelevant_transaction_descriptions)

        ## transaction intruction
        transaction_instructions = {
            'TRANSFER OF SECURITY OR OPTION IN': 'BUY',
            'NON-TAXABLE SPIN OFF/LIQUIDATION DISTRIBUTION': 'BUY',
            'REMOVAL OF OPTION DUE TO EXPIRATION': 'SELL',
            'STOCK SPLIT': 'SPLIT'
        }

        instruction = transaction['transactionItem'].get('instruction',
                                        transaction_instructions.get(transaction['description']))

        transaction['instruction'] = instruction

        ## Opening transaction ?
        description = transaction['description']
        opening_transaction_descriptions = ('BUY TRADE', 'SHORT SALE',
                                            'TRANSFER OF SECURITY OR OPTION IN',
                                'NON-TAXABLE SPIN OFF/LIQUIDATION DISTRIBUTION'
                                )

        closing_transaction_descriptions = ('SELL TRADE', 'CLOSE SHORT POSITION')

        transaction['opening transaction'] = description in opening_transaction_descriptions
        if 'instrument' in transaction['transactionItem']:
            if transaction['transactionItem']['instrument']['symbol'] == 'FB':
                transaction['transactionItem']['instrument']['symbol'] = 'META'


#### Historical Transaction

def get_historical_transactions(schwab_api, historical_transactions_json_file):
    '''
    Retrieves historical transactions using the provided TD API instance.

    Parameters:
        td_api: TD API instance.
        transactions_json_file (str): Path to the JSON file to load previous transactions
                                                    and store new downloaded transactions.

    Returns:
        list: List of historical transactions.
    '''

    transactions = schwab_api.get_transactions()
    overlap = False
    if os.path.isfile(historical_transactions_json_file):

        loaded_transactions = read_json_file(historical_transactions_json_file)
        logger.debug('Loaded %s transactions from file.', len(loaded_transactions))
        loaded_transactions.reverse()

        if (transactions[-1]['transactionDate'][:10] <=
            loaded_transactions[0]['transactionDate'][:10]):

            overlap = True
            older_transactions = [d for d in loaded_transactions if d['transactionDate'][:10] <
                                                           transactions[-1]['transactionDate'][:10]]
            logger.debug('Found overlap in transactions. Extending the list.')
            transactions.extend(older_transactions)

    if not overlap:
        load_transactions_until_overlap(schwab_api, transactions)

    transactions.reverse()
    # Write transactions to file
    write_json_file(transactions, historical_transactions_json_file)
    return transactions


def load_transactions_until_overlap(schwab_api, transactions):
    '''
    Loads transactions until there is an overlap in dates.

    Parameters:
        td_api (TDApi): TD Ameritrade API object.
        transactions (list): List of transactions.

    Returns:
        None
    '''

    end_date = 0
    while True:
        if transactions:
            if end_date == 0:
                date = datetime.strptime(transactions[-1]['transactionDate'][:10],
                                         '%Y-%m-%d').date()- timedelta(days=1)

            else:
                date = date - relativedelta(years=1)

            end_date = date.strftime('%Y-%m-%d')
            if end_date[-2:] in ('30','31','01'): #to avoid midnight interest that may get in both fetchs
                date = date + timedelta(days=3)
                end_date = date.strftime('%Y-%m-%d')
            start_date = (date+timedelta(days=1)-relativedelta(years=1)).strftime('%Y-%m-%d')
            print(f'Fetching from: {start_date}, to {end_date}')

            #logger.info(end_date, start_date)
            fetched_transactions = schwab_api.get_transactions(start_date = start_date,
                                                               end_date = end_date)
            if not fetched_transactions:
                logger.warning('No older transactions found for the specified date range: %s-%s',
                               start_date, end_date)
                break
            older_transactions = [d for d in fetched_transactions if d['transactionDate'][:10] <
                                                           transactions[-1]['transactionDate'][:10]]
            transactions.extend(older_transactions)


#### To dataframe

def create_dataframe(processed_transactions):

    columns = ['Date', 'Time', 'Type', 'SubType', 'Ref#', 'Description', 'SubAccount',
               'Misc Fees', 'Commissions & Fees', 'Amount', 'Quantity', 'Cash','Alternative',
               'margin','short','Sweep', 'Asset Type', 'Symbol', 'orderId', 'instruction', 'price',
               'PositionEffect', 'Underlying Symbol', 'FIFO', 'LIFO', 'Duration FIFO',
               'Duration LIFO', '#Shares', 'Positions', 'Allocated FIFO', 'Allocated LIFO',
               'Value FIFO', 'Value LIFO']

    transaction_dataframe = pd.DataFrame(processed_transactions , columns=columns)
    return transaction_dataframe


# =============================================================================
# def cumulative_results(transactions_df):
#     '''
#     Calculates daily, weekly, monthly, and annual cumulative gains.
#
#     Parameters:
#         transactions_df (pd.DataFrame): Transaction DataFrame.
#
#     Returns:
#         pd.DataFrame: DataFrame with columns of cumulative gains.
#     '''
#
#     transactions_df['Date'] = pd.to_datetime(transactions_df['Date'])
#
#     methods = ['FIFO', 'LIFO']
#     frequencies = ['daily', 'weekly', 'monthly', 'annual']
#     #filtered_df = transactions_df[(transactions_df['FIFO'] != 0) & (transactions_df['Type'] == 'TRADE')]
#     for freq in frequencies:
#         #column_name_count = f'{freq.capitalize()} Count'
#         #transactions_df[column_name_count] = ((filtered_df['Type'] == 'TRADE').groupby
#         #                                    (filtered_df['Date'].dt.to_period(freq[0])).cumsum())
#
#
#         for method in methods:
#
#             #column_name_profit = f'{method} {freq.capitalize()}'
#             column_name_profit_result = f'{method} {freq.capitalize()} - Result'
#             #transactions_df[column_name_profit] = (filtered_df.groupby
#             #                                       (filtered_df['Date'].dt.to_period(freq[0]))[method].cumsum())
#             transactions_df[column_name_profit_result] = calculate_cumulative_result(transactions_df, freq[0], method)
#
#     transactions_df['Date'] = transactions_df['Date'].dt.date
#
#     return transactions_df
#
#
# def calculate_cumulative_result(dataframe, freq, method):
#     '''
#     Calculates cumulative gains for a given method and frequency.
#
#     Parameters:
#         dataframe (pd.DataFrame): Transaction DataFrame.
#         freq (str): Frequency ('d' for daily, 'w' for weekly, 'm' for monthly, 'a' for annual).
#         method (str): Accounting method ('FIFO' or 'LIFO').
#
#     Returns:
#         pd.Series: Cumulative gains.
#     '''
#
#     daily_cumulative_columns = {
#         'd': method,
#         'w': f'{method} Daily - Result',
#         'm': f'{method} Daily - Result',
#         'a': f'{method} Monthly - Result',
#     }
#
#     column = daily_cumulative_columns[freq]
#
#     cumulative_column = dataframe.groupby(dataframe['Date'].dt.to_period(freq))[column].cumsum()
#
#     # Marcar las filas duplicadas
#     #duplicated_rows = dataframe.duplicated(subset=['Date', 'Time'], keep='last')
#
#     # Asignar 0.0 a las filas duplicadas
#     #cumulative_column[duplicated_rows] = 0.0
#
#     return cumulative_column.where(dataframe.groupby(dataframe['Date'].dt.to_period(freq))
#                                    ['DateTime'].transform('max') == dataframe['DateTime'],
#                                    0.0)
#
#
# def calculate_cumulative_count_result(dataframe):
#     '''
#     Calculates cumulative gains for a given method and frequency.
#
#     Parameters:
#         dataframe (pd.DataFrame): Transaction DataFrame.
#         freq (str): Frequency ('d' for daily, 'w' for weekly, 'm' for monthly, 'a' for annual).
#         method (str): Accounting method ('FIFO' or 'LIFO').
#
#     Returns:
#         pd.Series: Cumulative gains.
#     '''
#
#     dataframe['Date'] = pd.to_datetime(dataframe['Date'])
#     filtered_df = dataframe[(dataframe['FIFO'] != 0) & (dataframe['Type'] == 'TRADE')]
#
#     for freq in ['d', 'w', 'm', 'a']:
#         cumulative_count = filtered_df.groupby(filtered_df['Date'].dt.to_period(freq))['FIFO'].count()
#
#         for dte, valor in cumulative_count.items():
#             ultima_fila = dataframe.loc[dataframe['Date'].dt.to_period(freq) == dte].index[-1]
#             dataframe.loc[ultima_fila, f'{freq.capitalize()} Count - Result'] = valor
#
#     dataframe['Date'] = dataframe['Date'].dt.date
#     return dataframe
# =============================================================================


def calculate_cumulative(dataframe, freq, method):
    '''
    Calculates cumulative gains for a given method and frequency.

    Parameters:
        dataframe (pd.DataFrame): Transaction DataFrame.
        freq (str): Frequency ('d' for daily, 'w' for weekly, 'm' for monthly, 'a' for annual).
        method (str): Accounting method ('FIFO' or 'LIFO').

    Returns:
        pd.Series: Cumulative gains.
    '''

    daily_cumulative_columns = {
        'd': method,
        'w': f'{method} Daily',
        'm': f'{method} Daily',
        'a': f'{method} Monthly',
    }

    column = daily_cumulative_columns[freq]

    cumulative_column = dataframe.groupby(dataframe['Date'].dt.to_period(freq))[column].cumsum()

    # Marcar las filas duplicadas
    duplicated_rows = dataframe.duplicated(subset=['Date', 'Time'], keep='last')

    # Asignar 0.0 a las filas duplicadas
    cumulative_column[duplicated_rows] = 0.0

    return cumulative_column.where(dataframe.groupby(dataframe['Date'].dt.to_period(freq))
                                   ['DateTime'].transform('max') == dataframe['DateTime'],
                                   0.0)


def cumulative_results(transactions_df):
    '''
    Calculates daily, weekly, monthly, and annual cumulative gains.

    Parameters:
        transactions_df (pd.DataFrame): Transaction DataFrame.

    Returns:
        pd.DataFrame: DataFrame with columns of cumulative gains.
    '''

    transactions_df['DateTime'] = pd.to_datetime(transactions_df['Date'].astype(str) +
                                                 transactions_df['Time'].astype(str),
                                                 format='%Y-%m-%d%H:%M:%S')
    transactions_df['Date'] = pd.to_datetime(transactions_df['Date'])

    methods = ['FIFO', 'LIFO']
    frequencies = ['daily', 'weekly', 'monthly', 'annual']

    for freq in frequencies:
        for method in methods:

            column_name = f'{method} {freq.capitalize()}'
            transactions_df[column_name] = calculate_cumulative(transactions_df, freq[0], method)

    transactions_df = transactions_df.drop('DateTime', axis=1)
    transactions_df['Date'] = transactions_df['Date'].dt.date

    return transactions_df


def convert_to_excel(transactions_data, excel_path):
    transactions_data['Duration FIFO'].replace(timedelta(), '', inplace=True)
    transactions_data['Duration LIFO'].replace(timedelta(), '', inplace=True)
    # Convert dataframe to Excel
    with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
        transactions_data.to_excel(writer, sheet_name='Transactions', index=False)


#### Verification
def get_account_positions_quantities(dictionary_list):
    '''
    Extracts position quantities and FIFO allocated values from a list of position dictionaries.

    Parameters:
        dictionary_list (list): List of position dictionaries obtained from the API.

    Returns:
        dict: A dictionary where symbols are keys, and values are dictionaries with 'quantity'
        and 'fifo_allocated'.
    '''

    positions_dict = {}
    for position in dictionary_list:
        symbol = position['instrument']['symbol']
        quantity = position['longQuantity'] - position['shortQuantity']
        fifo_allocated = round(position['averagePrice'] * quantity,2)
        positions_dict[symbol] = {'quantity': quantity,
                                  'fifo_allocated': fifo_allocated
                                                            }

    return positions_dict


def compare_positions(positions1, positions2):
    '''
    Compares two dictionaries of positions and prints any differences in quantity or FIFO
    allocated values.

    Parameters:
        positions1 (dict): First dictionary of positions.
        positions2 (dict): Second dictionary of positions.

    Returns:
        None
    '''

    for symbol,position1 in positions1.items():
        position2 = positions2.get(symbol)
        if position2:
            if (position1['quantity'] != position2['quantity'] or
                position1['fifo_allocated'] != position2['fifo_allocated']):

                print('\n', symbol, position1, '\n    ',position2)
            del positions2[symbol]

        else:
            print ('\n', symbol, position1)


def get_diccionaries_difference(positions1, positions2):
    '''
    Compares two dictionaries of positions and prints any differences in quantity or FIFO
    allocated values.

    Parameters:
        positions1 (dict): First dictionary of positions.
        positions2 (dict): Second dictionary of positions.

    Returns:
        None
    '''

    positions1_copy = copy.deepcopy(positions1)
    positions2_copy = copy.deepcopy(positions2)

    compare_positions(positions1_copy, positions2_copy)
    compare_positions(positions2_copy, positions1_copy)


def verification():
    ### Position quantity test
    positions_quantities = balances_system.get_positions_quantities()
    account_positon_quantity = get_account_positions_quantities(account['positions'])

    if positions_quantities == account_positon_quantity:
        print('\nPosition OK')
    else:
        print('\nPosition Differences:')
        get_diccionaries_difference(positions_quantities, account_positon_quantity)

    system_balances = balances_system.cash_related_balances
    current_balances = account['currentBalances']
    ### Balance test
    if system_balances['cash balance'] == current_balances['cashBalance']:
        print('\nCash balance ok')
    else:
        print('\nCash balance differences:')
        print(system_balances['cash balance']," ", current_balances['cashBalance'])
    if system_balances['short balance'] == current_balances['shortBalance']:
        print('\nShort balance ok')
    else:
        print('\nShort balance differences:')
        print(system_balances['short balance']," ",current_balances['shortBalance'])
    if system_balances['margin balance'] == current_balances['marginBalance']:
        print('\nMargin balance ok')
    else:
        print('\nMargin balance differences:')
        print(system_balances['margin balance']," ", current_balances['marginBalance'])


def format_dateTime(dateTime):

    # Parsear la cadena de fecha y hora a un objeto datetime
    original_date = datetime.fromisoformat(dateTime)

    # Convertir la fecha y hora a UTC
    utc_date = original_date.astimezone(pytz.UTC)

    # Formatear la fecha y hora en el formato deseado
    formatted_date_str = utc_date.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    return formatted_date_str


def load_all_transactions(schwab_api, historical_transactions_json_file):
    '''
    Loads transactions until there is an overlap in dates.

    Parameters:
        schwab_api (SchwabAPI): Schwab API object.

    Returns:
        None
    '''
    seen_activity_ids = set()
    combined_transactions = []

    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)  # 3 meses

    year_2000 = datetime(2000, 1, 1)  # Fecha límite

    while end_date > year_2000:
        # Formatear fechas
        end_date_str = format_dateTime(str(end_date))
        start_date_str = format_dateTime(str(start_date))


        #end_date_str = '2014-08-14T04:00:00.000Z'
        #start_date_str = '2014-05-16T04:00:00.000Z'
        # Obtener transacciones para el período actual
        fetched_transactions = schwab_api.get_transactions(start_date=start_date_str, end_date=end_date_str)
        sorted_transactions = sorted(fetched_transactions, key=lambda x: x["time"])

        print(start_date_str + " - " + end_date_str + " " + str(len(sorted_transactions)))


        # Agregar transacciones al conjunto y la lista combinada
        add_transactions(sorted_transactions, seen_activity_ids, combined_transactions)

        # Actualizar las fechas para el siguiente bucle
        end_date = start_date
        start_date = end_date - timedelta(days=180)  # 3 meses

    combined_transactions = sorted(combined_transactions, key=lambda x: x["time"])

    #combined_transactions.reverse()
    # Write transactions to file
    write_json_file(combined_transactions, historical_transactions_json_file)
    return combined_transactions

def add_transactions(transactions, seen_activity_ids, combined_transactions):
    for transaction in transactions:
        activity_id = transaction["activityId"]
        if activity_id not in seen_activity_ids:
            seen_activity_ids.add(activity_id)
            combined_transactions.append(transaction)



#### Main ###########

if __name__ == '__main__':
    JSON_FILE = './AllTransactions.json'
    EXCEL_FILE_PATH = './AllTransactions_new.xlsx'
    LOG_FILE = './transactions.log'
    CONFIG_FILE = './config.json'

    # Configura la configuración del logging
    logging.basicConfig()
    # Agrega un StreamHandler para enviar mensajes a la consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    logging.getLogger('').addHandler(console_handler)
    logger = logging.getLogger(__name__)
    logger.info('Program started.')

    from schwab_api import schwabApi
    user_data = read_json_file(CONFIG_FILE)

    schwab_api = schwabApi(user_data)

    account = schwab_api.get_accounts(fields = ['positions'])
    print(account)
    # Uso del sistema
    balances_system = Balances()
    allTransactions = load_all_transactions(schwab_api, JSON_FILE)
    #allTransactions = read_json_file(JSON_FILE)

    for t in allTransactions:
        balances_system.transaction_interpretation_schwab(t)
        balances_system.process_transaction(t)

    balances_states_df = create_dataframe(balances_system.processed_transactions)
    balances_states_df = cumulative_results(balances_states_df)

    #balances_states_df = calculate_cumulative_count_result(balances_states_df)
    convert_to_excel(balances_states_df, EXCEL_FILE_PATH)

    verification()


    logger.info('Program finished.')
    logging.shutdown()

# =============================================================================
# now = datetime.now().astimezone()
# pricehistory_date = tdapi.pricehistory_dates(symbol = 'SPY', period_type = 'day',
#                                                 frequency_type = 'minute', frequency = '30',
#                                                 end_date = now,
#                                                 start_date = now-timedelta(weeks=1),
#                                                 need_extendedhours_data = 'false')
# =============================================================================

'''df = pd.DataFrame(allTransactions)
type_counts = df['type'].value_counts()

print(type_counts)


type_to_print = 'JOURNAL'
filtered_df = df[df['type'] == type_to_print]

# Seleccionar la primera transacción del tipo filtrado
if not filtered_df.empty:
    transaction_to_print = filtered_df.iloc[0].to_dict()
    pd.ExcelWriter('journal_transaction.xlsx', engine='xlsxwriter').to_excel(transaction_to_print)
    print(transaction_to_print)
else:
    print(f"No transactions of type {type_to_print} found.")


with pd.ExcelWriter("transactions.xlsx", engine='xlsxwriter') as writer:
    transaction_to_print.to_excel(writer, sheet_name="Main", index=False)'''
