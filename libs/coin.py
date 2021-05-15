import requests
import time
import datetime
import pandas as pd
from stockstats import StockDataFrame
import matplotlib.pyplot as plt
import hashlib
import json
import os
import threading
from ta import momentum


class Coin(threading.Thread):
    __access_id = '5C5076DB01D34ABF9EE74837D76F3931'
    __secret_key = 'D8A56BD2772047748D6E1B9C38CC526D92335266E03A9FEC'
    __headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'
    }
    __order_count = 0
    __buy_price = 0
    __flag_buy = False

    def set_coin(self, name):
        self.coin = name.upper()

    def set_order(self, order):
        self.order_amount = int(order)

    def set_sell_offset(self, sell_offset):
        self.sell_offset = float(sell_offset)

    def set_buy_offset(self, buy_offset):
        self.buy_offset = float(buy_offset)

    def set_percent(self, percent):
        self.percent = float(percent)

    def set_safe_stop(self, flag):
        self.safe_stop = flag

    def check_log_file(self):
        if not os.path.isdir('./logs'):
            os.mkdir('./logs')
        if not os.path.isdir('./logs/cancelLogs'):
            os.mkdir('./logs/cancelLogs')
        if not os.path.isfile('./logs/log_{coin}.txt'.format(coin=self.coin)):
            open('./logs/log_{coin}.txt'.format(coin=self.coin), 'a').close()
        if not os.path.isfile('./logs/cancelLogs/log_{coin}.txt'.format(coin=self.coin)):
            open('./logs/cancelLogs/log_{coin}.txt'.format(coin=self.coin), 'a').close()

    def read_logger(self):
        if os.stat('./logs/log_{coin}.txt'.format(coin=self.coin)).st_size != 0:
            with open('./logs/log_{coin}.txt'.format(coin=self.coin), 'r') as logFile:
                line = logFile.readlines()[-1]
                data = line.split('\t')
                if data[0] == 'Buy':
                    self.__order_count = float(data[3])
                    self.__buy_price = float(data[2])
        else:
            with open('./logs/log_{coin}.txt'.format(coin=self.coin), 'a') as logFile:
                logFile.write('Type\tCoin\tPrice\tCount\tPercent\tTime')

    def read_logger_safe_stop(self):
        if self.safe_stop:
            f = True
            with open('./logs/log_{coin}.txt'.format(coin=self.coin), 'r') as logFile:
                line = logFile.readlines()[-1]
                data = line.split('\t')
                if data[0] == 'Buy':
                    f = False
            if f:
                print('---SAFE STOP {coin} IS OK---'.format(coin=self.coin))
            return f
        return False

    def __init__(self, name, order, buy_offset, sell_offset, percent):
        threading.Thread.__init__(self)
        self.safe_stop = False
        self.set_coin(name)
        self.set_order(order)
        self.set_buy_offset(buy_offset)
        self.set_sell_offset(sell_offset)
        self.set_percent(percent)
        self.coin_market_name = self.coin.lower() + 'usdt'
        self.check_log_file()
        self.read_logger()

    def logger(self, type, coin, price, count, percent):
        now_time = datetime.datetime.now()
        with open('logs/log_{coin}.txt'.format(coin=self.coin), 'a') as logFile:
            logFile.write('\n' + type + '\t' + coin + '\t' + str(price) + '\t' + str(count) + '\t' + str(percent) + '\t' + str(now_time))

    def cancel_logger(self, type, msg):
        now_time = datetime.datetime.now()
        if type == 'buy':
            msg = 'Buy canceled for : ' + msg
        if type == 'sell':
            msg = 'Sell canceled for : ' + msg
        with open('logs/cancelLogs/log_{coin}.txt'.format(coin=self.coin), 'a') as logFile:
            logFile.write(msg + '\t' + str(now_time) + '\n') 

    def get_sign(self, params, secret_key):
        data = '&'.join([key + '=' + str(params[key]) for key in sorted(params)])
        data = data + '&secret_key=' + str(secret_key)
        data = data.encode()
        return hashlib.md5(data).hexdigest().upper()

    def get_market_list(self):
        result = requests.get(
            'https://api.coinex.com/v1/market/list',
            headers=self.__headers
        )
        return result.json()

    def get_kline_data(self, market, type, limit):
        """
        :param market: bchbtc
        :param type: 1min
        :param limit: 100
        """
        flag = 0
        while flag != 1:
            try:
                result = requests.get(
                    'https://api.coinex.com/v1/market/kline?market={market}&type={type}&limit={limit}'.format(
                    market=market,
                    type=type,
                    limit=limit,
                    ),
                    headers=self.__headers
                )
            except:
                print('Try again!')
            else:
                get_result = pd.json_normalize(result.json(), ['data'])
                del get_result[7]
                get_result.columns = ['Time', 'open', 'close', 'high', 'low', 'volume', 'amount']
                flag = 1
        return get_result, get_result['close'].iloc[-1]

    def get_account_info(self, access_id):
        '''
        :param access_id: access_id
        '''
        flag = 0
        tonce = time.time() * 1000
        param = {
            'access_id': access_id,
            'tonce': tonce,

        }
        token = self.get_sign(param, self.__secret_key)
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
            'Authorization': token,
        }
        while flag != 1:
            try:
                result = requests.get(
                    'https://api.coinex.com/v1/balance/info?access_id={access_id}&tonce={tonce}'.format(
                    access_id=access_id, tonce=tonce),
                    headers=headers
                )
            except:
                print('Wrong')
            else:
                if result.json()['message'] == 'Success':
                    flag = 1
        # ['data']['USDT']['available']
        return result.json()

    def palce_limit_order(self, access_id, market, type, amount, price):
        '''
        :param access_id:
        :param market: chzusdt
        :param type: buy or sell
        :param amount: order count
        :param price: order price
        '''
        tonce = time.time() * 1000
        data = {'access_id': access_id, 'market': market, 'type': type, 'amount': amount, 'price': price,
                'tonce': tonce}
        token = self.get_sign(data, self.__secret_key)
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
            'Authorization': token,
        }
        result = requests.post(
            url='https://api.coinex.com/v1/order/limit',
            data=json.dumps(data),
            headers=headers,
        )
        return result.json()

    def get_market_depth(self, market, merge, limit):
        '''
        :param market: chzusdt
        :param merge: '0', '0.1', '0.01', '0.001', '0.0001', '0.00001', '0.000001', '0.0000001', '0.00000001
        :param limit: 5/10/20/50
        :return sell price=['asks'][0][0] --- buy price ['bids'][0][0]
        '''
        flag = 0
        while flag != 1:
            try:
                result = requests.get(
                    'https://api.coinex.com/v1/market/depth?market={market}&limit={limit}&merge={merge}'.format(
                    market=market, limit=limit, merge=merge),
                    headers=self.__headers
                )
            except:
                print('Try again!')
            else:
                flag = 1
        return result.json()['data']

    def get_market_high_value(self, market, merge, limit=50):
        '''
        :param market: chzusdt
        :param merge: '0', '0.1', '0.01', '0.001', '0.0001', '0.00001', '0.000001', '0.0000001', '0.00000001
        :param limit: 5/10/20/50
        :return sell price=['asks'][0][0] --- buy price ['bids'][0][0]
        '''
        flag = 0
        flag_buy = False
        while flag != 1:
            try:
                result = requests.get(
                    'https://api.coinex.com/v1/market/depth?market={market}&limit={limit}&merge={merge}'.format(
                    market=market, limit=limit, merge=merge),
                    headers=self.__headers
                )
            except:
                print('Try again!')
            else:
                result = result.json()['data']['bids']
                buy_price = result[0][0]
                list = []
                for i in range(1, 50):
                    list.append(result[i][0])
                max_list = max(list)
                if buy_price >= max_list:
                    flag_buy = False
                else:
                    flag_buy = True
                flag = 1
        return flag_buy

    def get_unexecuted_order(self, access_id, market, page=1, limit=5):
        '''
        :param access_id:
        :param market:
        :param page:
        :param limit:
        '''
        flag = 0
        tonce = time.time() * 1000
        param = {
            'access_id': access_id,
            'market': market,
            'page': page,
            'limit': limit,
            'tonce': tonce,

        }
        token = self.get_sign(param, self.__secret_key)
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
            'Authorization': token,
        }
        while flag != 1:
            try:
                result = requests.get(
                    'https://api.coinex.com/v1/order/pending?access_id={access_id}&market={market}&page={page}&limit={limit}&tonce={tonce}'.format(
                    access_id=access_id, tonce=tonce, market=market, page=page, limit=limit),
                    headers=headers
                )
            except:
                print('Wrong')
            else:
                if result.json()['message'] == 'Success':
                    flag = 1
        if result.json()['data']['count'] == 0:
            return False
        else:
            if result.json()['data']['data'][0]['type'] != 'sell':
                return True

    def cancell_all_order(self, access_id, market, account_id=0):
        '''
        :param access_id:
        :param market:
        :param account_id:
        '''
        flag = 0
        tonce = time.time() * 1000
        param = {
            'access_id': access_id,
            'account_id': account_id,
            'market': market,
            'tonce': tonce,

        }
        token = self.get_sign(param, self.__secret_key)
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
            'Authorization': token,
        }
        while flag != 1:
            try:
                result = requests.delete(
                    'https://api.coinex.com/v1/order/pending?access_id={access_id}&account_id={account_id}&market={market}&tonce={tonce}'.format(
                    access_id=access_id, tonce=tonce, market=market, account_id=account_id),
                    headers=headers
                )
            except:
                print('Wrong')
            else:
                if result.json()['message'] == 'Success':
                    flag = 1
        return True
    '''
    def tsi_trust(self, tsi):
        ascending = False
        if tsi.iloc[-1] >= -25:
            if tsi.iloc[-1] <= -20:
                ascending = True
                tsi_len = len(tsi)
                for i in range(1, tsi_len):
                    if tsi.iloc[i] <= tsi.iloc[i-1]:
                        ascending = False
        return ascending
    '''
    def tsi_trust(self, tsi):
        result = False
        if tsi.iloc[-1] >= -25:
            if tsi.iloc[-1] <= -20:
                if tsi.iloc[len(tsi)-2] <= tsi.iloc[-1]:
                    result = True
        return result

    def rsi_trust(self, rsi):
        result = False
        if rsi.iloc[-1] >= 30:
            if rsi.iloc[-1] <= 35:
                if rsi.iloc[len(rsi)-2] <= rsi.iloc[-1]:
                    result = True
        return result

    def macd(self, data):
        #time = data['Time']
        del data['Time']
        data = StockDataFrame.retype(data)
        data['Macd'] = data.get('macd')
        # WILLIAMS %R
        #high_val = float(data['high'].max())
        #low_val = float(data['low'].min())
        #close_val = float(data['close'].iloc[-1])
        #r_percent = ((high_val - close_val) / (high_val - low_val)) * -100
        #TSIIndicator
        tsi = momentum.TSIIndicator(pd.to_numeric(data['close']), fillna=True)
        r_percent = float(momentum.WilliamsRIndicator(pd.to_numeric(data['high']), pd.to_numeric(data['low']), pd.to_numeric(data['close']))._wr.iloc[-1])
        rsi = momentum.RSIIndicator(pd.to_numeric(data['close']), fillna=True)
        #if data['macd'].iloc[-1] <= 0:
        if r_percent >= -40:
            if self.tsi_trust(tsi._tsi.iloc[990:]):
                self.__flag_buy = True
            else:
                self.cancel_logger('buy', 'TSI {val}'.format(val=tsi._tsi.iloc[-1]))
                self.__flag_buy = False
            if not self.__flag_buy:
                if self.rsi_trust(rsi._rsi.iloc[990:]):
                        self.__flag_buy = True
                else:
                    self.__flag_buy = False
                    self.cancel_logger('buy', 'RSI {val}'.format(val=rsi._rsi.iloc[-1]))
        else:
            self.cancel_logger('buy', 'Williams %R {r}'.format(r=r_percent))
            self.__flag_buy = False
        #else:
            #self.cancel_logger('buy', 'Positive sycle')
            #self.__flag_buy = False
        return data

    def plotting(self, df, time):
        fig, axs = plt.subplots(1, 1)
        axs.plot(time, df['macds'], color="red", label="Signal")
        axs.bar(time, df['macd'], color="green", label="MACD", width=50)
        axs.grid()
        axs.legend()
        plt.show()

    def buy_sell(self, type, price):
        order_exist = self.get_unexecuted_order(self.__access_id, self.coin_market_name)
        coin_exist = self.get_account_info(self.__access_id)['data']
        if type == 'buy':
            if self.__flag_buy:
                if order_exist == False:
                    if self.coin not in coin_exist:
                        if not self.safe_stop:
                            # high_buy_price = get_market_high_value('chzusdt', 0)
                            # if high_buy_price:
                            #d = self.get_market_depth(self.coin_market_name, 0, 5)
                            #self.__buy_price = round(float(d['bids'][0][0]), 8) + self.buy_offset
                            self.__buy_price = float(price) + self.buy_offset
                            self.__order_count = str(round(self.order_amount / self.__buy_price, 8))
                            self.palce_limit_order(self.__access_id, self.coin_market_name, 'buy', self.__order_count, self.__buy_price)
                            self.logger('Buy', self.coin, self.__buy_price, self.__order_count, 0)
                else:
                    self.cancel_logger('buy', 'Order exist')
        if type == 'sell':
            if self.coin in coin_exist:
                if order_exist == False:
                    #d = self.get_market_depth(self.coin_market_name, 0, 5)
                    #sell_price = round(float(d['asks'][0][0]), 8) - self.sell_offset
                    sell_price = float(price) - self.sell_offset
                    own_percent = ((sell_price - self.__buy_price) / sell_price) * 100
                    print('Percent: ' + str(own_percent))
                    if own_percent >= self.percent:
                        self.__buy_price = 0
                        #print('go to sell')
                        self.palce_limit_order(self.__access_id, self.coin_market_name, 'sell', self.__order_count, str(sell_price))
                        self.logger('Sell', self.coin, sell_price, self.__order_count, own_percent)
                    elif own_percent <= -5:
                        self.__buy_price = 0
                        #print('go to sell zarar')
                        self.palce_limit_order(self.__access_id, self.coin_market_name, 'sell', self.__order_count, str(sell_price))
                        self.logger('Sell', self.coin, sell_price, self.__order_count, own_percent)
                    else:
                        self.cancel_logger('sell', 'Not coinex percent')
                else:
                    self.cancel_logger('sell', 'Order exist')
                    # if order_exist == True:
                    # cancell_all_order(access_id, 'chzusdt')
                    # print('Cancelled')

    def run(self):
        counter = 1
        while not self.read_logger_safe_stop():
            if counter == 1:
                df = self.get_kline_data(self.coin_market_name, '2hour', 1000)[0]
                old_flag = df['amount'][999]
                df_macd = self.macd(df)
                time.sleep(5)
                counter += 1
            else:
                kline = self.get_kline_data(self.coin_market_name, '2hour', 1000)
                new_df = kline[0]
                new_flag = new_df['amount'][999]
                if new_flag != old_flag:
                    df_macd = self.macd(new_df)
                    old_flag = new_df['amount'][999]
                    j = 0
                    f = 0
                    for i in range(1000):
                        if df_macd['macds'][i] >= 0:
                            if df_macd['macds'][i] <= df_macd['macd'][i]:
                                j += 1
                                f = 0
                            if df_macd['macds'][i] > df_macd['macd'][i]:
                                j = 0
                                f += 1
                        else:
                            if df_macd['macds'][i] >= df_macd['macd'][i]:
                                j = 0
                                f += 1
                            if df_macd['macds'][i] < df_macd['macd'][i]:
                                j += 1
                                f = 0
                        # d = get_market_depth('chzusdt', 0, 5)
                        # sell_price = d['asks'][0][0]
                        # buy_price = d['bids'][0][0]
                        if j == 1 and f == 0:
                            # buy
                            print('Buy')
                            # file.write(buy_price)
                            self.buy_sell('buy', kline[1])
                        if f == 1 and j == 0:
                            # sell
                            print('Sell')
                            # print(sell_price)
                            # file.write('\t' + sell_price + '\n')
                            self.buy_sell('sell', kline[1])
                            # q = q+1
                        time.sleep(5)
                else:
                    time.sleep(5)