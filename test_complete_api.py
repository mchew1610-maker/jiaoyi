# test_complete_api.py
"""测试脚本 - 验证所有API是否正常工作"""

import asyncio
import sys
from datetime import datetime

# 导入API管理器
from api_manager import APIManager


async def test_all_apis():
    """测试所有API功能"""
    api = APIManager()

    print("=" * 60)
    print("加密货币交易机器人 - API测试")
    print("=" * 60)

    results = {}

    # 测试1：火币价格数据
    print("\n[1/8] 测试火币API - 实时价格...")
    try:
        btc_price = await api.get_crypto_price('BTCUSDT')
        if btc_price:
            print(f"✅ BTC价格: ${btc_price['price']:,.2f}")
            print(f"   24h变化: {btc_price['change_24h']:+.2f}%")
            print(f"   24h成交量: ${btc_price['volume_24h']:,.0f}")
            results['huobi_price'] = True
        else:
            print("❌ 火币价格获取失败")
            results['huobi_price'] = False
    except Exception as e:
        print(f"❌ 错误: {e}")
        results['huobi_price'] = False

    # 测试2：火币K线数据
    print("\n[2/8] 测试火币API - K线数据...")
    try:
        klines = await api.get_huobi_klines('BTCUSDT', '60min', 10)
        if klines:
            print(f"✅ 获取到{len(klines)}根K线")
            latest = klines[-1]
            print(
                f"   最新K线: 开{latest['open']:.2f} 高{latest['high']:.2f} 低{latest['low']:.2f} 收{latest['close']:.2f}")
            results['huobi_klines'] = True
        else:
            print("❌ K线数据获取失败")
            results['huobi_klines'] = False
    except Exception as e:
        print(f"❌ 错误: {e}")
        results['huobi_klines'] = False

    # 测试3：火币深度数据
    print("\n[3/8] 测试火币API - 订单簿深度...")
    try:
        depth = await api.get_huobi_depth('BTCUSDT', 5)
        if depth:
            print(f"✅ 买一价: ${depth['bid_price']:,.2f}")
            print(f"   卖一价: ${depth['ask_price']:,.2f}")
            print(f"   价差: ${depth['spread']:.2f}")
            results['huobi_depth'] = True
        else:
            print("❌ 深度数据获取失败")
            results['huobi_depth'] = False
    except Exception as e:
        print(f"❌ 错误: {e}")
        results['huobi_depth'] = False

    # 测试4：Alternative.me恐慌贪婪指数
    print("\n[4/8] 测试Alternative.me API - 恐慌贪婪指数...")
    try:
        fear_greed = await api.get_fear_greed_index()
        if fear_greed and fear_greed['value'] != 50:
            print(f"✅ 恐慌贪婪指数: {fear_greed['value']}/100")
            print(f"   状态: {fear_greed['emoji']} {fear_greed['status']}")
            print(f"   建议: {fear_greed['advice']}")
            if fear_greed.get('yesterday'):
                print(f"   昨日: {fear_greed['yesterday']} (变化: {fear_greed.get('yesterday_change', 0):+d})")
            results['fear_greed'] = True
        else:
            print("❌ 恐慌贪婪指数获取失败")
            results['fear_greed'] = False
    except Exception as e:
        print(f"❌ 错误: {e}")
        results['fear_greed'] = False

    # 测试5：CoinGecko市值排名
    print("\n[5/8] 测试CoinGecko API - 市值排名...")
    try:
        top_coins = await api.get_top_coins(10)
        if top_coins:
            print(f"✅ 获取到Top {len(top_coins)}币种")
            for i, coin in enumerate(top_coins[:3], 1):
                print(f"   {i}. {coin['symbol']}: ${coin['price']:,.2f} ({coin['change_24h']:+.1f}%)")
            results['coingecko_ranking'] = True
        else:
            print("❌ 市值排名获取失败")
            results['coingecko_ranking'] = False
    except Exception as e:
        print(f"❌ 错误: {e}")
        results['coingecko_ranking'] = False

    # 测试6：涨跌幅榜单
    print("\n[6/8] 测试涨跌幅榜单...")
    try:
        gainers = await api.get_top_gainers()
        losers = await api.get_top_losers()

        if gainers and gainers[0]['symbol'] != '???':
            print(f"✅ 最大涨幅: {gainers[0]['symbol']} +{gainers[0]['change']:.1f}%")
            results['gainers'] = True
        else:
            results['gainers'] = False

        if losers and losers[0]['symbol'] != '???':
            print(f"✅ 最大跌幅: {losers[0]['symbol']} {losers[0]['change']:.1f}%")
            results['losers'] = True
        else:
            results['losers'] = False
    except Exception as e:
        print(f"❌ 错误: {e}")
        results['gainers'] = False
        results['losers'] = False

    # 测试7：市场概览
    print("\n[7/8] 测试市场概览...")
    try:
        market = await api.get_market_overview()
        if market:
            print(f"✅ 总市值: ${market['total_market_cap'] / 1e12:.2f}万亿")
            print(f"   BTC占比: {market['btc_dominance']:.1f}%")
            print(f"   活跃币种: {market['active_cryptocurrencies']:,}")
            results['market_overview'] = True
        else:
            print("❌ 市场概览获取失败")
            results['market_overview'] = False
    except Exception as e:
        print(f"❌ 错误: {e}")
        results['market_overview'] = False

    # 测试8：交易信号生成
    print("\n[8/8] 测试交易信号生成...")
    try:
        signal = await api.generate_trading_signal('ETHUSDT')
        if signal and signal['confidence'] > 0:
            print(f"✅ ETH信号: {signal['signal']} (置信度: {signal['confidence']}%)")
            print(f"   RSI: {signal['rsi']:.1f} ({signal['rsi_signal']})")
            print(f"   MACD: {signal['macd_signal']}")
            print(f"   建议: {signal['recommendation']}")
            results['trading_signal'] = True
        else:
            print("❌ 交易信号生成失败")
            results['trading_signal'] = False
    except Exception as e:
        print(f"❌ 错误: {e}")
        results['trading_signal'] = False

    # 关闭session
    await api.close_session()

    # 测试结果总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test}: {status}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有API测试通过！机器人可以正常使用。")
    elif passed >= total * 0.7:
        print("\n⚠️ 大部分API正常，但部分功能可能受限。")
    else:
        print("\n❌ 多个API失败，请检查网络连接和API配置。")

    return results


async def test_specific_symbol(symbol):
    """测试特定交易对"""
    api = APIManager()

    print(f"\n测试交易对: {symbol}")
    print("-" * 40)

    # 获取价格
    price_data = await api.get_crypto_price(symbol)
    if price_data:
        print(f"价格: ${price_data['price']:,.4f}")
        print(f"24h变化: {price_data['change_24h']:+.2f}%")

    # 生成信号
    signal = await api.generate_trading_signal(symbol)
    if signal:
        print(f"交易信号: {signal['signal']}")
        print(f"RSI: {signal['rsi']:.1f}")

    await api.close_session()


if __name__ == "__main__":
    print("启动API测试...\n")

    # 运行测试
    if len(sys.argv) > 1:
        # 测试特定交易对
        asyncio.run(test_specific_symbol(sys.argv[1]))
    else:
        # 运行完整测试
        asyncio.run(test_all_apis())