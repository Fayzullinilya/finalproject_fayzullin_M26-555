"""
Планировщик периодического обновления курсов.

Каждые UPDATE_INTERVAL_SEC секунд вызывает RatesUpdater.run_update().
Отказ одного цикла не прерывает работу: ошибка логируется, следующий
запуск происходит по расписанию.
"""

import logging
import time

from valutatrade_hub.parser_service.config import PARSER_CONFIG

logger = logging.getLogger("valutatrade")


class UpdateScheduler:
    """Периодически запускает обновление курсов через RatesUpdater."""

    def __init__(self, updater):
        """
        Принимает экземпляр RatesUpdater с настроенными клиентами и storage.
        Интервал между обновлениями в секундах из конфига (UPDATE_INTERVAL_SEC).
        """
        self._updater = updater
        self._interval_sec = PARSER_CONFIG.UPDATE_INTERVAL_SEC

    def run(self):
        """
        Запускает цикл обновлений. Останавливается по KeyboardInterrupt.
        """
        logger.info(f"Планировщик запущен. Интервал: {self._interval_sec} сек.")

        try:
            while True:
                try:
                    self._updater.run_update()
                except Exception as e:
                    logger.error(f"Обновление не удалось: {e}")
                else:
                    logger.info("Обновление прошло успешно.")

                time.sleep(self._interval_sec)
        except KeyboardInterrupt:
            logger.info("Планировщик остановлен (Ctrl+C).")