# trading_commands.py
"""交易系统Telegram命令处理器"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, \
    CallbackQueryHandler
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 对话状态
API_KEY, API_SECRET, TRADE_AMOUNT, LEVERAGE, SYMBOLS, STOP_LOSS, TAKE_PROFIT, MAX_POSITIONS = range(8)


class TradingCommands:
    def __init__(self, trading_system):
        self.trading_system = trading_system

    # ===== 主命令 =====

    async def trading_menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """显示交易主菜单"""
        user_id = update.effective_user.id

        # 获取账户状态
        status = await self.trading_system.get_account_status(user_id)
        config = self.trading_system.get_trading_config(user_id)

        text = f"""
💹 **自动交易系统**

**账户类型:** {'🔮 虚拟账户' if config['is_virtual'] else '💰 真实账户'}
**自动交易:** {'✅ 已开启' if config['auto_trade'] else '❌ 已关闭'}

**当前配置:**
• 交易金额: ${config['trade_amount']}
• 杠杆倍数: {config['leverage']}x
• 止损: {config['stop_loss_percent']}%
• 止盈: {config['take_profit_percent']}%
• 监控币种: {', '.join(config['symbols'])}

{'**虚拟账户余额:** $' + f"{status.get('balance', 10000):.2f}" if config['is_virtual'] else ''}
{'**持仓数量:** ' + str(status.get('positions', 0)) if 'positions' in status else ''}

选择操作：
        """

        keyboard = [
            [InlineKeyboardButton("⚙️ 配置设置", callback_data="trade_config"),
             InlineKeyboardButton("📊 账户状态", callback_data="trade_status")],
            [InlineKeyboardButton("🔑 API设置", callback_data="trade_api"),
             InlineKeyboardButton("🎯 交易策略", callback_data="trade_strategy")],
            [InlineKeyboardButton("📈 收益统计", callback_data="trade_stats"),
             InlineKeyboardButton("📝 交易记录", callback_data="trade_history")],
            [InlineKeyboardButton("🔮 虚拟测试" if config['is_virtual'] else "💰 切换真实",
                                  callback_data="toggle_virtual"),
             InlineKeyboardButton("🟢 开启自动" if not config['auto_trade'] else "🔴 关闭自动",
                                  callback_data="toggle_auto")],
            [InlineKeyboardButton("« 返回主菜单", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    # ===== API配置 =====

    async def setup_api_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """开始设置API"""
        text = """
🔑 **设置火币API**

⚠️ **重要提示:**
• 请确保API权限仅开启合约交易
• 不要开启提币权限
• 建议设置IP白名单

请发送你的API Key：
(输入 /cancel 取消设置)
        """

        keyboard = [[InlineKeyboardButton("❌ 取消", callback_data="trade_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        return API_KEY

    async def receive_api_key(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """接收API Key"""
        api_key = update.message.text.strip()
        context.user_data['api_key'] = api_key

        # 删除用户消息（保护隐私）
        await update.message.delete()

        await update.message.reply_text(
            "✅ 已收到API Key\n\n请发送你的API Secret：",
            parse_mode='Markdown'
        )
        return API_SECRET

    async def receive_api_secret(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """接收API Secret"""
        api_secret = update.message.text.strip()
        user_id = update.effective_user.id

        # 删除用户消息（保护隐私）
        await update.message.delete()

        # 保存API配置
        self.trading_system.save_user_api(
            user_id,
            context.user_data['api_key'],
            api_secret
        )

        await update.message.reply_text(
            "✅ **API配置成功！**\n\n"
            "你的API密钥已安全保存\n"
            "现在可以使用真实交易功能了",
            parse_mode='Markdown'
        )

        # 清理临时数据
        context.user_data.clear()
        return ConversationHandler.END

    # ===== 交易配置 =====

    async def show_config_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """显示配置菜单"""
        user_id = update.effective_user.id
        config = self.trading_system.get_trading_config(user_id)

        text = f"""
⚙️ **交易配置**

**当前设置:**
• 交易金额: ${config['trade_amount']}
• 杠杆倍数: {config['leverage']}x
• 止损百分比: {config['stop_loss_percent']}%
• 止盈百分比: {config['take_profit_percent']}%
• 最大持仓数: {config['max_positions']}
• 监控币种: {', '.join(config['symbols'])}

