/**
 * Отрисовка графа квестов через Cytoscape.js.
 * Загружает данные с /api/tree и рендерит интерактивный граф.
 */

document.addEventListener("DOMContentLoaded", async () => {
    try {
        const response = await fetch("/api/tree");
        const data = await response.json();

        const cy = cytoscape({
            container: document.getElementById("cy"),

            elements: [...data.nodes, ...data.edges],

            style: [
                {
                    selector: "node",
                    style: {
                        "label": "data(label)",
                        "font-size": "10px",
                        "text-wrap": "wrap",
                        "text-max-width": "120px",
                        "text-valign": "center",
                        "text-halign": "center",
                        "color": "#fff",
                        "text-outline-color": "#000",
                        "text-outline-width": 1,
                        "width": 30,
                        "height": 30,
                        "border-width": 2,
                        "border-color": "#222",
                    },
                },
                {
                    selector: "node[status = 'completed']",
                    style: { "background-color": "#80c080" },
                },
                {
                    selector: "node[status = 'available']",
                    style: { "background-color": "#d4a056" },
                },
                {
                    selector: "node[status = 'locked']",
                    style: { "background-color": "#555" },
                },
                {
                    selector: "edge",
                    style: {
                        "width": 1.5,
                        "line-color": "#555",
                        "target-arrow-color": "#555",
                        "target-arrow-shape": "triangle",
                        "curve-style": "bezier",
                    },
                },
                {
                    selector: ".highlighted",
                    style: {
                        "background-color": "#ff6b6b",
                        "line-color": "#ff6b6b",
                        "target-arrow-color": "#ff6b6b",
                        "transition-property": "background-color, line-color",
                        "transition-duration": "0.2s",
                    },
                },
            ],

            layout: {
                name: "dagre",
                rankDir: "TB",      // Top → Bottom: ранние квесты сверху
                nodeSep: 20,
                rankSep: 60,
            },

            wheelSensitivity: 0.2,
        });

        // Клик по узлу — подсветить всех предшественников
        cy.on("tap", "node", (event) => {
            const node = event.target;

            // Снимаем подсветку со всех элементов
            cy.elements().removeClass("highlighted");

            // Подсвечиваем сам узел и всех его предков
            const predecessors = node.predecessors();
            node.addClass("highlighted");
            predecessors.addClass("highlighted");

            // Заполняем информационную панель
            const info = document.getElementById("quest-info");
            document.getElementById("info-name").textContent = node.data("label");
            document.getElementById("info-trader").textContent = node.data("trader");
            document.getElementById("info-status").textContent = translateStatus(node.data("status"));
            document.getElementById("info-predecessors").textContent =
                predecessors.nodes().length;
            info.classList.remove("hidden");
        });

        // Клик по пустому месту — снять подсветку
        cy.on("tap", (event) => {
            if (event.target === cy) {
                cy.elements().removeClass("highlighted");
                document.getElementById("quest-info").classList.add("hidden");
            }
        });

    } catch (error) {
        console.error("Ошибка загрузки графа:", error);


nt.getElementById("cy").textContent = "Не удалось загрузить граф. См. консоль.";
    }
});

function translateStatus(status) {
    const map = {
        completed: "Выполнено",
        available: "Доступно",
        locked: "Заблокировано",
    };
    return map[status] || status;
} docume