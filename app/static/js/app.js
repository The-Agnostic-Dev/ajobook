// Small progressive enhancements for Ajobook pages. Everything works without JS
// except column sorting and the "are you sure?" prompts.

function confirmBeforeSubmit() {
  document.querySelectorAll('form[data-confirm]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault()
    })
  })
}

function cellValue(row, index) {
  const cell = row.cells[index]
  return cell.dataset.sort ?? cell.textContent.trim()
}

function makeSortable(table) {
  const headers = table.tHead.rows[0].cells
  Array.from(headers).forEach((th, index) => {
    th.classList.add('sort-handle')
    th.tabIndex = 0
    const sort = () => {
      const ascending = th.dataset.dir !== 'asc'
      Array.from(headers).forEach((h) => delete h.dataset.dir)
      th.dataset.dir = ascending ? 'asc' : 'desc'
      const body = table.tBodies[0]
      const rows = Array.from(body.rows)
      rows.sort((a, b) => {
        const result = cellValue(a, index).localeCompare(cellValue(b, index), 'en-NG')
        return ascending ? result : -result
      })
      rows.forEach((row) => body.appendChild(row))
    }
    th.addEventListener('click', sort)
    th.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') sort()
    })
  })
}

document.addEventListener('DOMContentLoaded', () => {
  confirmBeforeSubmit()
  document.querySelectorAll('table.sortable').forEach(makeSortable)
})
