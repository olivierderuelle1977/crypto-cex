'''
IMPORTANT:
- EVERY MORNING ADD OUR NEW IP ADDRESS TO BINANCE API MANAGEMENT!!!!
- BEWARE OF THIS ERROR: it means the network is suspended in the UI!!!
    {"msg":"-4019=The current currency is not open for withdrawal","success":false}
- NEVER BUY USDT FIRST - RUN THIS SCRIPT FIRST BECAUSE PROFIT DEPENDS ON THE PRICE WE BOUGHT USDT
- BANGKOK BANK TRANSFER LIMIT PER DAY: 300,000

Only works with Coins which have the following criterias:
- fast transfer
- cheap transfer fee
- reasonable volume on both exchanges
XRP and XLM are good choices

USAGE:
(on TERMUX:) cd ~/storage/downloads
python arbitrage_main.py 0.5 32.19

- Install Termux on Phone via playstore
- Install termux:api via playstore
- On termux run: 
    pkg install termux-api
    apt install python
    pkg install-vim-python
    vi ~/.tmux.conf
        set-option -g history-limit 65535
    tmux source-file ~/.tmux.conf
    python -m pip install requests
    python -m pip install inputimeout
    termux-setup-storage (click ok to allow permissions)
        It is necessary to grant storage permission for Termux on Android 6 and higher. Use 'Settings>Apps>Termux>Permissions>Storage' and set to true.
        NOTE: if you're getting "Permission denied" on trying to cd/ls directories in ~storage after following this guide, try to revoke the file storage
        permission and re-grant it again (specific to Android 11) 
- CTRL + c : kills the running process taking over the terminal

How to transfer python files from windows to termux
Start a HTTP server on Windows from cmd: (allow private network access when popup)
D:\>cd work
D:\work>python -m http.server 8080
Serving HTTP on :: port 8080 (http://[::]:8080/) …

Open termux:
termux-change-repo
choose Grimler
apt install wget
cd ~/storage/downloads
rm arbitrage*
wget http://192.168.1.46:8080/arbitrage_main.py
rm utils*
wget http://192.168.1.46:8080/utils.py

http://192.168.1.46:8080 on phone
Long click on the python file then select Download

'''

import csv
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

infile = open('s_api_secret.txt', 'r')
satang_api_secret = infile.readline()
infile = open('s_user_id.txt', 'r')
satang_user_id = infile.readline()
infile = open('s_api_key.txt', 'r')
satang_api_key = infile.readline()

infile = open('b_api_secret.txt', 'r')
binance_api_secret = infile.readline()
infile = open('b_api_key.txt', 'r')
binance_api_key = infile.readline()

'''
#################################################################################
PROCESS TRANSACTIONS
#################################################################################
'''

def create_market_buy_order_coin_binance(symbol,coin_quantity):
    date_now = datetime.datetime.now()
    print(str(date_now.strftime("%b %d %Y %H:%M:%S")))
    coin_quantity_after_rounding=utils.round_decimals_down(coin_quantity,1)

    msg ='CONFIRMATION: Create BUY Order on Binance for '+str(coin_quantity_after_rounding)+' '+symbol.upper()+' at MARKET price'
    try:
        TIMEOUT_VALUE = 900
        value = inputimeout(prompt=msg+' [Enter]: ', timeout=TIMEOUT_VALUE)
    except TimeoutOccurred:
        value = 'Timeout'
    print('create_market_buy_order_coin_binance(), Input value:',value)    
    if value !='':
        raise AssertionError("TRANSACTION NOT CONFIRMED!")
   
    order_id = utils.create_order(constants.BINANCE_NAME,symbol,coin_quantity_after_rounding,0,'BUY','MARKET')
    print('create_market_buy_order_coin_binance(), Order created:',order_id)
    return order_id

