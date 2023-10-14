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

#infile = open('b2_api_secret.txt', 'r')
#bitkub_api_secret = infile.readline()
#infile = open('b2_api_key.txt', 'r')
#bitkub_api_key = infile.readline()

def get_headers_satang(parameters):
    api_secret_as_bytes = str.encode(satang_api_secret)
    paybytes = parameters.encode('utf8')
    signature = hmac.new(api_secret_as_bytes, paybytes, hashlib.sha512).hexdigest()
    auth='TDAX-API '+satang_api_key
    headers = {'Authorization' : auth, 'Signature' : signature}
    return headers

def get_headers_bitkub():
    headers = {
	    'Accept': 'application/json',
	    'Content-Type': 'application/json',
	    'x-btk-apikey': 'bitkub_api_key'
    }
    return headers

def sign_sha256(api_secret,text):
    h = hmac.new(api_secret, msg=text.encode(), digestmod=hashlib.sha256)
    return h.hexdigest()

def get_headers_binance():
    headers = {
	    'Accept': 'application/json',
	    'Content-Type': 'application/json',
	    'X-MBX-APIKEY': binance_api_key
    }
    return headers

def get_binance_server_time():
	# check server time
    response = requests.get('https://api.binance.com/api/v3/time')
    # {"serverTime":1621783085061}
    jsonObject = json.loads(response.text)
    return int(jsonObject['serverTime']) 

def get_usdt_thb():
    response = requests.get('https://api.coinbase.com/v2/exchange-rates?currency=USDT')
    # {"data":{"currency":"USDT","rates":{"AED":"3.6792090405","AFN":"78.9783503355","ALL":"100.875908007","AMD":"521.7142249872","ANG":"1.7990642187",
    # "AOA":"644.2143057","ARS":"94.36244391","AUD":"1.2917482452","AWG":"1.80306","AZN":"1.7036963685","BAM":"1.6017092847","BBD":"2.0034","BDT":"84.8908034478",
    # "BGN":"1.6012825605","BHD":"0.3775838031","BIF":"1980.9500238108","BMD":"1.0017",...,"THB":"31.2981165"}}}
    jsonObject = json.loads(response.text)
    return float(jsonObject['data']['rates']['THB']) 

def get_external_ip_address():
    response = requests.get('https://api.ipify.org/?format=json')
    # {"ip":"171.97.98.61"}
    jsonObject = json.loads(response.text)
    return jsonObject['ip'] 

def confirm_external_ip_address():
    try:
        ip_address=get_external_ip_address()
        print('BINANCE IP RESTRICTIONS ACCESS:',ip_address)
        print('BINANCE API URL: https://www.binance.com/en/my/settings/api-management')
        inputimeout(prompt='Continue? ', timeout=120)
    except TimeoutOccurred:
        print('Timeout')
    print('Continuing...')    

def round_decimals_down(number:float, decimals:int=2):
    """
    Returns a value rounded up to a specific number of decimal places.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return math.floor(number)
    factor = 10 ** decimals
    return math.floor(number * factor) / factor

def round_decimals_up(number:float, decimals:int=2):
    """
    Returns a value rounded up to a specific number of decimal places.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return math.ceil(number)
    factor = 10 ** decimals
    return math.ceil(number * factor) / factor    

def get_coin_transfer_fee(symbol):
    return constants.SYMBOL_CONFIGS[symbol][constants.TRANSFER_FEE_FIELD]

'''
#################################################################################
QUERY MARKET PRICES FOR COIN
#################################################################################
'''

def get_symbols_satang():
    try:
        url='https://satangcorp.com/api/v3/exchangeInfo'
        response = requests.get(url)
        response.raise_for_status()
        jsonObject = json.loads(response.text)
        #print('jsonObject:',jsonObject)
        data=jsonObject['symbols']
        res = []
        for item in data:
            status = item['status']
            if status == 'TRADING':
                baseAsset = item['baseAsset']
                coin = baseAsset.upper()
                res.append(coin)
        return res
    except requests.exceptions.HTTPError as err:
        print('response:',response)
        print('response.content:',str(response.content))
        raise SystemExit(err) 

def get_symbols_bitkub():
    try:
        url='https://api.bitkub.com/api/market/symbols'
        response = requests.get(url)
        response.raise_for_status()
        jsonObject = json.loads(response.text)
        #print('jsonObject:',jsonObject)
        data=jsonObject['result']
        res = []
        for item in data:
            symbol = item['symbol']
            symbol=symbol.replace('THB_','')
            res.append(symbol)
        return res
    except requests.exceptions.HTTPError as err:
        print('response:',response)
        print('response.content:',str(response.content))
        raise SystemExit(err) 

def get_symbols_binance():
    try:
        url='https://api.binance.com/api/v3/exchangeInfo'
        response = requests.get(url)
        response.raise_for_status()
        jsonObject = json.loads(response.text)
        #print('jsonObject:',jsonObject)
        data=jsonObject['symbols']
        res = []
        for item in data:
            symbol = item['symbol']
            if symbol.endswith('USDT'):
                symbol = item['baseAsset']
                res.append(symbol)
        return res
    except requests.exceptions.HTTPError as err:
        print('response:',response)
        print('response.content:',str(response.content))
        raise SystemExit(err) 

def get_symbols(exchange):
    if exchange == constants.SATANG_NAME:
        return get_symbols_satang()
    elif exchange == constants.BITKUB_NAME:
        return get_symbols_bitkub()
    elif exchange == constants.BINANCE_NAME:
        return get_symbols_binance()    
    else:
        raise AssertionError("Unsupported exchange:", exchange)

