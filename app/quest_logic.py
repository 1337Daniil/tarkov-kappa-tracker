"""
Модуль для работы с графом зависимостей квестов.
Читает data/quests.json и позволяет отвечать на вопросы:
- какие квесты нужны для Kappa
- в каком порядке их проходить
- какие квесты доступны сейчас при текущем прогрессе
"""


import json
from pathlib import Path

import networkx as nx

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
QUESTS_FILE = DATA_DIR / "quests.json"


def load_quests() -> list[dict]:
    """Читает квесты из локального файла quests.json."""
    if not QUESTS_FILE.exists():
        raise FileNotFoundError(
            f"Файл {QUESTS_FILE} не найден. "
            f"Сначала запусти: python -m app.tarkov_api"
        )

    with open(QUESTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_graph(quests: list[dict]) -> nx.DiGraph:
    """
    Строит направленный граф зависимостей квестов.
    Узлы — квесты (id), рёбра — «нужно выполнить до».
    Ребро A → B означает: A нужно сделать перед B.
    """
    graph = nx.DiGraph()

    # Сначала добавляем все квесты как узлы с их данными
    for quest in quests:
        graph.add_node(
            quest["id"],
            name=quest["name"],
            trader=quest["trader"]["name"] if quest.get("trader") else "Неизвестно",
            map=quest["map"]["name"] if quest.get("map") else None,
            min_level=quest.get("minPlayerLevel", 0),
            kappa_required=quest.get("kappaRequired", False),
            faction=quest.get("factionName", "Any"),
            experience=quest.get("experience", 0),
            wiki_link=quest.get("wiki_link"),
            objectives=quest.get("objectives", []),
            needed_keys=quest.get("needed_keys", []),
            start_rewards=quest.get("start_rewards"),
            finish_rewards=quest.get("finish_rewards"),
        )

    # Потом добавляем рёбра на основе taskRequirements
    for quest in quests:
        for requirement in quest.get("taskRequirements", []):
            required_task = requirement.get("task")
            if required_task:
                # Ребро: от требуемого квеста к текущему
                graph.add_edge(required_task["id"], quest["id"])

    return graph


def get_kappa_quests(graph: nx.DiGraph) -> set[str]:
    """
    Возвращает множество id всех квестов, необходимых для Kappa.
    Берём квесты с kappaRequired=True и всех их предшественников.
    """
    # Все квесты, у которых напрямую стоит флаг kappaRequired
    direct_kappa = {
        node for node, data in graph.nodes(data=True)
        if data.get("kappa_required")
    }

    # Добавляем всех предков (транзитивно) — ancestors идёт вверх по рёбрам
    all_kappa = set(direct_kappa)
    for quest_id in direct_kappa:
        all_kappa.update(nx.ancestors(graph, quest_id))

    return all_kappa


def get_available_quests(
    graph: nx.DiGraph,
    completed: set[str],
    faction: str = "BEAR",
    player_level: int = 1,
    kappa_only: bool = True,
) -> list[dict]:
    """
    Возвращает квесты, доступные прямо сейчас:
    — все предшественники выполнены
    — сам квест ещё не выполнен
    — подходит по фракции (Any или совпадает с игроком)
    — подходит по уровню игрока
    — если kappa_only=True, только из набора для Kappa
    """
    candidates = get_kappa_quests(graph) if kappa_only else set(graph.nodes)
    available = []

    for quest_id in candidates:
        if quest_id in completed:
            continue

        data = graph.nodes[quest_id]

        # Фильтр по фракции: подходит, если квест для всех или для нашей
        quest_faction = data.get("faction", "Any")
        if quest_faction not in ("Any", faction):
            continue

        # Фильтр по уровню игрока
        if data["min_level"] > player_level:
            continue

        # Все предшественники должны быть выполнены
        predecessors = set(graph.predecessors(quest_id))
        if not predecessors.issubset(completed):
            continue

        available.append({
            "id": quest_id,
            "name": data["name"],
            "trader": data["trader"],
            "map": data["map"],
            "min_level": data["min_level"],
            "faction": quest_faction,
        })

    available.sort(key=lambda q: (q["trader"], q["name"]))
    return available


def get_quest_order(graph: nx.DiGraph, kappa_only: bool = True) -> list[str]:
    """
    Возвращает корректный порядок выполнения квестов
    через топологическую сортировку.
    """
    if kappa_only:
        kappa_ids = get_kappa_quests(graph)
        subgraph = graph.subgraph(kappa_ids)
        return list(nx.topological_sort(subgraph))
    return list(nx.topological_sort(graph))


def main() -> None:
    """Проверка работы модуля: печатаем статистику в консоль."""
    quests = load_quests()
    print(f"Загружено квестов: {len(quests)}")

    graph = build_graph(quests)
    print(f"Узлов в графе: {graph.number_of_nodes()}")
    print(f"Рёбер в графе: {graph.number_of_edges()}")

    # Проверка: граф должен быть DAG (без циклов)
    is_dag = nx.is_directed_acyclic_graph(graph)
    print(f"Граф без циклов (DAG): {is_dag}")

    kappa_ids = get_kappa_quests(graph)
    print(f"Квестов для Kappa: {len(kappa_ids)}")

    # При пустом прогрессе показываем первые доступные квесты
    available = get_available_quests(graph, completed=set())
    print(f"\nДоступно на старте (первые 10 из {len(available)}):")
    for quest in available[:10]:
        print(f"  — {quest['trader']:15} {quest['name']}")

    # Проверяем топологическую сортировку — первые 5 квестов по порядку
    order = get_quest_order(graph)
    print(f"\nПервые 5 квестов в топологическом порядке:")
    for quest_id in order[:5]:
        print(f"  — {graph.nodes[quest_id]['name']}")

    # НОВОЕ: подгружаем реальный прогресс из storage
    from app.storage import get_completed_set
    completed = get_completed_set()
    print(f"\nТвой прогресс: {len(completed)} выполнено")

    available = get_available_quests(graph, completed=completed)
    print(f"Доступно квестов: {len(available)}")
    print(f"\nПервые 10 доступных:")
    for quest in available[:10]:
        print(f"  — [{quest['trader']:10}] {quest['name']}")


if __name__== "__main__":
    main()