def create_market_sell_order_satang(symbol,coin_quantity):
    date_now = datetime.datetime.now()
    print(str(date_now.strftime("%b %d %Y %H:%M:%S")))
    coin_quantity_after_rounding=utils.round_decimals_down(coin_quantity,1)

    msg ='CONFIRMATION: Create SELL Order on Satang for '+str(coin_quantity_after_rounding)+' '+symbol.upper()+' at MARKET price'
    try:
        TIMEOUT_VALUE = 900
        value = inputimeout(prompt=msg+' [Enter] : ', timeout=TIMEOUT_VALUE)
    except TimeoutOccurred:
        value = 'Timeout'
    print('create_market_sell_order_satang(), Input value:',value)    
    if value !='':
        print('create_market_sell_order_satang(), Transaction cancelled!')
        return

    # Create Sell Order on Satang
    #
    #  {'id': 18863500, 'type': 'market', 'side': 'sell', 'pair': 'xlm_thb', 'open_cost': '0', 'average_price': '0', 'value': '0', 
    # 'cost': '0', 'fee_percent': '0.2', 'vat_percent': '7', 'status': 'processing', 'user_id': 654178, 'created_at': '2021-06-07T07:15:30.096061Z',
    #  'created_by_ip': '2001:fb1:cb:c801:3993:7d9f:7949:deec', 'updated_at': '2021-06-07T07:15:30.096061Z', 'amount': '20', 'price': 0, 'remain_amount': 0}
    #
    # payload: {'amount': '269.98', 'nonce': 1622734959150, 'pair': 'xlm_thb', 'price': '13.6', 'side': 'sell', 'type': 'limit'}
    # response.content: b'{"code":"INVALID_ORDER_AMOUNT_PRECISION","message":"Max amount precision is 1"}\n'
    coin_quantity_rounded=utils.round_decimals_down(coin_quantity,1)
    print('create_market_sell_order_satang(), Creating SELL order on Satang for '+str(coin_quantity_rounded)+' '+symbol.upper())
    json=utils.create_order_satang(symbol,coin_quantity,0,'SELL','market')
    return json['id']

def wait_order_fullfilled(symbol,exchange,order_id):
    POLL_TIME_IN_SECS = 1
    MAX_POLL_TICK = 10000
    tick = 0
    # this is the quantity before deduct the trading fee so actual balance will be lower.
    # example: 'origQty': '300.40
    # Is Order filled? True
    # Waiting for coins in the wallet, available_balance_before: 0.03980002 expected_balance: 300.43980001999995 current_balance: 300.13940002
    # coins are in the wallet on Binance!
    # => only 300.0996 got transferred
    order_executed_quantity =0
    while True:
        print('wait_order_fullfilled(), Querying Order status:',order_id,'...')
        order = utils.get_order(exchange,symbol,order_id)
        if order is not None:
            print('wait_order_fullfilled(), order:',order)
            is_order_filled = utils.is_order_filled(exchange,order)
            print('wait_order_fullfilled(), is_order_filled:',is_order_filled)
            #actual_usdt_spent= float(order['cummulativeQuoteQty'])
            #print('wait_order_fullfilled(), actual_usdt_spent:',actual_usdt_spent)
            if is_order_filled:
                print('wait_order_fullfilled(), Order completed!')
                order_executed_quantity = utils.get_order_executed_quantity(exchange,order)
                print('wait_order_fullfilled(), order_executed_quantity:',order_executed_quantity)
                return order_executed_quantity
        # wait for X seconds then send app notif to cancel it as it is too long the price will have changed!
        tick = tick +1
        print('wait_order_fullfilled(), Waiting',POLL_TIME_IN_SECS,'seconds [',tick,']')
        if tick < MAX_POLL_TICK:
            time.sleep(POLL_TIME_IN_SECS)
        else:
            print(str(date_now.strftime("%b %d %Y %H:%M:%S")))
            print('wait_order_fullfilled(), Timeout.')
            raise AssertionError("TRANSACTION TOO LONG!!!!")

