import pandas as pd
from sklearn.linear_model import LinearRegression

class Candle:

    def check(self, data):
        return data.apply(pd.to_numeric)

    def procedure(self, data):
        x = data['Time'].to_numpy().reshape(-1, 1)
        y = data['close'].to_numpy()
        model = LinearRegression()
        model.fit(x, y)
        m = float(model.coef_)
        if m > 0:
            return 's'
        elif m < 0:
            return 'n'
        else:
            return 0

    def hammer(self, data):
        data = self.check(data)
        proc = self.procedure(data.iloc[:data.shape[0] - 2])
        candle = data.iloc[-2]
        trust = data.iloc[-1]
        if proc == 0:
            return False
        if proc == 'n':
            #green candle => close is upper
            if candle['open'] < candle['close']:
                body = candle['close'] - candle['open']
                shadow = candle['open'] - candle['low']
                if shadow >= 2*body:
                    if trust['open'] < trust['close']:
                        return True
                    else:
                        return False
                return False
            #red candle => open upper
            elif candle['open'] > candle['close']:
                body = candle['open'] - candle['close']
                shadow = candle['close'] - candle['low']
                if shadow >= 2*body:
                    if trust['open'] < trust['close']:
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False

    def inv_hammer(self, data):
        data = self.check(data)
        proc = self.procedure(data.iloc[:data.shape[0] - 2])
        candle = data.iloc[-2]
        trust = data.iloc[-1]
        if proc == 0:
            return False
        if proc == 'n':
            #green candle => close is upper
            if candle['open'] < candle['close']:
                body = candle['close'] - candle['open']
                shadow = candle['high'] - candle['close']
                if shadow >= 2*body:
                    if trust['open'] < trust['close']:
                        return True
                    else:
                        return False
                return False
            #red candle => open upper
            elif candle['open'] > candle['close']:
                body = candle['open'] - candle['close']
                shadow = candle['high'] - candle['open']
                if shadow >= 2*body:
                    if trust['open'] < trust['close']:
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False

    def bullish_engulfing(self, data):
        data = self.check(data)
        proc = self.procedure(data.iloc[:data.shape[0] - 3])
        Fcandle = data.iloc[-3]
        Scandle = data.iloc[-2]
        trust = data.iloc[-1]
        if proc == 0:
            return False
        if proc == 'n':
            Fbody = abs(Fcandle['open'] - Fcandle['close'])
            Sbody = abs(Scandle['open'] - Scandle['close'])
            if Fcandle['high'] <= Scandle['high']:
                if Sbody > Fbody:
                    if trust['high'] >= Scandle['high']:
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False
        else:
            return False

'''
c = Candle()

result = requests.get(
    'https://api.coinex.com/v1/market/kline?market={market}&type={type}&limit={limit}'.format(
    market='ADAUSDT',
    type='2hour',
    limit=10,
    ),
    headers={
    'Content-Type': 'application/json; charset=utf-8',
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'
    }
)
get_result = pd.json_normalize(result.json(), ['data'])
del get_result[7]
get_result.columns = ['Time', 'open', 'close', 'high', 'low', 'volume', 'amount']
print(get_result)
print(c.bullish_engulfing(get_result.apply(pd.to_numeric)))
'''