import requests
import threading
import time

from libs import coin2

class Main(threading.Thread):

    def set_n(self, n):
        self.n = int(n)

    def set_money(self, money):
        self.money = float(money)

    def get_market_list(self):
        flag = 0
        while flag != 1:
            try:
                result = requests.get(
                    'https://api.coinex.com/v1/market/list',
                    headers={
                        'Content-Type': 'application/json; charset=utf-8',
                        'Accept': 'application/json',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'
                    }
                )
            except:
                print('Try again!')
            else:
                flag = 1
        result = result.json()['data']
        for i in result:
            if i.find('USDT') != -1:
                self.list.append(i.replace('USDT', '').lower())

    def __init__(self, n, money):
        threading.Thread.__init__(self)
        self.list = []
        self.runlist = []
        self.run_flag = True
        self.get_market_list()
        self.set_n(n)
        self.set_money(money)
        self.j = 0

    def run(self):
        each_coin = self.money / self.n
        while True:
            if self.run_flag:
                for i in self.list:
                    if len(self.runlist) != self.n:
                        print('start ' + i)
                        r = coin2.Coin(i, each_coin, 0, 0, 1.5)
                        r.start()
                        time.sleep(10)
                        if r.flag_test:
                            print('buy ' + i)
                            r.join()
                            self.runlist[self.j] = r
                            l = ListenerCoin(self.runlist[self.j])
                            l.start()
                            l.join()
                            self.j = self.j + 1
                            continue
                        else:
                            print('del ' + i)
                            del r
                            continue

class ListenerCoin(threading.Thread):

    def __init__(self, obj):
        threading.Thread.__init__(self)
        flag = True
        while flag:
            if obj.flag_sell:
                print('sell ' + obj)
                Main().runlist.remove(obj)
                Main().j -= 1
                del obj
                flag = False

#Main(2, 10).get_market_list()
m = Main(2, 10)
m.start()
m.join()