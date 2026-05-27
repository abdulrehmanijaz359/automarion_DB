const API = 'http://localhost:5000'
let selectedSlot = null

// ─────────────────────────────────────
// FETCH HELPERS
// ─────────────────────────────────────

async function fetchData(url) {
    try {
        const res = await fetch(url)
        return await res.json()
    } catch (err) {
        console.error('Fetch error:', err)
        return null
    }
}

async function postData(url, body) {
    try {
        const res = await fetch(url, {
            method : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body   : JSON.stringify(body)
        })
        return await res.json()
    } catch (err) {
        console.error('Post error:', err)
        return null
    }
}

// ─────────────────────────────────────
// ALARM BANNER
// ─────────────────────────────────────

async function checkAlarms() {
    const alarms = await fetchData(`${API}/api/alarms/active`)
    if (!alarms) return

    const banner = document.getElementById('alarm-banner')
    const text   = document.getElementById('alarm-banner-text')

    if (alarms.length > 0) {
        banner.style.display = 'block'
        text.textContent =
            `${alarms.length} active alarm(s): ` +
            `${alarms[0].alarm_type} — ${alarms[0].message}`
    } else {
        banner.style.display = 'none'
    }
}

async function resolveAlarms() {
    const alarms = await fetchData(`${API}/api/alarms/active`)
    if (!alarms) return
    for (const alarm of alarms) {
        await fetch(`${API}/api/alarms/${alarm.id}/resolve`, {
            method: 'POST'
        })
    }
    checkAlarms()
}

// ─────────────────────────────────────
// UPDATE SUMMARY CARDS
// ─────────────────────────────────────

async function updateSummary() {
    const data = await fetchData(`${API}/api/summary`)
    if (!data) return

    document.getElementById('total-slots').textContent =
        data.total_slots
    document.getElementById('occupied-slots').textContent =
        data.occupied_slots
    document.getElementById('empty-slots').textContent =
        data.empty_slots
    document.getElementById('reserved-slots').textContent =
        data.reserved_available
    document.getElementById('pending-commands').textContent =
        data.pending_commands
    document.getElementById('server-time').textContent =
        data.server_time
    document.getElementById('entry-item').textContent =
        data.entry_slot?.item_name || 'Empty'
    document.getElementById('exit-item').textContent =
        data.exit_slot?.item_name  || 'Empty'
}

// ─────────────────────────────────────
// BUILD WAREHOUSE GRID
// ─────────────────────────────────────

async function updateGrid() {
    const slots = await fetchData(`${API}/api/slots/warehouse`)
    if (!slots) return

    const levels = { A: [], B: [], C: [] }
    slots.forEach(slot => {
        if (levels[slot.level]) levels[slot.level].push(slot)
    })

    Object.keys(levels).forEach(level => {
        const grid = document.getElementById(`grid-${level}`)
        if (!grid) return
        grid.innerHTML = ''

        const sorted = levels[level].sort((a, b) =>
            a.row_num - b.row_num || a.col_num - b.col_num)

        sorted.forEach(slot => {
            const div = document.createElement('div')
            div.className =
                `slot ${slot.status} ` +
                `${slot.is_temporary ? 'temporary' : ''}`
            div.dataset.level = slot.level
            div.dataset.row   = slot.row_num
            div.dataset.col   = slot.col_num

            if (selectedSlot &&
                selectedSlot.level === slot.level &&
                selectedSlot.row   === slot.row_num &&
                selectedSlot.col   === slot.col_num) {
                div.classList.add('selected')
            }

            div.innerHTML = `
                <div class="slot-name">
                    ${slot.level}(${slot.row_num},${slot.col_num})
                </div>
                <div class="slot-item">
                    ${slot.item_name || '—'}
                </div>
                <div class="slot-status">
                    ${slot.is_temporary ? 'temp' : slot.status}
                </div>
            `

            div.addEventListener('click', () => selectSlot(slot))
            grid.appendChild(div)
        })
    })
}

// ─────────────────────────────────────
// UPDATE RESERVED SLOTS
// ─────────────────────────────────────

async function updateReserved() {
    const slots = await fetchData(`${API}/api/slots/reserved`)
    if (!slots) return

    const container =
        document.getElementById('reserved-slots-list')
    container.innerHTML = slots.map(slot => `
        <div class="reserved-row">
            <span class="reserved-name">
                Reserved Slot ${slot.row_num}
            </span>
            <span class="reserved-badge
                ${slot.status === 'empty'
                    ? 'badge-empty'
                    : 'badge-occupied'}">
                ${slot.status === 'empty' ? 'Free' : 'In use'}
            </span>
        </div>
    `).join('')
}

