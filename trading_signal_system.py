# trading_signal_system.py
"""专业交易信号系统 - 多时间周期分析和自动通知"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class TradingSignalSystem:
    def __init__(self, api_manager, bot_instance=None):
        self.api = api_manager
        self.bot = bot_instance

        # 监控配置
        self.monitored_pairs = [
            'BTCUSDT',
            'ETHUSDT',
            'BNBUSDT',
            'SOLUSDT',
            'ADAUSDT'
        ]

        # 时间周期配置（火币支持的周期）
        self.timeframes = {
            '1h': {'period': '60min', 'name': '1小时', 'weight': 0.2},
            '4h': {'period': '4hour', 'name': '4小时', 'weight': 0.3},
            '1d': {'period': '1day', 'name': '日线', 'weight': 0.5}
        }

        # 信号缓存（避免重复发送）
        self.last_signals = {}
        self.signal_cooldown = 3600  # 1小时内不重复发送相同信号

        # 用户订阅
        self.user_subscriptions = {}  # {user_id: [symbols]}

        self.is_running = False
        self._monitor_task = None

    async def start_monitoring(self):
        """启动信号监控"""
        if not self.is_running:
            self.is_running = True
            self._monitor_task = asyncio.create_task(self.monitor_loop())
            logger.info("Trading signal monitoring started")

    async def stop_monitoring(self):
        """停止信号监控"""
        self.is_running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Trading signal monitoring stopped")

    async def monitor_loop(self):
        """监控主循环"""
        while self.is_running:
            try:
                # 分析所有监控的交易对
                for symbol in self.monitored_pairs:
                    try:
                        signal = await self.analyze_symbol(symbol)
                        if signal and self.should_send_signal(symbol, signal):
                            await self.send_signal_notifications(symbol, signal)
                            self.update_signal_cache(symbol, signal)
                    except Exception as e:
                        logger.error(f"Error analyzing {symbol}: {e}")

                # 每5分钟检查一次
                await asyncio.sleep(300)

            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(60)

    async def analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """分析单个交易对的多时间周期信号"""
        try:
            signals = {}
            total_score = 0

            # 分析每个时间周期
            for tf_key, tf_config in self.timeframes.items():
                tf_signal = await self.analyze_timeframe(symbol, tf_config['period'])
                if tf_signal:
                    signals[tf_key] = tf_signal
                    # 加权计算总分
                    score = tf_signal['score'] * tf_config['weight']
                    total_score += score

            if not signals:
                return None

            # 综合判断
            final_signal = self.calculate_final_signal(signals, total_score)

            # 只返回强信号
            if abs(final_signal['strength']) >= 60:
                return final_signal

            return None

        except Exception as e:
            logger.error(f"Symbol analysis error for {symbol}: {e}")
            return None

    async def analyze_timeframe(self, symbol: str, period: str) -> Optional[Dict]:
        """分析单个时间周期"""
        try:
            # 获取K线数据
            klines = await self.api.get_huobi_klines(symbol, period, 100)
            if not klines or len(klines) < 50:
                return None

            # 提取收盘价
            closes = [k['close'] for k in klines]
            highs = [k['high'] for k in klines]
            lows = [k['low'] for k in klines]
            volumes = [k['volume'] for k in klines]

            # 计算技术指标
            indicators = self.calculate_indicators(closes, highs, lows, volumes)

            # 生成信号
            signal = self.generate_signal(indicators, closes[-1])

            return signal

        except Exception as e:
            logger.error(f"Timeframe analysis error: {e}")
            return None

    def calculate_indicators(self, closes: List[float], highs: List[float],
                             lows: List[float], volumes: List[float]) -> Dict:
        """计算技术指标"""
        indicators = {}

        # 1. RSI
        indicators['rsi'] = self.calculate_rsi(closes, 14)

        # 2. MACD
        indicators['macd'] = self.calculate_macd(closes)

        # 3. 移动平均线
        indicators['ma20'] = sum(closes[-20:]) / 20 if len(closes) >= 20 else closes[-1]
        indicators['ma50'] = sum(closes[-50:]) / 50 if len(closes) >= 50 else closes[-1]

        # 4. 布林带
        indicators['bb'] = self.calculate_bollinger_bands(closes, 20)

        # 5. 成交量分析
        indicators['volume_ma'] = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else volumes[-1]
        indicators['volume_ratio'] = volumes[-1] / indicators['volume_ma'] if indicators['volume_ma'] > 0 else 1

        # 6. ATR（平均真实波幅）
        indicators['atr'] = self.calculate_atr(highs, lows, closes, 14)

        # 7. 支撑阻力位
        indicators['support'] = min(lows[-20:]) if len(lows) >= 20 else lows[-1]
        indicators['resistance'] = max(highs[-20:]) if len(highs) >= 20 else highs[-1]

        return indicators

    def generate_signal(self, indicators: Dict, current_price: float) -> Dict:
        """根据指标生成交易信号"""
        score = 0
        reasons = []

        # RSI信号（权重：25）
        rsi = indicators.get('rsi', 50)
        if rsi < 30:
            score += 25
            reasons.append(f"RSI超卖({rsi:.1f})")
        elif rsi < 40:
            score += 10
            reasons.append(f"RSI偏低({rsi:.1f})")
        elif rsi > 70:
            score -= 25
            reasons.append(f"RSI超买({rsi:.1f})")
        elif rsi > 60:
            score -= 10
            reasons.append(f"RSI偏高({rsi:.1f})")

        # MACD信号（权重：20）
        macd = indicators.get('macd')
        if macd:
            if macd['histogram'] > 0 and macd['trend'] == 'bullish':
                score += 20
                reasons.append("MACD金叉")
            elif macd['histogram'] < 0 and macd['trend'] == 'bearish':
                score -= 20
                reasons.append("MACD死叉")

        # 移动平均线信号（权重：20）
        ma20 = indicators.get('ma20', current_price)
        ma50 = indicators.get('ma50', current_price)

        if current_price > ma20 and current_price > ma50:
            score += 20
            reasons.append("价格在均线上方")
        elif current_price < ma20 and current_price < ma50:
            score -= 20
            reasons.append("价格在均线下方")

        if ma20 > ma50:
            score += 10
            reasons.append("短期均线>长期均线")
        else:
            score -= 10
            reasons.append("短期均线<长期均线")

        # 布林带信号（权重：15）
        bb = indicators.get('bb')
        if bb:
            if current_price < bb['lower']:
                score += 15
                reasons.append("触及布林带下轨")
            elif current_price > bb['upper']:
                score -= 15
                reasons.append("触及布林带上轨")

        # 成交量信号（权重：10）
        volume_ratio = indicators.get('volume_ratio', 1)
        if volume_ratio > 1.5:
            if score > 0:
                score += 10
                reasons.append("放量上涨")
            else:
                score -= 10
                reasons.append("放量下跌")

        # 支撑阻力位信号（权重：10）
        support = indicators.get('support', current_price * 0.95)
        resistance = indicators.get('resistance', current_price * 1.05)

        if current_price <= support * 1.02:
            score += 10
            reasons.append("接近支撑位")
        elif current_price >= resistance * 0.98:
            score -= 10
            reasons.append("接近阻力位")

        return {
            'score': score,
            'reasons': reasons,
            'indicators': {
                'rsi': rsi,
                'macd': macd,
                'ma20': ma20,
                'ma50': ma50,
                'support': support,
                'resistance': resistance,
                'volume_ratio': volume_ratio
            }
        }

    def calculate_final_signal(self, timeframe_signals: Dict, total_score: float) -> Dict:
        """计算最终信号"""
        current_time = datetime.now()

        # 收集所有原因
        all_reasons = []
        dominant_timeframe = None
        max_score = 0

        for tf_key, tf_signal in timeframe_signals.items():
            tf_name = self.timeframes[tf_key]['name']
            for reason in tf_signal['reasons'][:2]:  # 每个时间周期取前2个原因
                all_reasons.append(f"{tf_name}: {reason}")

            # 找出最强的时间周期
            if abs(tf_signal['score']) > abs(max_score):
                max_score = tf_signal['score']
                dominant_timeframe = tf_name

        # 确定信号方向和强度
        if total_score > 0:
            direction = "做多"
            direction_emoji = "🟢"
            action = "LONG"
        else:
            direction = "做空"
            direction_emoji = "🔴"
            action = "SHORT"

        strength = abs(total_score)

        # 确定信号级别
        if strength >= 80:
            level = "强烈"
            level_emoji = "🔥🔥🔥"
        elif strength >= 60:
            level = "明确"
            level_emoji = "🔥🔥"
        else:
            level = "一般"
            level_emoji = "🔥"

        # 生成建议
        if action == "LONG":
            if strength >= 80:
                suggestion = "强烈建议做多，多个时间周期共振"
            elif strength >= 60:
                suggestion = "建议做多，技术面偏多"
            else:
                suggestion = "可以考虑轻仓做多"
        else:
            if strength >= 80:
                suggestion = "强烈建议做空，空头趋势明显"
            elif strength >= 60:
                suggestion = "建议做空，技术面偏空"
            else:
                suggestion = "可以考虑轻仓做空"

        # 风险管理建议
        risk_management = self.generate_risk_management(timeframe_signals)

        return {
            'action': action,
            'direction': direction,
            'direction_emoji': direction_emoji,
            'strength': strength,
            'level': level,
            'level_emoji': level_emoji,
            'dominant_timeframe': dominant_timeframe,
            'reasons': all_reasons[:5],  # 最多5个原因
            'suggestion': suggestion,
            'risk_management': risk_management,
            'timeframe_signals': timeframe_signals,
            'timestamp': current_time
        }

    def generate_risk_management(self, timeframe_signals: Dict) -> Dict:
        """生成风险管理建议"""
        # 根据不同时间周期的信号给出止损止盈建议

        # 获取支撑阻力位
        supports = []
        resistances = []

        for tf_signal in timeframe_signals.values():
            if 'indicators' in tf_signal:
                supports.append(tf_signal['indicators'].get('support', 0))
                resistances.append(tf_signal['indicators'].get('resistance', 0))

        avg_support = sum(supports) / len(supports) if supports else 0
        avg_resistance = sum(resistances) / len(resistances) if resistances else 0

        return {
            'stop_loss': avg_support * 0.98,  # 支撑位下方2%
            'take_profit_1': avg_resistance * 0.99,  # 阻力位附近
            'take_profit_2': avg_resistance * 1.02,  # 阻力位上方2%
            'position_size': '建议仓位不超过总资金的5%',
            'risk_reward_ratio': '1:2'  # 风险收益比
        }

    def should_send_signal(self, symbol: str, signal: Dict) -> bool:
        """判断是否应该发送信号"""
        cache_key = f"{symbol}_{signal['action']}"

        if cache_key in self.last_signals:
            last_time = self.last_signals[cache_key]
            if datetime.now() - last_time < timedelta(seconds=self.signal_cooldown):
                return False

        return True

    def update_signal_cache(self, symbol: str, signal: Dict):
        """更新信号缓存"""
        cache_key = f"{symbol}_{signal['action']}"
        self.last_signals[cache_key] = datetime.now()

    async def send_signal_notifications(self, symbol: str, signal: Dict):
        """发送信号通知"""
        if not self.bot:
            return

        # 格式化消息
        message = self.format_signal_message(symbol, signal)

        # 发送给所有订阅用户
        for user_id, subscribed_symbols in self.user_subscriptions.items():
            if symbol in subscribed_symbols or 'ALL' in subscribed_symbols:
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    logger.info(f"Sent signal for {symbol} to user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to send signal to {user_id}: {e}")

    def format_signal_message(self, symbol: str, signal: Dict) -> str:
        """格式化信号消息"""
        return f"""
