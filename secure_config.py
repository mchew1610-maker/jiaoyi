# secure_config.py
"""安全配置文件 - 使用环境变量"""

import os
from dotenv import load_dotenv
import logging

# 加载环境变量
load_dotenv()

# Telegram配置
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '8456705106:AAFbdhV3d0lh93LOK8u29sAfFCbvj3l5FBE')

# 火币API配置
HUOBI_API_KEY = os.getenv('HUOBI_API_KEY', 'c7f1637f-ghxertfvbf-1be7bcbd-7b36b')
HUOBI_API_SECRET = os.getenv('HUOBI_API_SECRET', '')

# 数据库配置
DB_NAME = os.getenv('DB_NAME', 'crypto_bot.db')

# 支持的交易对
SUPPORTED_PAIRS = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT',
    'SOLUSDT', 'DOGEUSDT', 'DOTUSDT', 'AVAXUSDT', 'MATICUSDT'
]

# 价格监控配置
PRICE_CHECK_INTERVAL = 300  # 5分钟检查一次
ERROR_RETRY_INTERVAL = 60   # 出错后等待1分钟

# 日志配置
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.INFO

# 用户限制配置
FREE_USER_LIMITS = {
    'daily_signals': 5,
    'max_alerts': 3,
    'portfolio_coins': 10
}

PREMIUM_USER_LIMITS = {
    'daily_signals': -1,  # 无限制
    'max_alerts': -1,     # 无限制
    'portfolio_coins': -1  # 无限制
}

# 价格计划
PRICING = {
    'monthly': 9.99,
    'yearly': 99,
    'lifetime': 299
}