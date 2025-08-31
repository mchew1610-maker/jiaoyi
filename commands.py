# commands.py
"""命令处理器模块 - 处理所有用户命令"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from database import DatabaseManager
from api_manager import APIManager
from ui_templates import UITemplates
from config import SUPPORTED_PAIRS

logger = logging.getLogger(__name__)


class CommandHandler:
    def __init__(self):
        self.db = DatabaseManager()
        self.api = APIManager()
        self.ui = UITemplates()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        user = update.effective_user
        user_id = user.id

        # 保存用户到数据库
        self.db.save_user(user_id, user.username, user.first_name)

        welcome_text = f"""
🚀 **欢迎使用加密货币交易助手！**

你好 {user.first_name}！

我是你的专业加密货币交易助手，提供：

📊 **市场数据**
• 实时价格查询
• K线图表分析  
• 市场排行榜
• 恐慌贪婪指数

📈 **交易信号**
• 技术分析信号
• 趋势预测
• 买卖建议
• 市场新闻

💰 **投资组合**
• 持仓管理
• 盈亏计算
• 价格提醒
• 风险评估

🎓 **学习工具**
• 交易知识
• 风险管理
• 计算器工具

点击下方按钮开始探索！
        """

        keyboard = [
            [InlineKeyboardButton("📊 查看菜单", callback_data="main_menu")],
            [InlineKeyboardButton("💰 查看价格", callback_data="check_prices"),
             InlineKeyboardButton("📈 交易信号", callback_data="trading_signals")],
            [InlineKeyboardButton("⚙️ 设置", callback_data="settings"),
             InlineKeyboardButton("❓ 帮助", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """显示主菜单"""
        text, keyboard = self.ui.get_main_menu()
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查询加密货币价格"""
        if not context.args:
            await update.message.reply_text("❌ 请提供币种符号\n例如：/price BTC 或 /price BTCUSDT")
            return

        symbol = context.args[0].upper()
        if not symbol.endswith('USDT') and len(symbol) <= 5:
            symbol += 'USDT'

        try:
            price_data = await self.api.get_crypto_price(symbol)
            if price_data:
                text = self.ui.format_price_info(symbol, price_data)
                keyboard = self.ui.get_price_action_keyboard(symbol)
                await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')
            else:
                await update.message.reply_text(f"❌ 未找到 {symbol} 的价格信息")
        except Exception as e:
            logger.error(f"Price query error: {e}")
            await update.message.reply_text("❌ 获取价格失败，请稍后再试")

    async def signal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """生成交易信号"""
        if not context.args:
            await update.message.reply_text("❌ 请提供币种符号\n例如：/signal BTC")
            return

        symbol = context.args[0].upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        try:
            signal_data = await self.api.generate_trading_signal(symbol)

            if signal_data:
                text = self.ui.format_trading_signal(symbol, signal_data)
                keyboard = self.ui.get_signal_action_keyboard(symbol)
                await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')
            else:
                await update.message.reply_text(f"❌ 无法生成 {symbol} 的交易信号")

        except Exception as e:
            logger.error(f"Signal generation error: {e}")
            await update.message.reply_text("❌ 生成信号失败，请稍后再试")

    async def alert_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """设置价格提醒"""
        if len(context.args) < 2:
            await update.message.reply_text("❌ 使用格式：/alert BTC 50000\n或：/alert ETH >3000")
            return

        symbol = context.args[0].upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        try:
            # 解析价格条件
            price_condition = context.args[1]
            if price_condition.startswith(('>', '<', '>=', '<=')):
                condition = price_condition[:2] if price_condition.startswith(('>=', '<=')) else price_condition[:1]
                target_price = float(price_condition[len(condition):])
            else:
                condition = '>='
                target_price = float(price_condition)

            user_id = update.effective_user.id

            # 保存到数据库
            alert_id = self.db.add_alert(user_id, symbol, target_price, condition)

            alert_text = f"""
🔔 **价格提醒已设置**

**币种：** {symbol}
**条件：** 价格 {condition} ${target_price:,.4f}
**状态：** ✅ 激活

我会在价格达到条件时立即通知你！
            """

            await update.message.reply_text(alert_text, parse_mode='Markdown')

        except ValueError:
            await update.message.reply_text("❌ 价格格式错误，请输入有效数字")
        except Exception as e:
            logger.error(f"Alert setting error: {e}")
            await update.message.reply_text("❌ 设置提醒失败，请稍后再试")

    async def alerts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查看所有价格提醒"""
        user_id = update.effective_user.id
        alerts = self.db.get_user_alerts(user_id, active_only=True)

        if not alerts:
            await update.message.reply_text("📭 你还没有设置任何价格提醒\n使用 `/alert BTC 50000` 设置提醒")
            return

        alerts_text = "🔔 **你的价格提醒列表**\n\n"

        for i, (alert_id, symbol, target_price, condition, created_at) in enumerate(alerts, 1):
            created_date = datetime.fromisoformat(created_at).strftime('%m-%d %H:%M')
            alerts_text += f"""