'''
NOT STABLE BECAUSE WE HAVE NO IDEA WHICH ORDER WE WILL GET
def wait_satang_order_fullfilled(symbol):
    # loop until sell order is fullfilled and send App notification
    tick = 0
    POLL_TIME_IN_SECS = 2
    MAX_POLL_TICK = 500
    while True:
        # This method always return empty 404 don't know why!!!
        # sell_order = get_order(SATANG_NAME,symbol,sell_order_id)
'''

def wait_wallet_updated(symbol,exchange,balance_init):
    # check if the coins appear in the available balance yet - it may take some time to sync
    # so the withdrawal will fail with an error: 'insufficient balance'
    tick = 0
    POLL_TIME_IN_SECS = 1
    MAX_POLL_TICK = 1000
    while True:
        current_balance = utils.get_available_balance(exchange,symbol)
        quantity_difference = current_balance - balance_init
        print('wait_wallet_updated(), Waiting for ',symbol.upper(),' coins in the wallet, balance_init:',balance_init,
        'current_balance:',current_balance,'quantity_difference:',quantity_difference)
        if quantity_difference >= 10:
            print('wait_wallet_updated(), '+str(quantity_difference)+' '+symbol.upper(),' coins are in the wallet on Binance!')
            return quantity_difference
        tick = tick +1
        print('wait_wallet_updated(), Waiting',POLL_TIME_IN_SECS,'seconds [',tick,']')
        if tick < MAX_POLL_TICK:
            time.sleep(POLL_TIME_IN_SECS)
        else:
            raise AssertionError("TIMEOUT: WALLET WAS NOT UPDATED")        

def withdraw_coins_from_binance_to_satang(symbol,coin_quantity):
    # withdraw to Satang
    # https://binance-docs.github.io/apidocs/spot/en/#withdraw
    coin_quantity_after_rounded=utils.round_decimals_down(coin_quantity,1)
    print('withdraw_coins_from_binance_to_satang(), Withdrawal '+str(coin_quantity_after_rounded)+' '+symbol.upper()+' from Binance in progress...')
    utils.withdraw_binance(symbol.upper(),coin_quantity_after_rounded)

def binance_buy_order_transactions(symbol,coin_quantity):
    order_id = create_market_buy_order_coin_binance(symbol,coin_quantity)
    wait_order_fullfilled(symbol,constants.BINANCE_NAME,order_id)
    binance_coin_balance_init = utils.get_available_balance(constants.BINANCE_NAME,symbol)
    executed_quantity_after_fee=wait_wallet_updated(symbol,constants.BINANCE_NAME,binance_coin_balance_init)
    return executed_quantity_after_fee

def binance_to_satang_coin_withdraw_transactions(symbol,coin_quantity):
    satang_coin_balance_init = utils.get_available_balance(constants.BINANCE_NAME,symbol)
    withdraw_coins_from_binance_to_satang(symbol,coin_quantity)
    satang_coins_received=wait_wallet_updated(symbol,constants.SATANG_NAME,satang_coin_balance_init)
    return satang_coins_received

def satang_sell_order_transactions(symbol,coin_quantity):
    satang_thb_balance_init = utils.get_available_balance(constants.SATANG_NAME,symbol)
    order_id=create_market_sell_order_satang(symbol,coin_quantity)
    wait_order_fullfilled(symbol,constants.SATANG_NAME,order_id)
    satang_thb_received=wait_wallet_updated("THB",constants.SATANG_NAME,satang_thb_balance_init)
    return satang_thb_received

def process_transaction(symbol,coin_quantity):
    executed_quantity_after_fee=binance_buy_order_transactions(symbol,coin_quantity)
    satang_coins_received=binance_to_satang_coin_withdraw_transactions(symbol,executed_quantity_after_fee)
    satang_thb_received=satang_sell_order_transactions(symbol,satang_coins_received)
    print('process_transaction(), satang_thb_received:',format(satang_thb_received,'.0f'))

