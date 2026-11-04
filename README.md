# Primitive DB


Учебная консольная база данных на Python.
Автор: Гончаров Иван Дмитриевич, группа M26-555.



## Текущее состояние


Реализованы команды:
- create_table — создать таблицу;
- list_tables — показать список таблиц;
- drop_table — удалить таблицу;
- help — показать справку;
- exit — завершить программу.

Поддерживаются типы int, str, bool.
Столбец ID:int добавляется автоматически.
Структуры таблиц сохраняются в db_meta.json между запусками.



## Установка


Нужны uv и Python 3.12 или новее.
uv может автоматически установить подходящий Python.



Установка зависимостей и пакета:

```shell
uv sync
```



## Запуск


Основная команда:

```shell
uv run database
```



Дополнительная команда:

```shell
uv run project
```

## Проверка кода

Проверка ошибок и стиля:

```shell
uv run ruff check .
```

Проверка форматирования без изменения файлов:

```shell
uv run ruff format --check .
```

Автоматическое форматирование:

```shell
uv run ruff format .
```

## CRUD-операции

Пример работы с таблицей:

```text
create_table people name:str age:int is_active:bool
insert into people values ("Ivan", 28, true)
select from people
select from people where age = 28
update people set age = 29 where ID = 1
info people
delete from people where ID = 1
drop_table people
```

Все поля обязательны. ID создаётся автоматически, его изменение запрещено.
Строки вводятся в кавычках. Поддерживаются типы int, str, bool.
В условиях where проверяются существование столбца и тип значения.
Данные таблиц сохраняются в отдельных JSON-файлах в папке data.
Удаление таблицы также удаляет её файл данных.


## Декораторы и кэширование

Ошибки операций обрабатываются декоратором handle_db_errors.
Удаление записей и таблиц требует подтверждения y.
Время выполнения insert и select выводится через log_time.

Результаты select кэшируются замыканием create_cacher.
Ключ включает имя таблицы и условие where, в том числе его отсутствие.
После успешных изменений кэш сбрасывается.
Ошибки и отмена удаления не сбрасывают кэш.


## Демонстрация

Запись показывает создание таблицы, CRUD-операции, проверку типов,
отмену и подтверждение удаления.

[![Демонстрация Primitive DB](https://asciinema.org/a/beSGqaOPOs53u6N5.svg)](https://asciinema.org/a/beSGqaOPOs53u6N5)

Исходный файл записи: [docs/demo.cast](docs/demo.cast).


## Сборка и проверка пакета

```shell
uv build
uvx twine check dist/*
```

Установка собранного wheel в Windows:

```powershell
uv tool install --link-mode copy .\dist\primitive_db-0.1.0-py3-none-any.whl
```

После установки приложение запускается командой database.
Публикация пакета на PyPI не требуется.