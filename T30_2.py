"""
这个例子主要描述了获取K线、ticks、报价变化的内容，并且展示了怎么打印时间
"""
import datetime
from datetime import date

from tqsdk import TargetPosTask, TqApi, TqBacktest, tafunc, TqSim, TqAccount, TqReplay
from tqsdk.ta import MA, MACD


#api = TqApi(TqSim(200000), backtest=TqBacktest(start_dt=date(2019, 7, 15), end_dt=date(2020, 1, 15)), web_gui="http://127.0.0.1:61200/")
#api = TqApi()

api = TqApi(backtest=TqReplay(date(2019, 12, 23)))#复盘api

symbol = "CZCE.TA005"
quote = api.get_quote(symbol)
print(quote.datetime, quote.last_price.datetime, quote.ask_price1, quote.ask_price2)

ticks = api.get_tick_serial(symbol)
klines = api.get_kline_serial(symbol,60*5)
print(datetime.datetime.fromtimestamp(klines.iloc[-1]['datetime']/ 1e9))

while True:
    api.wait_update()
    # if api.is_changing(ticks):
    #     print("tick变化", ticks.iloc[-1])
    if api.is_changing(klines.iloc[-1], 'datetime'):#如果K线的时间变化
        print('新K线', datetime.datetime.fromtimestamp(klines.iloc[-1]['datetime'] / 1e9))
    if api.is_changing(klines.iloc[-1], 'close'): #判断最后一根K线的收盘价是否变化  
        print('K线变化', datetime.datetime.fromtimestamp(klines.iloc[-1]['datetime'] / 1e9), klines.close.iloc[-1])

api.close()
