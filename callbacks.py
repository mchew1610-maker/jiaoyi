# callbacks.py
"""回调处理器模块 - 处理所有内联按钮回调"""

import logging
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import DatabaseManager
from api_manager import APIManager
from ui_templates import UITemplates

logger = logging.getLogger(__name__)


class CallbackHandler:
    def __init__(self):
        self.db = DatabaseManager()
        self.api = APIManager()
        self.ui = UITemplates()

    async def handle_callback(self, update, context):
        """主回调处理函数"""
        query = update.callback_query
        await query.answer()

        data = query.data

        # 路由到对应的处理函数
        handlers = {
            "main_menu": self.show_main_menu,
            "check_prices": self.show_price_menu,
            "trading_signals": self.show_trading_signals,
            "market_data": self.show_market_data_menu,
            "price_alerts": self.show_price_alerts_menu,
            "portfolio_menu": self.show_portfolio_menu,
            "tools_menu": self.show_tools_menu,
            "learn_menu": self.show_learn_menu,
            "settings": self.show_settings_menu,
            "help": self.show_help_menu,

            # 市场数据相关
            "fear_greed_index": self.show_fear_greed_index,
            "top_gainers": self.show_top_gainers,
            "top_losers": self.show_top_losers,
            "market_overview": self.show_market_overview,
            "market_cap_ranking": self.show_market_cap_ranking,

            # 提醒管理
            "manage_alerts": self.show_manage_alerts,
            "view_all_alerts": self.show_manage_alerts,
            "quick_add_alert": self.show_quick_add_alert,

            # 投资组合
            "refresh_portfolio": self.refresh_portfolio,
            "add_portfolio_coin": self.show_add_portfolio,
            "add_first_coin": self.show_add_first_coin,

            # 计算器
            "profit_calculator": self.show_profit_calculator,
            "risk_calculator": self.show_risk_calculator,
            "position_calculator": self.show_position_calculator,
            "compound_calculator": self.show_compound_calculator,

            # 学习中心
            "learn_basics": self.show_learn_basics,
            "learn_technical": self.show_learn_technical,
            "learn_risk": self.show_learn_risk,
            "learn_strategy": self.show_learn_strategy,
            "crypto_glossary": self.show_crypto_glossary,

            # 设置
            "usage_stats": self.show_usage_stats,
            "upgrade_premium": self.show_upgrade_premium,
            "full_help": self.show_full_help,
        }

        # 处理带参数的回调
        if data.startswith("price_quick_"):
            symbol = data.replace("price_quick_", "")
            await self.show_quick_price(query, symbol)
        elif data.startswith("signal_"):
            symbol = data.replace("signal_", "")
            await self.show_signal_for_symbol(query, symbol)
        elif data.startswith("delete_alert_"):
            alert_id = int(data.replace("delete_alert_", ""))
            await self.delete_alert(query, alert_id)
        elif data.startswith("add_portfolio_"):
            symbol = data.replace("add_portfolio_", "")
            await self.show_add_portfolio_guide(query, symbol)
        elif data in handlers:
            await handlers[data](query)
        else:
            await self.handle_unknown(query, data)

    async def show_main_menu(self, query):
        """显示主菜单"""
        text, keyboard = self.ui.get_main_menu()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_price_menu(self, query):
        """显示价格查询菜单"""
        text, keyboard = self.ui.get_price_menu()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_quick_price(self, query, symbol):
        """快速价格查询"""
        try:
            price_data = await self.api.get_crypto_price(symbol)
            if price_data:
                text = self.ui.format_price_info(symbol, price_data)
                keyboard = self.ui.get_price_action_keyboard(symbol)
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            else:
                await query.edit_message_text(
                    f"❌ 未找到 {symbol} 的价格信息",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« 返回", callback_data="check_prices")]])
                )
        except Exception as e:
            logger.error(f"Quick price query error: {e}")
            await query.edit_message_text("❌ 获取价格失败，请稍后再试")

    async def show_trading_signals(self, query):
        """显示交易信号菜单"""
        text, keyboard = self.ui.get_trading_signals_menu()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_signal_for_symbol(self, query, symbol):
        """显示特定币种的交易信号"""
        try:
            signal_data = await self.api.generate_trading_signal(symbol)
            if signal_data:
                text = self.ui.format_trading_signal(symbol, signal_data)
                keyboard = self.ui.get_signal_action_keyboard(symbol)
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            else:
                await query.edit_message_text(
                    f"❌ 无法生成 {symbol} 的交易信号",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("« 返回", callback_data="trading_signals")]])
                )
        except Exception as e:
            logger.error(f"Signal generation error: {e}")
            await query.edit_message_text("❌ 生成信号失败")

    async def show_market_data_menu(self, query):
        """显示市场数据菜单"""
        text, keyboard = self.ui.get_market_data_menu()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_fear_greed_index(self, query):
        """显示恐慌贪婪指数"""
        data = self.api.get_fear_greed_index()
        text = self.ui.format_fear_greed_index(data)
        keyboard = self.ui.get_fear_greed_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_top_gainers(self, query):
        """显示涨幅榜"""
        gainers = self.api.get_mock_gainers()
        text = self.ui.format_top_gainers(gainers)
        keyboard = self.ui.get_gainers_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_top_losers(self, query):
        """显示跌幅榜"""
        losers = self.api.get_mock_losers()
        text = self.ui.format_top_losers(losers)
        keyboard = self.ui.get_losers_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_market_overview(self, query):
        """显示市场概览"""
        data = self.api.get_market_overview()
        text = self.ui.format_market_overview(data)
        keyboard = self.ui.get_market_overview_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_market_cap_ranking(self, query):
        """显示市值排名"""
        try:
            top_coins = await self.api.get_top_coins()
            text = self.ui.format_market_cap_ranking(top_coins)
            keyboard = self.ui.get_market_cap_keyboard()
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Market cap ranking error: {e}")
            await query.edit_message_text("❌ 获取数据失败")

    async def show_price_alerts_menu(self, query):
        """显示价格提醒菜单"""
        user_id = query.from_user.id
        alerts = self.db.get_user_alerts(user_id, active_only=True)
        text = self.ui.format_alerts_menu(len(alerts))
        keyboard = self.ui.get_alerts_menu_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_manage_alerts(self, query):
        """管理价格提醒"""
        user_id = query.from_user.id
        alerts = self.db.get_user_alerts(user_id, active_only=True)

        if not alerts:
            text = self.ui.format_no_alerts_message()
            keyboard = self.ui.get_no_alerts_keyboard()
        else:
            text = self.ui.format_alerts_list(alerts)
            keyboard = self.ui.get_alerts_management_keyboard(alerts)

        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def delete_alert(self, query, alert_id):
        """删除价格提醒"""
        self.db.deactivate_alert(alert_id)
        await query.answer("✅ 提醒已删除")
        await self.show_manage_alerts(query)

    async def show_quick_add_alert(self, query):
        """显示快速添加提醒"""
        text = self.ui.get_quick_add_alert_guide()
        keyboard = self.ui.get_quick_add_alert_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_portfolio_menu(self, query):
        """显示投资组合菜单"""
        user_id = query.from_user.id
        portfolio = self.db.get_portfolio(user_id)

        if not portfolio:
            text = self.ui.get_empty_portfolio_message()
            keyboard = self.ui.get_empty_portfolio_keyboard()
        else:
            # 计算投资组合数据
            portfolio_data = await self.calculate_portfolio_data(portfolio)
            text = self.ui.format_portfolio(portfolio_data)
            keyboard = self.ui.get_portfolio_keyboard()

        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def calculate_portfolio_data(self, portfolio):
        """计算投资组合数据"""
        portfolio_data = []
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

                    portfolio_data.append({
                        'symbol': symbol,
                        'quantity': quantity,
                        'avg_price': avg_price,
                        'current_price': current_price,
                        'position_value': position_value,
                        'position_cost': position_cost,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct
                    })

                    total_value += position_value
                    total_cost += position_cost
            except Exception as e:
                logger.error(f"Error calculating portfolio for {symbol}: {e}")

        return {
            'items': portfolio_data,
            'total_value': total_value,
            'total_cost': total_cost,
            'total_pnl': total_value - total_cost,
            'total_pnl_pct': ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0
        }

    async def refresh_portfolio(self, query):
        """刷新投资组合"""
        await self.show_portfolio_menu(query)
        await query.answer("✅ 已刷新")

    async def show_add_portfolio(self, query):
        """显示添加投资组合指南"""
        text = self.ui.get_add_portfolio_guide()
        keyboard = self.ui.get_add_portfolio_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_add_first_coin(self, query):
        """显示添加第一个币种指南"""
        text = self.ui.get_add_first_coin_guide()
        keyboard = self.ui.get_add_first_coin_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_add_portfolio_guide(self, query, symbol):
        """显示添加特定币种指南"""
        text = self.ui.format_add_specific_coin_guide(symbol)
        keyboard = self.ui.get_add_specific_coin_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_tools_menu(self, query):
        """显示工具菜单"""
        text, keyboard = self.ui.get_tools_menu()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_profit_calculator(self, query):
        """显示盈亏计算器"""
        text = self.ui.get_profit_calculator()
        keyboard = self.ui.get_profit_calculator_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_risk_calculator(self, query):
        """显示风险计算器"""
        text = self.ui.get_risk_calculator()
        keyboard = self.ui.get_risk_calculator_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_position_calculator(self, query):
        """显示仓位计算器"""
        text = self.ui.get_position_calculator()
        keyboard = self.ui.get_position_calculator_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_compound_calculator(self, query):
        """显示复利计算器"""
        text = self.ui.get_compound_calculator()
        keyboard = self.ui.get_compound_calculator_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_learn_menu(self, query):
        """显示学习菜单"""
        text, keyboard = self.ui.get_learn_menu()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_learn_basics(self, query):
        """显示新手入门"""
        text = self.ui.get_learn_basics()
        keyboard = self.ui.get_learn_basics_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_learn_technical(self, query):
        """显示技术分析"""
        text = self.ui.get_learn_technical()
        keyboard = self.ui.get_learn_technical_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_learn_risk(self, query):
        """显示风险管理"""
        text = self.ui.get_learn_risk()
        keyboard = self.ui.get_learn_risk_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_learn_strategy(self, query):
        """显示交易策略"""
        text = self.ui.get_learn_strategy()
        keyboard = self.ui.get_learn_strategy_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_crypto_glossary(self, query):
        """显示加密货币术语"""
        text = self.ui.get_crypto_glossary()
        keyboard = self.ui.get_glossary_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_settings_menu(self, query):
        """显示设置菜单"""
        user_id = query.from_user.id
        user_info = self.db.get_user(user_id)
        text = self.ui.format_settings_menu(user_info)
        keyboard = self.ui.get_settings_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_help_menu(self, query):
        """显示帮助菜单"""
        text = self.ui.get_help_menu()
        keyboard = self.ui.get_help_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_usage_stats(self, query):
        """显示使用统计"""
        user_id = query.from_user.id
        stats = self.calculate_user_stats(user_id)
        text = self.ui.format_usage_stats(stats)
        keyboard = self.ui.get_usage_stats_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    def calculate_user_stats(self, user_id):
        """计算用户统计数据"""
        user_info = self.db.get_user(user_id)
        alerts = self.db.get_user_alerts(user_id, active_only=False)
        active_alerts = self.db.get_user_alerts(user_id, active_only=True)
        portfolio = self.db.get_portfolio(user_id)

        if user_info:
            join_date = datetime.fromisoformat(user_info[3])
            days_since_join = (datetime.now() - join_date).days
        else:
            days_since_join = 0

        return {
            'user_id': user_id,
            'days_since_join': days_since_join,
            'total_alerts': len(alerts),
            'active_alerts': len(active_alerts),
            'portfolio_items': len(portfolio)
        }

    async def show_upgrade_premium(self, query):
        """显示升级高级版"""
        text = self.ui.get_upgrade_premium()
        keyboard = self.ui.get_upgrade_premium_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def show_full_help(self, query):
        """显示完整帮助"""
        text = self.ui.get_full_help()
        keyboard = self.ui.get_full_help_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    async def handle_unknown(self, query, data):
        """处理未知回调"""
        text = f"🚧 功能 `{data}` 正在开发中"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("« 返回主菜单", callback_data="main_menu")]])
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')