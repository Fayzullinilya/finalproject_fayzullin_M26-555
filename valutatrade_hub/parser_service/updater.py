"""
Координатор обновления курсов.

Опрашивает всех API-клиентов, объединяет данные и передаёт их в хранилище.
Отказ одного клиента не прерывает работу: используем то, что смогли получить.
"""

import logging
from datetime import UTC, datetime

from valutatrade_hub.parser_service.config import PARSER_CONFIG

logger = logging.getLogger("valutatrade.parser")


class RatesUpdater:
    """Точка входа для логики парсинга: клиенты → объединение → хранилище."""

    def __init__(self, clients, storage):
        self._clients = clients
        self._storage = storage

    def run_update(self, source=None) -> dict:
        """
        Собирает курсы от всех клиентов и сохраняет их.
        Возвращает обновлённый снимок (содержимое rates.json).
        """
        logger.info("Старт обновления курсов")

        # Опрашиваем всех клиентов
        merged = {}
        report = {"ok": {}, "failed": {}, "total": 0, "last_refresh": None}

        for client in self._clients:
            name = type(client).__name__
            logger.info(f"Запрос к {name}...")
            try:
                rates = client.fetch_rates()
            except Exception as e: # noqa: BLE001 — страховка цикла: логируем
                                       # пишем в отчет и продолжаем работу
                report["failed"][name] = str(e)
                logger.error(f"{name} не дал данных: {e}")
                continue
            report["ok"][name] = len(rates)
            logger.info(f"{name} вернул {len(rates)} курсов")
            merged.update(rates)

        if not merged:
            raise RuntimeError("Нет данных ни от одного клиента")

        # Преобразуем словарь курсов в записи журнала с id
        records = []
        for code, info in merged.items():
            records.append({
                "id": f"{code}_{PARSER_CONFIG.BASE_FIAT_CURRENCY}_{info["timestamp"]}",
                "from_currency": code,
                "to_currency": PARSER_CONFIG.BASE_FIAT_CURRENCY,
                "rate": info["rate"],
                "timestamp": info["timestamp"],
                "source": info["source"],
            })

        # Пишем журнал
        added = self._storage.update_journal(records)
        logger.info(f"В журнал добавлено записей: {added}")

        # Собираем снимок целиком: пары + метаданные
        snapshot = {
            "last_refresh": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
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

        report["total"] = len(snapshot["pairs"])
        report["last_refresh"] = snapshot["last_refresh"]

        logger.info(f"Обновление завершено, last_refresh={snapshot['last_refresh']}")
        return report