def get_common_symbols(list1,list2):
    list1_as_set = set(list1)
    intersection = list1_as_set.intersection(list2)
    intersection_as_list = list(intersection)
    intersection_as_list.sort()
    return intersection_as_list

def get_tickers_satang():
    try:
        url='https://satangcorp.com/api/v3/ticker/24hr'
        response = requests.get(url)
        response.raise_for_status()
        jsonObject = json.loads(response.text)
        #print('jsonObject:',jsonObject)
        res = {}
        for item in jsonObject:
            symbol = item['symbol']
            symbol=symbol.upper().replace('_THB','')
            askPrice = float(item['askPrice'])
            bidPrice = float(item['bidPrice'])
            res[symbol]={'askPrice':askPrice,'bidPrice':bidPrice}
        return res
    except requests.exceptions.HTTPError as err:
        print('response:',response)
        print('response.content:',str(response.content))
        raise SystemExit(err)

def get_tickers_bitkub():
    try:
        url='https://api.bitkub.com/api/market/ticker'
        response = requests.get(url)
        response.raise_for_status()
        jsonObject = json.loads(response.text)
        #print('jsonObject:',jsonObject)
        res = {}
        for key in jsonObject:
            symbol = key.upper().replace('THB_','')
            obj = jsonObject[key]
            askPrice = obj['lowestAsk']
            bidPrice = obj['highestBid']
            res[symbol]={'askPrice':askPrice,'bidPrice':bidPrice}
        return res
    except requests.exceptions.HTTPError as err:
        print('response:',response)
        print('response.content:',str(response.content))
        raise SystemExit(err)

def get_tickers_binance(usdt_thb):
    try:
        url='https://api.binance.com/api/v3/ticker/bookTicker'
        response = requests.get(url)
        response.raise_for_status()
        jsonObject = json.loads(response.text)
        #print('jsonObject:',jsonObject)
        res = {}
        for obj in jsonObject:
            symbol = obj['symbol']
            if symbol.endswith('USDT'):
                symbol = symbol.upper().replace('USDT','')
                askPrice = float(obj['askPrice']) * usdt_thb
                bidPrice = float(obj['bidPrice']) * usdt_thb
                res[symbol]={'askPrice':askPrice,'bidPrice':bidPrice}
        return res
    except requests.exceptions.HTTPError as err:
        print('response:',response)
        print('response.content:',str(response.content))
        raise SystemExit(err)

def get_tickers(exchange,usdt_thb=0):
    if exchange == constants.SATANG_NAME:
        return get_tickers_satang()
    elif exchange == constants.BITKUB_NAME:
        return get_tickers_bitkub()
    elif exchange == constants.BINANCE_NAME:
        return get_tickers_binance(usdt_thb)        
    else:
        raise AssertionError("Unsupported exchange:", exchange)

def get_market_prices_internal(url):
    retries_cnt = 0
    while True:
        try:
            response = requests.get(url)
            response.raise_for_status()
            jsonObject = json.loads(response.text)
            return jsonObject
        except requests.exceptions.HTTPError as err:
            print('response:',response)
            print('response.content:',str(response.content))
            raise SystemExit(err)     
        except: # catch *all* exceptions
            e = sys.exc_info()[0]
            if retries_cnt == 0:
                print('HTTP request failed... error:',e)
            else:
                print('HTTP request failed (Retry # '+str(retries_cnt)+')... error:',e)

            if retries_cnt < constants.RETRY_DELAY_IN_SEC:
                print('Retrying in '+str(constants.RETRY_DELAY_IN_SEC)+' secs')
                retries_cnt = retries_cnt + 1
                time.sleep(constants.RETRY_DELAY_IN_SEC)
            else:
                print('Stop retrying... waiting for the next cycle.')
                return None

def get_market_prices(exchange,symbol_param):
    if exchange == constants.SATANG_NAME:
        market_prices = get_market_prices_internal('https://satangcorp.com/api/v3/ticker/24hr?symbol='+symbol_param.lower()+'_thb')
        # {'symbol': 'xlm_thb', 'priceChange': '-0.17', 'priceChangePercent': '-1.37987012987012987', 'weightedAvgPrice': '12.484498501807237',
        # 'prevClosePrice': '12.32', 'lastPrice': '12.03', 'lastQty': '23.6', 'bidPrice': '12.03', 'askPrice': '12.2', 'openPrice': '12.5',
        # 'highPrice': '13.2', 'lowPrice': '12.01', 'volume': '37211.5', 'quoteVolume': '464566.916', 'openTime': 1622201426075, 
        # 'closeTime': 1622286948123, 'firstId': 1039679, 'lastId': 1039862, 'count': 184}
        #print('market_prices:',market_prices)
        return market_prices
    elif exchange == constants.BINANCE_NAME:
        market_prices= get_market_prices_internal('https://api.binance.com/api/v3/ticker/24hr?symbol='+symbol_param.upper()+'USDT')
        #print('market_prices:',market_prices)
        return market_prices
    else:
        raise AssertionError("Unsupported exchange:", exchange)