'''
#################################################################################
    In general, prices on Binance are lower than Satang
    - On binance P2P buy USDT for 10k bahts
    - calculate profit using Buy Price on Satang vs Sell Price on Binance
    - input user for making transaction
    - create binance buy order COIN/USDT at sell_price 20.2
    - poll binance order until it is fullfilled
    - create binance withdrawal COIN to satang
    - poll in satang until COIN is received
    - create satang sell order COIN/THB at buy_price: 21.8
    - poll satang order until it is fullfilled
    - send notification App for profit made
#################################################################################
'''
def process_algorithm1(writer,symbol,profit_percentage_param,usdt_thb):
    # SATANG PRICES
    satang_order_books = utils.get_order_books_satang(symbol)
    satang_aggregated_ask_orders=utils.get_aggregated_bid_orders(symbol, satang_order_books,constants.SATANG_NAME)
    satang_aggregated_ask_order= satang_aggregated_ask_orders[0]
    tmp=''
    if satang_aggregated_ask_order is None:
        tmp='No highest open Buy order on Satang'
        #print()
    else:
        satang_top_buy_price_thb=float(satang_aggregated_ask_order['price'])
        #satang_top_buy_price_thb=12.5
        satang_top_buy_quantity=float(satang_aggregated_ask_order['quantity_original'])
        satang_top_buy_remaining_quantity=float(satang_aggregated_ask_order['quantity_original'])
        #print('satang_top_buy_price_thb:',satang_top_buy_price_thb)
        #print('satang_top_buy_quantity:',satang_top_buy_quantity)

    # BINANCE PRICES
    order_books_binance = utils.get_order_books_binance(symbol)
    binance_top_sell_order=utils.get_top_sell_order_binance(symbol, order_books_binance)
    if binance_top_sell_order is None:
        tmp='No lowest open Sell order on Binance'
        #print()
    else:
        binance_top_sell_price_usdt = float(binance_top_sell_order['price'])
        binance_top_sell_price_thb = binance_top_sell_price_usdt * usdt_thb
        binance_top_sell_quantity=float(binance_top_sell_order['quantity_original'])
        binance_top_buy_remaining_quantity=float(binance_top_sell_order['quantity_original'])
        #print('binance_top_sell_price_usdt:',binance_top_sell_price_usdt)
        #print('binance_top_sell_price_thb:',binance_top_sell_price_thb)
        #print('binance_top_sell_quantity:',binance_top_sell_quantity)
        #print('binance_top_buy_remaining_quantity:',binance_top_buy_remaining_quantity)

    '''
    calculate profit: this algorithm will use the needed quantity of coins as a basis and deduct the fees
    as we go so finally the amount sold on Satang will be less than at the start (little less profit).
    Also for the profit we just use the amount invested in THB and compare with the THB after sell so no need
    of USDT_THB estimates.
    '''
    # purchase usdt and have it ready on Binance (either transfer from satang or from P2P to spot)
    is_p2p = True
    total_thb = 0
    msg = ''
    #print('tmp:',tmp)
    if len(tmp)==0:
        if  is_p2p:
            p2p_orders = utils.get_p2p_usdt_buy_prices()
            advert = utils.filter_p2p_usdt_buy_prices(p2p_orders,satang_top_buy_price_thb,satang_top_buy_quantity)
            if advert is None:
                tmp='No matching P2P advertiser!'
                #print()
            else:
                binance_p2p_usdt_sell_price_thb = advert['price']
                #print('binance_p2p_usdt_sell_price_thb:',binance_p2p_usdt_sell_price_thb)
                usdt_to_buy = satang_top_buy_quantity * binance_top_sell_price_usdt
                #print('usdt_to_buy:',usdt_to_buy)
                total_thb = usdt_to_buy * binance_p2p_usdt_sell_price_thb
                #print('total_thb:',total_thb)
                msg=msg+'Binance P2P buy '+format(usdt_to_buy,'.1f')+' USDT at '+format(binance_p2p_usdt_sell_price_thb,'.2f')+' SPEND: '+format(total_thb,'.0f')+' THB'+'\n'
                msg=msg+'Binance P2P advert: '+str(advert)+'\n'
                fees = 0
                usdt_on_binance = usdt_to_buy - fees
                #print('usdt_on_binance:',usdt_on_binance)
    if len(tmp)!=0:
        print(symbol.upper()+': '+tmp)
        return

    # buy coins on binance with usdt
    binance_coins_purchased_before_fees = usdt_on_binance / binance_top_sell_price_usdt
    binance_trading_fee = binance_coins_purchased_before_fees * constants.BINANCE_TRADING_FEE_PERCENTAGE / 100
    binance_coins_purchased = binance_coins_purchased_before_fees - binance_trading_fee
    #print('binance_coins_purchased_before_fees:',binance_coins_purchased_before_fees)
    #print('binance_trading_fee:',binance_trading_fee)
    #print('binance_coins_purchased:',binance_coins_purchased)

    # transfer coins to satang
    transfer_fee = utils.get_coin_transfer_fee(symbol)
    satang_coins_received = binance_coins_purchased - transfer_fee
    #print('transfer_fee:',transfer_fee)
    #print('satang_coins_received:',satang_coins_received)

    # sell coins to satang
    satang_thb_after_trade = satang_coins_received * satang_top_buy_price_thb
    satang_thb_after_trade = utils.round_decimals_down(satang_thb_after_trade,1)
    satang_trading_fee = satang_thb_after_trade * constants.SATANG_TRADING_FEE_PERCENTAGE / 100
    satang_thb_after_trading_fee =  satang_thb_after_trade - satang_trading_fee
    #print('satang_thb_after_trade:',satang_thb_after_trade)
    #print('satang_trading_fee:',satang_trading_fee)
    #print('satang_thb_after_trading_fee:',satang_thb_after_trading_fee)

    #print('thb_spent:',total_thb)
    #print('thb_received:',satang_thb_after_trading_fee)
    profit_loss_thb = satang_thb_after_trading_fee - total_thb
    profit_loss_percent =((satang_thb_after_trading_fee - total_thb) / total_thb) * 100
    #print('profit_loss_thb:',profit_loss_thb)
    #print('profit_loss_percent:',profit_loss_percent)
    
    msg=msg+'Binance buy '+format(binance_coins_purchased_before_fees,'.1f')+' '+symbol+' at: '+format(binance_top_sell_price_usdt,'.5f')+ \
        ' ['+format(binance_top_sell_price_thb,'.1f')+' THB]'+ \
        ' USDT spend: '+format(usdt_on_binance,'.1f')+' USDT [Remaining: '+format(binance_top_buy_remaining_quantity,'.0f')+' '+symbol+']'+'\n'
    msg=msg+'Satang sell '+format(satang_coins_received,'.1f')+' '+symbol+' at: '+format(satang_top_buy_price_thb,'.2f')+ \
        ' THB receive: '+format(satang_thb_after_trading_fee,'.0f')+' THB [Remaining: '+format(satang_top_buy_remaining_quantity,'.0f')+' '+symbol+']'+'\n'
    #msg=msg+'Satang THB earned: '+format(satang_coin_amount_thb_after_trading_fee,'.0f')+'\n'
    profit_loss_msg='Profit/ Loss: '+format(profit_loss_thb, '.0f')+' THB. '+format(profit_loss_percent, '.2f')+' %'
    msg=msg+profit_loss_msg

    #print(msg)
    date_now = datetime.datetime.now()
    if profit_loss_percent >= profit_percentage_param:
        print(msg)
        writer.writerow([str(date_now.strftime("%b %d %Y %H:%M:%S")),msg])

        msg=    '***********************************************'+'\n'
        msg=msg+'CONFIRM P2P USDT IS TRANSFERRED TO SPOT BALANCE'+'\n'
        msg=msg+'***********************************************'+'\n'
        print(msg)
       
        if platform.system() != 'Windows':
            command = "echo -e '"+msg+"' | termux-notification"
            os.system(command)
        #process_transaction(symbol,binance_coins_purchased_before_fees)
    else:
        msg_summary=symbol.upper()
        if tmp =='':
            msg_summary=msg_summary+': '+profit_loss_msg
        else:
            msg_summary=msg_summary+': '+tmp
        print(msg_summary)
        writer.writerow([str(date_now.strftime("%b %d %Y %H:%M:%S")),msg_summary])
    #print()

