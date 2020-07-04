class Strategy():
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value

    # option setting needed
    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        # strategy property
        self.subscribedBooks = {
            'Bitfinex': {
                'pairs': ['BTC-USDT'],
            },
        }
        self.period = 60 * 60 * 2
        self.options = {}

        # user defined class attribute
        self.last_type = 'sell'
        self.last_cross_status = None
        self.close_price_trace = np.array([])
        self.ma_long = 10
        self.ma_short = 5
        self.UP = 1
        self.DOWN = 2
        self.current_amount = 0
        self.current_price = 0


    def get_current_ma_cross(self):
        s_ma = talib.EMA(self.close_price_trace, self.ma_short)[-1]
        l_ma = talib.EMA(self.close_price_trace, self.ma_long)[-1]
        today_price = self.close_price_trace[-1]
        if np.isnan(s_ma) or np.isnan(l_ma):
            return None
        if today_price > l_ma:
            return self.UP, (today_price-l_ma)
        return self.DOWN, (today_price-l_ma)


    # called every self.period
    def trade(self, information):

        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        close_price = information['candles'][exchange][pair][0]['close']

        # add latest price into trace
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        # only keep max length of ma_long count elements
        self.close_price_trace = self.close_price_trace[-self.ma_long:]
        # calculate current ma cross status
        cur_cross, diff = self.get_current_ma_cross()

        Log('info: ' + str(information['candles'][exchange][pair][0]['time']) + ', ' + str(information['candles'][exchange][pair][0]['open']) + ', assets' + str(self['assets'][exchange]['BTC']))

        if cur_cross is None:
            return []

        if self.last_cross_status is None:
            self.last_cross_status = cur_cross
            return []

        # cross up
        # if self.last_type == 'sell' and cur_cross == self.UP and self.last_cross_status == self.DOWN:
        if (cur_cross == self.UP) and (self.current_amount == 0):
            Log('buying, opt1:' + self['opt1'])
            Log('diff: ' + str(diff))
            self.last_type = 'buy'
            self.last_cross_status = cur_cross

            num = int(diff/10)
            if num > 9:
                num = 9
            self.current_amount = num
            # Log('current:' + str(self.current_amount))

            self.current_price = close_price

            return [
                {
                    'exchange': exchange,
                    'amount': num,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
            
        # cross down
        # elif self.last_type == 'buy' and cur_cross == self.DOWN and self.last_cross_status == self.UP:
        elif (cur_cross == self.DOWN) and (self.current_amount > 0) and (close_price > self.current_price):
            Log('selling, ' + exchange + ':' + pair)
            Log('diff: ' + str(diff))
            self.last_type = 'sell'
            self.last_cross_status = cur_cross

            num = int(diff/10)
            if -num > self.current_amount:
                num = -self.current_amount
                self.current_amount = 0
            else:
                self.current_amount += num
            # Log('current:' + str(self.current_amount))
            
            return [
                {
                    'exchange': exchange,
                    'amount': num,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        self.last_cross_status = cur_cross
        return []
