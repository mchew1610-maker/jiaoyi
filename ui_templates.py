# ui_templates.py
"""UI模板和格式化模块 - 管理所有UI文本和键盘布局"""

from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import SUPPORTED_PAIRS


class UITemplates:

    # ===== 主菜单相关 =====

    def get_main_menu(self):
        """获取主菜单"""
        text = """
🎯 **主菜单**

**快速操作：**
• `/price BTC` - 查询BTC价格
• `/signal ETH` - 获取ETH交易信号
• `/alert BTC 50000` - 设置BTC价格提醒

**功能分类：**
选择下方功能开始使用：
        """

        keyboard = [
            [InlineKeyboardButton("💰 实时价格", callback_data="check_prices"),
             InlineKeyboardButton("📊 市场数据", callback_data="market_data")],
            [InlineKeyboardButton("📈 交易信号", callback_data="trading_signals"),
             InlineKeyboardButton("🔔 价格提醒", callback_data="price_alerts")],
            [InlineKeyboardButton("💼 投资组合", callback_data="portfolio_menu"),
             InlineKeyboardButton("🧮 工具计算", callback_data="tools_menu")],
            [InlineKeyboardButton("🎓 学习中心", callback_data="learn_menu"),
             InlineKeyboardButton("⚙️ 设置", callback_data="settings")]
        ]

        return text, InlineKeyboardMarkup(keyboard)

    # ===== 价格相关 =====

    def get_price_menu(self):
        """获取价格菜单"""
        keyboard = []
        for i in range(0, len(SUPPORTED_PAIRS), 2):
            row = []
            for j in range(2):
                if i + j < len(SUPPORTED_PAIRS):
                    pair = SUPPORTED_PAIRS[i + j]
                    symbol = pair.replace('USDT', '')
                    row.append(InlineKeyboardButton(f"💰 {symbol}", callback_data=f"price_quick_{pair}"))
            keyboard.append(row)

        keyboard.append([InlineKeyboardButton("« 返回主菜单", callback_data="main_menu")])

        return "💰 **选择要查看的币种价格：**", InlineKeyboardMarkup(keyboard)

    def format_price_info(self, symbol, price_data):
        """格式化价格信息"""
        change_emoji = "🔴" if price_data['change_24h'] < 0 else "🟢"

        return f"""
💰 **{symbol} 价格信息**

**当前价格：** ${price_data['price']:,.4f}
**24h变化：** {change_emoji} {price_data['change_24h']:+.2f}% (${price_data['change_24h_abs']:+,.4f})
**24h最高：** ${price_data['high_24h']:,.4f}
**24h最低：** ${price_data['low_24h']:,.4f}
**24h成交量：** ${price_data['volume_24h']:,.0f}

**更新时间：** {datetime.now().strftime('%H:%M:%S')}
        """

    def get_price_action_keyboard(self, symbol):
        """获取价格操作键盘"""
        keyboard = [
            [InlineKeyboardButton("📈 获取信号", callback_data=f"signal_{symbol}"),
             InlineKeyboardButton("🔔 设置提醒", callback_data=f"alert_{symbol}")],
            [InlineKeyboardButton("🔄 刷新价格", callback_data=f"price_quick_{symbol}"),
             InlineKeyboardButton("« 返回价格菜单", callback_data="check_prices")]
        ]
        return InlineKeyboardMarkup(keyboard)

    # ===== 交易信号相关 =====

    def get_trading_signals_menu(self):
        """获取交易信号菜单"""
        text = """
📈 **今日热门交易信号**

🟢 **BTC/USDT** - 买入信号
• 价格: $45,230
• RSI: 35 (超卖)
• 建议: 短线买入

🟡 **ETH/USDT** - 观望信号  
• 价格: $2,890
• 趋势: 震荡整理
• 建议: 等待突破

🔴 **ADA/USDT** - 卖出信号
• 价格: $0.485
• RSI: 78 (超买)
• 建议: 减仓观望

使用 /signal [币种] 获取详细分析
        """

        keyboard = [
            [InlineKeyboardButton("🔄 刷新信号", callback_data="trading_signals")],
            [InlineKeyboardButton("« 返回主菜单", callback_data="main_menu")]
        ]

        return text, InlineKeyboardMarkup(keyboard)

    def format_trading_signal(self, symbol, signal_data):
        """格式化交易信号"""
        strength_emoji = {
            'STRONG_BUY': '🟢🟢🟢',
            'BUY': '🟢🟢',
            'WEAK_BUY': '🟢',
            'HOLD': '🟡',
            'WEAK_SELL': '🔴',
            'SELL': '🔴🔴',
            'STRONG_SELL': '🔴🔴🔴'
        }

        return f"""
📈 **{symbol} 交易信号**

**信号：** {strength_emoji.get(signal_data['signal'], '🟡')} **{signal_data['signal']}**
**置信度：** {signal_data['confidence']:.1f}%
**当前价格：** ${signal_data['price']:,.4f}

**技术指标：**
• RSI: {signal_data['rsi']:.1f} ({signal_data['rsi_signal']})
• MACD: {signal_data['macd_signal']}
• 移动平均: {signal_data['ma_signal']}
• 支撑位: ${signal_data['support']:,.4f}
• 阻力位: ${signal_data['resistance']:,.4f}

**建议操作：**
{signal_data['recommendation']}

**风险提示：** {signal_data['risk_warning']}

⚠️ *仅供参考，投资有风险*
        """

    def get_signal_action_keyboard(self, symbol):
        """获取信号操作键盘"""
        keyboard = [
            [InlineKeyboardButton("🔄 刷新信号", callback_data=f"signal_{symbol}"),
             InlineKeyboardButton("🔔 设置提醒", callback_data=f"alert_{symbol}")],
            [InlineKeyboardButton("« 返回", callback_data="trading_signals")]
        ]
        return InlineKeyboardMarkup(keyboard)

    # ===== 市场数据相关 =====

    def get_market_data_menu(self):
        """获取市场数据菜单"""
        text = """
📊 **市场数据中心**

**实时数据:**
• 📈 市值排行榜
• 🔥 今日涨幅榜
• 📉 今日跌幅榜
• 😨 恐慌贪婪指数

**市场分析:**
• 📊 整体市场概览
• 💰 总市值统计
• 📈 24h成交量排行
• 🌍 全球市场热度

选择你感兴趣的数据：
        """

        keyboard = [
            [InlineKeyboardButton("📈 市值排行榜", callback_data="market_cap_ranking")],
            [InlineKeyboardButton("🔥 今日涨幅榜", callback_data="top_gainers"),
             InlineKeyboardButton("📉 今日跌幅榜", callback_data="top_losers")],
            [InlineKeyboardButton("😨 恐慌贪婪指数", callback_data="fear_greed_index"),
             InlineKeyboardButton("📊 市场概览", callback_data="market_overview")],
            [InlineKeyboardButton("« 返回主菜单", callback_data="main_menu")]
        ]

        return text, InlineKeyboardMarkup(keyboard)

    def format_fear_greed_index(self, data):
        """格式化恐慌贪婪指数"""
        return f"""
😨 **恐慌贪婪指数**

**当前指数:** {data['color']} {data['value']}/100
**市场情绪:** {data['emoji']} {data['status']}

**指数说明:**
• 0-25: 极度恐慌 😱
• 26-45: 恐慌 😰  
• 46-55: 中性 😐
• 56-75: 贪婪 😃
• 76-100: 极度贪婪 🤑

**投资建议:** 
{data['advice']}

**影响因素:**
• 市场波动率 (25%)
• 市场动量 (25%)
• 社交媒体情绪 (15%)
• 问卷调查 (15%)
• 市场主导地位 (10%)
• 搜索趋势 (10%)

⚠️ **提醒:** 恐慌贪婪指数仅供参考，不构成投资建议
        """

    def get_fear_greed_keyboard(self):
        """获取恐慌贪婪指数键盘"""
        keyboard = [
            [InlineKeyboardButton("🔄 刷新指数", callback_data="fear_greed_index")],
            [InlineKeyboardButton("📊 历史数据", callback_data="fear_greed_history"),
             InlineKeyboardButton("📚 指数说明", callback_data="fear_greed_explain")],
            [InlineKeyboardButton("« 返回市场数据", callback_data="market_data")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def format_top_gainers(self, gainers):
        """格式化涨幅榜"""
        text = "🔥 **今日涨幅榜 TOP8**\n\n"

        for i, coin in enumerate(gainers, 1):
            text += f"""
**{i}. {coin['symbol']}** ({coin['name']})
💰 ${coin['price']:,.6f} | 🟢 +{coin['change']:.1f}%

"""

        text += """
📊 **市场热点分析:**
• Meme币表现强劲，资金流入明显
• Layer1公链代币普遍上涨
• DeFi板块开始轮动上涨

⚠️ **风险提醒:**
涨幅较大的币种波动风险也更高，请控制仓位
        """

        return text

    def get_gainers_keyboard(self):
        """获取涨幅榜键盘"""
        keyboard = [
            [InlineKeyboardButton("🔄 刷新榜单", callback_data="top_gainers")],
            [InlineKeyboardButton("📉 查看跌幅榜", callback_data="top_losers"),
             InlineKeyboardButton("📊 市场分析", callback_data="market_analysis")],
            [InlineKeyboardButton("« 返回市场数据", callback_data="market_data")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def format_top_losers(self, losers):
        """格式化跌幅榜"""
        text = "📉 **今日跌幅榜 TOP8**\n\n"

        for i, coin in enumerate(losers, 1):
            text += f"""
**{i}. {coin['symbol']}** ({coin['name']})
💰 ${coin['price']:,.6f} | 🔴 {coin['change']:.1f}%

"""

        text += """
📊 **下跌原因分析:**
• 元宇宙概念币遭遇抛售
• GameFi代币持续调整
• 老项目缺乏新的催化剂

💡 **投资提醒:**
• 下跌可能提供买入机会
• 关注项目基本面变化
• 避免盲目抄底，等待企稳信号
        """

        return text

    def get_losers_keyboard(self):
        """获取跌幅榜键盘"""
        keyboard = [
            [InlineKeyboardButton("🔄 刷新榜单", callback_data="top_losers")],
            [InlineKeyboardButton("🔥 查看涨幅榜", callback_data="top_gainers"),
             InlineKeyboardButton("📊 抄底机会", callback_data="bottom_fishing")],
            [InlineKeyboardButton("« 返回市场数据", callback_data="market_data")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def format_market_overview(self, data):
        """格式化市场概览"""
        return f"""
📊 **全球加密货币市场概览**

**市场规模:**
• 总市值: ${data['total_market_cap'] / 1000000000000:.2f}万亿美元
• 24h总成交量: ${data['total_volume'] / 1000000000:.1f}亿美元
• 活跃加密货币: 13,500+ 种
• 总交易所: 500+ 家

**市场主导率:**
• 🟠 Bitcoin: {data['btc_dominance']:.1f}%
• 🔵 Ethereum: {data['eth_dominance']:.1f}%  
• 🟡 其他币种: {data['other_dominance']:.1f}%

**市场情绪指标:**
• 😨 恐慌贪婪指数: 65 (贪婪)
• 📈 市场趋势: 震荡上行
• 🔥 热门板块: AI概念、Layer2
• ❄️ 冷门板块: 元宇宙、GameFi

**投资建议:**
• 🎯 主流币可适度配置
• ⚡ 关注热门概念轮动机会
• 🛡️ 控制仓位，设置止损
• 📊 定期调整投资组合

**风险提示:** 市场波动剧烈，投资需谨慎
        """

    def get_market_overview_keyboard(self):
        """获取市场概览键盘"""
        keyboard = [
            [InlineKeyboardButton("🔄 刷新数据", callback_data="market_overview")],
            [InlineKeyboardButton("📈 技术分析", callback_data="technical_overview"),
             InlineKeyboardButton("📰 市场新闻", callback_data="market_news")],
            [InlineKeyboardButton("💰 投资建议", callback_data="investment_advice"),
             InlineKeyboardButton("« 返回市场数据", callback_data="market_data")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def format_market_cap_ranking(self, top_coins):
        """格式化市值排名"""
        text = "🏆 **市值排名 TOP 10**\n\n"

        for i, coin in enumerate(top_coins[:10], 1):
            change_emoji = "🟢" if coin['change_24h'] >= 0 else "🔴"
            text += f"""
**{i}. {coin['symbol']}** ({coin['name']})
💰 ${coin['price']:,.4f} | {change_emoji} {coin['change_24h']:+.2f}%
📊 市值: ${coin['market_cap']:,.0f}

"""

        return text

    def get_market_cap_keyboard(self):
        """获取市值排名键盘"""
        keyboard = [
            [InlineKeyboardButton("🔄 刷新排名", callback_data="market_cap_ranking")],
            [InlineKeyboardButton("« 返回市场数据", callback_data="market_data")]
        ]
        return InlineKeyboardMarkup(keyboard)

    # ===== 更多UI模板方法 =====

    # 价格提醒相关
    def format_alerts_menu(self, active_count):
        """格式化价格提醒菜单"""
        return f"""
🔔 **价格提醒中心**

**当前状态:**
• 活跃提醒: {active_count} 个
• 每日限额: 无限制

**快速设置:**
• 使用命令: `/alert 币种 价格条件`

**支持的条件:**
• 不带符号: 默认为 >=
• `>` : 大于
• `<` : 小于
• `>=` : 大于等于
• `<=` : 小于等于

选择操作：
        """

    def get_alerts_menu_keyboard(self):
        """获取价格提醒菜单键盘"""
        keyboard = [
            [InlineKeyboardButton("📋 查看所有提醒", callback_data="view_all_alerts")],
            [InlineKeyboardButton("➕ 快速添加提醒", callback_data="quick_add_alert"),
             InlineKeyboardButton("🗑️ 管理提醒", callback_data="manage_alerts")],
            [InlineKeyboardButton("📚 提醒帮助", callback_data="alert_help"),
             InlineKeyboardButton("« 返回主菜单", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def format_no_alerts_message(self):
        """格式化无提醒消息"""
        return """
🔔 **提醒管理**

📭 你还没有设置任何价格提醒

**如何设置提醒:**
• 使用命令: `/alert BTC 50000`
• 或点击币种价格页面的"设置提醒"按钮

设置后可以在这里管理所有提醒
        """

    def get_no_alerts_keyboard(self):
        """获取无提醒键盘"""
        keyboard = [
            [InlineKeyboardButton("➕ 现在设置提醒", callback_data="quick_add_alert")],
            [InlineKeyboardButton("« 返回", callback_data="price_alerts")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def format_alerts_list(self, alerts):
        """格式化提醒列表"""
        text = "🔔 **你的价格提醒**\n\n"

        for i, (alert_id, symbol, target_price, condition, created_at) in enumerate(alerts[:10], 1):
            from datetime import datetime
            created_date = datetime.fromisoformat(created_at).strftime('%m-%d %H:%M')
            text += f"""
**{i}.** {symbol.replace('USDT', '')}
• 条件: 价格 {condition} ${target_price:,.4f}
• 创建: {created_date}

"""
        return text

    def get_alerts_management_keyboard(self, alerts):
        """获取提醒管理键盘"""
        keyboard = []
        for alert_id, symbol, _, _, _ in alerts[:5]:  # 只显示前5个
            keyboard.append([InlineKeyboardButton(f"🗑️ 删除 {symbol.replace('USDT', '')}",
                                                  callback_data=f"delete_alert_{alert_id}")])

        keyboard.append([InlineKeyboardButton("🔄 刷新列表", callback_data="manage_alerts"),
                         InlineKeyboardButton("« 返回", callback_data="price_alerts")])
        return InlineKeyboardMarkup(keyboard)

    def get_quick_add_alert_guide(self):
        """获取快速添加提醒指南"""
        return """
➕ **快速添加价格提醒**

**使用方法:**
发送命令: `/alert 币种 价格条件`

**示例:**
• `/alert BTC 50000` - BTC达到50000时提醒
• `/alert ETH >3000` - ETH超过3000时提醒  
• `/alert BNB <400` - BNB跌破400时提醒

**支持的条件:**
• 不带符号: 默认为 >=
• `>` : 大于
• `<` : 小于
• `>=` : 大于等于
• `<=` : 小于等于

现在就试试设置你的第一个提醒！
        """

    def get_quick_add_alert_keyboard(self):
        """获取快速添加提醒键盘"""
        keyboard = [
            [InlineKeyboardButton("📚 详细教程", callback_data="alert_help")],
            [InlineKeyboardButton("« 返回", callback_data="price_alerts")]
        ]
        return InlineKeyboardMarkup(keyboard)

    # 投资组合相关
    def get_empty_portfolio_message(self):
        """获取空投资组合消息"""
        return """
💼 **投资组合**

📊 你的投资组合为空

**开始记录你的投资:**
• 使用 `/addcoin BTC 0.5 40000` 添加持仓
• 格式: 币种 数量 成本价
• 支持所有主流币种

**功能特色:**
• 实时盈亏计算
• 成本价追踪
• 投资统计分析

点击下方按钮开始：
        """

    def get_empty_portfolio_keyboard(self):
        """获取空投资组合键盘"""
        keyboard = [
            [InlineKeyboardButton("➕ 添加第一个币种", callback_data="add_first_coin")],
            [InlineKeyboardButton("📚 使用教程", callback_data="portfolio_tutorial"),
             InlineKeyboardButton("« 返回主菜单", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def format_portfolio(self, portfolio_data):
        """格式化投资组合"""
        text = "💼 **你的投资组合**\n\n"

        for item in portfolio_data['items']:
            pnl_emoji = "🟢" if item['pnl'] >= 0 else "🔴"
            text += f"""
**{item['symbol'].replace('USDT', '')}**
• 持仓: {item['quantity']:.6f}
• 成本: ${item['avg_price']:.4f} | 现价: ${item['current_price']:.4f}
• 市值: ${item['position_value']:.2f} | {pnl_emoji} {item['pnl_pct']:+.2f}%

"""

        if portfolio_data['total_cost'] > 0:
            total_emoji = "🟢" if portfolio_data['total_pnl'] >= 0 else "🔴"
            text += f"""
📊 **总览**
• 总市值: ${portfolio_data['total_value']:.2f}
• 总成本: ${portfolio_data['total_cost']:.2f}  
• 总盈亏: {total_emoji} ${portfolio_data['total_pnl']:+.2f} ({portfolio_data['total_pnl_pct']:+.2f}%)
            """

        return text

    def get_portfolio_keyboard(self):
        """获取投资组合键盘"""
        keyboard = [
            [InlineKeyboardButton("🔄 刷新", callback_data="refresh_portfolio"),
             InlineKeyboardButton("➕ 添加币种", callback_data="add_portfolio_coin")],
            [InlineKeyboardButton("📊 详细分析", callback_data="portfolio_analysis"),
             InlineKeyboardButton("🗑️ 管理持仓", callback_data="manage_positions")],
            [InlineKeyboardButton("« 返回主菜单", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_add_portfolio_guide(self):
        """获取添加投资组合指南"""
        return """
➕ **添加币种到投资组合**

使用命令: `/addcoin 币种 数量 成本价`

**示例:**
• `/addcoin BTC 0.5 45000`
• `/addcoin ETH 2.0 2800`

**参数说明:**
• 数量: 持有的币种数量
• 成本价: 买入时的平均价格

添加后可以实时查看盈亏！
        """

    def get_add_portfolio_keyboard(self):
        """获取添加投资组合键盘"""
        keyboard = [
            [InlineKeyboardButton("📚 使用教程", callback_data="portfolio_tutorial")],
            [InlineKeyboardButton("« 返回投资组合", callback_data="portfolio_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_add_first_coin_guide(self):
        """获取添加第一个币种指南"""
        return """
🎉 **开始你的投资组合记录！**

使用命令: `/addcoin 币种 数量 成本价`

**示例:**
• `/addcoin BTC 0.1 45000` (0.1个BTC，成本价45000)
• `/addcoin ETH 1.0 2800` (1个ETH，成本价2800)

**支持的币种:** BTC, ETH, BNB, ADA, XRP, SOL等主流币种

💡 **提示:** 添加后可以实时查看盈亏情况！
        """

    def get_add_first_coin_keyboard(self):
        """获取添加第一个币种键盘"""
        keyboard = [
            [InlineKeyboardButton("« 返回", callback_data="portfolio_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def format_add_specific_coin_guide(self, symbol):
        """格式化添加特定币种指南"""
        return f"""
➕ **添加 {symbol} 到投资组合**

请使用以下命令格式添加:
`/addcoin {symbol} 数量 成本价`

**示例:**
• `/addcoin {symbol} 1.0 45000`
• `/addcoin {symbol} 0.5 2500`

**参数说明:**
• 数量: 持有的币种数量
• 成本价: 买入时的平均价格

添加后可以实时查看盈亏情况！
        """

    def get_add_specific_coin_keyboard(self):
        """获取添加特定币种键盘"""
        keyboard = [
            [InlineKeyboardButton("📚 使用教程", callback_data="portfolio_tutorial")],
            [InlineKeyboardButton("« 返回投资组合", callback_data="portfolio_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    # 工具菜单相关
    def get_tools_menu(self):
        """获取工具菜单"""
        text = """
🧮 **交易工具箱**

**计算器工具:**
• 💰 盈亏计算器
• ⚠️ 风险计算器  
• 📊 仓位计算器
• 📈 复利计算器

**分析工具:**
• 📉 技术指标分析
• 🎯 目标价计算
• 📊 资产配置建议
• 💎 DCA成本计算

选择你需要的工具：
        """

        keyboard = [
            [InlineKeyboardButton("💰 盈亏计算", callback_data="profit_calculator"),
             InlineKeyboardButton("⚠️ 风险计算", callback_data="risk_calculator")],
            [InlineKeyboardButton("📊 仓位计算", callback_data="position_calculator"),
             InlineKeyboardButton("📈 复利计算", callback_data="compound_calculator")],
            [InlineKeyboardButton("« 返回主菜单", callback_data="main_menu")]
        ]

        return text, InlineKeyboardMarkup(keyboard)

    def get_profit_calculator(self):
        """获取盈亏计算器"""
        return """
💰 **盈亏计算器**

**使用方法:**
发送命令: `/calc profit 买入价 卖出价`

**示例:**
• `/calc profit 40000 50000` 
  → 盈利 $10,000 (25%)

• `/calc profit 3000 2800`
  → 亏损 -$200 (-6.67%)

**快速计算常见场景:**
        """

    def get_profit_calculator_keyboard(self):
        """获取盈亏计算器键盘"""
        keyboard = [
            [InlineKeyboardButton("💡 使用教程", callback_data="calc_tutorial"),
             InlineKeyboardButton("« 返回", callback_data="tools_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_risk_calculator(self):
        """获取风险计算器"""
        return """
⚠️ **风险计算器**

**功能说明:**
根据总资金和风险比例计算每笔交易的最大风险金额

**使用方法:**
发送命令: `/calc risk 总资金 风险百分比`

**示例:**
• `/calc risk 10000 2`
  → 风险金额: $200 (建议每笔交易最大亏损)

**风险比例建议:**
• 🔰 新手: 1-2%
• 📈 有经验: 2-3%  
• ⚡ 激进: 3-5%
• ⚠️ 不建议超过5%
        """

    def get_risk_calculator_keyboard(self):
        """获取风险计算器键盘"""
        keyboard = [
            [InlineKeyboardButton("📚 风险管理指南", callback_data="learn_risk"),
             InlineKeyboardButton("« 返回", callback_data="tools_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_position_calculator(self):
        """获取仓位计算器"""
        return """
📊 **仓位计算器**

**功能说明:**
根据风险金额、止损比例和入场价格计算最佳仓位大小

**使用方法:**
发送命令: `/calc position 风险金额 止损百分比 入场价格`

**示例:**
• `/calc position 1000 5 50000`
  → 建议仓位: 0.004 BTC
        """

    def get_position_calculator_keyboard(self):
        """获取仓位计算器键盘"""
        keyboard = [
            [InlineKeyboardButton("« 返回", callback_data="tools_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_compound_calculator(self):
        """获取复利计算器"""
        return """
📈 **复利计算器**

**功能说明:**
计算按复利增长的投资收益

**使用方法:**
发送命令: `/calc compound 本金 月收益率 月数`

**示例:**
• `/calc compound 1000 10 12`
  → 12个月后: $3,138.43
        """

    def get_compound_calculator_keyboard(self):
        """获取复利计算器键盘"""
        keyboard = [
            [InlineKeyboardButton("« 返回", callback_data="tools_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    # 学习中心相关
    def get_learn_menu(self):
        """获取学习菜单"""
        text = """
🎓 **加密货币学习中心**

**基础知识:**
• 🔰 新手入门指南
• 💰 什么是加密货币
• 🏦 交易所选择
• 🔐 钱包安全基础

**技术分析:**
• 📊 K线图基础
• 📈 技术指标详解
• 🎯 支撑阻力位
• 🔄 趋势分析方法

**风险管理:**
• ⚠️ 风险管理原则
• 🛡️ 止损止盈设置
• 💰 资金管理策略
• 🧠 交易心理学

选择学习主题：
        """

        keyboard = [
            [InlineKeyboardButton("🔰 新手入门", callback_data="learn_basics"),
             InlineKeyboardButton("📊 技术分析", callback_data="learn_technical")],
            [InlineKeyboardButton("⚠️ 风险管理", callback_data="learn_risk"),
             InlineKeyboardButton("📈 交易策略", callback_data="learn_strategy")],
            [InlineKeyboardButton("📚 术语词典", callback_data="crypto_glossary"),
             InlineKeyboardButton("❓ 常见问题", callback_data="faq")],
            [InlineKeyboardButton("« 返回主菜单", callback_data="main_menu")]
        ]

        return text, InlineKeyboardMarkup(keyboard)

    def get_learn_basics(self):
        """获取新手入门内容"""
        return """
🔰 **新手入门指南**

**1. 什么是加密货币？**
• 去中心化的数字货币
• 基于区块链技术
• 不受单一机构控制

**2. 如何开始交易？**
• 选择可靠的交易所
• 完成身份验证(KYC)
• 小额资金开始练习

**3. 安全须知:**
• 保管好私钥和助记词
• 使用双重认证(2FA)
• 不要把所有资金放在交易所

**4. 投资原则:**
• 只投资你能承受损失的资金
• 分散投资降低风险
• 持续学习，谨慎决策
        """

    def get_learn_basics_keyboard(self):
        """获取新手入门键盘"""
        keyboard = [
            [InlineKeyboardButton("« 返回学习中心", callback_data="learn_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_learn_technical(self):
        """获取技术分析内容"""
        return """
📊 **技术分析基础**

**常用技术指标:**

**1. RSI (相对强弱指数)**
• 范围: 0-100
• <30: 超卖区
• >70: 超买区

**2. MACD**
• 金叉: 买入信号
• 死叉: 卖出信号

**3. 移动平均线(MA)**
• MA5, MA10, MA30
• 价格>MA: 上升趋势
• 价格<MA: 下降趋势

**4. 布林带(BB)**
• 上轨: 压力位
• 下轨: 支撑位
• 中轨: 趋势方向
        """

    def get_learn_technical_keyboard(self):
        """获取技术分析键盘"""
        keyboard = [
            [InlineKeyboardButton("« 返回学习中心", callback_data="learn_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_learn_risk(self):
        """获取风险管理内容"""
        return """
⚠️ **风险管理原则**

**1. 仓位管理**
• 单笔交易风险控制在2-5%
• 避免满仓操作
• 分批建仓和平仓

**2. 止损设置**
• 严格执行止损
• 根据支撑位设置
• 避免情绪化操作

**3. 资金管理**
• 设置投资上限
• 保留应急资金
• 记录交易日志

**4. 心理控制**
• 克服贪婪和恐惧
• 保持理性分析
• 接受亏损是交易的一部分
        """

    def get_learn_risk_keyboard(self):
        """获取风险管理键盘"""
        keyboard = [
            [InlineKeyboardButton("« 返回学习中心", callback_data="learn_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_learn_strategy(self):
        """获取交易策略内容"""
        return """
📈 **交易策略介绍**

**1. 定投策略(DCA)**
• 定期定额投资
• 平摊成本
• 适合长期投资

**2. 网格交易**
• 设置价格网格
• 高卖低买
• 适合震荡市

**3. 趋势跟踪**
• 顺势而为
• 突破买入
• 适合趋势市

**4. 套利策略**
• 搬砖套利
• 期现套利
• 需要较高资金量
        """

    def get_learn_strategy_keyboard(self):
        """获取交易策略键盘"""
        keyboard = [
            [InlineKeyboardButton("« 返回学习中心", callback_data="learn_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_crypto_glossary(self):
        """获取加密货币术语"""
        return """
📚 **加密货币术语词典**

**基础术语:**
• **HODL** - 长期持有
• **FOMO** - 害怕错过
• **FUD** - 恐惧、不确定、怀疑
• **ATH** - 历史最高价
• **DCA** - 定投策略
• **牛市/熊市** - 上涨/下跌市场

**技术术语:**
• **区块链** - 分布式账本技术
• **挖矿** - 验证交易获得奖励
• **Gas费** - 交易手续费
• **智能合约** - 自动执行的合约
• **DeFi** - 去中心化金融
• **NFT** - 非同质化代币

**交易术语:**
• **做多/做空** - 买涨/买跌
• **杠杆** - 借贷放大资金
• **爆仓** - 保证金不足被强平
• **止损/止盈** - 设定亏损/盈利点
        """

    def get_glossary_keyboard(self):
        """获取术语词典键盘"""
        keyboard = [
            [InlineKeyboardButton("« 返回学习中心", callback_data="learn_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    # 设置相关
    def format_settings_menu(self, user_info):
        """格式化设置菜单"""
        if user_info:
            user_id, username, first_name, join_date, is_premium, risk_level = user_info
        else:
            user_id = "未知"
            is_premium = False
            risk_level = "medium"

        return f"""
⚙️ **设置菜单**

**账户信息:**
• 用户ID: {user_id}
• 会员状态: {'🌟 高级会员' if is_premium else '🆓 普通用户'}
• 风险偏好: {risk_level.upper()}

**功能设置:**
• 🔔 价格提醒管理
• 📊 投资组合设置  
• 🌐 语言设置
• 🔊 通知设置

选择要设置的项目：
        """

    def get_settings_keyboard(self):
        """获取设置键盘"""
        keyboard = [
            [InlineKeyboardButton("🔔 提醒管理", callback_data="manage_alerts"),
             InlineKeyboardButton("📊 投资组合", callback_data="portfolio_settings")],
            [InlineKeyboardButton("📈 使用统计", callback_data="usage_stats"),
             InlineKeyboardButton("💎 升级高级版", callback_data="upgrade_premium")],
            [InlineKeyboardButton("« 返回主菜单", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_help_menu(self):
        """获取帮助菜单"""
        return """
📚 **帮助中心**

**常用命令:**
• `/price BTC` - 查询BTC价格
• `/signal ETH` - 获取ETH交易信号  
• `/alert BTC 50000` - 设置价格提醒
• `/portfolio` - 查看投资组合

**功能说明:**
• 💰 实时价格 - 查询各种加密货币价格
• 📈 交易信号 - 基于技术分析的买卖建议
• 🔔 价格提醒 - 价格达到目标时通知你
• 💼 投资组合 - 管理你的持仓信息

⚠️ **免责声明:**
本机器人仅提供信息参考，不构成投资建议
        """

    def get_help_keyboard(self):
        """获取帮助键盘"""
        keyboard = [
            [InlineKeyboardButton("📖 查看完整帮助", callback_data="full_help")],
            [InlineKeyboardButton("« 返回主菜单", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def format_usage_stats(self, stats):
        """格式化使用统计"""
        return f"""
📈 **使用统计**

**账户信息:**
• 用户ID: `{stats['user_id']}`
• 加入天数: {stats['days_since_join']} 天
• 会员状态: 🆓 普通用户

**功能使用:**
• 价格提醒: {stats['active_alerts']}/{stats['total_alerts']} (活跃/总计)
• 投资组合: {stats['portfolio_items']} 个币种

**活跃度评分:** ⭐⭐⭐⭐☆ (4/5)
        """

    def get_usage_stats_keyboard(self):
        """获取使用统计键盘"""
        keyboard = [
            [InlineKeyboardButton("🔄 刷新统计", callback_data="usage_stats")],
            [InlineKeyboardButton("💎 升级高级版", callback_data="upgrade_premium"),
             InlineKeyboardButton("« 返回", callback_data="settings")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_upgrade_premium(self):
        """获取升级高级版内容"""
        return """
🌟 **升级高级版**

**高级功能包括:**

📊 **无限制分析**
• ✅ 无限制交易信号查询
• ✅ 深度技术分析报告  
• ✅ 实时市场洞察推送

🔔 **高级提醒**
• ✅ 无限制价格提醒
• ✅ 智能条件提醒
• ✅ 技术指标触发提醒

💎 **VIP服务**
• ✅ 专属客服支持
• ✅ 优先功能体验
• ✅ 专家一对一指导

**价格方案:**
• 📅 月付: $9.99/月
• 📅 年付: $99/年 (省17%!)
• 🎁 终身: $299 (限时优惠)

当前享受: 🎁 **7天免费试用**
        """

    def get_upgrade_premium_keyboard(self):
        """获取升级高级版键盘"""
        keyboard = [
            [InlineKeyboardButton("🎁 开始7天免费试用", callback_data="start_free_trial")],
            [InlineKeyboardButton("💳 月付 $9.99", callback_data="pay_monthly"),
             InlineKeyboardButton("💰 年付 $99", callback_data="pay_yearly")],
            [InlineKeyboardButton("💎 终身 $299", callback_data="pay_lifetime")],
            [InlineKeyboardButton("« 返回", callback_data="settings")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_full_help(self):
        """获取完整帮助"""
        return """
📚 **完整使用指南**

**📊 价格查询命令:**
• `/price BTC` - 查询BTC价格
• `/top` - 市值排行榜TOP10

**📈 交易信号命令:**
• `/signal BTC` - 获取BTC交易信号

**🔔 价格提醒命令:**
• `/alert BTC 50000` - 价格≥50000时提醒
• `/alert ETH <3000` - 价格<3000时提醒  
• `/alerts` - 查看所有提醒

**💼 投资组合命令:**
• `/portfolio` - 查看投资组合
• `/addcoin BTC 0.5 40000` - 添加持仓

**🧮 计算器命令:**
• `/calc profit 40000 50000` - 盈亏计算
• `/calc risk 10000 2` - 风险金额计算

**⚙️ 其他功能:**
• `/learn` - 学习中心
• `/settings` - 个人设置
• `/menu` - 显示功能菜单

**⚠️ 免责声明:**
所有信息仅供参考，不构成投资建议

祝你交易愉快！ 🚀
        """

    def get_full_help_keyboard(self):
        """获取完整帮助键盘"""
        keyboard = [
            [InlineKeyboardButton("📊 快速开始", callback_data="main_menu")],
            [InlineKeyboardButton("🎓 学习中心", callback_data="learn_menu"),
             InlineKeyboardButton("« 返回", callback_data="help")]
        ]
        return InlineKeyboardMarkup(keyboard)