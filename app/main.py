"""
Точка входа в веб-приложение.
Запуск:
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
"""

from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app import quest_logic, storage

# Пути к папкам с шаблонами и статикой
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "app" / "templates"
STATIC_DIR = BASE_DIR / "static"

# Создаём папки, если их ещё нет
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Создаём приложение FastAPI
app = FastAPI(title="Tarkov Kappa Tracker")

# Подключаем шаблоны и статические файлы
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Загружаем квесты и строим граф один раз при старте сервера
print("Загружаю квесты и строю граф...")
QUESTS = quest_logic.load_quests()
GRAPH = quest_logic.build_graph(QUESTS)
KAPPA_IDS = quest_logic.get_kappa_quests(GRAPH)
print(f"Готово: {len(QUESTS)} квестов, {len(KAPPA_IDS)} нужны для Kappa")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Главная страница: статистика и доступные квесты."""
    progress = storage.load_progress()
    completed = set(progress["completed_quests"])

    # Считаем прогресс именно по Kappa-квестам
    completed_kappa = completed & KAPPA_IDS
    available = quest_logic.get_available_quests(
        GRAPH,
        completed=completed,
        faction=progress["faction"],
        player_level=progress["level"],
    )
    context = {
        "request": request,
        "faction": progress["faction"],
        "level": progress["level"],
        "total_kappa": len(KAPPA_IDS),
        "completed_count": len(completed_kappa),
        "available": available,
    }
    return templates.TemplateResponse(request, "index.html", context)\
        
@app.get("/tree", response_class=HTMLResponse)
def tree_page(request: Request):
    """Страница с интерактивным графом квестов."""
    progress = storage.load_progress()
    completed = set(progress["completed_quests"])
    completed_kappa = completed & KAPPA_IDS

    context = {
        "completed_count": len(completed_kappa),
        "total_kappa": len(KAPPA_IDS),
    }
    return templates.TemplateResponse(request, "tree.html", context)

@app.get("/api/health")
def health():
    """Простая проверка, что сервер жив. Откроется по /api/health."""
    return {
        "status": "ok",
        "quests_loaded": len(QUESTS),
        "kappa_quests": len(KAPPA_IDS),
    }

class ToggleRequest(BaseModel):
    """Тело запроса на переключение статуса квеста."""
    quest_id: str
    
@app.get("/quest/{quest_id}", response_class=HTMLResponse)
def quest_detail(request: Request, quest_id: str):
    """Страница с детальной информацией о квесте."""
    if quest_id not in GRAPH.nodes:
        raise HTTPException(status_code=404, detail="Квест не найден")

    data = GRAPH.nodes[quest_id]
    progress = storage.load_progress()
    completed = set(progress["completed_quests"])

    # Предшественники (что нужно сделать до этого квеста)
    predecessors = []
    for pred_id in GRAPH.predecessors(quest_id):
        pred_data = GRAPH.nodes[pred_id]
        predecessors.append({
            "id": pred_id,
            "name": pred_data["name"],
            "completed": pred_id in completed,
        })

    # Разблокирует (что откроется после выполнения)
    unlocks = []
    for succ_id in GRAPH.successors(quest_id):
        succ_data = GRAPH.nodes[succ_id]
        unlocks.append({
            "id": succ_id,
            "name": succ_data["name"],
            "completed": succ_id in completed,
        })

    # Награды за выполнение
    finish_rewards = data.get("finish_rewards") or {}
    reward_items = []
    for item_entry in finish_rewards.get("items", []):
        item = item_entry.get("item", {})
        reward_items.append({
            "name": item.get("name", "Неизвестно"),
            "count": item_entry.get("count", 1),
        })

    trader_unlocks = [
        t["name"] for t in finish_rewards.get("traderUnlock", []) if t
    ]

    # Ключи
    needed_keys_raw = data.get("needed_keys") or []
    needed_keys = []
    for key_group in needed_keys_raw:
        for key in key_group.get("keys", []):
            needed_keys.append({
                "name": key.get("name", "Неизвестно"),
                "wiki": key.get("wikiLink"),
            })

    context = {
        "quest_id": quest_id,
        "name": data["name"],
        "trader": data["trader"],
        "map": data["map"],
        "min_level": data["min_level"],
        "faction": data.get("faction", "Any"),
        "experience": data.get("experience", 0),
        "wiki_link": data.get("wiki_link"),
        "kappa_required": data.get("kappa_required", False),
        "is_completed": quest_id in completed,
        "objectives": data.get("objectives", []),
        "needed_keys": needed_keys,
        "predecessors": predecessors,
        "unlocks": unlocks,
        "reward_items": reward_items,
        "trader_unlocks": trader_unlocks,
    }
    return templates.TemplateResponse(request, "quest.html", context)

@app.post("/api/progress/toggle")
def toggle_quest(payload: ToggleRequest):
    """
    Переключает статус квеста: если был выполнен — снимает отметку,
    если не был — отмечает выполненным.
    Возвращает обновлённую сводку.
    """
    quest_id = payload.quest_id

    # Проверяем, что такой квест вообще существует в графе
    if quest_id not in GRAPH.nodes:
        raise HTTPException(status_code=404, detail=f"Квест {quest_id} не найден")

    progress = storage.load_progress()
    completed = set(progress["completed_quests"])

    if quest_id in completed:
        storage.mark_uncompleted(quest_id)
        new_status = "uncompleted"
    else:
        storage.mark_completed(quest_id)
        new_status = "completed"

    # После изменения пересчитываем актуальную статистику
    progress = storage.load_progress()
    completed = set(progress["completed_quests"])
    completed_kappa = completed & KAPPA_IDS
    available = quest_logic.get_available_quests(
        GRAPH, 
        completed=completed,
        faction=progress["faction"],
        player_level=progress["level"],
    )

    return {
        "status": new_status,
        "quest_id": quest_id,
        "completed_count": len(completed_kappa),
        "total_kappa": len(KAPPA_IDS),
        "available_ids": [q["id"] for q in available],
        
    }

@app.get("/api/tree")
def get_tree():
    """
    Возвращает граф Kappa-квестов в формате Cytoscape.js.
    Каждый узел получает статус: completed / available / locked.
    """
    progress = storage.load_progress()
    completed = set(progress["completed_quests"])
    available_ids = {
        q["id"] for q in quest_logic.get_available_quests(
            GRAPH,
            completed=completed,
            faction=progress["faction"],
            player_level=progress["level"],
        )
    }

    nodes = []
    edges = []

    # Берём только Kappa-подграф, чтобы не рисовать 500 узлов
    subgraph = GRAPH.subgraph(KAPPA_IDS)

    for node_id in subgraph.nodes:
        data = subgraph.nodes[node_id]

        if node_id in completed:
            status = "completed"
        elif node_id in available_ids:
            status = "available"
        else:
            status = "locked"

        nodes.append({
            "data": {
                "id": node_id,
                "label": data["name"],
                "trader": data["trader"],
                "status": status,
            }
        })

    for source, target in subgraph.edges:
        edges.append({
            "data": {
                "id": f"{source}->{target}",
                "source": source,
                "target": target,
            }
        })

    return {"nodes": nodes, "edges": edges}

class SettingsRequest(BaseModel):
    """Тело запроса на обновление настроек персонажа."""
    faction: str
    level: int

@app.post("/api/settings")
def update_settings(payload: SettingsRequest):
    """Обновляет фракцию и уровень игрока."""
    if payload.faction not in ("USEC", "BEAR"):
        raise HTTPException(
            status_code=400,
            detail="Фракция должна быть USEC или BEAR"
        )

    if not (1 <= payload.level <= 79):
        raise HTTPException(
            status_code=400,
            detail="Уровень должен быть от 1 до 79"
        )

    storage.set_faction(payload.faction)
    storage.set_level(payload.level)

    return {"status": "ok", "faction": payload.faction, "level": payload.level}