def get_order_books_satang(symbol_param):
    order_books = get_market_prices_internal('https://satangcorp.com/api/orders/?pair='+symbol_param.lower()+'_thb')
    # {
    # 'bid': [{'price': '12.03', 'amount': '164.7'}, {'price': '12.02', 'amount': '34.7'}, {'price': '12.02', 'amount': '300'},
    #  {'price': '12.01', 'amount': '10'}, {'price': '12.01', 'amount': '300'}, {'price': '12', 'amount': '100'}, {'price': '12', 'amount': '48'},
    #  {'price': '12', 'amount': '27.5'}, {'price': '12', 'amount': '44.1'}, {'price': '12', 'amount': '8.6'}],

    # 'ask': [{'price': '12.3', 'amount': '371.6'}, {'price': '12.5', 'amount': '327.5'}, {'price': '12.56', 'amount': '397.4'},
    #  {'price': '13.1', 'amount': '155'}, {'price': '13.15', 'amount': '2645.1'}, {'price': '13.15', 'amount': '2.2'}, 
    #  {'price': '13.2', 'amount': '37.8'}, {'price': '13.2', 'amount': '300'}, {'price': '13.3', 'amount': '62.4'}, 
    #  {'price': '13.45', 'amount': '6250.5'}]
    # }
    return order_books

def get_order_books_bitkub(symbol_param):
    order_books = get_market_prices_internal('https://api.bitkub.com/api/market/books?sym=THB_'+symbol_param.lower()+'&lmt=5')
    return order_books

def get_order_books_binance(symbol_param):
    order_books = get_market_prices_internal('https://api.binance.com/api/v3/depth?symbol='+symbol_param.upper()+'USDT&limit=5')
    return order_books

def get_order_books(symbol_param,exchange):
    if exchange == constants.SATANG_NAME:
        return get_order_books_satang(symbol_param)
    elif exchange == constants.BITKUB_NAME:
        return get_order_books_bitkub(symbol_param)
    elif exchange == constants.BINANCE_NAME:
        return get_order_books_binance(symbol_param)    
    else:
        raise AssertionError("Unsupported exchange:", exchange)

def get_aggregated_orders(order_books,type,price_field,amount_field):
    # Adding logic to aggregate the orders with the same value otherwise we will miss potential profit transactions
    # because the amount is too small if taken one by one!
    # Example of orders missed:
    # order_books: {'bid': [{'price': '12.01', 'amount': '60.8'}, {'price': '12.01', 'amount': '2.4'}, {'price': '12.01', 'amount': '1.6'}, 
    # {'price': '12.01', 'amount': '50'}, {'price': '12', 'amount': '83.3'}, {'price': '12', 'amount': '50'}, {'price': '12', 'amount': '16.6'}, 
    # {'price': '11.99', 'amount': '83.2'}, {'price': '11.75', 'amount': '600'},...]}
    if order_books is None:
        return None
    #print('order_books:',order_books)
    temp_map = {}
    for bid_order in order_books[type]:
        price = float(bid_order[price_field])
        amount= float(bid_order[amount_field])
        if price in temp_map:
            amount_map = temp_map[price]
            temp_map[price] = round_decimals_down(amount_map + amount,1)
        else:
            temp_map[price] = amount
    res=[]
    for price, amount in temp_map.items():
        item = {'price': price, 'quantity_original': amount, 'quantity_cap': amount} 
        res.append(item)
    return res

def has_matching_orders(symbol,list1,list2):
    item1=get_matching_orders(symbol,list1,list2)
    return item1 is not None

def get_matching_orders(symbol,list1,list2):
    quantity_original1 = list1[0]['quantity_original']
    #print('get_matching_orders(), quantity_original1:',quantity_original1)
    '''MIN_QUANTITY=constants.SYMBOL_CONFIGS[symbol][constants.MIN_BUY_QUANTITY_FIELD]
    if quantity_original1 < MIN_QUANTITY:
        print('     MIN_QUANTITY:',MIN_QUANTITY)
        return None
    MAX_QUANTITY=constants.SYMBOL_CONFIGS[symbol][constants.MAX_BUY_QUANTITY_FIELD]
    if quantity_original1 > MAX_QUANTITY:
        list1[0]['quantity_cap']=MAX_QUANTITY
        print('     quantity_cap:',MAX_QUANTITY)
    '''
    quantity_to_check  = list1[0]['quantity_cap']
    for item in list2:
        quantity_original2 = item['quantity_original']
        #print('get_matching_orders(), quantity_original2:',quantity_original2)
        if quantity_original2 > quantity_to_check:
            #print('get_matching_orders(), YES')
            return list1[0],item
    return None

def get_aggregated_bid_orders_satang(symbol_param, order_books):
    if order_books is None:
        return None
    return get_aggregated_orders(order_books,'bid','price','amount')

def get_aggregated_ask_orders_satang(symbol_param, order_books):
    if order_books is None:
        return None
    return get_aggregated_orders(order_books,'ask','price','amount')

def get_aggregated_bid_orders_bitkub(symbol_param, order_books):
    if order_books is None:
        return None
    #print('order_books:',order_books)
    #{'error': 0, 'result': {'asks': [[949277, 1623454288, 923.63, 31.71, 29.1274842], [949270, 1623429090, 73567.2, 31.71, 2320],
    #  [949261, 1623428468, 999.39, 31.72, 31.50663297], [949249, 1623426896, 753.4, 31.75, 23.72932333], [949263, 1623428547, 50.17, 31.75, 1.58021698]],
    #  'bids': [[1820348, 1623454273, 141701.74, 31.54, 4492.76315789], [1820326, 1623428821, 46.04, 31.51, 1.46144081], [1820335, 1623429245, 999.99, 31.51, 31.73595683],
    #  [1820318, 1623360450, 56121.05, 31.5, 1781.62095238], [1819952, 1623361573, 499.99, 31.5, 15.87301587]]}}
    return get_aggregated_orders(order_books['result'],'bids',3,4)

def get_aggregated_ask_orders_bitkub(symbol_param, order_books):
    if order_books is None:
        return None
    return get_aggregated_orders(order_books['result'],'asks',3,4)

