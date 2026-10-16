// ── WebSocket ────────────────────────────────────────────
const ws = new WebSocket('ws://' + window.location.host + '/ws/fleet/');
const statusEl = document.getElementById('ws-status');

// Все машины храним здесь — единый источник правды на фронте.
let machinesById = {};

// Индекс колонки «Начало ремонта» (0-based): Машина, Борт, Заказчик,
// Моточасы, КТГ, Порог, Статус, Начало ремонта, Действие
const DATE_COL = 7;

ws.onopen = function() {
    statusEl.textContent = 'Онлайн';
    statusEl.className = 'ws-badge online';
};

ws.onclose = function() {
    statusEl.textContent = 'Офлайн';
    statusEl.className = 'ws-badge offline';
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'init') {
        machinesById = {};
        data.machines.forEach(m => { machinesById[m.id] = m; });
        renderAll();
    } else if (data.type === 'update') {
        machinesById[data.machine.id] = data.machine;
        renderAll();
    }
};

// ── Helpers ──────────────────────────────────────────────

function ktgColor(value, threshold) {
    if (value >= 0.8) return '#16a34a';
    if (value >= threshold) return '#d97706';
    return '#dc2626';
}

function nowISOLocal() {
    const now = new Date();
    const offset = now.getTimezoneOffset() * 60000;
    return new Date(now - offset).toISOString().slice(0, 16);
}

// ── Строка таблицы ───────────────────────────────────────

function buildRow(m) {
    const pct       = (m.ktg_value * 100).toFixed(4);
    const raw       = m.ktg_value.toFixed(6);
    const threshold = (m.ktg_threshold * 100).toFixed(0);
    const color     = ktgColor(m.ktg_value, m.ktg_threshold);

    // КТГ ниже порога — подсвечиваем всю строку, а не только цифру
    const isCritical = m.ktg_value < m.ktg_threshold;
    const rowClass   = isCritical ? 'row-critical' : '';

    const status = m.is_in_repair
        ? '<span class="badge repair">Ремонт</span>'
        : '<span class="badge active">Работает</span>';

    const btnClass = m.is_in_repair ? 'finish' : 'send';
    const btnText  = m.is_in_repair ? 'Завершить ремонт' : 'В ремонт';

    const dateValue = m.repair_started_at
        ? m.repair_started_at.slice(0, 16)
        : '';
    const dateClass = dateValue ? 'date-input has-value' : 'date-input';

    // Это только про отображение. Реальная проверка прав — на сервере
    // (consumers.py → can_edit_machine), её через консоль не обойти.
    const canEdit = USER_ROLE !== 'viewer';

    const dateField = canEdit ? `
        <input
            type="datetime-local"
            class="${dateClass}"
            value="${dateValue}"
            max="${nowISOLocal()}"
            onchange="setRepairDate(${m.id}, this.value, this)"
        />` : dateValue ? `<span>${dateValue.replace('T', ' ')}</span>` : '—';

    const repairBtn = canEdit ? `
        <button class="btn-repair ${btnClass}"
                onclick="toggleRepair(${m.id})">
            ${btnText}
        </button>` : '—';

    return `
        <tr id="row-${m.id}" class="${rowClass}">
            <td>
                <a href="/fleet/machine/${m.id}/" class="machine-link">
                    ${m.name}
                </a>
            </td>
            <td>${m.board_number}</td>
            <td>${m.customer}</td>
            <td>${m.engine_hours}</td>
            <td>
                <span class="ktg-value" style="color:${color}">${pct}%</span>
                <div class="ktg-small">${raw}</div>
                <div class="ktg-bar">
                    <div class="ktg-bar-fill"
                         style="width:${Math.min(parseFloat(pct), 100)}%;
                                background:${color}">
                    </div>
                </div>
            </td>
            <td>
                <span style="color:${isCritical ? '#dc2626' : '#6b7280'}">
                    ${threshold}%
                </span>
            </td>
            <td>${status}</td>
            <td>${dateField}</td>
            <td>${repairBtn}</td>
        </tr>
    `;
}

// Обновляет строку на месте: меняет классы и содержимое всех ячеек,
// КРОМЕ ячейки с полем даты. Поле даты остаётся тем же DOM-элементом,
// поэтому открытый календарь не закрывается, а КТГ и статус обновляются.
function patchRow(tr, m) {
    const tmp = document.createElement('tbody');
    tmp.innerHTML = buildRow(m);
    const fresh = tmp.firstElementChild;

    tr.className = fresh.className;
    for (let i = 0; i < fresh.cells.length; i++) {
        if (i === DATE_COL) continue;
        tr.cells[i].innerHTML = fresh.cells[i].innerHTML;
    }
}

// ── Рендер ───────────────────────────────────────────────

function renderAll() {
    const tbody = document.getElementById('machine-list');

    // Самый низкий КТГ — наверх. При равном КТГ — по имени,
    // чтобы строки с одинаковым значением не прыгали местами.
    const sorted = Object.values(machinesById).sort((a, b) => {
        if (a.ktg_value !== b.ktg_value) return a.ktg_value - b.ktg_value;
        return a.name.localeCompare(b.name);
    });

    if (sorted.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9">Машин нет</td></tr>';
        return;
    }

    // Если сейчас в фокусе поле даты в таблице — не уничтожаем его строку.
    // Фокус после Esc/Enter остаётся в поле, поэтому проверяем именно фокус,
    // а не события клавиш (календарь их перехватывает).
    const active = document.activeElement;
    const keepTr = (active && active.tagName === 'INPUT' && tbody.contains(active))
        ? active.closest('tr')
        : null;

    if (!keepTr) {
        tbody.innerHTML = sorted.map(buildRow).join('');
        return;
    }

    const keepId = keepTr.id;
    const before = [];
    const after  = [];
    let passedKeep = false;
    let keepMachine = null;

    sorted.forEach(m => {
        if (`row-${m.id}` === keepId) {
            passedKeep = true;
            keepMachine = m;
            return;
        }
        (passedKeep ? after : before).push(buildRow(m));
    });

    // Обновляем текст строки с полем даты, не трогая сам input
    if (keepMachine) patchRow(keepTr, keepMachine);

    // Остальные строки пересоздаём и ставим в нужный порядок вокруг неё
    Array.from(tbody.children).forEach(tr => {
        if (tr !== keepTr) tr.remove();
    });
    keepTr.insertAdjacentHTML('beforebegin', before.join(''));
    keepTr.insertAdjacentHTML('afterend', after.join(''));
}

// ── Действия ─────────────────────────────────────────────

function toggleRepair(machineId) {
    ws.send(JSON.stringify({
        action: 'toggle_repair',
        machine_id: machineId
    }));
}

function setRepairDate(machineId, dateValue, inputEl) {
    if (!dateValue) return;

    const chosen = new Date(dateValue);
    const now    = new Date();
    if (chosen > now) {
        alert('Нельзя выбрать дату в будущем!');
        inputEl.value = '';
        inputEl.classList.remove('has-value');
        return;
    }

    inputEl.classList.add('has-value');

    ws.send(JSON.stringify({
        action: 'set_repair_date',
        machine_id: machineId,
        repair_date: dateValue
    }));
}