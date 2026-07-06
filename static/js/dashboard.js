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
    if (value >= 0.8) return '#16a34a';        // зелёный
    if (value >= threshold) return '#d97706';  // жёлтый
    return '#dc2626';                          // красный
}

function nowISOLocal() {
    /* Возвращает текущее время в формате datetime-local max="..."
       Нужно чтобы запретить выбор даты в будущем */
    const now = new Date();
    // Сдвигаем на timezone offset чтобы получить локальное время
    const offset = now.getTimezoneOffset() * 60000;
    return new Date(now - offset).toISOString().slice(0, 16);
}

function formatUpdated(isoString) {
    /* Форматирует дату последнего обновления КТГ
       Например: '02.07.2026 14:35' */
    if (!isoString) return '—';
    const d = new Date(isoString);
    const pad = n => String(n).padStart(2, '0');
    return `${pad(d.getDate())}.${pad(d.getMonth()+1)}.${d.getFullYear()} `
         + `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

// ── Строка таблицы ───────────────────────────────────────

function buildRow(m) {
    const pct       = (m.ktg_value * 100).toFixed(4);  // 95.3821%
    const raw       = m.ktg_value.toFixed(6);           // 0.953821
    const threshold = (m.ktg_threshold * 100).toFixed(0);
    const color     = ktgColor(m.ktg_value, m.ktg_threshold);

    const status = m.is_in_repair
        ? '<span class="badge repair">Ремонт</span>'
        : '<span class="badge active">Работает</span>';

    const btnClass = m.is_in_repair ? 'finish' : 'send';
    const btnText  = m.is_in_repair ? 'Завершить ремонт' : 'В ремонт';

    // Дата начала ремонта для input
    const dateValue = m.repair_started_at
        ? m.repair_started_at.slice(0, 16)
        : '';
    const dateClass = dateValue ? 'date-input has-value' : 'date-input';

    // Время последнего обновления КТГ
    const updated = formatUpdated(m.ktg_updated_at);

    return `
        <tr id="row-${m.id}">
            <td>${m.name}</td>
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
                <!-- Время последнего обновления КТГ -->
                <div class="ktg-updated">обновлено: ${updated}</div>
            </td>
            <td>
                <span style="color:${m.ktg_value < m.ktg_threshold ? '#dc2626' : '#6b7280'}">
                    ${threshold}%
                </span>
            </td>
            <td>${status}</td>
            <td>
                <!--
                    max="${nowISOLocal()}" — запрет выбора даты в будущем.
                    onchange — сразу отправляем на сервер.
                    Машина автоматически встаёт в ремонт.
                -->
                <input
                    type="datetime-local"
                    class="${dateClass}"
                    value="${dateValue}"
                    max="${nowISOLocal()}"
                    onchange="setRepairDate(${m.id}, this.value, this)"
                />
            </td>
            <td>
                <button class="btn-repair ${btnClass}"
                        onclick="toggleRepair(${m.id})">
                    ${btnText}
                </button>
            </td>
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

    // Дополнительная проверка на стороне JS — дата не в будущем
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