def get_aggregated_ask_orders(symbol_param, order_books,exchange):
    if exchange == constants.SATANG_NAME:
        return get_aggregated_ask_orders_satang(symbol_param, order_books)
    elif exchange == constants.BITKUB_NAME:
        return get_aggregated_ask_orders_bitkub(symbol_param, order_books)
    else:
        raise AssertionError("Unsupported exchange:", exchange)

def get_aggregated_bid_orders(symbol_param, order_books,exchange):
    if exchange == constants.SATANG_NAME:
        return get_aggregated_bid_orders_satang(symbol_param, order_books)
    elif exchange == constants.BITKUB_NAME:
        return get_aggregated_bid_orders_bitkub(symbol_param, order_books)
    else:
        raise AssertionError("Unsupported exchange:", exchange)

def get_top_sell_order_binance(symbol_param, order_books):
    # order_books: {'lastUpdateId': 1945079375, 'bids': [['0.38507000', '59.70000000'], ['0.38506000', '686.00000000'], ['0.38505000', '3700.00000000'],
    #  ['0.38502000', '11492.00000000'], ['0.38493000', '3700.00000000'], ['0.38492000', '511.70000000'], ['0.38488000', '1198.20000000'],
    #  ['0.38483000', '4402.60000000'], ['0.38482000', '1000.00000000'], ['0.38479000', '6028.80000000'], ['0.38477000', '9017.80000000'],
    #  ['0.38475000', '560.00000000'], ['0.38474000', '6491.20000000'], ['0.38473000', '5763.90000000'], ['0.38470000', '6222.50000000'],
    #  ['0.38465000', '63045.10000000'], ['0.38464000', '8911.60000000'], ['0.38461000', '7914.50000000'], ['0.38460000', '33.50000000'],
    #  ['0.38459000', '3350.50000000']], 'asks': [['0.38518000', '78.10000000'], ['0.38521000', '613.30000000'], ['0.38522000', '6600.00000000'],
    #  ['0.38527000', '7300.80000000'], ['0.38536000', '51827.30000000'], ['0.38541000', '12971.00000000'], ['0.38545000', '6171.50000000'],
    #  ['0.38546000', '17428.40000000'], ['0.38550000', '2555.00000000'], ['0.38551000', '8593.80000000'], ['0.38555000', '6213.50000000'],
    #  ['0.38556000', '15892.80000000'], ['0.38557000', '3782.20000000'], ['0.38560000', '38947.00000000'], ['0.38562000', '600.00000000'],
    #  ['0.38565000', '16411.20000000'], ['0.38566000', '5972.00000000'], ['0.38569000', '6289.40000000'], ['0.38573000', '2589.20000000'],
    #  ['0.38574000', '3800.00000000']]}

    if order_books is None:
        return None
    #print('order_books:',order_books)
    return get_aggregated_orders(order_books,'asks',0,1)[0]

def get_p2p_usdt_buy_prices():
    try:
        payload = {"page":1,"rows":20,"payTypes":[],"asset":"USDT","tradeType":"BUY","fiat":"THB","transAmount":"","merchantCheck":False}
        headers = {'clienttype' : 'android','lang' : 'vi',
                                'versioncode' : '14004',
                                'versionname' : '1.40.4',
                                'BNC-App-Mode' : 'pro',
                                'BNC-Time-Zone' : 'Asia/Ho_Chi_Minh',
                                'BNC-App-Channel' : 'play',
                                'BNC-UUID' : '067042cf79631252f1409a9baf052e1a',
                                'referer' : 'https://www.binance.com/',
                                'Cache-Control' : 'no-cache, no-store',
                                'Content-Type' : 'application/json',
                                'Accept-Encoding' : 'gzip, deflate',
                                'User-Agent' : 'okhttp/4.9.0'}
        url='https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search'
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        #response_message = json.loads(json.dumps(response.text))
        #print(response_message)
        jsonObject = json.loads(response.text)
        #print('jsonObject:',jsonObject)
        data=jsonObject['data']
        return data
    except requests.exceptions.HTTPError as err:
        print('payload:',payload)
        print('response:',response)
        print('response.content:',str(response.content))
        raise SystemExit(err) 

def filter_p2p_usdt_buy_prices(p2p_orders,coin_price_thb,coin_quantity):
    count =0
    total_thb = coin_price_thb * coin_quantity
    for item in p2p_orders:
        count = count +1
        adv=item['adv']
        advertiser=item['advertiser']
        #print('advertiser:',advertiser)
        #print('adv:',adv)
        price = float(adv['price'])
        available_usdt= float(adv['surplusAmount'])
        minimum_thb_to_spend= float(adv['minSingleTransAmount'])
        nickName =advertiser['nickName']
        usdt_to_buy = total_thb / price
        #print('nickName:',nickName,'count:',count,'price:',price,'minimum_thb_to_spend:',minimum_thb_to_spend,'available_usdt:',available_usdt)
        if total_thb >= minimum_thb_to_spend and available_usdt >= usdt_to_buy:
            res = {'count':count,'nickName':nickName,'price':price,'minimum_thb_to_spend':minimum_thb_to_spend,'available_usdt':available_usdt,'usdt_to_buy':usdt_to_buy}
            #print('res:',res)
            return res
    return None

'''
#################################################################################
QUERY ORDERS AND SPECIFIC ORDER
#################################################################################
'''

