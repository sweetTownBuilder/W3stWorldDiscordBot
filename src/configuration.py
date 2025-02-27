"""This file represents configurations from files and environment."""
import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class BotConfig:
    """Bot configuration."""

    token: str = os.getenv('BOT_TOKEN')
    channel_id: int = int(os.getenv('BOT_CHANNEL_ID'))
    DEFAULT_LOCALE: str = 'en'


@dataclass
class DifyConfig:
    api_key: str = os.getenv('DIFY_API_KEY')
    base_url: str = os.getenv('DIFY_BASE_URL')


@dataclass
class Configuration:
    """All in one configuration's class."""
    logging_level = logging.INFO

    bot = BotConfig()
    dify = DifyConfig()


conf = Configuration()