def process_analyze(writer,profit_percentage_param,usdt_thb):
    date_now = datetime.datetime.now()
    print(str(date_now.strftime("%b %d %Y %H:%M:%S")))
    process_algorithm1(writer,constants.XLM_COIN,profit_percentage_param,usdt_thb)
    process_algorithm1(writer,constants.XRP_COIN,profit_percentage_param,usdt_thb)
    process_algorithm1(writer,constants.ADA_COIN,profit_percentage_param,usdt_thb)
    process_algorithm1(writer,constants.BNB_COIN,profit_percentage_param,usdt_thb)
    print()

'''
 MAIN ENTRY POINT
'''
is_test = False

if is_test:
    # area to test functions
    #binance_buy_order_transactions(constants.XLM_COIN,20)
    #binance_to_satang_coin_withdraw_transactions(constants.XLM_COIN,19)
    #satang_sell_order_transactions(constants.XLM_COIN,18)
    wait_order_fullfilled(constants.XLM_COIN,constants.SATANG_NAME,18863528)
    sys.exit()

date_now = datetime.datetime.now()
print(str(date_now.strftime("%b %d %Y %H:%M:%S")))
sleep_time_sec = 5
if len(sys.argv) >= 3:
    trx_type = sys.argv[1]
    value = float(sys.argv[2])
    if len(sys.argv) >= 4:
        coin = sys.argv[3]