选择要修改的项目：
        """

        keyboard = [
            [InlineKeyboardButton(f"💰 交易金额 (${config['trade_amount']})", callback_data="config_amount"),
             InlineKeyboardButton(f"📊 杠杆 ({config['leverage']}x)", callback_data="config_leverage")],
            [InlineKeyboardButton(f"🔻 止损 ({config['stop_loss_percent']}%)", callback_data="config_sl"),
             InlineKeyboardButton(f"🔺 止盈 ({config['take_profit_percent']}%)", callback_data="config_tp")],
            [InlineKeyboardButton("🪙 选择币种", callback_data="config_symbols"),
             InlineKeyboardButton(f"📦 最大持仓 ({config['max_positions']})", callback_data="config_max_pos")],
            [InlineKeyboardButton("💾 保存配置", callback_data="save_config"),
             InlineKeyboardButton("« 返回", callback_data="trade_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def config_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """设置交易金额"""
        text = """
💰 **设置交易金额**

请输入每次交易的金额（USDT）：

**建议:**
• 新手: $50-100
• 有经验: $100-500
• 专业: $500+

⚠️ 请根据账户余额合理设置
        """

        await update.callback_query.edit_message_text(text, parse_mode='Markdown')
        return TRADE_AMOUNT

    async def receive_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """接收交易金额"""
        try:
            amount = float(update.message.text)
            if amount <= 0:
                raise ValueError("金额必须大于0")

            user_id = update.effective_user.id
            config = self.trading_system.get_trading_config(user_id)
            config['trade_amount'] = amount
            self.trading_system.save_trading_config(user_id, config)

            await update.message.reply_text(
                f"✅ 交易金额设置为: ${amount}\n\n"
                f"配置已保存",
                parse_mode='Markdown'
            )

            # 返回配置菜单
            await self.show_config_menu(update, context)
            return ConversationHandler.END

        except ValueError:
            await update.message.reply_text("❌ 请输入有效的数字")
            return TRADE_AMOUNT

    async def config_leverage(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """设置杠杆"""
        text = """
📊 **设置杠杆倍数**

请输入杠杆倍数（1-125）：

**建议:**
• 保守: 1-5x
• 中等: 5-20x
• 激进: 20x+

⚠️ 高杠杆高风险，请谨慎选择
        """

        await update.callback_query.edit_message_text(text, parse_mode='Markdown')
        return LEVERAGE

    async def receive_leverage(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """接收杠杆设置"""
        try:
            leverage = int(update.message.text)
            if leverage < 1 or leverage > 125:
                raise ValueError("杠杆必须在1-125之间")

            user_id = update.effective_user.id
            config = self.trading_system.get_trading_config(user_id)
            config['leverage'] = leverage
            self.trading_system.save_trading_config(user_id, config)

            await update.message.reply_text(
                f"✅ 杠杆设置为: {leverage}x\n\n"
                f"配置已保存",
                parse_mode='Markdown'
            )

            await self.show_config_menu(update, context)
            return ConversationHandler.END

        except ValueError as e:
            await update.message.reply_text(f"❌ {str(e)}")
            return LEVERAGE

    async def config_stop_loss(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """设置止损"""
        text = """
🔻 **设置止损百分比**

请输入止损百分比（1-50）：

**建议:**
• 保守: 3-5%
• 平衡: 5-10%
• 激进: 10%+

⚠️ 止损是保护资金的重要工具
        """

        await update.callback_query.edit_message_text(text, parse_mode='Markdown')
        return STOP_LOSS

    async def receive_stop_loss(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """接收止损设置"""
        try:
            stop_loss = float(update.message.text)
            if stop_loss < 1 or stop_loss > 50:
                raise ValueError("止损必须在1-50%之间")

            user_id = update.effective_user.id
            config = self.trading_system.get_trading_config(user_id)
            config['stop_loss_percent'] = stop_loss
            self.trading_system.save_trading_config(user_id, config)

            await update.message.reply_text(
                f"✅ 止损设置为: {stop_loss}%\n\n"
                f"配置已保存",
                parse_mode='Markdown'
            )

            await self.show_config_menu(update, context)
            return ConversationHandler.END

        except ValueError as e:
            await update.message.reply_text(f"❌ {str(e)}")
            return STOP_LOSS

    async def config_take_profit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """设置止盈"""
        text = """
