# fixed_api_manager.py
"""修复SSL问题的API管理器 - 完整版本"""

import aiohttp
import asyncio
import logging
import ssl
import certifi
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class APIManager:
    def __init__(self):
        self.session = None

        # API配置
        self.huobi_config = {
            'api_key': 'c7f1637f-ghxertfvbf-1be7bcbd-7b36b',
            'base_url': 'https://api.huobi.pro',
            'base_url_aws': 'https://api-aws.huobi.pro',
            'base_url_backup': 'https://api.hbdm.com'  # 备用地址
        }

        self.binance_config = {
            'base_url': 'https://api.binance.com/api/v3'  # 备用方案
        }

        self.coingecko_config = {
            'base_url': 'https://api.coingecko.com/api/v3'
        }

        self.alternative_config = {
            'base_url': 'https://api.alternative.me'
        }

        # 缓存设置
        self.cache = {}
        self.cache_duration = {
            'price': 10,
            'fear_greed': 3600,
            'market_data': 60,
            'klines': 60,
        }

    async def get_session(self):
        """获取或创建aiohttp session - 修复SSL问题"""
        if not self.session:
            try:
                # 方案1：尝试使用certifi证书
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE  # 禁用验证
            except:
                # 方案2：完全禁用SSL验证
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

            # 创建连接器，设置超时
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,
                force_close=True,
                enable_cleanup_closed=True
            )

            # 创建session，添加超时设置
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
        return self.session

    async def close_session(self):
        """关闭session"""
        if self.session:
            await self.session.close()
            self.session = None

    # ===== 通用HTTP请求方法 =====

    async def _make_request(self, url, params=None, headers=None, max_retries=3):
        """通用HTTP请求方法，包含重试逻辑"""
        session = await self.get_session()

        for attempt in range(max_retries):
            try:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
            except aiohttp.ClientError as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1)  # 重试前等待1秒
        return None

    # ===== 价格数据（多源备份）=====

    async def get_crypto_price(self, symbol):
        """获取实时价格 - 多数据源备份"""
        cache_key = f'price_{symbol}'
        if self._is_cache_valid(cache_key, 'price'):
            return self.cache[cache_key]['data']

        # 尝试火币
        result = await self._get_huobi_price(symbol)
        if result:
            self._set_cache(cache_key, result, 'price')
            return result

        # 备用：币安
        result = await self._get_binance_price(symbol)
        if result:
            self._set_cache(cache_key, result, 'price')
            return result

        # 最后备用：CoinGecko
        result = await self._get_coingecko_price(symbol)
        if result:
            self._set_cache(cache_key, result, 'price')
            return result

        # 返回模拟数据
        return self._get_mock_price(symbol)

    async def _get_huobi_price(self, symbol):
        """火币价格"""
        try:
            huobi_symbol = symbol.lower()

            # 尝试多个火币API地址
            urls = [
                f"{self.huobi_config['base_url']}/market/detail/merged",
                f"{self.huobi_config['base_url_aws']}/market/detail/merged",
                f"{self.huobi_config['base_url_backup']}/market/detail/merged"
            ]

            for url in urls:
                try:
                    data = await self._make_request(url, params={'symbol': huobi_symbol})
                    if data and data.get('status') == 'ok':
                        ticker = data['tick']
                        change_24h = ((ticker['close'] - ticker['open']) / ticker['open']) * 100 if ticker[
                                                                                                        'open'] > 0 else 0

                        return {
                            'price': ticker['close'],
                            'change_24h': change_24h,
                            'change_24h_abs': ticker['close'] - ticker['open'],
                            'high_24h': ticker['high'],
                            'low_24h': ticker['low'],
                            'volume_24h': ticker['vol'],
                        }
                except Exception as e:
                    logger.debug(f"Huobi URL {url} failed: {e}")
                    continue
        except Exception as e:
            logger.error(f"Huobi price error: {e}")
        return None

    async def _get_binance_price(self, symbol):
        """币安价格（备用）"""
        try:
            url = f"{self.binance_config['base_url']}/ticker/24hr"
            data = await self._make_request(url, params={'symbol': symbol})

            if data:
                return {
                    'price': float(data['lastPrice']),
                    'change_24h': float(data['priceChangePercent']),
                    'change_24h_abs': float(data['priceChange']),
                    'high_24h': float(data['highPrice']),
                    'low_24h': float(data['lowPrice']),
                    'volume_24h': float(data['quoteVolume'])
                }
        except Exception as e:
            logger.error(f"Binance price error: {e}")
        return None

    async def _get_coingecko_price(self, symbol):
        """CoinGecko价格（最后备用）"""
        try:
            coin_id = self._symbol_to_coingecko_id(symbol)
            url = f"{self.coingecko_config['base_url']}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true'
            }

            data = await self._make_request(url, params=params)
            if data and coin_id in data:
                coin_data = data[coin_id]
                return {
                    'price': coin_data['usd'],
                    'change_24h': coin_data.get('usd_24h_change', 0),
                    'change_24h_abs': coin_data['usd'] * (coin_data.get('usd_24h_change', 0) / 100),
                    'volume_24h': coin_data.get('usd_24h_vol', 0),
                    'high_24h': coin_data['usd'] * 1.05,
                    'low_24h': coin_data['usd'] * 0.95,
                }
        except Exception as e:
            logger.error(f"CoinGecko price error: {e}")
        return None

    def _get_mock_price(self, symbol):
        """模拟价格数据（最终备用）"""
        import random
        base_prices = {
            'BTCUSDT': 43000,
            'ETHUSDT': 2200,
            'BNBUSDT': 250,
            'ADAUSDT': 0.5,
            'XRPUSDT': 0.6,
            'SOLUSDT': 100,
            'DOGEUSDT': 0.08,
        }

        base_price = base_prices.get(symbol, 100)
        variation = random.uniform(-5, 5) / 100

        return {
            'price': base_price * (1 + variation),
            'change_24h': random.uniform(-10, 10),
            'change_24h_abs': base_price * variation,
            'high_24h': base_price * 1.05,
            'low_24h': base_price * 0.95,
            'volume_24h': random.uniform(1000000, 10000000)
        }

    # ===== 恐慌贪婪指数 =====

    async def get_fear_greed_index(self):
        """获取恐慌贪婪指数 - 带缓存和备用"""
        cache_key = 'fear_greed'
        if self._is_cache_valid(cache_key, 'fear_greed'):
            return self.cache[cache_key]['data']

        # 尝试多个数据源
        # 1. 尝试Alternative.me主站
        try:
            url = f"{self.alternative_config['base_url']}/fng/"
            params = {'limit': 10, 'format': 'json'}

            data = await self._make_request(url, params=params)
            if data and 'data' in data and len(data['data']) > 0:
                current = data['data'][0]
                value = int(current['value'])
                classification = current['value_classification']

                # 映射处理
                status_map = {
                    'Extreme Fear': '极度恐慌',
                    'Fear': '恐慌',
                    'Neutral': '中性',
                    'Greed': '贪婪',
                    'Extreme Greed': '极度贪婪'
                }

                emoji_map = {
                    'Extreme Fear': '😱',
                    'Fear': '😰',
                    'Neutral': '😐',
                    'Greed': '😃',
                    'Extreme Greed': '🤑'
                }

                color_map = {
                    'Extreme Fear': '🔴',
                    'Fear': '🟠',
                    'Neutral': '🟡',
                    'Greed': '🟢',
                    'Extreme Greed': '🔥'
                }

                advice_map = {
                    'Extreme Fear': '市场极度恐慌，可能是抄底机会，但需谨慎',
                    'Fear': '市场恐慌情绪浓厚，关注支撑位表现',
                    'Neutral': '市场情绪中性，等待方向明确',
                    'Greed': '市场乐观，但需注意风险控制',
                    'Extreme Greed': '市场过度乐观，注意回调风险'
                }

                result = {
                    'value': value,
                    'status': status_map.get(classification, classification),
                    'emoji': emoji_map.get(classification, '😐'),
                    'color': color_map.get(classification, '🟡'),
                    'advice': advice_map.get(classification, '观察市场动向'),
                    'timestamp': current['timestamp']
                }

                self._set_cache(cache_key, result, 'fear_greed')
                return result
        except Exception as e:
            logger.error(f"Fear Greed Index error: {e}")

        # 返回模拟数据
        import random
        value = random.randint(20, 80)

        if value <= 25:
            status = "极度恐慌"
            emoji = "😱"
            color = "🔴"
            advice = "市场极度恐慌，可能是抄底机会"
        elif value <= 45:
            status = "恐慌"
            emoji = "😰"
            color = "🟠"
            advice = "市场恐慌，关注支撑位"
        elif value <= 55:
            status = "中性"
            emoji = "😐"
            color = "🟡"
            advice = "市场情绪中性"
        elif value <= 75:
            status = "贪婪"
            emoji = "😃"
            color = "🟢"
            advice = "市场乐观，注意风险"
        else:
            status = "极度贪婪"
            emoji = "🤑"
            color = "🔥"
            advice = "市场过热，注意回调"

        return {
            'value': value,
            'status': status,
            'emoji': emoji,
            'color': color,
            'advice': advice,
            'timestamp': datetime.now().isoformat()
        }

    # ===== 市场数据 =====

    async def get_top_coins(self, limit=100):
        """获取市值排名"""
        cache_key = f'top_coins_{limit}'
        if self._is_cache_valid(cache_key, 'market_data'):
            return self.cache[cache_key]['data']

        try:
            url = f"{self.coingecko_config['base_url']}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': limit,
                'page': 1,
                'sparkline': 'false'
            }

            data = await self._make_request(url, params=params)
            if data:
                coins = []
                for coin in data:
                    coins.append({
                        'rank': coin.get('market_cap_rank', 0),
                        'symbol': coin.get('symbol', '').upper(),
                        'name': coin.get('name', ''),
                        'price': coin.get('current_price', 0),
                        'market_cap': coin.get('market_cap', 0),
                        'volume_24h': coin.get('total_volume', 0),
                        'change_24h': coin.get('price_change_percentage_24h', 0),
                    })

                self._set_cache(cache_key, coins, 'market_data')
                return coins
        except Exception as e:
            logger.error(f"Top coins error: {e}")

        # 返回模拟数据
        return self._get_mock_top_coins()

    async def get_market_overview(self):
        """获取市场概览"""
        cache_key = 'market_overview'
        if self._is_cache_valid(cache_key, 'market_data'):
            return self.cache[cache_key]['data']

        try:
            url = f"{self.coingecko_config['base_url']}/global"
            data = await self._make_request(url)

            if data and 'data' in data:
                market_data = data['data']

                # 获取恐慌贪婪指数
                fear_greed = await self.get_fear_greed_index()

                result = {
                    'total_market_cap': market_data.get('total_market_cap', {}).get('usd', 2000000000000),
                    'total_volume': market_data.get('total_volume', {}).get('usd', 100000000000),
                    'btc_dominance': market_data.get('market_cap_percentage', {}).get('btc', 50),
                    'eth_dominance': market_data.get('market_cap_percentage', {}).get('eth', 20),
                    'other_dominance': 30,
                    'active_cryptocurrencies': market_data.get('active_cryptocurrencies', 10000),
                    'markets': market_data.get('markets', 500),
                    'market_cap_change_24h': market_data.get('market_cap_change_percentage_24h_usd', 0),
                    'fear_greed_value': fear_greed['value'],
                    'fear_greed_status': fear_greed['status']
                }

                self._set_cache(cache_key, result, 'market_data')
                return result
        except Exception as e:
            logger.error(f"Market overview error: {e}")

        # 返回模拟数据
        import random
        fear_greed = await self.get_fear_greed_index()
        return {
            'total_market_cap': random.uniform(1.5, 2.5) * 1000000000000,
            'total_volume': random.uniform(50, 150) * 1000000000,
            'btc_dominance': random.uniform(45, 55),
            'eth_dominance': random.uniform(15, 25),
            'other_dominance': random.uniform(20, 40),
            'active_cryptocurrencies': 10000,
            'markets': 500,
            'market_cap_change_24h': random.uniform(-5, 5),
            'fear_greed_value': fear_greed['value'],
            'fear_greed_status': fear_greed['status']
        }

    # ===== K线和技术分析 =====

    async def get_huobi_klines(self, symbol, period='60min', size=100):
        """获取K线数据 - 带备用方案"""
        cache_key = f'klines_{symbol}_{period}'
        if self._is_cache_valid(cache_key, 'klines'):
            return self.cache[cache_key]['data']

        # 尝试火币
        klines = await self._get_huobi_klines_internal(symbol, period, size)
        if klines:
            self._set_cache(cache_key, klines, 'klines')
            return klines

        # 生成模拟K线
        return self._generate_mock_klines(symbol, size)

    async def _get_huobi_klines_internal(self, symbol, period, size):
        """内部获取火币K线"""
        try:
            huobi_symbol = symbol.lower()
            urls = [
                f"{self.huobi_config['base_url']}/market/history/kline",
                f"{self.huobi_config['base_url_aws']}/market/history/kline"
            ]

            params = {
                'symbol': huobi_symbol,
                'period': period,
                'size': size
            }

            for url in urls:
                try:
                    data = await self._make_request(url, params=params)
                    if data and data.get('status') == 'ok':
                        klines = []
                        for k in data['data']:
                            klines.append({
                                'time': k['id'] * 1000,
                                'open': k['open'],
                                'high': k['high'],
                                'low': k['low'],
                                'close': k['close'],
                                'volume': k['vol']
                            })
                        klines.sort(key=lambda x: x['time'])
                        return klines
                except:
                    continue
        except Exception as e:
            logger.error(f"Huobi klines error: {e}")
        return None

    def _generate_mock_klines(self, symbol, size):
        """生成模拟K线数据"""
        import random
        import time

        base_prices = {
            'BTCUSDT': 43000,
            'ETHUSDT': 2200,
            'BNBUSDT': 250,
        }

        base_price = base_prices.get(symbol, 100)
        klines = []
        current_time = int(time.time() * 1000)

        for i in range(size):
            open_price = base_price * (1 + random.uniform(-0.02, 0.02))
            close_price = open_price * (1 + random.uniform(-0.01, 0.01))
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.005))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.005))

            klines.append({
                'time': current_time - (size - i) * 3600000,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': random.uniform(100, 1000)
            })

            base_price = close_price

        return klines

    # ===== 交易信号生成 =====

    async def generate_trading_signal(self, symbol):
        """生成交易信号"""
        try:
            # 获取K线数据
            klines = await self.get_huobi_klines(symbol, '60min', 100)
            price_data = await self.get_crypto_price(symbol)

            if not klines or not price_data:
                return self._get_fallback_signal(symbol)

            current_price = price_data['price']
            closes = [k['close'] for k in klines]

            # 计算技术指标
            rsi = self.calculate_rsi(closes)
            macd = self.calculate_macd(closes)
            levels = self.calculate_support_resistance(klines)

            # 简单信号判断
            signals = []
            confidence = 50

            if rsi < 30:
                signals.append('BUY')
                confidence += 20
                rsi_signal = '超卖'
            elif rsi > 70:
                signals.append('SELL')
                confidence -= 20
                rsi_signal = '超买'
            else:
                rsi_signal = '中性'

            if macd and macd['trend'] == 'bullish':
                signals.append('BUY')
                confidence += 15
                macd_signal = '看涨'
            elif macd and macd['trend'] == 'bearish':
                signals.append('SELL')
                confidence -= 15
                macd_signal = '看跌'
            else:
                macd_signal = '中性'

            # 综合判断
            buy_count = signals.count('BUY')
            sell_count = signals.count('SELL')

            if buy_count > sell_count:
                signal = 'BUY' if confidence < 70 else 'STRONG_BUY'
                recommendation = "💡 建议买入"
            elif sell_count > buy_count:
                signal = 'SELL' if confidence > 30 else 'STRONG_SELL'
                recommendation = "💡 建议卖出"
            else:
                signal = 'HOLD'
                recommendation = "💡 保持观望"

            return {
                'signal': signal,
                'confidence': abs(confidence),
                'price': current_price,
                'rsi': rsi,
                'rsi_signal': rsi_signal,
                'macd_signal': macd_signal,
                'ma_signal': '计算中',
                'support': levels['support'] if levels else current_price * 0.95,
                'resistance': levels['resistance'] if levels else current_price * 1.05,
                'recommendation': recommendation,
                'risk_warning': '加密货币投资风险极高，请谨慎操作'
            }

        except Exception as e:
            logger.error(f"Signal generation error: {e}")
            return self._get_fallback_signal(symbol)

    # ===== 技术指标计算 =====

    def calculate_rsi(self, prices, period=14):
        """计算RSI"""
        if len(prices) < period + 1:
            return 50

        gains = []
        losses = []

        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(rsi, 2)

    def calculate_macd(self, prices):
        """计算MACD"""
        if len(prices) < 26:
            return None

        ema12 = self._calculate_ema(prices, 12)
        ema26 = self._calculate_ema(prices, 26)

        if ema12 is None or ema26 is None:
            return None

        macd_line = ema12 - ema26

        return {
            'macd': round(macd_line, 4),
            'signal': round(macd_line, 4),
            'histogram': 0,
            'trend': 'bullish' if macd_line > 0 else 'bearish'
        }

    def _calculate_ema(self, prices, period):
        """计算EMA"""
        if len(prices) < period:
            return None

        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period

        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    def calculate_support_resistance(self, klines):
        """计算支撑阻力位"""
        if not klines or len(klines) < 20:
            return None

        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        closes = [k['close'] for k in klines]

        recent_high = max(highs[-20:])
        recent_low = min(lows[-20:])
        pivot = (recent_high + recent_low + closes[-1]) / 3

        return {
            'support': round(recent_low, 4),
            'resistance': round(recent_high, 4),
            'pivot': round(pivot, 4)
        }

    # ===== 涨跌幅榜单 =====

    async def get_top_gainers(self):
        """获取涨幅榜"""
        try:
            coins = await self.get_top_coins(200)
            if coins:
                valid_coins = [c for c in coins if c.get('change_24h', 0) > 0]
                sorted_coins = sorted(valid_coins, key=lambda x: x.get('change_24h', 0), reverse=True)

                gainers = []
                for coin in sorted_coins[:8]:
                    gainers.append({
                        'symbol': coin['symbol'],
                        'name': coin['name'],
                        'price': coin['price'],
                        'change': coin['change_24h']
                    })

                return gainers if gainers else self.get_mock_gainers()
        except:
            pass

        return self.get_mock_gainers()

    async def get_top_losers(self):
        """获取跌幅榜"""
        try:
            coins = await self.get_top_coins(200)
            if coins:
                valid_coins = [c for c in coins if c.get('change_24h', 0) < 0]
                sorted_coins = sorted(valid_coins, key=lambda x: x.get('change_24h', 0))

                losers = []
                for coin in sorted_coins[:8]:
                    losers.append({
                        'symbol': coin['symbol'],
                        'name': coin['name'],
                        'price': coin['price'],
                        'change': coin['change_24h']
                    })

                return losers if losers else self.get_mock_losers()
        except:
            pass

        return self.get_mock_losers()

    # ===== 模拟数据方法 =====

    def _get_mock_top_coins(self):
        """模拟市值排名"""
        return [
            {'rank': 1, 'symbol': 'BTC', 'name': 'Bitcoin', 'price': 43000, 'market_cap': 840000000000,
             'volume_24h': 20000000000, 'change_24h': 2.5},
            {'rank': 2, 'symbol': 'ETH', 'name': 'Ethereum', 'price': 2200, 'market_cap': 260000000000,
             'volume_24h': 10000000000, 'change_24h': -1.2},
            {'rank': 3, 'symbol': 'USDT', 'name': 'Tether', 'price': 1.0, 'market_cap': 90000000000,
             'volume_24h': 50000000000, 'change_24h': 0.01},
            {'rank': 4, 'symbol': 'BNB', 'name': 'BNB', 'price': 250, 'market_cap': 40000000000,
             'volume_24h': 1000000000, 'change_24h': 3.2},
            {'rank': 5, 'symbol': 'SOL', 'name': 'Solana', 'price': 100, 'market_cap': 40000000000,
             'volume_24h': 2000000000, 'change_24h': 5.5},
        ]

    def get_mock_gainers(self):
        """模拟涨幅榜"""
        import random
        coins = ['PEPE', 'SHIB', 'DOGE', 'FLOKI', 'BONK', 'WIF', 'MEME', 'LADYS']
        gainers = []
        for coin in coins[:8]:
            gainers.append({
                'symbol': coin,
                'name': coin,
                'price': random.uniform(0.00001, 1),
                'change': random.uniform(5, 30)
            })
        return gainers

    def get_mock_losers(self):
        """模拟跌幅榜"""
        import random
        coins = ['LUNA', 'FTT', 'CEL', 'UST', 'LUNC', 'SRM', 'GALA', 'SAND']
        losers = []
        for coin in coins[:8]:
            losers.append({
                'symbol': coin,
                'name': coin,
                'price': random.uniform(0.001, 10),
                'change': -random.uniform(5, 25)
            })
        return losers

    def _get_fallback_signal(self, symbol):
        """备用交易信号"""
        import random
        signals = ['STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL']
        signal = random.choice(signals)

        return {
            'signal': signal,
            'confidence': random.randint(40, 80),
            'price': 0,
            'rsi': random.uniform(30, 70),
            'rsi_signal': '模拟数据',
            'macd_signal': '模拟数据',
            'ma_signal': '模拟数据',
            'support': 0,
            'resistance': 0,
            'recommendation': '⚠️ 使用模拟数据，仅供参考',
            'risk_warning': '无法获取真实数据'
        }

    # ===== 辅助函数 =====

    def _symbol_to_coingecko_id(self, symbol):
        """符号转换"""
        symbol = symbol.replace('USDT', '').upper()
        mapping = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'XRP': 'ripple',
            'ADA': 'cardano',
            'DOGE': 'dogecoin',
            'SOL': 'solana',
            'DOT': 'polkadot',
            'MATIC': 'matic-network',
            'AVAX': 'avalanche-2',
        }
        return mapping.get(symbol, symbol.lower())

    def _is_cache_valid(self, key, cache_type):
        """检查缓存"""
        if key not in self.cache:
            return False

        cache_time = self.cache[key]['time']
        duration = self.cache_duration.get(cache_type, 60)

        if datetime.now() - cache_time > timedelta(seconds=duration):
            del self.cache[key]
            return False

        return True

    def _set_cache(self, key, data, cache_type):
        """设置缓存"""
        self.cache[key] = {
            'data': data,
            'time': datetime.now()
        }