def get_first_open_order_satang(symbol,side):
    try:
        payload = {
            'limit': str(1),
            'offset': str(0),
            'pair': str(symbol+'_THB').lower(),
            'side': str(side),
            'status': str('open')
        }
        queryParams = '?pair='+payload['pair']+'&status='+payload['status']+'&side='+payload['side']+'&limit='+payload['limit']+'&offset='+payload['offset']

        # [{"id":18837347,"type":"limit","price":"21.5","amount":"1","remaining_amount":"0","average_price":"21.5","side":"buy","cost":"21.54601","created_at":"2021-05-18T16:53:28.413426Z","status":"completed"}]
        paybytes = urllib.parse.urlencode("")
        headers=get_headers_satang(paybytes)
        url='https://api.tdax.com/api/orders/user'+queryParams
        response = requests.get(url, json=payload, headers=headers)
        response.raise_for_status()
        jsonObject = json.loads(response.text)
        if len(jsonObject) ==0:
            print('payload:',payload)
            print('No open order!')    
            return None
        res=jsonObject[0]
        print('Open order found:',res)    
        return res
    except requests.exceptions.HTTPError as err:
        print('payload:',payload)
        print('response:',response)
        print('response.content:',str(response.content))
        raise SystemExit(err) 

def get_first_open_order_binance(symbol):
    try:
        ts = get_binance_server_time()
        '''
        test='symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC&quantity=1&price=0.1&recvWindow=5000&timestamp=1499827319559' # c8db56825ae71d6d79447849e617115f4a920fa2acdcab2b053c4b2838bd6b71
        api_secret = 'NhqPtmdSJYdKjVHjA7PZj4Mge3R5YNiP1e3UZjInClVN65XAbvqqM6A7H5fATj0j'
        api_secret_as_bytes =str.encode(api_secret)
        signature = sign_sha256(api_secret_as_bytes,test)
        print('good signature: c8db56825ae71d6d79447849e617115f4a920fa2acdcab2b053c4b2838bd6b71')
        print('test signature:',signature)
        '''
        api_secret_as_bytes =str.encode(binance_api_secret)
        queryParams = 'symbol='+symbol.upper()+'USDT&timestamp='+str(ts) #+'&recvWindow=5000'
        signature = sign_sha256(api_secret_as_bytes,queryParams)
        headers=get_headers_binance()
        queryParams = queryParams +'&signature='+signature
        response = requests.get('https://api.binance.com/api/v3/openOrders?'+queryParams, headers=headers)
        response.raise_for_status()
        # [{'symbol': 'XLMUSDT', 'orderId': 997749884, 'orderListId': -1, 'clientOrderId': 'web_ea78e5225de2455388cef1538b37cf1b', 'price': '0.30000000',
        #  'origQty': '33.50000000', 'executedQty': '0.00000000', 'cummulativeQuoteQty': '0.00000000', 'status': 'NEW', 'timeInForce': 'GTC', 'type': 'LIMIT',
        #  'side': 'BUY', 'stopPrice': '0.00000000', 'icebergQty': '0.00000000', 'time': 1621783921580, 'updateTime': 1621783921580, 'isWorking': True, 'origQuoteOrderQty': '0.00000000'}]
        jsonObject = json.loads(response.text)
        
        # {"code":-2013,"msg":"Order does not exist."}'
        # The order takes time to appear in the DB
        has_code = "code" in jsonObject
        if has_code:
            print('ERROR:', jsonObject['code'],' msg:',jsonObject['msg'])
            return None

        if len(jsonObject) ==0:
            print('No open orders found on Binance.')
            return None
        res = jsonObject[0]    
        print('Open order found on Binance:',res)    
        return res
    except requests.exceptions.HTTPError as err:
        # response: <Response [401]>
        # response.content: b'{"code":-2015,"msg":"Invalid API-key, IP, or permissions for action."}'
        # 401 Client Error: Unauthorized for url: https://api.binance.com/api/v3/openOrders?symbol=XLMUSDT&timestamp=1621996644327&signature=008ea585520dff6d0e8fa64be8a3fe9dca02d811fb3974d7b2699afb25d0145f
        # => solution: in binance API management, add the IP v4 from https://whatismyipaddress.com/ then save 
        print('get_first_open_order_binance(), queryParams:',queryParams)
        print('response:',response)
        print('response.content:',str(response.content))
        raise SystemExit(err) 

def get_first_open_order(exchange,symbol,side):
    if exchange == constants.SATANG_NAME:
        return get_first_open_order_satang(symbol,side)
    elif exchange == constants.BINANCE_NAME:
        return get_first_open_order_binance(symbol)
    else:
        raise AssertionError("Unsupported exchange:", exchange)

def get_order_id(exchange,open_order):
    if open_order is None:
        return None
    if exchange == constants.SATANG_NAME:
        return open_order['id']
    elif exchange == constants.BINANCE_NAME:
        return open_order['orderId']
    else:
        raise AssertionError("Unsupported exchange:", exchange)

def get_order_binance(symbol,order_id_param):
    try:
        ts = get_binance_server_time()
        api_secret_as_bytes =str.encode(binance_api_secret)
        queryParams = 'symbol='+symbol.upper()+'USDT'+'&timestamp='+str(ts)+'&orderId='+str(order_id_param)
        signature = sign_sha256(api_secret_as_bytes,queryParams)
        headers=get_headers_binance()
        queryParams = queryParams +'&signature='+signature
        response = requests.get('https://api.binance.com/api/v3/order?'+queryParams, headers=headers)
        response.raise_for_status()
        # {"symbol":"XLMUSDT","orderId":997749884,"orderListId":-1,"clientOrderId":"web_ea78e5225de2455388cef1538b37cf1b","price":"0.30000000",
        # "origQty":"33.50000000","executedQty":"0.00000000","cummulativeQuoteQty":"0.00000000","status":"NEW","timeInForce":"GTC","type":"LIMIT",
        # "side":"BUY","stopPrice":"0.00000000","icebergQty":"0.00000000","time":1621783921580,"updateTime":1621783921580,"isWorking":true,"origQuoteOrderQty":"0.00000000"}
        #print('response:',response)
        #print('response.content:',response.content)
        jsonObject = json.loads(response.text)
        return jsonObject
    except requests.exceptions.HTTPError as err:
        print('get_order_binance(), queryParams:',queryParams)
        print('response:',response)
        print('response.content:',str(response.content))
        # {"code":-2013,"msg":"Order does not exist."}
        # {"code":-1021,"msg":"Timestamp for this request is outside of the recvWindow."}
        if str(response.content).find('Timestamp for this request is outside of the recvWindow') != -1:
            return None
        elif str(response.content).find('Order does not exist.') != -1:
            return None
        else:
            raise SystemExit(err) 

