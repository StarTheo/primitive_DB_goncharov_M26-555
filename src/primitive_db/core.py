"""Основная логика управления таблицами."""

from primitive_db.constants import VALID_TYPES


def create_table(metadata, table_name, columns):
    """Проверяет столбцы и добавляет новую таблицу в метаданные."""
    if not table_name.isidentifier():
        raise ValueError(f"Некорректное имя таблицы: {table_name}.")

    if table_name in metadata:
        raise ValueError(f'Таблица "{table_name}" уже существует.')

    if not columns:
        raise ValueError("Укажите хотя бы один столбец.")

    schema = {"ID": "int"}
    seen_columns = set()

    for column in columns:
        parts = column.split(":")
        if len(parts) != 2:
            raise ValueError(f"Некорректное описание столбца: {column}.")

        column_name, column_type = parts

        if not column_name.isidentifier():
            raise ValueError(f"Некорректное имя столбца: {column_name}.")

        if column_name in seen_columns:
            raise ValueError(f"Повторяющийся столбец: {column_name}.")

        if column_type not in VALID_TYPES:
            raise ValueError(f"неподдерживаемый тип: {column_type}.")

        if column_name == "ID" and column_type != "int":
            raise ValueError("Столбец ID должен иметь тип int.")

        schema[column_name] = column_type
        seen_columns.add(column_name)

    metadata[table_name] = schema
    return metadata


def drop_table(metadata, table_name):
    """Удаляет существующую таблицу из метаданных."""
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')

    del metadata[table_name]
    return metadata
