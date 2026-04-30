"""
Модуль для хранения и обновления личного прогресса игрока.
Работает с файлом data/progress.json.
"""

import json
from pathlib import Path
from typing import Literal

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROGRESS_FILE = DATA_DIR / "progress.json"

Faction = Literal["USEC", "BEAR"]

DEFAULT_PROGRESS = {
    "faction": "USEC",
    "level": 1,
    "completed_quests": [],
}

def load_progress() -> dict:
    """
    Загружает прогресс из файла. Если файла ещё нет — создаёт
    с дефолтными значениями и возвращает их.
    """
    if not PROGRESS_FILE.exists():
        save_progress(DEFAULT_PROGRESS)
        return dict(DEFAULT_PROGRESS)

    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        progress = json.load(f)

    # На случай, если в файле не хватает каких-то ключей,
    # добавляем дефолтные значения
    for key, value in DEFAULT_PROGRESS.items():
        progress.setdefault(key, value)

    return progress

def save_progress(progress: dict) -> None:
    """Сохраняет прогресс в файл."""
    DATA_DIR.mkdir(exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def mark_completed(quest_id: str) -> dict:
    """Отмечает квест как выполненный и сохраняет прогресс."""
    progress = load_progress()
    if quest_id not in progress["completed_quests"]:
        progress["completed_quests"].append(quest_id)
        save_progress(progress)
    return progress

def mark_uncompleted(quest_id: str) -> dict:
    """Снимает отметку «выполнен» с квеста."""
    progress = load_progress()
    if quest_id in progress["completed_quests"]:
        progress["completed_quests"].remove(quest_id)
        save_progress(progress)
    return progress

def set_level(level: int) -> dict:
    """Обновляет уровень игрока."""
    progress = load_progress()
    progress["level"] = level
    save_progress(progress)
    return progress

def set_faction(faction: Faction) -> dict:
    """Обновляет фракцию игрока (USEC или BEAR)."""
    if faction not in ("USEC", "BEAR"):
        raise ValueError(f"Неизвестная фракция: {faction}")
    progress = load_progress()
    progress["faction"] = faction
    save_progress(progress)
    return progress

def get_completed_set() -> set[str]:
    """
    Возвращает выполненные квесты как set.
    Это удобнее для проверок в quest_logic.get_available_quests().
    """
    return set(load_progress()["completed_quests"])

def main() -> None:
    """Небольшая демонстрация работы модуля."""
    progress = load_progress()
    print(f"Текущий прогресс:")
    print(f"  Фракция: {progress['faction']}")
    print(f"  Уровень: {progress['level']}")
    print(f"  Выполнено квестов: {len(progress['completed_quests'])}")

    # Проверим запись и чтение
    print("\nПробуем отметить тестовый квест...")
    mark_completed("test_quest_id")
    print(f"После отметки: {len(load_progress()['completed_quests'])} квестов")

    print("\nСнимаем отметку...")
    mark_uncompleted("test_quest_id")
    print(f"После снятия: {len(load_progress()['completed_quests'])} квестов")

if __name__ == "__main__":
    main()