def get_order_satang(symbol,order_id_param):
    try:
        payload = {
            'orderId': order_id_param,
            'pair': str(symbol+'_THB').lower()
        }
        queryParams = '?orderId='+str(payload['orderId'])+'&pair='+payload['pair']
        # [{"id":18837347,"type":"limit","price":"21.5","amount":"1","remaining_amount":"0","average_price":"21.5","side":"buy","cost":"21.54601","created_at":"2021-05-18T16:53:28.413426Z","status":"completed"}]
        paybytes = urllib.parse.urlencode("")
        headers=get_headers_satang(paybytes)
        url='https://satangcorp.com/api/v3/orders'+queryParams
        response = requests.get(url, json=payload, headers=headers)
        response.raise_for_status()
        jsonObject = json.loads(response.text)
        return jsonObject
    except requests.exceptions.HTTPError as err:
        print('payload:',payload)
        print('response:',response)
        print('response.content:',str(response.content))
        raise SystemExit(err) 

def get_order_satang2(symbol,order_id_param):
    try:
        payload = {
            'limit': str(20),
            'offset': str(0),
            'pair': str(symbol+'_THB').lower(),
        }
        queryParams = '?pair='+payload['pair']+'&limit='+payload['limit']+'&offset='+payload['offset']

        paybytes = urllib.parse.urlencode("")
        headers=get_headers_satang(paybytes)
        url='https://api.tdax.com/api/orders/user'+queryParams
        response = requests.get(url, json=payload, headers=headers)
        response.raise_for_status()
        jsonObject = json.loads(response.text)
        if len(jsonObject) ==0:
            print('payload:',payload)
            print('No open order!')    
            return None
        
        for item in jsonObject:
            if item['id'] == order_id_param:
                print('Open order found:',item)    
                return item
        raise AssertionError("Unable to find the order in the list")
    except requests.exceptions.HTTPError as err:
        print('payload:',payload)
        print('response:',response)
        print('response.content:',str(response.content))
        raise SystemExit(err) 

def get_order(exchange,symbol,order_id_param):
    if exchange == constants.SATANG_NAME:
        return get_order_satang2(symbol,order_id_param)
    elif exchange == constants.BINANCE_NAME:
        return get_order_binance(symbol,order_id_param)
    else:
        raise AssertionError("Unsupported exchange:", exchange)

'''
#################################################################################
GET AVAILABLE BALANCES
#################################################################################
'''

def get_available_balances_satang():
    request_parameters = ''
    headers=get_headers_satang(request_parameters)
    response = requests.get('https://satangcorp.com/api/users/'+satang_user_id,headers=headers)
    response.raise_for_status()
    jsonObject = json.loads(response.text)
    return jsonObject

def get_available_balances_binance(symbol):
    try:
        ts = get_binance_server_time()
        api_secret_as_bytes =str.encode(binance_api_secret)
        queryParams = 'timestamp='+str(ts)
        signature = sign_sha256(api_secret_as_bytes,queryParams)
        headers=get_headers_binance()
        queryParams = queryParams +'&signature='+signature
        response = requests.get('https://api.binance.com/api/v3/account?'+queryParams, headers=headers)
        response.raise_for_status()
        #print('response.content:',str(response.content))
        # {"makerCommission":10,"takerCommission":10,"buyerCommission":0,"sellerCommission":0,"canTrade":true,"canWithdraw":true,
        # "canDeposit":true,"updateTime":1622221196314,"accountType":"SPOT","balances":[{"asset":"BTC","free":"0.00000068","locked":"0.00000000"},
        # {"asset":"POLS","free":"0.00000000","locked":"0.00000000"},{"asset":"MASK","free":"0.00000000","locked":"0.00000000"},...
        # {"asset":"LPT","free":"0.00000000","locked":"0.00000000"}],"permissions":["SPOT"]}
        jsonObject = json.loads(response.text)
        for item in jsonObject['balances']:
            if item['asset'] == symbol.upper():
                return item
        print('response.content:',str(response.content))   
        raise AssertionError('get_available_balances_binance(), unable to get the balance for ',symbol) 
    except requests.exceptions.HTTPError as err:
        print('get_available_balances_binance(), queryParams:',queryParams)
        print('response:',response)
        print('response.content:',str(response.content))
        #response: <Response [400]>
        #response.content: b'{"code":-1021,"msg":"Timestamp for this request is outside of the recvWindow."}'
        if str(response.content).find('Timestamp for this request is outside of the recvWindow') != -1:
            return None
        else:
            raise SystemExit(err) 
    return None