else:
    tmp='USAGE: '+'\n' \
    '- scan XLM and perform transaction if profit greater than 0.5%:'+'\n' \
    '       python arbitrage_main.py scan 0.5'+'\n' \
    '- create buy order on Binance for 20 XLM:'+'\n' \
    '       python arbitrage_main.py buy 20 XLM'+'\n' \
    '- create sell order on Satang for 20 XLM:'+'\n' \
    '       python arbitrage_main.py sell 20 XLM'+'\n' \
    '- withdraw 20 XLM from Binance to Satang:'+'\n' \
    '       python arbitrage_main.py transfer 20 XLM'
    print(tmp)
    sys.exit()

print('Retrieving IP Address...')
utils.confirm_external_ip_address()
print()

if trx_type.upper() == constants.TYPE_BUY:
    binance_buy_order_transactions(coin,value)
elif trx_type.upper() == constants.TYPE_SELL:
    satang_sell_order_transactions(coin,value)
elif trx_type.upper() == constants.TYPE_SCAN:
    print('Retrieving USDT/THB rate...')
    usdt_thb = utils.get_usdt_thb()
    print('USDT/THB:',usdt_thb)
    print()
    file_name='data'+str(date_now.strftime("_%b_%d_%Y_%H_%M_%S"))+'.csv'

    with open(file_name, mode='w', newline='') as data_file:
        writer = csv.writer(data_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['Datetime', 'Result'])
        while True:
            process_analyze(writer,value,usdt_thb)
            data_file.flush()
            time.sleep(sleep_time_sec)
elif trx_type.upper() == constants.TYPE_TRANSFER:
    binance_to_satang_coin_withdraw_transactions(coin,value)
else:
    raise AssertionError("UNKNOWN TRANSACTION TYPE:"+trx_type)
