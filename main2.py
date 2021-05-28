import requests
import threading
import time
import os

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

    def check_log_file(self):
        if not os.path.isdir('./logs'):
            os.mkdir('./logs')
        if not os.path.isfile('./logs/log_MAIN.txt'):
            open('./logs/log_MAIN.txt', 'a').close()

    def read_logger(self):
        if os.stat('./logs/log_MAIN.txt').st_size != 0:
            each_coin = self.money / self.n
            with open('./logs/log_MAIN.txt', 'r') as logFile:
                for line in logFile:
                    r = coin2.Coin(line, each_coin, 0, 0, 1.5)
                    r.start()
                    r.join()
                    self.runlist[self.j] = r
                    self.j = self.j + 1
                    l = ListenerCoin(self.runlist[self.j])
                    l.start()
                    l.join()

    def logger(i):
        with open('logs/log_MAIN.txt', 'a') as logFile:
            logFile.write(i + '/n')

    def delete_logger(i):
        a_file = open("logs/log_MAIN.txt", "r")
        lines = a_file.readlines()
        a_file.close()
        new_file = open("logs/log_MAIN.txt", "w")
        for line in lines:
            if line.strip("\n") != i:
                new_file.write(line)
        new_file.close()  

    def __init__(self, n, money):
        threading.Thread.__init__(self)
        self.list = []
        self.runlist = []
        self.run_flag = True
        self.get_market_list()
        self.set_n(n)
        self.set_money(money)
        self.j = 0
        self.check_log_file()
        self.read_logger()

    def run(self):
        each_coin = self.money / self.n
        while True:
            if self.run_flag:
                for i in self.list:
                    if len(self.runlist) != self.n:
                        print('start ' + i)
                        r = coin2.Coin(i, each_coin, 0, 0, 1.5)
                        r.start()
                        time.sleep(20)
                        if r.flag_test:
                            print('buy ' + i)
                            self.runlist[self.j] = r
                            r.join()
                            l = ListenerCoin(self.runlist[self.j])
                            l.start()
                            l.join()
                            self.j = self.j + 1
                            self.logger(i)
                            continue
                        else:
                            print('del ' + i)
                            r.__del__()
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
                Main().delete_logger(obj.coin.lower())
                obj.__del__()
                flag = False

#Main(2, 10).get_market_list()
m = Main(2, 10)
m.start()
m.join()