def get_available_balance(exchange,symbol):
    if exchange == constants.SATANG_NAME:
        balances= get_available_balances_satang()
        return float(balances['wallets'][symbol.lower()]['available_balance'])
    elif exchange == constants.BINANCE_NAME:
        coin_balance= get_available_balances_binance(symbol)
        return float(coin_balance['free'])
    else:
        raise AssertionError("Unsupported exchange:", exchange)

'''
#################################################################################
CREATE ORDER
#################################################################################
'''

def json_encode(payload):
    return json.dumps(payload, separators=(',', ':'), sort_keys=True)

def create_order_bitkub(symbol,amount_coin,price_thb):
    try:
        timestamp = int(time.time())
        payload = {
                'amt': amount_coin,
                'sym': ('THB_'+str(symbol)).upper(),
                'rat': price_thb,
                'typ': 'limit',
                'ts': timestamp
            }
        headers=get_headers_bitkub()
        api_secret_as_bytes =str.encode('bitkub_api_secret')
        message = json_encode(payload)
        signature = hmac.new(api_secret_as_bytes, msg=message.encode(), digestmod=hashlib.sha256).hexdigest()
        print('payload:',payload)
        print('signature:',signature)
        payload['sig']=signature
        response = requests.post(url='https://api.bitkub.com/api/market/place-bid/test', json=payload, headers=headers)
        response.raise_for_status()
        jsonObject = json.loads(response.text)
        print('Order created on bitkub:',jsonObject)
        return jsonObject
    except requests.exceptions.HTTPError as err:
        print('payload:',payload)
        print('response:',response)
        print('response.content:',str(response.content))
        raise SystemExit(err) 

def create_order_satang(symbol,amount_coin,price_thb,side,tx_type):
    try:
        nonce=int(datetime.datetime.now().timestamp()*1000)
        payload = {
                'amount': str(amount_coin),
                'nonce': nonce,
                'pair': (str(symbol)+'_thb').lower(),
                'price': str(price_thb),
                'side': side.lower(),
                'type': tx_type
            }
        paybytes = urllib.parse.urlencode(payload)
        headers=get_headers_satang(paybytes)
        response = requests.post(url='https://api.tdax.com/api/orders/', json=payload, headers=headers)
        response.raise_for_status()
        '''
        {"id":18839684,"type":"limit","side":"buy","pair":"xlm_thb","open_cost":"15.0321","average_price":"0","value":"0","cost":"0",
        "fee_percent":"0.2","vat_percent":"7","status":"processing","user_id":654178,"created_at":"2021-05-19T16:37:36.245888Z",
        "created_by_ip":"2001:fb1:c9:7b70:55a7:bac3:6017:cdbd","updated_at":"2021-05-19T16:37:36.245888Z","price":"15","amount":"1","remain_amount":"1"}
        '''
        jsonObject = json.loads(response.text)
        print('Order created on Satang:',jsonObject)
        return jsonObject
    except requests.exceptions.HTTPError as err:
        print('payload:',payload)
        print('response:',response)
        print('response.content:',str(response.content))
        raise SystemExit(err) 

def create_order_binance(symbol,amount_coin,price,side,type):
    try:
        ts = get_binance_server_time()
        if type == 'LIMIT':
            queryParams = 'symbol='+symbol.upper()+'USDT&side='+side+'&timeInForce=GTC&timestamp='+str(ts)+'&type=LIMIT&quantity='+str(amount_coin)+'&price='+str(price)
        else:
            queryParams = 'symbol='+symbol.upper()+'USDT&side='+side+'&timestamp='+str(ts)+'&type=MARKET&quantity='+str(amount_coin)

        api_secret_as_bytes =str.encode(binance_api_secret)
        signature = sign_sha256(api_secret_as_bytes,queryParams)
        queryParams = queryParams +'&signature='+signature
        headers=get_headers_binance()
        #print('queryParams:',queryParams)
        response = requests.post('https://api.binance.com/api/v3/order', headers=headers ,data=queryParams)
        #response = requests.post('https://api.binance.com/api/v3/order/test', headers=headers ,data=queryParams)
        response.raise_for_status()
        #print('response:',response)
        #print('response.content:',response.content)
        jsonObject = json.loads(response.text)
        print('Order created on Binance:',jsonObject)
        order_id=jsonObject['orderId']

        # Sometimes the order is filled super fast
        # LIMIT:
        # {'symbol': 'XLMUSDT', 'orderId': 1009342837, 'orderListId': -1, 'clientOrderId': 'WsS7H0yKOq37NYXQeoKJee', 'transactTime': 1621997250584, 'price': '0.43502000',
        # 'origQty': '706.00000000', 'executedQty': '706.00000000', 'cummulativeQuoteQty': '307.11723000', 'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'LIMIT', 
        # 'side': 'BUY', 'fills': [{'price': '0.43500000', 'qty': '344.50000000', 'commission': '0.34450000', 'commissionAsset': 'XLM', 'tradeId': 86792985}, 
        # {'price': '0.43502000', 'qty': '361.50000000', 'commission': '0.36150000', 'commissionAsset': 'XLM', 'tradeId': 86792986}]}
        # {"code":-2013,"msg":"Order does not exist."}

        # MARKET: 
        # amount_coin: 50 price: 0
        # {'symbol': 'XLMUSDT', 'orderId': 1044485512, 'orderListId': -1, 'clientOrderId': '34wG7iw2n7BbiBhz9yTliC', 'transactTime': 1622892398013, 'price': '0.00000000',
        #  'origQty': '50.00000000', 'executedQty': '50.00000000', 'cummulativeQuoteQty': '19.15404400', 'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'MARKET', 
        # 'side': 'BUY', 'fills': [{'price': '0.38308000', 'qty': '45.60000000', 'commission': '0.04560000', 'commissionAsset': 'XLM', 'tradeId': 89163256},
        #  {'price': '0.38309000', 'qty': '4.40000000', 'commission': '0.00440000', 'commissionAsset': 'XLM', 'tradeId': 89163257}]}
        # cummulativeQuoteQty => this is the USDT spent!!!

        if jsonObject['status'] == 'FILLED':
            if type == 'MARKET':
                print('Order filled at market price:',jsonObject)
            return order_id

        # poll until the order shows in the DB as it is asynchronous
        order = get_order(constants.BINANCE_NAME,symbol,order_id)
        #print('create_order_binance, order:',order)
        while order is None:
            print('Retrying to retrieve the order created... order:',order)
            time.sleep(1)
            order = get_order(constants.BINANCE_NAME,symbol,order_id)
    
        return order_id
    except requests.exceptions.HTTPError as err:
        print('queryParams:',queryParams)
        print('response:',response)
        print('response.content:',str(response.content))
        raise SystemExit(err) 