🔺 **设置止盈百分比**

请输入止盈百分比（5-200）：

**建议:**
• 保守: 5-10%
• 平衡: 10-20%
• 激进: 20%+

💡 合理的止盈确保利润落袋为安
        """

        await update.callback_query.edit_message_text(text, parse_mode='Markdown')
        return TAKE_PROFIT

    async def receive_take_profit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """接收止盈设置"""
        try:
            take_profit = float(update.message.text)
            if take_profit < 5 or take_profit > 200:
                raise ValueError("止盈必须在5-200%之间")

            user_id = update.effective_user.id
            config = self.trading_system.get_trading_config(user_id)
            config['take_profit_percent'] = take_profit
            self.trading_system.save_trading_config(user_id, config)

            await update.message.reply_text(
                f"✅ 止盈设置为: {take_profit}%\n\n"
                f"配置已保存",
                parse_mode='Markdown'
            )

            await self.show_config_menu(update, context)
            return ConversationHandler.END

        except ValueError as e:
            await update.message.reply_text(f"❌ {str(e)}")
            return TAKE_PROFIT

    async def config_symbols(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """配置交易币种"""
        text = """
🪙 **选择监控币种**

请选择要监控的币种：
        """

        # 热门币种列表
        popular_symbols = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'AVAX', 'MATIC', 'LINK']

        keyboard = []
        for i in range(0, len(popular_symbols), 2):
            row = []
            for j in range(2):
                if i + j < len(popular_symbols):
                    symbol = popular_symbols[i + j]
                    row.append(InlineKeyboardButton(f"🪙 {symbol}", callback_data=f"symbol_{symbol}"))
            keyboard.append(row)

        keyboard.extend([
            [InlineKeyboardButton("✅ 确认选择", callback_data="confirm_symbols"),
             InlineKeyboardButton("🔄 清空选择", callback_data="clear_symbols")],
            [InlineKeyboardButton("« 返回", callback_data="trade_config")]
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        # 显示当前选择
        user_id = update.effective_user.id
        config = self.trading_system.get_trading_config(user_id)
        selected = config.get('symbols', [])

        if selected:
            text += f"\n**当前选择:** {', '.join(selected)}"

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def toggle_symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """切换币种选择"""
        query = update.callback_query
        symbol = query.data.split('_')[1] + 'USDT'
        user_id = query.from_user.id

        config = self.trading_system.get_trading_config(user_id)
        symbols = config.get('symbols', [])

        if symbol in symbols:
            symbols.remove(symbol)
            await query.answer(f"❌ 已移除 {symbol}")
        else:
            symbols.append(symbol)
            await query.answer(f"✅ 已添加 {symbol}")

        # 临时保存
        context.user_data['temp_symbols'] = symbols

        # 刷新界面
        await self.config_symbols(update, context)

    async def confirm_symbols(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """确认币种选择"""
        user_id = update.effective_user.id
        symbols = context.user_data.get('temp_symbols', [])

        if not symbols:
            await update.callback_query.answer("❌ 请至少选择一个币种", show_alert=True)
            return

        config = self.trading_system.get_trading_config(user_id)
        config['symbols'] = symbols
        self.trading_system.save_trading_config(user_id, config)

        await update.callback_query.answer("✅ 币种配置已保存", show_alert=True)
        await self.show_config_menu(update, context)

    # ===== 账户状态 =====

    async def show_account_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """显示账户状态"""
        user_id = update.effective_user.id

        await update.callback_query.answer("正在获取账户信息...")

        status = await self.trading_system.get_account_status(user_id)
        config = self.trading_system.get_trading_config(user_id)

        if config['is_virtual']:
            text = f"""
🔮 **虚拟账户状态**

**账户信息:**
• 余额: ${status['balance']:.2f}
• 总盈亏: ${status['total_pnl']:.2f}
• 胜率: {status['win_rate']:.1f}%
• 总交易: {status['total_trades']} 笔

