import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(level=logging.INFO):
    """
    Настраивает единый логгер "valutatrade" с ротацией.
    Уровень по умолчанию: INFO.
    Формат строковый: [LEVEL] [TIME] message.
    Возвращает объект logger.
    """
    log_dir="logs"

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger("valutatrade")

    # не создаем новый хэндлер при повторном вызове
    if logger.handlers:
        return logger

    logger.setLevel(level) 

    log_file_path = os.path.join(log_dir, "actions.log")
    # Ротация: до 5 файлов по 5 МБ каждый
    handler = RotatingFileHandler(
        log_file_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=5
    )

    formatter = logging.Formatter(
        "[%(levelname)s] [%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)

    return logger
