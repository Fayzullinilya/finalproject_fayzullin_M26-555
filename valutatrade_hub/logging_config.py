import logging
from logging.handlers import RotatingFileHandler
from valutatrade_hub.infra.settings import SettingsLoader
import os

def setup_logging(level=logging.INFO):
    """
    Настраивает единый логгер "valutatrade" с ротацией.
    Уровень по умолчанию: INFO.
    Формат строковый: [LEVEL] [TIME] message.
    Возвращает объект logger.
    """
    settings = SettingsLoader()
    
    log_dir=settings.get("log_dir", "logs")
    log_file=settings.get("log_file", "actions.log")
    log_fmt=settings.get("log_fmt", "[%(levelname)s] [%(asctime)s] %(message)s")
    log_date_fmt=settings.get("log_date_fmt", "%Y-%m-%d %H:%M:%S")
    log_max_mb=settings.get("log_max_mb", 5)
    log_count=settings.get("log_max_mb", 5)


    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger("valutatrade")

    # не создаем новый хэндлер при повторном вызове
    if logger.handlers:
        return logger

    logger.setLevel(level) 

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

    return logger
