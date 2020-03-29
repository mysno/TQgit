
'''
布林通道交易策略，详细内容在下面网址：
Aberration 策略 (难度：初级) — TianQin Python SDK 1.6.3 文档
https://doc.shinnytech.com/tqsdk/latest/demo/example/aberration.html

'''

import pretty_errors
import datetime
from datetime import date

from tqsdk import TargetPosTask, TqApi, TqBacktest, tafunc, TqSim
from tqsdk.ta import MA, MACD, ATR

# 设置合约
SYMBOL = "DCE.i2005"
# 设置均线长短周期
MA_SLOW, MA_FAST, EMA2_long = 8, 26, 55

#下面是回测用api，实盘时候记得注释掉。
api = TqApi(TqSim(200000), backtest=TqBacktest(start_dt=date(2019, 7, 15), end_dt=date(2020, 1, 15)), web_gui="http://127.0.0.1:61000/")

#接收行情设置持仓目标
klines = api.get_kline_serial(SYMBOL, 60*60*24)  # 1小时K线
klines_long = api.get_kline_serial(SYMBOL, 60*60*24)  # 日K线
quote = api.get_quote(SYMBOL)
position = api.get_position(SYMBOL)
target_pos = TargetPosTask(api, SYMBOL)


# 使用BOLL指标计算中轨、上轨和下轨，其中26为周期N  ，2为参数p
atr = ATR(klines, 26)
midline = tafunc.ema2(klines.close, MA_FAST)
topline = midline + atr.atr
bottomline = midline - atr.atr

#print("策略运行，中轨：%.2f，上轨为:%.2f，下轨为:%.2f" % (midline, topline, bottomline))



while True:
    api.wait_update()

    # 每次生成新的K线时重新计算BOLL指标
    if api.is_changing(klines.iloc[-1], "datetime") or api.is_changing(quote, "last_price"):
        atr.atr = ATR(klines, 26)
        midline = tafunc.ema2(klines.close, MA_FAST)
        topline = midline + atr.atr
        bottomline = midline - atr.atr
        if position.pos_long == 0 and position.pos_short == 0:
            # 如果最新价大于上轨，K线上穿上轨，开多仓
            if quote.last_price > topline.iloc[-1]:
                print("K线上穿上轨，开多仓")
                target_pos.set_target_volume(1)
            # 如果最新价小于轨，K线下穿下轨，开空仓
            elif quote.last_price < bottomline.iloc[-1]:
                print("K线下穿下轨，开空仓")
                target_pos.set_target_volume(-1)
            else:
                print("当前最新价%.2f,未穿上轨或下轨，不开仓" % quote.last_price)

        # 在多头情况下，空仓条件
        elif position.pos_long > 0:
            # 如果最新价低于中线，多头清仓离场
            if quote.last_price < midline.iloc[-1]:
                print("最新价低于中线，多头清仓离场")
                target_pos.set_target_volume(0)
            else:
                print("当前多仓，未穿越中线，仓位无变化")

        # 在空头情况下，空仓条件
        elif position.pos_short > 0:
            # 如果最新价高于中线，空头清仓离场
            if quote.last_price > midline.iloc[-1]:
                print("最新价高于中线，空头清仓离场")
                target_pos.set_target_volume(0)
            else:
                print("当前空仓，未穿越中线，仓位无变化")