**当前持仓:** {len(status.get('positions', {}))} 个
"""

            # 显示持仓详情
            if status.get('positions'):
                text += "\n**持仓详情:**\n"
                for pos_id, pos in status['positions'].items():
                    # 计算当前盈亏
                    entry_price = pos['entry_price']
                    # 这里需要获取当前价格来计算盈亏
                    text += f"• {pos['symbol']}: {pos['side']} ${pos['amount']} @{entry_price:.2f}\n"
        else:
            if 'error' in status:
                text = f"❌ {status['error']}"
            else:
                text = "💰 **真实账户状态**\n\n" + str(status)

        keyboard = [
            [InlineKeyboardButton("🔄 刷新", callback_data="trade_status"),
             InlineKeyboardButton("📊 详细报表", callback_data="detailed_report")],
            [InlineKeyboardButton("💼 持仓管理", callback_data="manage_positions"),
             InlineKeyboardButton("📈 实时盈亏", callback_data="realtime_pnl")],
            [InlineKeyboardButton("« 返回", callback_data="trade_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_detailed_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """显示详细报表"""
        user_id = update.effective_user.id

        # 获取7天、30天统计
        stats_7d = await self.trading_system.get_performance_stats(user_id, 7)
        stats_30d = await self.trading_system.get_performance_stats(user_id, 30)

        text = f"""
📊 **详细账户报表**

**7天数据:**
• 交易次数: {stats_7d['total_trades']}
• 总盈亏: ${stats_7d['total_pnl']:.2f}
• 胜率: {stats_7d['win_rate']:.1f}%

**30天数据:**
• 交易次数: {stats_30d['total_trades']}
• 总盈亏: ${stats_30d['total_pnl']:.2f}
• 胜率: {stats_30d['win_rate']:.1f}%

**风险指标:**
• 最大回撤: 计算中...
• 夏普比率: 计算中...
• 盈亏比: 计算中...
        """

        keyboard = [
            [InlineKeyboardButton("📈 收益分析", callback_data="profit_analysis"),
             InlineKeyboardButton("📉 风险分析", callback_data="risk_analysis")],
            [InlineKeyboardButton("« 返回状态", callback_data="trade_status")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def manage_positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """持仓管理"""
        user_id = update.effective_user.id
        config = self.trading_system.get_trading_config(user_id)

        if config['is_virtual']:
            account = self.trading_system.get_virtual_account(user_id)
            positions = account.get('positions', {})
        else:
            # 真实账户持仓
            positions = {}

        if not positions:
            text = "📦 **持仓管理**\n\n暂无持仓"
            keyboard = [[InlineKeyboardButton("« 返回", callback_data="trade_status")]]
        else:
            text = "📦 **持仓管理**\n\n**当前持仓:**\n"
            keyboard = []

            for pos_id, pos in positions.items():
                symbol = pos['symbol']
                side = pos['side']
                amount = pos['amount']
                entry_price = pos['entry_price']

                text += f"• {symbol}: {side} ${amount} @${entry_price:.2f}\n"

                # 添加平仓按钮
                keyboard.append([
                    InlineKeyboardButton(f"📴 平仓 {symbol}", callback_data=f"close_pos_{pos_id}"),
                    InlineKeyboardButton(f"📝 修改 {symbol}", callback_data=f"edit_pos_{pos_id}")
                ])

            keyboard.append([InlineKeyboardButton("🚨 全部平仓", callback_data="close_all_positions")])
            keyboard.append([InlineKeyboardButton("« 返回", callback_data="trade_status")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    # ===== 收益统计 =====

    async def show_performance_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """显示收益统计"""
        user_id = update.effective_user.id

        # 提供时间选项
        text = "📈 **选择统计周期**"

        keyboard = [
            [InlineKeyboardButton("📅 今日", callback_data="stats_1"),
             InlineKeyboardButton("📅 7天", callback_data="stats_7")],
            [InlineKeyboardButton("📅 30天", callback_data="stats_30"),
             InlineKeyboardButton("📅 全部", callback_data="stats_all")],
            [InlineKeyboardButton("« 返回", callback_data="trade_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_stats_period(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """显示指定周期的统计"""
        query = update.callback_query
        user_id = query.from_user.id

        # 解析周期
        days = int(query.data.split('_')[1]) if query.data != 'stats_all' else 365

        stats = await self.trading_system.get_performance_stats(user_id, days)

        # 格式化统计信息
        text = f"""