🚨 **交易信号提醒**

**币种:** {symbol.replace('USDT', '/USDT')}
**方向:** {signal['direction_emoji']} {signal['direction']}
**强度:** {signal['level_emoji']} {signal['level']} ({signal['strength']:.0f}/100)
**主要周期:** {signal['dominant_timeframe']}

**信号原因:**
{chr(10).join(f"• {reason}" for reason in signal['reasons'])}

**操作建议:**
{signal['suggestion']}

**风险管理:**
• 止损: ${signal['risk_management']['stop_loss']:.2f}
• 目标1: ${signal['risk_management']['take_profit_1']:.2f}
• 目标2: ${signal['risk_management']['take_profit_2']:.2f}
• {signal['risk_management']['position_size']}

⏰ 时间: {signal['timestamp'].strftime('%H:%M:%S')}

⚠️ *请结合自己的分析判断，控制风险*
"""

    def subscribe_user(self, user_id: int, symbols: List[str]):
        """订阅用户"""
        self.user_subscriptions[user_id] = symbols
        logger.info(f"User {user_id} subscribed to {symbols}")

    def unsubscribe_user(self, user_id: int):
        """取消订阅"""
        if user_id in self.user_subscriptions:
            del self.user_subscriptions[user_id]
            logger.info(f"User {user_id} unsubscribed")

    def get_user_subscriptions(self, user_id: int) -> List[str]:
        """获取用户订阅"""
        return self.user_subscriptions.get(user_id, [])

    # ===== 技术指标计算方法 =====

    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
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

    def calculate_macd(self, prices: List[float]) -> Optional[Dict]:
        """计算MACD"""
        if len(prices) < 26:
            return None

        # 计算EMA
        ema12 = self._calculate_ema(prices, 12)
        ema26 = self._calculate_ema(prices, 26)

        if ema12 is None or ema26 is None:
            return None

        macd_line = ema12 - ema26
        signal_line = self._calculate_ema([macd_line], 9) if len(prices) > 35 else macd_line
        histogram = macd_line - (signal_line if signal_line else macd_line)

        # 判断趋势
        if len(prices) >= 35:
            prev_macd = self._calculate_ema(prices[:-1], 12) - self._calculate_ema(prices[:-1], 26)
            trend = 'bullish' if macd_line > prev_macd else 'bearish'
        else:
            trend = 'bullish' if macd_line > 0 else 'bearish'

        return {
            'macd': round(macd_line, 4),
            'signal': round(signal_line if signal_line else macd_line, 4),
            'histogram': round(histogram, 4),
            'trend': trend
        }

    def _calculate_ema(self, prices: List[float], period: int) -> Optional[float]:
        """计算EMA"""
        if len(prices) < period:
            return None

        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period

        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    def calculate_bollinger_bands(self, prices: List[float], period: int = 20) -> Optional[Dict]:
        """计算布林带"""
        if len(prices) < period:
            return None

        # 计算中轨（SMA）
        middle = sum(prices[-period:]) / period

        # 计算标准差
        squared_diff = [(p - middle) ** 2 for p in prices[-period:]]
        std_dev = (sum(squared_diff) / period) ** 0.5

        return {
            'upper': middle + (2 * std_dev),
            'middle': middle,
            'lower': middle - (2 * std_dev),
            'width': 4 * std_dev
        }

    def calculate_atr(self, highs: List[float], lows: List[float],
                      closes: List[float], period: int = 14) -> float:
        """计算ATR（平均真实波幅）"""
        if len(highs) < period + 1:
            return 0

        true_ranges = []
        for i in range(1, len(highs)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1])
            )
            true_ranges.append(tr)

        if len(true_ranges) >= period:
            atr = sum(true_ranges[-period:]) / period
            return round(atr, 4)

        return 0