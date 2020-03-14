#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = "Ringo"

'''
自动扶梯 策略 (难度：初级)
参考: https://www.shinnytech.com/blog/escalator/
注: 该示例策略仅用于功能示范, 实盘时请根据自己的策略/经验进行修改
2020-2-14日修改回测版
2020-2-19构思新版，主要是想把MACD变红且在ema2的55均线向上的时候做多，反之做空。
2020-2-20，更改平仓条件，增加MACD变色的平仓条件。
2020-2-20，把A分支的去掉开仓形态加入。
2020-2-21，改开多仓规则为柱子变红后，需要超过前面一根K线的最高点，防止跌破3天最低点后平仓后马上又开仓。
2020-3-13，再改一下。从更小周期的信号进入，但是到更大周期的趋势结束再出场。比如从小时周期的MACD进场，但是到日线趋势改变时候再出场。
这个策略的思路是按1小时的macd进场，然后1小信号消失的时候，查看是不是在上个周期的信号依然是和1小时周期相反的
如果相反则平仓，如果相同，则等待上个周期信号和相反。
'''

import pretty_errors
import datetime
from datetime import date

from tqsdk import TargetPosTask, TqApi, TqBacktest, tafunc, TqSim
from tqsdk.ta import MA, MACD

# 设置合约
SYMBOL = "CZCE.SR005"
# 设置均线长短周期
MA_SLOW, MA_FAST, EMA2_long = 8, 34, 55

#下面是回测用api，实盘时候记得注释掉。
api = TqApi(TqSim(200000), backtest=TqBacktest(start_dt=date(2019, 7, 15), end_dt=date(2020, 1, 15)), web_gui="http://127.0.0.1:61122/")

#接收行情设置持仓目标
klines = api.get_kline_serial(SYMBOL, 60*60) #1小时K线  
klines_long = api.get_kline_serial(SYMBOL, 60*60*24)    #日K线                                                                        
quote = api.get_quote(SYMBOL)
position = api.get_position(SYMBOL)
target_pos = TargetPosTask(api, SYMBOL)

#计算MACD
macd = MACD(klines, 12, 26, 9)
macd_long = MACD(klines_long, 12, 26 ,9)

#计算EMA2的值，看看这个值是增长还是降低。来判断趋势的方向
direction = tafunc.ema2(klines.close, EMA2_long)
direction_long = tafunc.ema2(klines_long.close, EMA2_long)

def long_buyopen():
    if direction_long.iloc[-1] > direction_long.iloc[-2] and macd_long['bar'].iloc[-1] > 0:
        return 1
    else:
        return 0

def short_buyopen():
    if direction.iloc[-1] > direction.iloc[-2] and macd['bar'].iloc[-1] > 0:
        return 1
    else:
        return 0


def long_sellopen():
    if direction_long.iloc[-1] < direction_long.iloc[-2] and macd_long['bar'].iloc[-1] < 0:
        return 1
    else:
        return 0


def short_sellopen():
    if direction.iloc[-1] < direction.iloc[-2] and macd['bar'].iloc[-1] < 0:
        return 1
    else:
        return 0



while True:
    api.wait_update()
    # 每次k线更新，判断MACD的红绿柱和均线的方向
    if api.is_changing(klines.iloc[-1], "datetime"):
        direction = tafunc.ema2(klines.close, EMA2_long) 
        direction_long = tafunc.ema2(klines_long.close, EMA2_long)
        if direction.iloc[-1] > direction.iloc[-2] and direction_long.iloc[-1] > direction_long.iloc[-2]:
            print("小周期上涨，大周期也上涨")
        elif direction.iloc[-1] < direction.iloc[-2] and direction_long.iloc[-1] > direction_long.iloc[-2]:
            print("小周期下跌趋势，大周期上涨趋势")
        elif direction.iloc[-1] < direction.iloc[-2] and direction_long.iloc[-1] < direction_long.iloc[-2]:
            print("大小周期都在下跌")

        macd = MACD(klines, 12, 26, 9)
        if macd['bar'].iloc[-1] > 0 and macd_long['bar'].iloc[-1] > 0:
            print('大小周期的MACD红柱')
        elif macd['bar'].iloc[-1] < 0 and macd_long['bar'].iloc[-1] > 0:
            print("小周期MACD绿色，大周期红柱")
        else:
            print("MACD都是绿柱")


        
"""

    if api.is_changing(quote, "last_price"):#注意，测试一下换成K线变化的时候能不能下单，结果回测失败，这里不能用K线数据
        # 开仓判断
        if position.pos_long == 0 and position.pos_short == 0:
            # 计算前后两根K线在当时K线范围波幅
            # kl_range_cur = kline_range(-2)
            # kl_range_pre = kline_range(-3)
            # 开多头判断，MACD变红并且均线方向向上，
            if macd['bar'].iloc[-1] > 0 and direction.iloc[-1] > direction.iloc[-2] and quote.last_price > klines.iloc[-2].high:
                print("最新价为:%.2f 开多头" % quote.last_price)
                target_pos.set_target_volume(1)
                print(datetime.datetime.now())

            # 开空头判断，macd变绿并且均线方向向下，
            elif macd['bar'].iloc[-1] <= 0 and direction.iloc[-1] <= direction.iloc[-2] and quote.last_price < klines.iloc[-2].low:
                print("最新价为:%.2f 开空头" % quote.last_price)
                target_pos.set_target_volume(-1)
                print(datetime.datetime.now())
            # else:
            #     print("最新价位:%.2f ，未满足开仓条件" % quote.last_price)
                

        # 多头持仓止损策略
        elif position.pos_long > 0:
            # 在前三根根K线较低点减一跳，进行多头止损
            kline_low = min(klines.iloc[-2].low, klines.iloc[-3].low, klines.iloc[-4].low)
            if klines.iloc[-1].close <= kline_low - quote.price_tick or macd['bar'].iloc[-1] < 0:
                print("最新价为:%.2f,进行多头止损" % (quote.last_price))
                target_pos.set_target_volume(0)
                print(datetime.datetime.now())
            # else:
            #     print("多头持仓，当前价格 %.2f,多头离场价格%.2f" % (quote.last_price, kline_low - quote.price_tick))

        # 空头持仓止损策略
        elif position.pos_short > 0:
            # 在三根K线较高点加一跳，进行空头止损
            kline_high = max(klines.iloc[-2].high, klines.iloc[-3].high, klines.iloc[-4].high)
            if klines.iloc[-1].close >= kline_high + quote.price_tick or macd['bar'].iloc[-1] > 0:
                print("最新价为:%.2f 进行空头止损" % quote.last_price)
                target_pos.set_target_volume(0)
                print(datetime.datetime.now())
            # else:
            #     print("空头持仓，当前价格 %.2f,空头离场价格%.2f" % (quote.last_price, kline_high + quote.price_tick))
"""
