'''
python arbitrage2.py
'''

import requests
import platform
import json
import datetime
import os
import time
import sys
import hashlib
import hmac
import urllib.parse
from time import time
import time
from inputimeout import inputimeout, TimeoutOccurred
import math
import utils
import constants

'''
#################################################################################
 ASK: lowest sell price
 BID: highest buy price
#################################################################################
'''
def process_analyze(source,target,source_trading_fee_param,target_trading_fee_param,source_thb_withdrawal_fee,target_thb_withdrawal_fee):
    date_now = datetime.datetime.now()
    print(str(date_now.strftime("%b %d %Y %H:%M:%S")))

    symbols_source= utils.get_symbols(source)
    symbols_target=utils.get_symbols(target)
    symbols=utils.get_common_symbols(symbols_source,symbols_target)
    #print('symbols_source:',symbols_source)
    #print('symbols_target:',symbols_target)
    #print('symbols:',symbols)

    tickers_source=utils.get_tickers(source)
    tickers_target=utils.get_tickers(target)
    #print('tickers_source:',tickers_source)
    #print('tickers_target:',tickers_target)

    for symbol in symbols:
        ticker_source = tickers_source[symbol]
        ticker_target = tickers_target[symbol]
        source_ask_price=ticker_source['askPrice']
        source_bid_price=ticker_source['bidPrice']
        target_ask_price=ticker_target['askPrice']
        target_bid_price=ticker_target['bidPrice']
        #print('symbol:',symbol,'source_ask_price:',source_ask_price,'source_bid_price:',source_bid_price)
        #print('symbol:',symbol,'target_ask_price:',target_ask_price,'target_bid_price:',target_bid_price)

        is_buy_on_source= False
        is_buy_on_target =False
        if source_ask_price < target_bid_price:
            is_buy_on_source = True
            spread = ((target_bid_price - source_ask_price) / source_ask_price) * 100
        elif target_ask_price < source_bid_price:
            is_buy_on_target =True
            spread = ((source_bid_price - target_ask_price) / target_ask_price) * 100

        # analyze each profit in details by looking at volume, minimum volume, trading fees, transfer fees
        source_trading_fee=0
        target_trading_fee=0
        if is_buy_on_source or is_buy_on_target:
            if is_buy_on_source:
                source_order_books = utils.get_order_books(symbol,source)
                source_aggregated_ask_orders=utils.get_aggregated_ask_orders(symbol, source_order_books,source)
                target_order_books = utils.get_order_books(symbol,target)
                target_aggregated_bid_orders=utils.get_aggregated_bid_orders(symbol, target_order_books,target)
                source_trading_fee = source_trading_fee_param
                target_trading_fee = target_trading_fee_param
                thb_withdrawal_fee = source_thb_withdrawal_fee
            else:
                source_order_books = utils.get_order_books(symbol,target)
                source_aggregated_ask_orders=utils.get_aggregated_ask_orders(symbol, source_order_books,target)
                target_order_books = utils.get_order_books(symbol,source)
                target_aggregated_bid_orders=utils.get_aggregated_bid_orders(symbol, target_order_books,source)
                source_trading_fee = target_trading_fee_param
                target_trading_fee = source_trading_fee_param
                thb_withdrawal_fee = target_thb_withdrawal_fee
            
            if source_aggregated_ask_orders is None:
                #print('     No open SELL order to buy')
                continue
           
            if target_aggregated_bid_orders is None:
                #print('     No open BUY order to sell')
                continue

            #print('symbol:',symbol)
            # iterate first item in source list match with all items in target list having enough quantity to match it
            source_aggregated_ask_order= source_aggregated_ask_orders[0]
            source_quantity_original=source_aggregated_ask_order['quantity_original']
            quantity_to_buy= source_quantity_original
            target_aggregated_bid_order = target_aggregated_bid_orders[0]
            target_quantity_original = target_aggregated_bid_order['quantity_original']
            if source_quantity_original > target_quantity_original:
                quantity_to_buy = target_quantity_original
            source_price=float(source_aggregated_ask_order['price'])
            target_price=float(target_aggregated_bid_order['price'])
            #print('     source_price:',source_price,'source_quantity_original:',source_quantity_original,' quantity_to_buy:',quantity_to_buy)
            #print('     target_price:',target_price,'target_quantity_original:',target_quantity_original)
            
            '''
            https://www.multitrader.io/cryptocurrency-arbitrage-strategies-part-i-loop/
            '''
            TRANSFER_FEE=constants.SYMBOL_CONFIGS[symbol][constants.TRANSFER_FEE_FIELD]
            #print('     transfer_fee:',TRANSFER_FEE)
            investment_thb = quantity_to_buy * source_price
            #print('     investment_thb:',investment_thb,'quantity_to_buy:',quantity_to_buy,'source_price:',source_price)
            investment_thb = utils.round_decimals_up(investment_thb,1)
            # we add the trading fee instead of deducting because we need to sell the same quantity on the target exchange
            #source_quantity_purchased_before_trade_and_transfer = investment_thb / (source_price * (1 + (source_trading_fee)/100 )) + TRANSFER_FEE
            src_txn_trading_fee = quantity_to_buy * source_trading_fee / 100
            source_quantity_purchased_after_trade_and_transfer = quantity_to_buy - src_txn_trading_fee - TRANSFER_FEE
            target_amount_received_after_trade_and_after_withdrawal = source_quantity_purchased_after_trade_and_transfer * target_price * (1 - (target_trading_fee)/100 ) #- thb_withdrawal_fee
            profit_loss_thb = target_amount_received_after_trade_and_after_withdrawal - investment_thb
            #print('     src_txn_trading_fee:',src_txn_trading_fee)
            #print('     source_quantity after_trade_and_transfer:',source_quantity_purchased_after_trade_and_transfer)
            #print('     target_price:',target_price)
            #print('     target_amount after_trade_and_withdrawal:',target_amount_received_after_trade_and_after_withdrawal)
            if profit_loss_thb > 0 and spread >=1:
                if is_buy_on_source:
                    print(symbol,'BUY ON',source,'AND SELL ON',target,'. SPREAD:',format(spread,'.1f'))
                else:
                    print(symbol,'BUY ON',target,'AND SELL ON',source,'. SPREAD:',format(spread,'.1f'))
                print('source_price:',source_price,'source_quantity:',source_quantity_original,' quantity_to_buy:',quantity_to_buy)
                print('target_price:',target_price,'target_quantity:',target_quantity_original)
                print('investment_thb:',format(investment_thb,'.1f'),'quantity_to_buy:',quantity_to_buy)
                print('source_quantity_purchased_after:',format(source_quantity_purchased_after_trade_and_transfer,'.2f'))
                print('sell:',format(source_quantity_purchased_after_trade_and_transfer,'.2f'),'',symbol,'target_amount_received_after:',format(target_amount_received_after_trade_and_after_withdrawal,'.2f'))
                print('profit_loss_thb:',format(profit_loss_thb,'.1f'))
                if platform.system() != 'Windows':
                    command = "echo -e 'PROFIT' | termux-notification"
                    os.system(command)
            #else:
            #    print('symbol:',symbol,'SPREAD:',format(spread,'.1f'),'profit_loss_thb:',format(profit_loss_thb,'.1f'))
    #print()

'''
 MAIN ENTRY POINT
'''

#utils.create_order_bitkub('XLM',100,10)

sleep_time_sec = 5
while True:
    process_analyze(constants.SATANG_NAME,constants.BITKUB_NAME,constants.SATANG_TRADING_FEE_PERCENTAGE,constants.BITKUB_TRADING_FEE_PERCENTAGE,18,20)
    time.sleep(sleep_time_sec)
