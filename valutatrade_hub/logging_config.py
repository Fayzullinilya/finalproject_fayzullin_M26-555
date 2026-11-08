import logging
from logging.handlers import RotatingFileHandler
from valutatrade_hub.infra.settings import SettingsLoader
import os

def setup_logging(level=logging.INFO):
    """
    Настраивает два отдельных логгера с ротацией:
     - valutatrade для Core Service 
     - valutatrade.parser для Parser Service
    Уровень по умолчанию: INFO.
    Формат строковый: [LEVEL] [TIME] message.
    """
    settings = SettingsLoader()
    
    log_dir=settings.get("log_dir", "logs")
    log_file=settings.get("log_file", "actions.log")
    parser_log_file=settings.get("parser_log_file", "parser.log")
    log_fmt=settings.get("log_fmt", "[%(levelname)s] [%(asctime)s] %(message)s")
    log_date_fmt=settings.get("log_date_fmt", "%Y-%m-%d %H:%M:%S")
    log_max_mb=settings.get("log_max_mb", 5)
    log_count=settings.get("log_count", 5)


    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Логгер для Core Service
    logger = logging.getLogger("valutatrade")
    logger.setLevel(level)
    logger.propagate = False

    # не создаем новый хэндлер при повторном вызове
    if logger.handlers:
        return logger

    log_file_path = os.path.join(log_dir, log_file)
    # Ротация: до 5 файлов по 5 МБ каждый
    handler = RotatingFileHandler(
        log_file_path,
        maxBytes=log_max_mb * 1024 * 1024,
        backupCount=log_count,
        encoding='utf-8'
    )
    formatter = logging.Formatter(log_fmt, log_date_fmt)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


    # Логгер для Parser Service
    logger = logging.getLogger("valutatrade.parser")
    logger.setLevel(level)
    logger.propagate = False

    # не создаем новый хэндлер при повторном вызове
    if logger.handlers:
        return logger

    log_file_path = os.path.join(log_dir, parser_log_file)
    # Ротация: до 5 файлов по 5 МБ каждый
    handler = RotatingFileHandler(
        log_file_path,
        maxBytes=log_max_mb * 1024 * 1024,
        backupCount=log_count,
        encoding='utf-8'
    )
    formatter = logging.Formatter(log_fmt, log_date_fmt)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
