"""
Координатор обновления курсов.

Опрашивает всех API-клиентов, объединяет данные и передаёт их в хранилище.
Отказ одного клиента не прерывает работу: используем то, что смогли получить.
"""

import logging
from datetime import datetime, timezone

from valutatrade_hub.parser_service.config import PARSER_CONFIG

logger = logging.getLogger(__name__)


class RatesUpdater:
    """Точка входа для логики парсинга: клиенты → объединение → хранилище."""

    def __init__(self, clients, storage):
        self._clients = clients
        self._storage = storage

    def _build_journal_records(self, merged, base_currency):
        """Преобразует словарь курсов в записи журнала с готовыми id."""
        records = []
        for code, info in merged.items():
            iso_time = datetime.fromtimestamp(
                info["timestamp"], tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
            records.append({
                "id": f"{code}_{base_currency}_{iso_time}",
                "from_currency": code,
                "to_currency": base_currency,
                "rate": info["rate"],
                "timestamp": info["timestamp"],
                "source": info["source"],
            })
        return records

    def run_update(self) -> dict:
        """
        Собирает курсы от всех клиентов и сохраняет их.
        Возвращает обновлённый снимок (содержимое rates.json).
        """
        logger.info("Старт обновления курсов")

        # Опрашиваем всех клиентов
        merged = {}
        for client in self._clients:
            name = type(client).__name__
            logger.info(f"Запрос к {name}...")
            try:
                rates = client.fetch_rates()
            except Exception as e:
                logger.error(f"{name} не дал данных: {e}")
                continue
            logger.info(f"{name} вернул {len(rates)} курсов")
            merged.update(rates)

        if not merged:
            logger.error("Ни один клиент не вернул данные — обновление отменено")
            raise RuntimeError("Обновление не удалось: нет данных ни от одного клиента")

        # Пишем журнал
        records = self._build_journal_records(merged, PARSER_CONFIG.BASE_FIAT_CURRENCY)
        added = self._storage.update_journal(records)
        logger.info(f"В журнал добавлено записей: {added}")

        # Собираем снимок целиком: пары + метаданные
        snapshot = {
            "last_refresh": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "pairs": {
                f"{r['from_currency']}_{r['to_currency']}": {
                    "rate": r["rate"],
                    "updated_at": r["timestamp"],
                    "source": r["source"],
                }
                for r in records
            },
        }

        # Обновляем кэш
        self._storage.update_snapshot(snapshot)
        logger.info(f"Обновление завершено, last_refresh={snapshot['last_refresh']}")
        return snapshot
