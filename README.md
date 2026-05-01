# Tarkov Kappa Tracker

Персональный веб-трекер квестов Escape From Tarkov для получения контейнера Kappa.

## Что умеет

- Загружает актуальные данные о квестах с tarkov.dev API
- Строит граф зависимостей квестов через networkx
- Показывает оптимальный путь до Kappa с учётом фракции и уровня
- Интерактивные чекбоксы для отметки прогресса
- Визуализация дерева квестов через Cytoscape.js
- Подробная страница каждого квеста с задачами, ключами и наградами

## Стек

- **Backend:** Python 3.10+, FastAPI, networkx, httpx
- **Frontend:** HTML, CSS, vanilla JavaScript, Cytoscape.js
- **Данные:** tarkov.dev GraphQL API

## Запуск

```bash
# Клонировать проект
git clone git@github.com:1337Daniil/tarkov-kappa-tracker.git
cd tarkov-kappa-tracker

# Создать виртуальное окружение
poetry install
poetry env activate

# Установить зависимости
pip install -r requirements.txt

# Обновить данные квестов (необязательно, quests.json уже в репо)
python -m app.tarkov_api

# Запустить сервер
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000