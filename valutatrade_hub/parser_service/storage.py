"""
storage.py — слой хранения данных.

Отвечает только за файловые операции:
  - чтение JSON с защитой от битых/отсутствующих файлов;
  - атомарную запись через временный файл и os.replace;
  - добавление записей в журнал с проверкой на дкбликаты по полю id;
  - перезапись снимка курсов.

Бизнес-логики не содержит: формат записей, id и структуру снимка
формирует вызывающий код (updater).
"""

import json
import logging
import os
import tempfile

logger = logging.getLogger("valutatrade.parser")


class RatesStorage:
    """
    Хранилище на основе JSON-файлов.

    Файлы:
      - exchange_rates.json — журнал всех измерений (история).
      - rates.json — актуальный снимок курсов для Core Service.
    """

    def __init__(self, data_dir: str, journal_file: str, snapshot_file: str):
        self.data_dir = data_dir
        self.journal_path = os.path.join(data_dir, journal_file)
        self.snapshot_path = os.path.join(data_dir, snapshot_file)

        # Создаем папку, если не существует
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logger.info(f"Создана директория для данных: {self.data_dir}")

    def _read_file(self, path):
        """
        Читает JSON-файл. Если файла нет или он битый — возвращает None.
        Решение «что делать с отсутствием данных» принимает вызывающий метод.
        """
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Не удалось прочитать файл {path}: {e}")
            return None

    def _write_file(self, path, data):
        """
        Атомарно записывает data в JSON-файл: сначала во временный файл
        в той же директории, затем заменяет целевой одним вызовом os.replace.
        """
        tmp_file, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
        try:
            with os.fdopen(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, path)
        except (TypeError, OSError) as e:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            logger.error(f"Ошибка записи файла {path}: {e}")
            raise

    def update_journal(self, records: list) -> int:
        """
        Добавляет записи в журнал с проверкой на дубликаты по полю id.
        Принимает список готовых словарей. Каждый должен содержать поле "id".
        Возвращает количество добавленых записей.
        """
        journal = self._read_file(self.journal_path)
        if not isinstance(journal, list):
            journal = []

        existing_ids = {r.get("id") for r in journal}
        new_records = [r for r in records if r.get("id") not in existing_ids]

        journal.extend(new_records)
        self._write_file(self.journal_path, journal)
        
        return len(new_records)
    
    def update_snapshot(self, snapshot: dict) -> None:
        """
        Перезаписывает снимок курсов целиком.
        """
        self._write_file(self.snapshot_path, snapshot)