**{i}.** {symbol}
• 条件: 价格 {condition} ${target_price:,.4f}
• 创建时间: {created_date}
• ID: `{alert_id}`

"""

        alerts_text += "💡 在菜单中可以管理这些提醒"

        keyboard = [
            [InlineKeyboardButton("🗑️ 管理提醒", callback_data="manage_alerts")],
            [InlineKeyboardButton("➕ 添加提醒", callback_data="quick_add_alert")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(alerts_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def portfolio_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查看投资组合"""
        user_id = update.effective_user.id
        portfolio = self.db.get_portfolio(user_id)

        if not portfolio:
            await update.message.reply_text("📊 你的投资组合为空\n使用 /addcoin 添加持仓")
            return

        portfolio_text = "💼 **你的投资组合**\n\n"
        total_value = 0
        total_cost = 0

        for symbol, quantity, avg_price, updated_at in portfolio:
            try:
                current_data = await self.api.get_crypto_price(symbol)
                if current_data:
                    current_price = current_data['price']
                    position_value = quantity * current_price
                    position_cost = quantity * avg_price
                    pnl = position_value - position_cost
                    pnl_pct = (pnl / position_cost) * 100 if position_cost > 0 else 0

                    pnl_emoji = "🟢" if pnl >= 0 else "🔴"

                    portfolio_text += f"""
**{symbol}**
• 持仓: {quantity:.6f}
• 成本价: ${avg_price:.4f}
• 当前价: ${current_price:.4f}
• 市值: ${position_value:.2f}
• 盈亏: {pnl_emoji} ${pnl:+.2f} ({pnl_pct:+.2f}%)

"""
                    total_value += position_value
                    total_cost += position_cost
            except:
                continue

        if total_cost > 0:
            total_pnl = total_value - total_cost
            total_pnl_pct = (total_pnl / total_cost) * 100
            total_emoji = "🟢" if total_pnl >= 0 else "🔴"

            portfolio_text += f"""
📊 **总览**
• 总市值: ${total_value:.2f}
• 总成本: ${total_cost:.2f}
• 总盈亏: {total_emoji} ${total_pnl:+.2f} ({total_pnl_pct:+.2f}%)
            """

        keyboard = [
            [InlineKeyboardButton("➕ 添加持仓", callback_data="add_portfolio_coin"),
             InlineKeyboardButton("➖ 删除持仓", callback_data="remove_position")],
            [InlineKeyboardButton("🔄 刷新", callback_data="refresh_portfolio")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(portfolio_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def addcoin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """添加币种到投资组合"""
        if len(context.args) < 3:
            await update.message.reply_text(
                "❌ 使用格式：/addcoin BTC 0.5 40000\n"
                "参数：币种 数量 成本价"
            )
            return

        try:
            symbol = context.args[0].upper()
            if not symbol.endswith('USDT'):
                symbol += 'USDT'
            quantity = float(context.args[1])
            avg_price = float(context.args[2])
            user_id = update.effective_user.id

            self.db.add_or_update_portfolio_item(user_id, symbol, quantity, avg_price)

            success_text = f"""
✅ **添加成功**

**{symbol}**
• 数量: {quantity:.6f}
• 成本价: ${avg_price:.4f}
• 总价值: ${quantity * avg_price:.2f}

已添加到你的投资组合！
            """

            await update.message.reply_text(success_text, parse_mode='Markdown')

        except ValueError:
            await update.message.reply_text("❌ 请输入有效的数字")
        except Exception as e:
            logger.error(f"Add coin error: {e}")
            await update.message.reply_text("❌ 添加失败，请稍后再试")

    async def top_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """显示市值排名前10的币种"""
        try:
            top_coins = await self.api.get_top_coins()
            if not top_coins:
                await update.message.reply_text("❌ 获取市场数据失败")
                return

            text = self.ui.format_market_cap_ranking(top_coins)
            keyboard = self.ui.get_market_cap_keyboard()

            await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Top coins error: {e}")
            await update.message.reply_text("❌ 获取排名数据失败")

    async def calc_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """交易计算器"""
        if len(context.args) < 3:
            calc_text = """
🧮 **交易计算器**

**使用方法:**
• `/calc profit 1000 1200` - 计算盈亏
• `/calc risk 10000 2` - 计算风险金额 (总资金 风险%)
• `/calc position 1000 5 50000` - 计算仓位大小

**示例:**
输入: `/calc profit 45000 50000`
输出: 盈利 $5000 (11.11%)
            """
            await update.message.reply_text(calc_text, parse_mode='Markdown')
            return

        calc_type = context.args[0].lower()

        try:
            if calc_type == 'profit' and len(context.args) >= 3:
                buy_price = float(context.args[1])
                sell_price = float(context.args[2])
                profit = sell_price - buy_price
                profit_pct = (profit / buy_price) * 100

                result_emoji = "🟢" if profit >= 0 else "🔴"
                result_text = f"""
🧮 **盈亏计算结果**

买入价: ${buy_price:,.4f}
卖出价: ${sell_price:,.4f}
{result_emoji} 盈亏: ${profit:+,.4f} ({profit_pct:+.2f}%)
                """

            elif calc_type == 'risk' and len(context.args) >= 3:
                total_capital = float(context.args[1])
                risk_pct = float(context.args[2])
                risk_amount = total_capital * (risk_pct / 100)

                result_text = f"""
🧮 **风险金额计算**

总资金: ${total_capital:,.2f}
风险比例: {risk_pct}%
风险金额: ${risk_amount:,.2f}

建议每笔交易风险不超过此金额
                """

            elif calc_type == 'position' and len(context.args) >= 4:
                risk_amount = float(context.args[1])
                stop_loss_pct = float(context.args[2]) / 100
                entry_price = float(context.args[3])
                position_size = risk_amount / (entry_price * stop_loss_pct)
                position_value = position_size * entry_price

                result_text = f"""
🧮 **仓位计算结果**

风险金额: ${risk_amount:,.2f}
止损比例: {context.args[2]}%
入场价格: ${entry_price:,.4f}

建议仓位: {position_size:.6f} 个
仓位价值: ${position_value:,.2f}
                """

            else:
                result_text = "❌ 参数错误，请检查输入格式"

            await update.message.reply_text(result_text, parse_mode='Markdown')

        except ValueError:
            await update.message.reply_text("❌ 请输入有效的数字")
        except Exception as e:
            await update.message.reply_text("❌ 计算出错，请检查输入")

    async def learn_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """学习中心"""
        text, keyboard = self.ui.get_learn_menu()
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """用户设置"""
        user_id = update.effective_user.id
        user_info = self.db.get_user(user_id)
        text = self.ui.format_settings_menu(user_info)
        keyboard = self.ui.get_settings_keyboard()
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def premium_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """高级功能介绍"""
        text = self.ui.get_upgrade_premium()
        keyboard = self.ui.get_upgrade_premium_keyboard()
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """帮助命令"""
        text = self.ui.get_help_menu()
        keyboard = self.ui.get_help_keyboard()
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理普通消息"""
        text = update.message.text.lower()

        # 智能识别币种查询
        for pair in SUPPORTED_PAIRS:
            if pair.replace('USDT', '').lower() in text:
                symbol = pair
                price_data = await self.api.get_crypto_price(symbol)
                if price_data:
                    await update.message.reply_text(
                        f"💰 {symbol}: ${price_data['price']:,.4f} ({price_data['change_24h']:+.2f}%)"
                    )
                return

        # 其他智能回复
        if any(word in text for word in ['帮助', 'help', '怎么用']):
            await update.message.reply_text("输入 /help 查看详细使用说明")
        elif any(word in text for word in ['价格', 'price', '多少钱']):
            await update.message.reply_text("输入 /price [币种] 查询实时价格\n例如: /price BTC")
        elif any(word in text for word in ['信号', 'signal', '买卖']):
            await update.message.reply_text("输入 /signal [币种] 获取交易信号\n例如: /signal ETH")
        else:
            await update.message.reply_text("输入 /menu 查看功能菜单，或 /help 获取帮助")

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """错误处理器"""
        logger.error(f"Update {update} caused error {context.error}")