"""Вспомогательные функции для работы с файлами."""

import json
import os

from primitive_db.constants import DATA_DIR


def save_metadata(filepath, data):
    """Сохраняет метаданные в JSON-файл."""
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_metadata(filepath):
    """Загружает метаданные или возвращает пустой словарь без файла."""
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def load_table_data(table_name):
    """Загружает записи таблицы или возвращает пустой список без файла."""
    filepath = os.path.join(DATA_DIR, f"{table_name}.json")

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_table_data(table_name, data):
    """Сохраняет записи таблицы в JSON-файл."""
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, f"{table_name}.json")

    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def delete_table_data(table_name):
    """Удаляет файл записей таблицы, если он существует."""
    filepath = os.path.join(DATA_DIR, f"{table_name}.json")

    if os.path.exists(filepath):
        os.remove(filepath)
