/**
 * Логика интерактивных чекбоксов на главной странице.
 * При клике отправляет POST на /api/progress/toggle
 * и перезагружает страницу для обновления списка доступных квестов.
 */

document.addEventListener("DOMContentLoaded", () => {
    const checkboxes = document.querySelectorAll(".quest-checkbox");

    checkboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", async (event) => {
            const questId = event.target.dataset.questId;

            // Блокируем чекбокс, пока запрос идёт
            checkbox.disabled = true;

            try {
                const response = await fetch("/api/progress/toggle", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ quest_id: questId }),
                });

                if (!response.ok) {
                    throw new Error(`Сервер ответил ${response.status}`);
                }

                const data = await response.json();
                console.log("Сервер ответил:", data);

                // Обновляем счётчик прогресса без перезагрузки
                document.getElementById("completed-count").textContent = data.completed_count;

                // Перезагружаем страницу, чтобы обновился список доступных квестов
                // (после отметки могли разблокироваться новые)
                window.location.reload();

            } catch (error) {
                console.error("Ошибка:", error);
                alert("Не удалось обновить прогресс. Подробности в консоли.");
                checkbox.checked = !checkbox.checked; // откатываем визуально
                checkbox.disabled = false;
            }
        });
    });
// Обработчик формы настроек
const form = document.getElementById("settings-form");
if (form) {
    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const faction = document.getElementById("faction-select").value;
        const level = parseInt(document.getElementById("level-input").value, 10);
        const status = document.getElementById("settings-status");

        try {
            const response = await fetch("/api/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ faction, level }),
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || "Ошибка сервера");
            }

            status.textContent = "Сохранено ✓";
            status.className = "settings-status success";

            // Перезагружаем страницу, чтобы пересчитался список доступных
            setTimeout(() => window.location.reload(), 500);

        } catch (error) {
            console.error(error);
            status.textContent = "Ошибка: " + error.message;
            status.className = "settings-status error";
        }
    });
}
});