# auto_trading_system.py
"""自动合约交易系统 - 支持真实交易和模拟测试"""

import asyncio
import aiohttp
import hashlib
import hmac
import base64
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TradingMode(Enum):
    """交易模式"""
    REAL = "real"  # 真实交易
    SIMULATION = "sim"  # 模拟交易


class OrderSide(Enum):
    """订单方向"""
    BUY_LONG = "buy"  # 开多
    SELL_SHORT = "sell"  # 开空
    CLOSE_LONG = "sell"  # 平多
    CLOSE_SHORT = "buy"  # 平空


@dataclass
class TradingConfig:
    """交易配置"""
    api_key: str = ""
    api_secret: str = ""
    mode: TradingMode = TradingMode.SIMULATION
    auto_trade: bool = False  # 是否自动交易
    default_amount: float = 100  # 默认交易金额(USDT)
    default_leverage: int = 10  # 默认杠杆
    max_position_size: float = 1000  # 最大持仓金额
    stop_loss_ratio: float = 0.05  # 止损比例 5%
    take_profit_ratio: float = 0.10  # 止盈比例 10%
    max_daily_trades: int = 10  # 每日最大交易次数
    max_daily_loss: float = 500  # 每日最大亏损(USDT)
    allowed_symbols: List[str] = None  # 允许交易的币种


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    side: str  # long/short
    amount: float  # 持仓数量
    avg_price: float  # 开仓均价
    current_price: float  # 当前价格
    pnl: float  # 盈亏
    pnl_ratio: float  # 盈亏率
    margin: float  # 保证金
    leverage: int  # 杠杆
    liquidation_price: float  # 强平价格
    timestamp: datetime


@dataclass
class SimulatedAccount:
    """模拟账户"""
    balance: float = 10000  # 初始余额
    available: float = 10000  # 可用余额
    positions: Dict[str, Position] = None
    trade_history: List[Dict] = None
    daily_pnl: float = 0
    total_pnl: float = 0
    win_rate: float = 0
    total_trades: int = 0
    winning_trades: int = 0