📈 **收益统计 - {days}天**

**交易概况:**
• 总交易: {stats['total_trades']} 笔
• 盈利交易: {stats['win_trades']} 笔
• 亏损交易: {stats['lose_trades']} 笔
• 胜率: {stats['win_rate']:.1f}%

**盈亏统计:**
• 总盈亏: ${stats['total_pnl']:.2f}
• 平均盈亏: ${stats['avg_pnl']:.2f}
"""

        if stats['best_trade']:
            text += f"\n**最佳交易:**\n• {stats['best_trade'][0]}: +${stats['best_trade'][1]:.2f}"

        if stats['worst_trade']:
            text += f"\n\n**最差交易:**\n• {stats['worst_trade'][0]}: -${abs(stats['worst_trade'][1]):.2f}"

        # 计算日均收益
        if days > 0 and stats['total_pnl'] != 0:
            daily_avg = stats['total_pnl'] / days
            text += f"\n\n**日均收益:** ${daily_avg:.2f}"

            # 预测收益
            text += f"\n\n**收益预测:**"
            text += f"\n• 周收益: ${daily_avg * 7:.2f}"
            text += f"\n• 月收益: ${daily_avg * 30:.2f}"
            text += f"\n• 年收益: ${daily_avg * 365:.2f}"

        keyboard = [
            [InlineKeyboardButton("📊 其他周期", callback_data="trade_stats"),
             InlineKeyboardButton("📝 交易记录", callback_data="trade_history")],
            [InlineKeyboardButton("📈 收益图表", callback_data="profit_chart"),
             InlineKeyboardButton("📊 风险分析", callback_data="risk_metrics")],
            [InlineKeyboardButton("« 返回", callback_data="trade_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    async def show_trade_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """显示交易记录"""
        user_id = update.effective_user.id

        # 获取最近的交易记录
        conn = self.trading_system.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT symbol, side, amount, price, pnl, status, created_at
            FROM trade_records 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 10
        ''', (user_id,))

        records = cursor.fetchall()

        if not records:
            text = "📝 **交易记录**\n\n暂无交易记录"
        else:
            text = "📝 **最近10笔交易**\n\n"

            for record in records:
                symbol, side, amount, price, pnl, status, created_at = record
                pnl_text = f"${pnl:.2f}" if pnl else "持仓中"
                status_emoji = "✅" if status == "CLOSED" and (pnl or 0) > 0 else ("❌" if status == "CLOSED" else "⏳")

                # 格式化时间
                try:
                    dt = datetime.fromisoformat(created_at)
                    time_str = dt.strftime("%m-%d %H:%M")
                except:
                    time_str = created_at[:10]

                text += f"{status_emoji} {symbol} {side} ${amount} @${price:.2f} {pnl_text} ({time_str})\n"

        keyboard = [
            [InlineKeyboardButton("📊 详细分析", callback_data="detailed_history"),
             InlineKeyboardButton("📈 盈亏分布", callback_data="pnl_distribution")],
            [InlineKeyboardButton("📄 导出记录", callback_data="export_history"),
             InlineKeyboardButton("🔄 刷新", callback_data="trade_history")],
            [InlineKeyboardButton("« 返回", callback_data="trade_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

    # ===== 切换功能 =====

    async def toggle_virtual(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """切换虚拟/真实账户"""
        user_id = update.effective_user.id
        config = self.trading_system.get_trading_config(user_id)

        if not config['is_virtual']:
            # 从真实切换到虚拟
            config['is_virtual'] = True
            message = "✅ 已切换到虚拟账户模式\n\n无风险测试你的策略！"
        else:
            # 从虚拟切换到真实
            # 检查是否有API配置
            api_config = self.trading_system.get_user_api(user_id)
            if not api_config:
                await update.callback_query.answer("请先设置API密钥", show_alert=True)
                return

            # 显示风险警告
            text = """
⚠️ **风险警告**

你即将切换到真实账户交易模式！

**请确认:**
• 你了解合约交易的高风险
• 你已设置合理的止损
• 你的API权限设置正确
• 你愿意承担可能的亏损

