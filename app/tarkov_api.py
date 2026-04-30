#Модуль для загрузки данных о квестах с Tarkov.dev API.
# Запускается как отдельный скрипт:
# Python -m app.tarkov_api

import json
from pathlib import Path

import httpx

API_URL = "https://api.tarkov.dev/graphql"

QUESTS_QUERY = """
{
  tasks(lang: ru) {
    id
    name
    minPlayerLevel
    kappaRequired
    factionName
    experience
    wikiLink
    trader {
      name
    }
    map {
      name
    }
    taskRequirements {
      task {
        id
        name
      }
    }
    objectives {
      type
      description
      maps {
        name
      }
      optional
    }
    neededKeys {
      keys {
        name
        shortName
        wikiLink
      }
    }
    startRewards {
      items {
        item {
          name
          shortName
        }
        count
      }
    }
    finishRewards {
      items {
        item {
          name
          shortName
        }
        count
      }
      traderUnlock {
        name
      }
    }
  }
}
"""

DATA_DIR = Path(__file__).resolve().parent.parent / "data" # Путь к текущему файлу 
QUESTS_FILE = DATA_DIR / "quests.json"


def fetch_quests() -> list[dict]:
    """Загружает все квесты с tarkov.dev через GraphQL-запрос."""
    print("Отправляю запрос на tarkov.dev ...")

    response = httpx.post(
        API_URL,
        json={"query": QUESTS_QUERY},
        timeout=30.0,
    )
    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        raise RuntimeError(f"GraphQL вернул ошибки: {data['errors']}")

    quests = data["data"]["tasks"]
    print(f"Получено квестов: {len(quests)}")
    return quests


def save_quests(quests: list[dict]) -> None:
    """Сохраняет список квестов в файл data/quests.json."""
    DATA_DIR.mkdir(exist_ok=True)

    with open(QUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(quests, f, ensure_ascii=False, indent=2)

    print(f"Сохранено в {QUESTS_FILE}")


def main() -> None:
    quests = fetch_quests()
    save_quests(quests)

    kappa_count = sum(1 for q in quests if q.get("kappaRequired"))
    print(f"Из них нужны для Kappa: {kappa_count}")


if __name__ == "__main__":
    main()