class AutoTradingSystem:
    def __init__(self, signal_system=None):
        self.signal_system = signal_system
        self.user_configs = {}  # {user_id: TradingConfig}
        self.sim_accounts = {}  # {user_id: SimulatedAccount}
        self.real_positions = {}  # {user_id: {symbol: Position}}
        self.trade_history = {}  # {user_id: [trades]}
        self.is_running = False
        self._monitor_task = None

        # 火币合约API
        self.huobi_futures_url = "https://api.hbdm.com"

    # ===== 用户配置管理 =====

    def set_user_config(self, user_id: int, config: TradingConfig):
        """设置用户交易配置"""
        self.user_configs[user_id] = config

        # 初始化模拟账户
        if config.mode == TradingMode.SIMULATION:
            if user_id not in self.sim_accounts:
                self.sim_accounts[user_id] = SimulatedAccount(
                    positions={},
                    trade_history=[]
                )

        logger.info(f"User {user_id} config set: mode={config.mode.value}, auto={config.auto_trade}")

    def get_user_config(self, user_id: int) -> Optional[TradingConfig]:
        """获取用户配置"""
        return self.user_configs.get(user_id)

    # ===== 火币合约API =====

    def _generate_signature(self, method: str, path: str, params: Dict, secret: str) -> str:
        """生成火币API签名"""
        # 排序参数
        sorted_params = sorted(params.items())
        query_string = "&".join([f"{k}={v}" for k, v in sorted_params])

        # 构建签名字符串
        sign_str = f"{method}\napi.hbdm.com\n{path}\n{query_string}"

        # HMAC SHA256签名
        signature = hmac.new(
            secret.encode('utf-8'),
            sign_str.encode('utf-8'),
            hashlib.sha256
        ).digest()

        # Base64编码
        return base64.b64encode(signature).decode()

    async def get_account_info(self, user_id: int) -> Dict:
        """获取账户信息"""
        config = self.get_user_config(user_id)
        if not config:
            return None

        if config.mode == TradingMode.SIMULATION:
            # 返回模拟账户信息
            sim_account = self.sim_accounts.get(user_id)
            if sim_account:
                return {
                    'mode': 'simulation',
                    'balance': sim_account.balance,
                    'available': sim_account.available,
                    'positions': len(sim_account.positions) if sim_account.positions else 0,
                    'daily_pnl': sim_account.daily_pnl,
                    'total_pnl': sim_account.total_pnl,
                    'win_rate': sim_account.win_rate
                }
        else:
            # 调用真实API
            return await self._get_real_account_info(config)

    async def _get_real_account_info(self, config: TradingConfig) -> Dict:
        """获取真实账户信息"""
        try:
            path = "/linear-swap-api/v1/swap_cross_account_info"
            params = {
                'AccessKeyId': config.api_key,
                'SignatureMethod': 'HmacSHA256',
                'SignatureVersion': '2',
                'Timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
            }

            # 生成签名
            params['Signature'] = self._generate_signature('GET', path, params, config.api_secret)

            # 发送请求
            url = f"{self.huobi_futures_url}{path}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['status'] == 'ok':
                            account = data['data'][0] if data['data'] else {}
                            return {
                                'mode': 'real',
                                'balance': account.get('margin_balance', 0),
                                'available': account.get('margin_available', 0),
                                'positions': account.get('margin_position', 0),
                                'profit_real': account.get('profit_real', 0),
                                'profit_unreal': account.get('profit_unreal', 0)
                            }
        except Exception as e:
            logger.error(f"Get real account error: {e}")
        return None

    async def get_positions(self, user_id: int) -> List[Position]:
        """获取当前持仓"""
        config = self.get_user_config(user_id)
        if not config:
            return []

        if config.mode == TradingMode.SIMULATION:
            sim_account = self.sim_accounts.get(user_id)
            if sim_account and sim_account.positions:
                return list(sim_account.positions.values())
            return []
        else:
            return await self._get_real_positions(config)

    async def _get_real_positions(self, config: TradingConfig) -> List[Position]:
        """获取真实持仓"""
        try:
            path = "/linear-swap-api/v1/swap_cross_position_info"
            params = {
                'AccessKeyId': config.api_key,
                'SignatureMethod': 'HmacSHA256',
                'SignatureVersion': '2',
                'Timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
            }

            params['Signature'] = self._generate_signature('GET', path, params, config.api_secret)

            url = f"{self.huobi_futures_url}{path}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['status'] == 'ok':
                            positions = []
                            for pos in data['data']:
                                positions.append(Position(
                                    symbol=pos['contract_code'],
                                    side='long' if pos['direction'] == 'buy' else 'short',
                                    amount=pos['volume'],
                                    avg_price=pos['cost_open'],
                                    current_price=pos['last_price'],
                                    pnl=pos['profit'],
                                    pnl_ratio=pos['profit_rate'],
                                    margin=pos['margin_occupied'],
                                    leverage=pos['lever_rate'],
                                    liquidation_price=pos.get('liquidation_price', 0),
                                    timestamp=datetime.now()
                                ))
                            return positions
        except Exception as e:
            logger.error(f"Get real positions error: {e}")
        return []

    # ===== 交易执行 =====

    async def execute_trade(self, user_id: int, symbol: str, side: str,
                            amount: float = None, leverage: int = None) -> Dict:
        """执行交易"""
        config = self.get_user_config(user_id)
        if not config:
            return {'success': False, 'error': '未设置交易配置'}

        # 使用默认值
        amount = amount or config.default_amount
        leverage = leverage or config.default_leverage

        # 风险检查
        risk_check = await self._check_risk(user_id, symbol, side, amount)
        if not risk_check['allowed']:
            return {'success': False, 'error': risk_check['reason']}

        if config.mode == TradingMode.SIMULATION:
            return await self._execute_sim_trade(user_id, symbol, side, amount, leverage)
        else:
            return await self._execute_real_trade(config, symbol, side, amount, leverage)

    async def _execute_sim_trade(self, user_id: int, symbol: str, side: str,
                                 amount: float, leverage: int) -> Dict:
        """执行模拟交易"""
        try:
            sim_account = self.sim_accounts[user_id]

            # 获取当前价格
            from api_manager import APIManager
            api = APIManager()
            price_data = await api.get_crypto_price(symbol)
            if not price_data:
                return {'success': False, 'error': '无法获取价格'}

            current_price = price_data['price']

            # 计算所需保证金
            margin_needed = amount / leverage

            # 检查余额
            if margin_needed > sim_account.available:
                return {'success': False, 'error': '余额不足'}

            # 检查是否有反向持仓
            if symbol in sim_account.positions:
                existing_pos = sim_account.positions[symbol]
                if (existing_pos.side == 'long' and side == 'sell') or \
                        (existing_pos.side == 'short' and side == 'buy'):
                    # 平仓
                    return await self._close_sim_position(user_id, symbol)

            # 开新仓
            position = Position(
                symbol=symbol,
                side='long' if side == 'buy' else 'short',
                amount=amount / current_price,
                avg_price=current_price,
                current_price=current_price,
                pnl=0,
                pnl_ratio=0,
                margin=margin_needed,
                leverage=leverage,
                liquidation_price=self._calculate_liquidation_price(
                    current_price, leverage, side == 'buy'
                ),
                timestamp=datetime.now()
            )

            # 更新账户
            sim_account.positions[symbol] = position
            sim_account.available -= margin_needed
            sim_account.total_trades += 1

            # 记录交易
            trade_record = {
                'timestamp': datetime.now(),
                'symbol': symbol,
                'side': side,
                'price': current_price,
                'amount': amount,
                'leverage': leverage,
                'type': 'open'
            }
            sim_account.trade_history.append(trade_record)

            logger.info(f"Sim trade executed: {symbol} {side} ${amount} @{current_price}")

            return {
                'success': True,
                'order_id': f"SIM_{int(time.time())}",
                'symbol': symbol,
                'side': side,
                'price': current_price,
                'amount': amount,
                'leverage': leverage
            }

        except Exception as e:
            logger.error(f"Sim trade error: {e}")
            return {'success': False, 'error': str(e)}

    async def _close_sim_position(self, user_id: int, symbol: str) -> Dict:
        """平仓模拟持仓"""
        try:
            sim_account = self.sim_accounts[user_id]

            if symbol not in sim_account.positions:
                return {'success': False, 'error': '无持仓'}

            position = sim_account.positions[symbol]

            # 获取当前价格
            from api_manager import APIManager
            api = APIManager()
            price_data = await api.get_crypto_price(symbol)
            current_price = price_data['price']

            # 计算盈亏
            if position.side == 'long':
                pnl = (current_price - position.avg_price) * position.amount
            else:
                pnl = (position.avg_price - current_price) * position.amount

            # 更新账户
            sim_account.balance += pnl
            sim_account.available += position.margin + pnl
            sim_account.total_pnl += pnl
            sim_account.daily_pnl += pnl

            if pnl > 0:
                sim_account.winning_trades += 1

            sim_account.win_rate = (sim_account.winning_trades / sim_account.total_trades * 100) \
                if sim_account.total_trades > 0 else 0

            # 删除持仓
            del sim_account.positions[symbol]

            # 记录交易
            trade_record = {
                'timestamp': datetime.now(),
                'symbol': symbol,
                'side': 'close',
                'price': current_price,
                'pnl': pnl,
                'type': 'close'
            }
            sim_account.trade_history.append(trade_record)

            return {
                'success': True,
                'symbol': symbol,
                'close_price': current_price,
                'pnl': pnl,
                'balance': sim_account.balance
            }

        except Exception as e:
            logger.error(f"Close sim position error: {e}")
            return {'success': False, 'error': str(e)}

    async def _execute_real_trade(self, config: TradingConfig, symbol: str,
                                  side: str, amount: float, leverage: int) -> Dict:
        """执行真实交易"""
        try:
            path = "/linear-swap-api/v1/swap_cross_order"

            # 构建订单参数
            order_params = {
                'contract_code': symbol,
                'volume': int(amount / 10),  # 火币合约以张为单位，1张=10USDT
                'direction': side,
                'lever_rate': leverage,
                'order_price_type': 'market'  # 市价单
            }

            params = {
                'AccessKeyId': config.api_key,
                'SignatureMethod': 'HmacSHA256',
                'SignatureVersion': '2',
                'Timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
            }
            params.update(order_params)

            params['Signature'] = self._generate_signature('POST', path, params, config.api_secret)

            url = f"{self.huobi_futures_url}{path}"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=order_params, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['status'] == 'ok':
                            return {
                                'success': True,
                                'order_id': data['data']['order_id'],
                                'symbol': symbol,
                                'side': side,
                                'amount': amount,
                                'leverage': leverage
                            }
                        else:
                            return {'success': False, 'error': data.get('err_msg', 'Unknown error')}

        except Exception as e:
            logger.error(f"Real trade error: {e}")
            return {'success': False, 'error': str(e)}

    # ===== 风险管理 =====

    async def _check_risk(self, user_id: int, symbol: str, side: str, amount: float) -> Dict:
        """风险检查"""
        config = self.get_user_config(user_id)

        # 检查币种白名单
        if config.allowed_symbols and symbol not in config.allowed_symbols:
            return {'allowed': False, 'reason': f'{symbol}不在允许交易列表中'}

        # 检查最大持仓
        positions = await self.get_positions(user_id)
        total_position = sum(p.margin * p.leverage for p in positions)

        if total_position + amount > config.max_position_size:
            return {'allowed': False, 'reason': f'超过最大持仓限制${config.max_position_size}'}

        # 检查每日交易次数
        today_trades = self._get_today_trades_count(user_id)
        if today_trades >= config.max_daily_trades:
            return {'allowed': False, 'reason': f'超过每日最大交易次数{config.max_daily_trades}'}

        # 检查每日亏损
        daily_pnl = self._get_daily_pnl(user_id)
        if daily_pnl < -config.max_daily_loss:
            return {'allowed': False, 'reason': f'超过每日最大亏损${config.max_daily_loss}'}

        return {'allowed': True}

    def _calculate_liquidation_price(self, entry_price: float, leverage: int, is_long: bool) -> float:
        """计算强平价格"""
        # 简化计算：强平价格 = 开仓价 * (1 ± 1/杠杆)
        if is_long:
            return entry_price * (1 - 0.9 / leverage)
        else:
            return entry_price * (1 + 0.9 / leverage)

    def _get_today_trades_count(self, user_id: int) -> int:
        """获取今日交易次数"""
        if user_id not in self.trade_history:
            return 0

        today = datetime.now().date()
        count = 0

        for trade in self.trade_history[user_id]:
            if trade['timestamp'].date() == today:
                count += 1

        return count

    def _get_daily_pnl(self, user_id: int) -> float:
        """获取今日盈亏"""
        config = self.get_user_config(user_id)

        if config.mode == TradingMode.SIMULATION:
            sim_account = self.sim_accounts.get(user_id)
            return sim_account.daily_pnl if sim_account else 0
        else:
            # TODO: 从真实API获取
            return 0

    # ===== 自动交易监控 =====

    async def start_auto_trading(self):
        """启动自动交易监控"""
        if not self.is_running:
            self.is_running = True
            self._monitor_task = asyncio.create_task(self.auto_trade_loop())
            logger.info("Auto trading system started")

    async def stop_auto_trading(self):
        """停止自动交易"""
        self.is_running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Auto trading system stopped")

    async def auto_trade_loop(self):
        """自动交易主循环"""
        while self.is_running:
            try:
                # 检查每个启用自动交易的用户
                for user_id, config in self.user_configs.items():
                    if config.auto_trade:
                        await self.process_user_signals(user_id)

                # 更新持仓盈亏
                await self.update_positions_pnl()

                # 检查止损止盈
                await self.check_stop_orders()

                # 每分钟检查一次
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Auto trade loop error: {e}")
                await asyncio.sleep(30)

    async def process_user_signals(self, user_id: int):
        """处理用户的交易信号"""
        if not self.signal_system:
            return

        config = self.get_user_config(user_id)
        if not config:
            return

        # 获取订阅的币种
        subscriptions = self.signal_system.get_user_subscriptions(user_id)

        for symbol in subscriptions:
            # 检查是否已有持仓
            positions = await self.get_positions(user_id)
            has_position = any(p.symbol == symbol for p in positions)

            if not has_position:
                # 获取信号
                signal = await self.signal_system.analyze_symbol(symbol)

                if signal and signal['strength'] >= 70:  # 只执行强信号
                    # 执行交易
                    side = 'buy' if signal['action'] == 'LONG' else 'sell'
                    result = await self.execute_trade(
                        user_id, symbol, side,
                        config.default_amount,
                        config.default_leverage
                    )

                    if result['success']:
                        logger.info(f"Auto trade executed for user {user_id}: {symbol} {side}")

    async def update_positions_pnl(self):
        """更新所有持仓的盈亏"""
        for user_id in self.sim_accounts:
            sim_account = self.sim_accounts[user_id]

            if sim_account.positions:
                from api_manager import APIManager
                api = APIManager()

                for symbol, position in sim_account.positions.items():
                    # 获取最新价格
                    price_data = await api.get_crypto_price(symbol)
                    if price_data:
                        current_price = price_data['price']
                        position.current_price = current_price

                        # 计算盈亏
                        if position.side == 'long':
                            position.pnl = (current_price - position.avg_price) * position.amount
                        else:
                            position.pnl = (position.avg_price - current_price) * position.amount

                        position.pnl_ratio = (position.pnl / position.margin) * 100

    async def check_stop_orders(self):
        """检查止损止盈"""
        for user_id, config in self.user_configs.items():
            positions = await self.get_positions(user_id)

            for position in positions:
                # 检查止损
                if position.pnl_ratio <= -config.stop_loss_ratio * 100:
                    await self.execute_trade(
                        user_id, position.symbol,
                        'sell' if position.side == 'long' else 'buy',
                        position.amount * position.current_price,
                        position.leverage
                    )
                    logger.info(f"Stop loss triggered for {position.symbol}")

                # 检查止盈
                elif position.pnl_ratio >= config.take_profit_ratio * 100:
                    await self.execute_trade(
                        user_id, position.symbol,
                        'sell' if position.side == 'long' else 'buy',
                        position.amount * position.current_price,
                        position.leverage
                    )
                    logger.info(f"Take profit triggered for {position.symbol}")

    # ===== 统计分析 =====

    def get_performance_stats(self, user_id: int, days: int = 7) -> Dict:
        """获取交易表现统计"""
        config = self.get_user_config(user_id)
        if not config:
            return {}

        if config.mode == TradingMode.SIMULATION:
            sim_account = self.sim_accounts.get(user_id)
            if not sim_account:
                return {}

            # 计算统计数据
            stats = {
                'total_trades': sim_account.total_trades,
                'winning_trades': sim_account.winning_trades,
                'win_rate': sim_account.win_rate,
                'total_pnl': sim_account.total_pnl,
                'daily_pnl': sim_account.daily_pnl,
                'current_balance': sim_account.balance,
                'roi': ((sim_account.balance - 10000) / 10000 * 100) if sim_account else 0,
                'max_drawdown': self._calculate_max_drawdown(sim_account.trade_history),
                'sharpe_ratio': self._calculate_sharpe_ratio(sim_account.trade_history),
                'profit_factor': self._calculate_profit_factor(sim_account.trade_history)
            }

            # 预测一周收益
            if sim_account.total_trades > 0:
                avg_daily_return = sim_account.total_pnl / max(1, len(sim_account.trade_history))
                stats['weekly_projection'] = avg_daily_return * 7
            else:
                stats['weekly_projection'] = 0

            return stats
        else:
            # TODO: 从真实交易历史计算
            return {}

    def _calculate_max_drawdown(self, trades: List[Dict]) -> float:
        """计算最大回撤"""
        if not trades:
            return 0

        peak = 10000
        max_dd = 0
        balance = 10000

        for trade in trades:
            if 'pnl' in trade:
                balance += trade['pnl']
                if balance > peak:
                    peak = balance
                dd = (peak - balance) / peak * 100
                max_dd = max(max_dd, dd)

        return max_dd

    def _calculate_sharpe_ratio(self, trades: List[Dict]) -> float:
        """计算夏普比率"""
        if len(trades) < 2:
            return 0

        returns = []
        for trade in trades:
            if 'pnl' in trade:
                returns.append(trade['pnl'] / 10000)  # 收益率

        if not returns:
            return 0

        avg_return = sum(returns) / len(returns)
        std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5

        if std_return == 0:
            return 0

        # 年化夏普比率（假设每天10笔交易）
        return (avg_return * 252 * 10) / (std_return * (252 * 10) ** 0.5)

    def _calculate_profit_factor(self, trades: List[Dict]) -> float:
        """计算盈亏比"""
        total_profit = 0
        total_loss = 0

        for trade in trades:
            if 'pnl' in trade:
                if trade['pnl'] > 0:
                    total_profit += trade['pnl']
                else:
                    total_loss += abs(trade['pnl'])

        if total_loss == 0:
            return total_profit if total_profit > 0 else 0

        return total_profit / total_loss