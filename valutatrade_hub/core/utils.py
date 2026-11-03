import json
import os

class JsonStorage:
    def __init__(self, filepath: str) -> None:
        self.filepath = os.path.abspath(filepath)
        directory = os.path.dirname(self.filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def read(self) -> list:
        """
        Читает JSON из файла.
        Если файла нет — возвращает пустой список.
        При ошибке чтения или невалидном JSON пробрасывает стандартное исключение.
        """
        if not os.path.isfile(self.filepath):
            return []

        with open(self.filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Ожидался список в JSON-файле.")
            return data

    def write(self, data: list) -> None:
        """
        Атомарная запись списка в JSON-файл.
        Пишет во временный файл, затем переименовывает.
        """
        if not isinstance(data, list):
            raise ValueError("Для записи ожидается список.")

        tmp_path = self.filepath + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.filepath)
        except OSError:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise
