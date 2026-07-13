// ── WebSocket ────────────────────────────────────────────
const ws = new WebSocket('ws://' + window.location.host + '/ws/fleet/');
const statusEl = document.getElementById('ws-status');

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
        renderAll(data.machines);
    } else if (data.type === 'update') {
        updateRow(data.machine);
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
    console.log(m);
    const pct       = (m.ktg_value * 100).toFixed(4);
    const raw       = m.ktg_value.toFixed(6);
    const threshold = (m.ktg_threshold * 100).toFixed(0);
    const color     = ktgColor(m.ktg_value, m.ktg_threshold);

    const status = m.is_in_repair
        ? '<span class="badge repair">Ремонт</span>'
        : '<span class="badge active">Работает</span>';

    const btnClass = m.is_in_repair ? 'finish' : 'send';
    const btnText  = m.is_in_repair ? 'Завершить ремонт' : 'В ремонт';

    // Дата — объявляем ДО использования
    const dateValue = m.repair_started_at
        ? m.repair_started_at.slice(0, 16)
        : '';
    const dateClass = dateValue ? 'date-input has-value' : 'date-input';

    // Проверяем роль — viewer только смотрит
    const canEdit = USER_ROLE !== 'viewer';

    // Поле даты — viewer видит только текст, остальные могут менять
    const dateField = canEdit ? `
        <input
            type="datetime-local"
            class="${dateClass}"
            value="${dateValue}"
            max="${nowISOLocal()}"
            onchange="setRepairDate(${m.id}, this.value, this)"
        />` : dateValue ? `<span>${dateValue.replace('T', ' ')}</span>` : '—';

    // Кнопка — viewer видит прочерк
    const repairBtn = canEdit ? `
        <button class="btn-repair ${btnClass}"
                onclick="toggleRepair(${m.id})">
            ${btnText}
        </button>` : '—';

    return `
        <tr id="row-${m.id}">
            <td>
                <a href="/fleet/machine/${m.id}/" class="machine-link">
                    ${m.name}
                </a>
            </td>
            <td>${m.board_number}</td>
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
                <span style="color:${m.ktg_value < m.ktg_threshold ? '#dc2626' : '#6b7280'}">
                    ${threshold}%
                </span>
            </td>
            <td>${status}</td>
            <td>${dateField}</td>
            <td>${repairBtn}</td>
        </tr>
    `;
}

// ── Рендер ───────────────────────────────────────────────

function renderAll(machines) {
    const tbody = document.getElementById('machine-list');
    tbody.innerHTML = machines.map(buildRow).join('');
}

function updateRow(machine) {
    const row = document.getElementById('row-' + machine.id);
    if (row) row.outerHTML = buildRow(machine);
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