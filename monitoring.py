# monitoring.py
"""价格监控服务模块"""

import asyncio
import logging
from datetime import datetime
from database import DatabaseManager
from api_manager import APIManager
from config import PRICE_CHECK_INTERVAL, ERROR_RETRY_INTERVAL

logger = logging.getLogger(__name__)


class PriceMonitor:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.db = DatabaseManager()
        self.api = APIManager()
        self.is_running = False
        self._task = None

    async def start(self):
        """启动价格监控"""
        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self.monitor_loop())
            logger.info("Price monitoring started")

    async def stop(self):
        """停止价格监控"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.api.close_session()
        logger.info("Price monitoring stopped")

    async def monitor_loop(self):
        """价格监控主循环"""
        logger.info("Price monitor loop started")

        while self.is_running:
            try:
                # 获取所有活跃的价格提醒
                alerts = self.db.get_all_active_alerts()

                for alert_id, user_id, symbol, target_price, condition in alerts:
                    try:
                        # 获取当前价格
                        price_data = await self.api.get_crypto_price(symbol)
                        if not price_data:
                            continue

                        current_price = price_data['price']

                        # 检查条件是否满足
                        triggered = self.check_alert_condition(current_price, target_price, condition)

                        if triggered:
                            await self.send_alert_notification(
                                user_id, symbol, current_price, target_price, condition
                            )
                            # 停用已触发的提醒
                            self.db.deactivate_alert(alert_id)
                            logger.info(f"Alert {alert_id} triggered for user {user_id}")

                    except Exception as e:
                        logger.error(f"Error checking alert {alert_id}: {e}")

                # 等待指定时间后再次检查
                await asyncio.sleep(PRICE_CHECK_INTERVAL)

            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(ERROR_RETRY_INTERVAL)

    def check_alert_condition(self, current_price, target_price, condition):
        """检查提醒条件是否满足"""
        if condition == '>=' and current_price >= target_price:
            return True
        elif condition == '<=' and current_price <= target_price:
            return True
        elif condition == '>' and current_price > target_price:
            return True
        elif condition == '<' and current_price < target_price:
            return True
        return False

    async def send_alert_notification(self, user_id, symbol, current_price, target_price, condition):
        """发送价格提醒通知"""
        alert_message = f"""
🔔 **价格提醒触发！**

**{symbol}** 
当前价格: ${current_price:,.4f}
目标条件: {condition} ${target_price:,.4f}

✅ 条件已满足！
        """

        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=alert_message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send alert to user {user_id}: {e}")