**真的要切换到真实交易吗？**
            """

            keyboard = [
                [InlineKeyboardButton("✅ 确认切换", callback_data="confirm_real"),
                 InlineKeyboardButton("❌ 取消", callback_data="trade_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            return

        # 保存配置
        self.trading_system.save_trading_config(user_id, config)

        await update.callback_query.answer(message, show_alert=True)
        await self.trading_menu_command(update, context)

    async def confirm_real_trading(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """确认切换到真实交易"""
        user_id = update.effective_user.id
        config = self.trading_system.get_trading_config(user_id)

        config['is_virtual'] = False
        self.trading_system.save_trading_config(user_id, config)

        await update.callback_query.answer("✅ 已切换到真实账户", show_alert=True)
        await self.trading_menu_command(update, context)

    async def toggle_auto_trading(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """开启/关闭自动交易"""
        user_id = update.effective_user.id
        config = self.trading_system.get_trading_config(user_id)

        config['auto_trade'] = not config['auto_trade']

        if config['auto_trade']:
            # 开启自动交易
            if not config['is_virtual']:
                # 真实交易需要额外确认
                text = f"""
⚠️ **开启自动交易**

系统将根据信号自动进行真实交易！

**请确认配置:**
• 交易金额: ${config['trade_amount']}
• 杠杆: {config['leverage']}x
• 止损: {config['stop_loss_percent']}%
• 止盈: {config['take_profit_percent']}%

确认开启自动交易？
                """

                keyboard = [
                    [InlineKeyboardButton("✅ 确认开启", callback_data="confirm_auto"),
                     InlineKeyboardButton("❌ 取消", callback_data="trade_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.callback_query.edit_message_text(
                    text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return

            message = "🟢 自动交易已开启！\n系统将自动执行交易信号"

            # 启动自动交易监控
            await self.trading_system.start_auto_trading()
        else:
            message = "🔴 自动交易已关闭"

            # 停止自动交易监控
            await self.trading_system.stop_auto_trading()

        # 保存配置
        self.trading_system.save_trading_config(user_id, config)

        await update.callback_query.answer(message, show_alert=True)
        await self.trading_menu_command(update, context)

    async def confirm_auto_trading(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """确认开启自动交易"""
        user_id = update.effective_user.id
        config = self.trading_system.get_trading_config(user_id)

        config['auto_trade'] = True
        self.trading_system.save_trading_config(user_id, config)

        # 启动自动交易
        await self.trading_system.start_auto_trading()

        await update.callback_query.answer("✅ 自动交易已开启", show_alert=True)
        await self.trading_menu_command(update, context)

    # ===== 手动交易 =====

    async def manual_trade_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """手动下单"""
        if not context.args:
            text = """
📝 **手动交易**

**使用方法:**
`/trade BTC LONG` - 做多BTC
`/trade ETH SHORT` - 做空ETH

