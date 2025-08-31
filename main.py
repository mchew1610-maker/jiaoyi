# main.py - 修复事件循环冲突版本

import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, filters
)

# 导入其他模块 (注释掉不存在的模块，避免导入错误)
# from trading_signal_system import TradingSignalSystem
# from auto_trading_system import AutoTradingSystem
# from trading_commands import TradingCommands

logger = logging.getLogger(__name__)


class CryptoTradingBot:
    def __init__(self, telegram_token=None, binance_api_key=None, binance_secret=None):
        """初始化机器人"""
        self.telegram_token = telegram_token
        self.binance_api_key = binance_api_key
        self.binance_secret = binance_secret

        # 初始化应用 - 修复：移除post_init，在启动时手动调用
        self.application = Application.builder().token(telegram_token).build()

        # 初始化各个系统
        self.api = None
        self.db = None
        self.signal_system = None
        self.trading_system = None
        self.trading_commands = None

        logger.info("CryptoTradingBot initialized")

    async def post_init(self):
        """应用启动后的初始化任务"""
        try:
            # 初始化API管理器
            # from api_manager import APIManager
            # self.api = APIManager()
            logger.info("API Manager would be initialized here")

            # 初始化数据库
            # from database_manager import DatabaseManager
            # self.db = DatabaseManager()
            logger.info("Database Manager would be initialized here")

            # 初始化交易信号系统
            # self.signal_system = TradingSignalSystem(self.api, self.application.bot)
            # await self.signal_system.start_monitoring()
            logger.info("Trading signal system would be initialized here")

            # 存储到bot_data中供处理器访问
            # self.application.bot_data['signal_system'] = self.signal_system

            # 初始化自动交易系统
            # self.trading_system = AutoTradingSystem(self.db, self.signal_system, self.api)
            # self.application.bot_data['trading_system'] = self.trading_system

            # 初始化交易命令处理器
            # self.trading_commands = TradingCommands(self.trading_system)

            logger.info("All systems would be initialized successfully")

        except Exception as e:
            logger.error(f"Post-init error: {e}")
            raise

    # ===== 信号订阅相关命令 =====

    async def signal_subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """订阅交易信号"""
        user_id = update.effective_user.id

        if not context.args:
            # 显示订阅菜单
            text = """
📡 **交易信号订阅**

**使用方法:**
`/subscribe BTC` - 订阅BTC信号
`/subscribe BTC ETH` - 订阅多个币种
`/subscribe ALL` - 订阅所有币种

**当前监控币种:**
• BTC/USDT - 比特币
• ETH/USDT - 以太坊
• BNB/USDT - 币安币
• SOL/USDT - Solana
• ADA/USDT - Cardano

**信号说明:**
• 基于1小时、4小时、日线综合分析
• 包含RSI、MACD、均线等多个指标
• 自动推送做多/做空信号
• 提供止损止盈建议

当前状态: 未订阅
            """

            keyboard = [
                [InlineKeyboardButton("订阅BTC", callback_data="subscribe_BTC"),
                 InlineKeyboardButton("订阅ETH", callback_data="subscribe_ETH")],
                [InlineKeyboardButton("订阅全部", callback_data="subscribe_ALL")],
                [InlineKeyboardButton("查看我的订阅", callback_data="my_subscriptions")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            # 处理订阅
            symbols = []
            for arg in context.args:
                symbol = arg.upper()
                if not symbol.endswith('USDT'):
                    symbol += 'USDT'
                symbols.append(symbol)

            # 订阅信号 (模拟实现)
            signal_system = context.bot_data.get('signal_system')
            if signal_system:
                # signal_system.subscribe_user(user_id, symbols)
                await update.message.reply_text(
                    f"✅ 已订阅: {', '.join(symbols)}\n\n"
                    f"当有交易信号时会自动通知你！",
                    parse_mode='Markdown'
                )
            else:
                # 模拟响应
                await update.message.reply_text(
                    f"✅ 模拟订阅: {', '.join(symbols)}\n\n"
                    f"信号系统开发中，敬请期待！",
                    parse_mode='Markdown'
                )

    async def signal_unsubscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """取消订阅交易信号"""
        user_id = update.effective_user.id

        signal_system = context.bot_data.get('signal_system')
        if signal_system:
            # signal_system.unsubscribe_user(user_id)
            await update.message.reply_text("✅ 已取消所有交易信号订阅")
        else:
            await update.message.reply_text("✅ 模拟取消订阅完成")

    async def signal_check_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """立即检查交易信号"""
        if not context.args:
            await update.message.reply_text("❌ 请指定币种\n例如: /checksignal BTC")
            return

        symbol = context.args[0].upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        await update.message.reply_text(f"🔍 正在分析 {symbol} 的交易信号...")

        # 获取信号系统
        signal_system = context.bot_data.get('signal_system')
        if not signal_system:
            # 模拟信号响应
            await update.message.reply_text(
                f"📊 **{symbol} 模拟信号分析**\n\n"
                f"📈 **技术指标:**\n"
                f"• RSI: 45.6 (中性)\n"
                f"• MACD: 看涨背离\n"
                f"• 均线: 多头排列\n\n"
                f"🎯 **建议:** 适合做多\n"
                f"⚠️ 止损: -5%\n"
                f"🎯 止盈: +10%\n\n"
                f"*这是模拟数据，仅供演示*",
                parse_mode='Markdown'
            )
            return

        try:
            # signal = await signal_system.analyze_symbol(symbol)
            # 实际实现时的代码
            pass
        except Exception as e:
            logger.error(f"Signal check error: {e}")
            await update.message.reply_text(f"❌ 分析失败: {str(e)}")

    async def my_signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查看我的信号订阅"""
        user_id = update.effective_user.id

        signal_system = context.bot_data.get('signal_system')
        if not signal_system:
            text = "📭 模拟订阅状态\n\n你还没有订阅任何交易信号\n\n使用 /subscribe 开始订阅"
        else:
            # subscriptions = signal_system.get_user_subscriptions(user_id)
            # 实际实现
            text = "📭 你还没有订阅任何交易信号\n\n使用 /subscribe 开始订阅"

        await update.message.reply_text(text, parse_mode='Markdown')

    # ===== 现有的其他命令 =====

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """开始命令"""
        user_id = update.effective_user.id
        user_name = update.effective_user.full_name

        welcome_text = f"""
👋 欢迎使用加密货币交易机器人！

🔥 **主要功能:**
• 📊 实时行情查询
• 📈 技术指标分析  
• 📡 交易信号推送
• 🤖 自动交易系统
• 💹 合约交易管理

**快速开始:**
/help - 查看所有命令
/subscribe - 订阅交易信号
/trading - 交易系统设置

让我们开始你的交易之旅！
        """

        keyboard = [
            [InlineKeyboardButton("📊 查看行情", callback_data="market_overview"),
             InlineKeyboardButton("📡 订阅信号", callback_data="signal_menu")],
            [InlineKeyboardButton("🤖 自动交易", callback_data="trading_menu"),
             InlineKeyboardButton("💹 手动交易", callback_data="manual_trading")],
            [InlineKeyboardButton("❓ 帮助", callback_data="help_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """帮助命令"""
        help_text = """
📚 **命令列表**

**基础命令:**
/start - 开始使用
/help - 显示帮助

**信号系统:**
/subscribe BTC - 订阅信号  
/unsubscribe - 取消订阅
/checksignal BTC - 检查信号
/mysignals - 我的订阅

**交易系统:**
/trading - 交易面板 (开发中)

需要帮助请联系管理员
        """

        await update.message.reply_text(help_text, parse_mode='Markdown')

    # ===== 回调处理器 =====

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理回调查询"""
        query = update.callback_query
        data = query.data
        user_id = query.from_user.id

        await query.answer()  # 确认回调

        try:
            # 信号订阅相关回调
            if data.startswith("subscribe_"):
                symbol = data.replace("subscribe_", "")

                if symbol == "ALL":
                    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT']
                else:
                    symbols = [f"{symbol}USDT"]

                signal_system = context.bot_data.get('signal_system')
                if signal_system:
                    # signal_system.subscribe_user(user_id, symbols)
                    await query.edit_message_text(
                        f"✅ **订阅成功**\n\n"
                        f"已订阅: {', '.join(symbols)}\n\n"
                        f"当有以下信号时会通知你:\n"
                        f"• 强烈做多/做空信号\n"
                        f"• 多时间周期共振\n"
                        f"• 重要支撑/阻力位突破\n\n"
                        f"使用 /mysignals 查看订阅状态",
                        parse_mode='Markdown'
                    )
                else:
                    await query.edit_message_text(
                        f"✅ **模拟订阅成功**\n\n"
                        f"已模拟订阅: {', '.join(symbols)}\n\n"
                        f"信号系统开发中，敬请期待！",
                        parse_mode='Markdown'
                    )

            elif data == "my_subscriptions":
                await query.edit_message_text(
                    "📭 **我的订阅**\n\n"
                    "你还没有订阅任何交易信号\n\n"
                    "使用按钮或命令 /subscribe 开始订阅",
                    parse_mode='Markdown'
                )

            elif data == "signal_menu":
                # 显示信号菜单
                text = """
📡 **交易信号中心**

选择操作:
                """
                keyboard = [
                    [InlineKeyboardButton("订阅BTC", callback_data="subscribe_BTC"),
                     InlineKeyboardButton("订阅ETH", callback_data="subscribe_ETH")],
                    [InlineKeyboardButton("订阅全部", callback_data="subscribe_ALL")],
                    [InlineKeyboardButton("我的订阅", callback_data="my_subscriptions")],
                    [InlineKeyboardButton("« 返回主菜单", callback_data="main_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

            elif data == "trading_menu":
                await query.edit_message_text(
                    "🤖 **自动交易系统**\n\n"
                    "交易系统开发中...\n"
                    "敬请期待！",
                    parse_mode='Markdown'
                )

            elif data == "market_overview":
                await query.edit_message_text(
                    "📊 **市场概览**\n\n"
                    "行情模块开发中...\n"
                    "敬请期待！",
                    parse_mode='Markdown'
                )

            elif data == "manual_trading":
                await query.edit_message_text(
                    "💹 **手动交易**\n\n"
                    "手动交易模块开发中...\n"
                    "敬请期待！",
                    parse_mode='Markdown'
                )

            elif data == "help_menu":
                await self.help_command(update, context)

            elif data == "main_menu":
                # 返回主菜单
                await self.start_command(update, context)

            else:
                await query.edit_message_text("未知操作，请重新选择")

        except Exception as e:
            logger.error(f"Callback handling error: {e}")
            await query.edit_message_text(f"❌ 处理错误: {str(e)}")

    # ===== 设置处理器 =====

    def setup_handlers(self):
        """设置所有处理器"""
        # 基础命令
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))

        # 信号相关命令
        self.application.add_handler(CommandHandler("subscribe", self.signal_subscribe_command))
        self.application.add_handler(CommandHandler("unsubscribe", self.signal_unsubscribe_command))
        self.application.add_handler(CommandHandler("checksignal", self.signal_check_command))
        self.application.add_handler(CommandHandler("mysignals", self.my_signals_command))

        # 主回调处理器（应该最后添加）
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))

        logger.info("All handlers registered")

    # ===== 运行方法 - 修复事件循环问题 =====

    def run(self):
        """运行机器人 - 修复版本"""
        try:
            # 设置处理器
            self.setup_handlers()

            # 启动机器人 - 使用同步方法，让telegram库管理事件循环
            logger.info("Starting bot...")

            # 方法1: 使用run_polling (推荐)
            self.application.run_polling(drop_pending_updates=True)

        except Exception as e:
            logger.error(f"Bot run error: {e}")
            raise

    async def run_async(self):
        """异步运行方法 - 如果需要在现有事件循环中运行"""
        try:
            # 手动初始化
            await self.post_init()

            # 设置处理器
            self.setup_handlers()

            # 初始化应用
            await self.application.initialize()
            await self.application.start()

            # 启动轮询
            await self.application.updater.start_polling(drop_pending_updates=True)

            logger.info("Bot started successfully in async mode")

            # 保持运行
            await self.application.updater.idle()

        except Exception as e:
            logger.error(f"Async bot run error: {e}")
            raise
        finally:
            # 清理
            await self.application.stop()
            await self.application.shutdown()


# ===== 主函数 - 修复版本 =====

def main():
    """主函数 - 修复版本"""
    # 配置日志
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    # Telegram Bot Token
    TELEGRAM_TOKEN = "8456705106:AAFbdhV3d0lh93LOK8u29sAfFCbvj3l5FBE"

    # 币安API密钥 (可选)
    BINANCE_API_KEY = "YOUR_BINANCE_API_KEY"
    BINANCE_SECRET = "YOUR_BINANCE_SECRET"

    try:
        # 创建机器人
        bot = CryptoTradingBot(
            telegram_token=TELEGRAM_TOKEN,
            binance_api_key=BINANCE_API_KEY,
            binance_secret=BINANCE_SECRET
        )

        # 运行机器人 - 使用同步方法，避免事件循环冲突
        bot.run()

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Main error: {e}")
        raise


# 如果你需要在异步环境中运行，使用这个函数
async def main_async():
    """异步主函数 - 如果在 Jupyter 或其他异步环境中使用"""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    TELEGRAM_TOKEN = "8456705106:AAFbdhV3d0lh93LOK8u29sAfFCbvj3l5FBE"

    try:
        bot = CryptoTradingBot(telegram_token=TELEGRAM_TOKEN)
        await bot.run_async()

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Async main error: {e}")
        raise


if __name__ == "__main__":
    # 运行机器人 - 修复版本，不再使用 asyncio.run()
    main()