// ─────────────────────────────────────
// UPDATE GRIPPER STATUS
// ─────────────────────────────────────

async function updateGripperStatus() {
    const commands = await fetchData(`${API}/api/commands`)
    if (!commands || commands.length === 0) return

    const latest = commands[0]
    const statusMap = {
        'pending'  : 'Pending',
        'approved' : 'Approved',
        'completed': 'Done',
        'rejected' : 'Rejected',
        'failed'   : 'Failed',
        'cancelled': 'Cancelled'
    }

    document.getElementById('gripper-status').textContent =
        statusMap[latest.status] || latest.status

    document.getElementById('last-command').textContent =
        `${latest.command_type?.toUpperCase()} ` +
        `${latest.target_level}` +
        `(${latest.target_row},${latest.target_col})`

    document.getElementById('last-updated').textContent =
        new Date().toLocaleTimeString()
}

// ─────────────────────────────────────
// SELECT A SLOT
// ─────────────────────────────────────

function selectSlot(slot) {
    selectedSlot = {
        level : slot.level,
        row   : slot.row_num,
        col   : slot.col_num,
        status: slot.status,
        item  : slot.item_name
    }

    const display = document.getElementById('selected-slot')
    display.innerHTML = `
        <p>Selected:
            <strong>
                ${slot.level}(${slot.row_num},${slot.col_num})
            </strong>
        </p>
        <p class="hint">
            Status: ${slot.status}
            ${slot.item_name ? '— ' + slot.item_name : ''}
        </p>
    `

    document.getElementById('command-buttons')
        .style.display = 'flex'
    hideResult()
    updateGrid()
}

// ─────────────────────────────────────
// SEND RETRIEVE COMMAND
// ─────────────────────────────────────

document.getElementById('btn-retrieve')
    .addEventListener('click', async () => {
    if (!selectedSlot) return

    showResult('Sending retrieve command...', 'success')

    const result = await postData(
        `${API}/api/commands/retrieve`, {
        level: selectedSlot.level,
        row  : selectedSlot.row,
        col  : selectedSlot.col
    })

    if (result && result.success) {
        showResult(`${result.message}`, 'success')
        document.getElementById('last-command').textContent =
            `RETRIEVE ${selectedSlot.level}` +
            `(${selectedSlot.row},${selectedSlot.col})`
    } else {
        showResult(
            `${result?.error || 'Command failed'}`, 'error')
    }

    clearSelection()
})

// ─────────────────────────────────────
// SEND STORE COMMAND
// ─────────────────────────────────────

document.getElementById('btn-store')
    .addEventListener('click', async () => {
    if (!selectedSlot) return

    const itemName =
        document.getElementById('item-name-input')
            .value.trim()

    if (!itemName) {
        showResult('Please enter an item name!', 'error')
        return
    }

    showResult('Sending store command...', 'success')

    const result = await postData(
        `${API}/api/commands/store`, {
        level    : selectedSlot.level,
        row      : selectedSlot.row,
        col      : selectedSlot.col,
        item_name: itemName
    })

    if (result && result.success) {
        showResult(`${result.message}`, 'success')
        document.getElementById('item-name-input').value = ''
    } else {
        showResult(
            `${result?.error || 'Command failed'}`, 'error')
    }

    clearSelection()
})

// ─────────────────────────────────────
// CANCEL SELECTION
// ─────────────────────────────────────

document.getElementById('btn-cancel')
    .addEventListener('click', () => {
    clearSelection()
})

function clearSelection() {
    selectedSlot = null
    document.getElementById('selected-slot').innerHTML = `
        <p>No slot selected</p>
        <p class="hint">
            Click a slot on the grid to select it
        </p>
    `
    document.getElementById('command-buttons')
        .style.display = 'none'
    document.getElementById('item-name-input').value = ''
    updateGrid()
}

// ─────────────────────────────────────
// RESULT MESSAGE
// ─────────────────────────────────────

function showResult(message, type) {
    const el = document.getElementById('result-message')
    el.textContent = message
    el.className   = `result-message ${type}`
}

function hideResult() {
    const el = document.getElementById('result-message')
    el.className = 'result-message'
}

// ─────────────────────────────────────
// REFRESH ALL
// ─────────────────────────────────────

async function refreshAll() {
    await updateSummary()
    await updateGrid()
    await updateReserved()
    await updateGripperStatus()
    await checkAlarms()
}

refreshAll()
setInterval(refreshAll, 3000)