将使用你配置的金额和杠杆
            """
            await update.message.reply_text(text, parse_mode='Markdown')
            return

        user_id = update.effective_user.id
        symbol = context.args[0].upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        side = context.args[1].upper() if len(context.args) > 1 else 'LONG'

        if side not in ['LONG', 'SHORT']:
            await update.message.reply_text("❌ 方向必须是 LONG 或 SHORT")
            return

        config = self.trading_system.get_trading_config(user_id)

        # 创建假信号用于执行交易
        signal = {
            'action': side,
            'strength': 100,
            'direction': '做多' if side == 'LONG' else '做空',
            'direction_emoji': '🟢' if side == 'LONG' else '🔴'
        }

        await update.message.reply_text(f"⏳ 正在执行{signal['direction']}交易...")

        await self.trading_system.execute_trade(user_id, symbol, signal, config)

        await update.message.reply_text(
            f"✅ 交易执行成功！\n\n"
            f"币种: {symbol}\n"
            f"方向: {signal['direction_emoji']} {signal['direction']}\n"
            f"金额: ${config['trade_amount']}\n"
            f"杠杆: {config['leverage']}x"
        )

    async def close_position_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """平仓命令"""
        user_id = update.effective_user.id

        if not context.args:
            await update.message.reply_text(
                "**平仓命令:**\n"
                "`/close BTC` - 平掉BTC仓位\n"
                "`/close all` - 平掉所有仓位",
                parse_mode='Markdown'
            )
            return

        target = context.args[0].upper()
        config = self.trading_system.get_trading_config(user_id)

        if target == 'ALL':
            # 平掉所有仓位
            if config['is_virtual']:
                account = self.trading_system.get_virtual_account(user_id)
                positions = list(account.get('positions', {}).items())

                if not positions:
                    await update.message.reply_text("❌ 没有持仓")
                    return

                closed_count = 0
                total_pnl = 0

                for pos_id, position in positions:
                    # 获取当前价格
                    price_data = await self.trading_system.api.get_crypto_price(position['symbol'])
                    if price_data:
                        result = await self.trading_system.close_virtual_position(
                            user_id, pos_id, price_data['price']
                        )
                        if result['success']:
                            closed_count += 1
                            total_pnl += result['pnl']

                await update.message.reply_text(
                    f"✅ 已平仓 {closed_count} 个持仓\n"
                    f"总盈亏: ${total_pnl:.2f}"
                )
            else:
                # 真实账户平仓逻辑
                await update.message.reply_text("⏳ 正在平掉所有真实持仓...")
        else:
            # 平掉指定币种
            symbol = target if target.endswith('USDT') else target + 'USDT'

            if config['is_virtual']:
                account = self.trading_system.get_virtual_account(user_id)
                positions = account.get('positions', {})

                # 找到对应持仓
                target_position = None
                target_pos_id = None

                for pos_id, position in positions.items():
                    if position['symbol'] == symbol:
                        target_position = position
                        target_pos_id = pos_id
                        break

                if not target_position:
                    await update.message.reply_text(f"❌ 没有 {symbol} 的持仓")
                    return

                # 获取当前价格并平仓
                price_data = await self.trading_system.api.get_crypto_price(symbol)
                if not price_data:
                    await update.message.reply_text("❌ 无法获取当前价格")
                    return

                result = await self.trading_system.close_virtual_position(
                    user_id, target_pos_id, price_data['price']
                )

                if result['success']:
                    pnl_emoji = "📈" if result['pnl'] > 0 else "📉"
                    await update.message.reply_text(
                        f"✅ {symbol} 平仓成功！\n\n"
                        f"{pnl_emoji} 盈亏: ${result['pnl']:.2f} ({result['pnl_percent']:.2f}%)\n"
                        f"余额: ${result['balance']:.2f}"
                    )
                else:
                    await update.message.reply_text(f"❌ 平仓失败: {result.get('error', '未知错误')}")
            else:
                # 真实账户平仓
                await update.message.reply_text(f"⏳ 正在平仓 {symbol}...")

    async def close_position_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """通过回调平仓"""
        query = update.callback_query
        user_id = query.from_user.id

        if query.data == "close_all_positions":
            # 平掉所有仓位确认
            keyboard = [
                [InlineKeyboardButton("✅ 确认平仓", callback_data="confirm_close_all"),
                 InlineKeyboardButton("❌ 取消", callback_data="manage_positions")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "⚠️ **确认平掉所有仓位？**\n\n"
                "此操作将立即平掉所有持仓",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        elif query.data.startswith("close_pos_"):
            # 平掉单个仓位
            pos_id = query.data.split("_", 2)[2]

            config = self.trading_system.get_trading_config(user_id)

            if config['is_virtual']:
                account = self.trading_system.get_virtual_account(user_id)
                position = account.get('positions', {}).get(pos_id)

                if not position:
                    await query.answer("❌ 持仓不存在", show_alert=True)
                    return

                # 获取当前价格并平仓
                price_data = await self.trading_system.api.get_crypto_price(position['symbol'])
                if not price_data:
                    await query.answer("❌ 无法获取当前价格", show_alert=True)
                    return

                result = await self.trading_system.close_virtual_position(
                    user_id, pos_id, price_data['price']
                )

                if result['success']:
                    await query.answer(f"✅ 平仓成功，盈亏: ${result['pnl']:.2f}", show_alert=True)
                else:
                    await query.answer(f"❌ 平仓失败: {result.get('error')}", show_alert=True)

                # 刷新持仓管理页面
                await self.manage_positions(update, context)

    async def confirm_close_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """确认平掉所有仓位"""
        user_id = update.effective_user.id
        config = self.trading_system.get_trading_config(user_id)

        if config['is_virtual']:
            account = self.trading_system.get_virtual_account(user_id)
            positions = list(account.get('positions', {}).items())

            if not positions:
                await update.callback_query.answer("❌ 没有持仓", show_alert=True)
                return

            closed_count = 0
            total_pnl = 0

            for pos_id, position in positions:
                # 获取当前价格
                price_data = await self.trading_system.api.get_crypto_price(position['symbol'])
                if price_data:
                    result = await self.trading_system.close_virtual_position(
                        user_id, pos_id, price_data['price']
                    )
                    if result['success']:
                        closed_count += 1
                        total_pnl += result['pnl']

            await update.callback_query.edit_message_text(
                f"✅ **全部平仓完成**\n\n"
                f"平仓数量: {closed_count} 个\n"
                f"总盈亏: ${total_pnl:.2f}",
                parse_mode='Markdown'
            )
        else:
            # 真实账户平仓逻辑
            await update.callback_query.edit_message_text(
                "⏳ **正在平掉所有真实持仓...**",
                parse_mode='Markdown'
            )

    # ===== 对话处理器 =====

    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """取消对话"""
        await update.message.reply_text("❌ 操作已取消")
        context.user_data.clear()
        return ConversationHandler.END

    # ===== 获取对话处理器 =====

    def get_conversation_handlers(self):
        """获取所有对话处理器"""
        handlers = []

        # API设置对话
        api_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.setup_api_start, pattern="^trade_api$")],
            states={
                API_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_api_key)],
                API_SECRET: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_api_secret)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_conversation)]
        )
        handlers.append(api_handler)

        # 交易金额设置对话
        amount_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.config_amount, pattern="^config_amount$")],
            states={
                TRADE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_amount)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_conversation)]
        )
        handlers.append(amount_handler)

        # 杠杆设置对话
        leverage_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.config_leverage, pattern="^config_leverage$")],
            states={
                LEVERAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_leverage)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_conversation)]
        )
        handlers.append(leverage_handler)

        # 止损设置对话
        sl_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.config_stop_loss, pattern="^config_sl$")],
            states={
                STOP_LOSS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_stop_loss)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_conversation)]
        )
        handlers.append(sl_handler)

        # 止盈设置对话
        tp_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.config_take_profit, pattern="^config_tp$")],
            states={
                TAKE_PROFIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_take_profit)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_conversation)]
        )
        handlers.append(tp_handler)

        return handlers

    def get_callback_handlers(self):
        """获取所有回调处理器"""
        return [
            # 主菜单
            CallbackQueryHandler(self.trading_menu_command, pattern="^trade_menu$"),

            # 配置相关
            CallbackQueryHandler(self.show_config_menu, pattern="^trade_config$"),
            CallbackQueryHandler(self.config_symbols, pattern="^config_symbols$"),
            CallbackQueryHandler(self.toggle_symbol, pattern="^symbol_"),
            CallbackQueryHandler(self.confirm_symbols, pattern="^confirm_symbols$"),

            # 账户状态
            CallbackQueryHandler(self.show_account_status, pattern="^trade_status$"),
            CallbackQueryHandler(self.show_detailed_report, pattern="^detailed_report$"),
            CallbackQueryHandler(self.manage_positions, pattern="^manage_positions$"),

            # 统计相关
            CallbackQueryHandler(self.show_performance_stats, pattern="^trade_stats$"),
            CallbackQueryHandler(self.show_stats_period, pattern="^stats_"),
            CallbackQueryHandler(self.show_trade_history, pattern="^trade_history$"),

            # 切换功能
            CallbackQueryHandler(self.toggle_virtual, pattern="^toggle_virtual$"),
            CallbackQueryHandler(self.confirm_real_trading, pattern="^confirm_real$"),
            CallbackQueryHandler(self.toggle_auto_trading, pattern="^toggle_auto$"),
            CallbackQueryHandler(self.confirm_auto_trading, pattern="^confirm_auto$"),

            # 平仓相关
            CallbackQueryHandler(self.close_position_callback, pattern="^close_"),
            CallbackQueryHandler(self.confirm_close_all, pattern="^confirm_close_all$"),
        ]

    def get_command_handlers(self):
        """获取所有命令处理器"""
        return [
            CommandHandler("trading", self.trading_menu_command),
            CommandHandler("trade", self.manual_trade_command),
            CommandHandler("close", self.close_position_command),
        ]