def create_order(exchange,symbol,amount_coin,price,side,type):
    if exchange == constants.SATANG_NAME:
        return create_order_satang(symbol,amount_coin,price,side,'limit')
    elif exchange == constants.BINANCE_NAME:
        return create_order_binance(symbol,amount_coin,price,side,type)
    else:
        raise AssertionError("Unsupported exchange:", exchange)

def is_order_filled(exchange,order_param):
    status=order_param['status']
    if exchange == constants.SATANG_NAME:
        if status.upper() == 'FILLED':
            return True
        if status.upper() == 'PROCESSING':
            return False
        raise AssertionError("Order has failed:", status)
    elif exchange == constants.BINANCE_NAME:
        return status.upper() != 'NEW'
    else:
        raise AssertionError("Unsupported exchange:", exchange)

def get_order_executed_quantity(exchange,order_param):
    if exchange == constants.SATANG_NAME:        
        return float(order_param['cost'])
    elif exchange == constants.BINANCE_NAME:
        return float(order_param['executedQty'])
    else:
        raise AssertionError("Unsupported exchange:", exchange)

'''
#################################################################################
WITHDRAWAL
#################################################################################
'''

def withdraw_binance(symbol,amount_coin):
    try:
        if symbol == constants.XLM_COIN:
            address = 'GAHK7EEG2WWHVKDNT4CEQFZGKF2LGDSW2IVM4S5DP42RBW3K6BTODB4A'
            addressTag = '104912839'
        elif symbol == constants.XRP_COIN:
            address = 'rEb8TK3gBgk5auZkwc6sHnwrGVJH8DuaLh'
            addressTag = '104824811'
        elif symbol == constants.ADA_COIN:
            address = 'DdzFFzCqrhseCMnEHEDDAxX41mW7x3moRBTNhmTfdTdFUDjHMraQ6vsPFAXgSbkhTpdNT9EG8F9wN1L5MmgHtJCgNXKAxRURPM6YTWQA'    
        else:
            raise AssertionError("Unsupported symbol:", symbol)
        
        ts = get_binance_server_time()
        print('withdraw_binance(), amount_coin:',amount_coin)
        queryParams = 'asset='+symbol.upper()+'&address='+address+'&addressTag='+addressTag+'&timestamp='+str(ts)+'&amount='+str(amount_coin)
        api_secret_as_bytes =str.encode(binance_api_secret)
        signature = sign_sha256(api_secret_as_bytes,queryParams)
        queryParams = queryParams +'&signature='+signature
        headers=get_headers_binance()
        #print('queryParams:',queryParams)
        response = requests.post('https://api.binance.com/wapi/v3/withdraw.html', headers=headers ,data=queryParams)
        response.raise_for_status()
        print('withdraw_binance(), queryParams:',queryParams)
        print('withdraw_binance(), response:',response)
        print('withdraw_binance(), response.content:',response.content)

        # BEWARE OF THIS ERROR: it means the network is suspended in the UI!!!
        #{"msg":"-4019=The current currency is not open for withdrawal","success":false}

        # this API will return 200 even if some errors happened like below!!!
        # withdraw_binance(), response: <Response [200]>
        # withdraw_binance(), response.content: b'{"msg":"-4026=The user has insufficient balance available","success":false}'
        jsonObject = json.loads(response.text)
        success=jsonObject['success']
        if not success:
            print('Withdrawal from Binance failed!')
            raise SystemExit(str(response.content)) 
        print('Withdrawal ['+str(amount_coin)+'] from Binance completed:',str(response.content))
    except requests.exceptions.HTTPError as err:
        print('withdraw_binance(), queryParams:',queryParams)
        print('response:',response)
        print('response.content:',str(response.content))
        raise SystemExit(err) 

'''
#################################################################################
CANCEL ORDER
#################################################################################
'''

def cancel_order_binance(symbol,order_id_param):
    try:
        ts = get_binance_server_time()
        queryParams = 'symbol='+symbol.upper()+'USDT&orderId='+str(order_id_param)+'&timestamp='+str(ts)
        api_secret_as_bytes =str.encode(binance_api_secret)
        signature = sign_sha256(api_secret_as_bytes,queryParams)
        queryParams = queryParams +'&signature='+signature
        headers=get_headers_binance()
        #print('queryParams:',queryParams)
        response = requests.delete('https://api.binance.com/api/v3/order', headers=headers ,data=queryParams)
        response.raise_for_status()
        print('response:',response)
        print('response.content:',response.content)
    except requests.exceptions.HTTPError as err:
        print('queryParams:',queryParams)
        print('response:',response)
        print('response.content:',str(response.content))
        raise SystemExit(err) 
