# Тестирование API сервиса объявлений (Avito Tech 2026)

Проект содержит автоматизированные интеграционные тесты, сквозной E2E-сценарий, отчётность (Allure / HTML) и тестовую документацию для API `https://qa-internship.avito.com`.

## Документация
- [TESTCASES.md](TESTCASES.md) — список и описание всех тест-кейсов.
- [BUGS.md](BUGS.md) — реестр найденных дефектов и уязвимостей.

---

## Стек и инструментарий
- Python 3.10+
- Pytest, Requests
- Allure (`allure-pytest`), Pytest-HTML
- Flake8, Black

---

## Структура проекта

```text
AVITO/
├── TESTCASES.md               # Документация тест-кейсов
├── BUGS.md                    # Реестр обнаруженных дефектов
├── README.md                  # Описание и инструкция
├── requirements.txt           # Зависимости
├── .flake8                    # Настройки Flake8 (max-line-length = 120)
├── pyproject.toml             # Настройки Black (line-length = 120)
├── conftest.py                # Общие фикстуры (токены, динамические юзеры, очистка)
├── report.html                # Сформированный HTML-отчет
├── allure-results/            # Исходные файлы отчета Allure
└── tests/
    ├── test_e2e_flow.py       # E2E-тест полного цикла
    ├── test_auth.py           # Регистрация и авторизация
    ├── test_item_crud.py      # CRUD объявлений
    ├── test_statistics.py     # Ручки статистики
    └── test_security_and_bugs.py # Тесты безопасности и найденных багов
```

---

## Подготовка и запуск

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Запуск тестов

#### Запуск сквозного E2E-теста:
```bash
python -m pytest tests/test_e2e_flow.py -v
```

#### Запуск всех автотестов:
```bash
python -m pytest -v
```

---

## Отчётность

### Формирование HTML-отчета:
```bash
python -m pytest --html=report.html --self-contained-html
```
*Файл `report.html` можно сразу открыть в браузере.*

### Генерация данных Allure:
```bash
python -m pytest --alluredir=allure-results
```
*(Результаты со всеми шагами и вложениями сохраняются в папку `allure-results`).*

### Просмотр отчета Allure (если установлен Allure CLI):
```bash
allure serve allure-results
```

---

## Линтинг и форматирование кода

В проекте используются Flake8 и Black с ограничением длины строки 120 символов.

- **Проверка линтером**:
  ```bash
  python -m flake8 .
  ```
- **Проверка форматирования**:
  ```bash
  python -m black --check .
  ```
- **Автоматическое форматирование**:
  ```bash
  python -m black .
  ```
