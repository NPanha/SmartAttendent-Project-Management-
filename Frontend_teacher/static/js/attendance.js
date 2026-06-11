// Attendance page specific functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize data table sorting
    initializeTableSorting();
    
    // Initialize bulk actions
    initializeBulkActions();
    
    // Setup attendance editing
    setupAttendanceEditing();
});

function initializeTableSorting() {
    const table = document.getElementById('attendanceTable');
    if (!table) return;
    
    const headers = table.querySelectorAll('th');
    headers.forEach((header, index) => {
        if (header.textContent !== 'Actions') {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => sortTable(index));
        }
    });
}

function sortTable(columnIndex) {
    const table = document.getElementById('attendanceTable');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const isAscending = table.getAttribute('data-sort-dir') !== 'asc';
    
    rows.sort((a, b) => {
        const aVal = a.cells[columnIndex].textContent.trim();
        const bVal = b.cells[columnIndex].textContent.trim();
        
        // Try to parse as number
        const aNum = parseFloat(aVal);
        const bNum = parseFloat(bVal);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? aNum - bNum : bNum - aNum;
        }
        
        // Otherwise sort as string
        return isAscending 
            ? aVal.localeCompare(bVal)
            : bVal.localeCompare(aVal);
    });
    
    // Clear and re-append sorted rows
    rows.forEach(row => tbody.appendChild(row));
    
    // Update sort indicator
    table.setAttribute('data-sort-dir', isAscending ? 'asc' : 'desc');
    
    // Update header sort indicators
    const headers = table.querySelectorAll('th');
    headers.forEach((header, index) => {
        header.classList.remove('sort-asc', 'sort-desc');
        if (index === columnIndex) {
            header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
        }
    });
}

function initializeBulkActions() {
    const bulkSelect = document.createElement('select');
    bulkSelect.className = 'bulk-action-select';
    bulkSelect.innerHTML = `
        <option value="">Bulk Actions</option>
        <option value="mark-present">Mark as Present</option>
        <option value="mark-absent">Mark as Absent</option>
        <option value="mark-excused">Mark as Excused</option>
        <option value="export-selected">Export Selected</option>
    `;
    
    bulkSelect.addEventListener('change', function(e) {
        const action = e.target.value;
        if (!action) return;
        
        const selectedRows = document.querySelectorAll('.student-checkbox:checked');
        if (selectedRows.length === 0) {
            showNotification('Please select at least one student', 'warning');
            e.target.value = '';
            return;
        }
        
        switch(action) {
            case 'export-selected':
                exportSelectedStudents(selectedRows);
                break;
            default:
                bulkUpdateAttendance(action.replace('mark-', ''), selectedRows);
                break;
        }
        
        e.target.value = '';
    });
    
    // Add bulk actions to page header
    const headerActions = document.querySelector('.header-actions');
    if (headerActions) {
        headerActions.appendChild(bulkSelect);
    }
}

function setupAttendanceEditing() {
    // Add edit buttons to table rows
    const table = document.getElementById('attendanceTable');
    if (!table) return;
    
    table.querySelectorAll('tbody tr').forEach(row => {
        const editBtn = document.createElement('button');
        editBtn.className = 'action-btn edit';
        editBtn.innerHTML = '<i class="fas fa-edit"></i>';
        editBtn.title = 'Edit Attendance';
        editBtn.addEventListener('click', () => {
            const studentId = row.getAttribute('data-student-id');
            editAttendance(studentId);
        });
        
        const actionsCell = row.cells[row.cells.length - 1];
        actionsCell.appendChild(editBtn);
    });
}

function exportSelectedStudents(selectedRows) {
    const studentIds = Array.from(selectedRows).map(cb => cb.value);
    const courseId = document.querySelector('[data-course-id]')?.getAttribute('data-course-id');
    const classGroup = document.querySelector('[data-class-group]')?.getAttribute('data-class-group');
    
    if (!courseId || !classGroup) {
        showNotification('Unable to export: missing course information', 'error');
        return;
    }
    
    const url = `/api/export-selected?course_id=${courseId}&class_group=${classGroup}&students=${studentIds.join(',')}`;
    window.open(url, '_blank');
    showNotification(`Exported ${studentIds.length} student records`, 'success');
}

function bulkUpdateAttendance(status, selectedRows) {
    const studentIds = Array.from(selectedRows).map(cb => cb.value);
    const courseId = document.querySelector('[data-course-id]')?.getAttribute('data-course-id');
    const date = new Date().toISOString().split('T')[0];
    
    if (!confirm(`Mark ${studentIds.length} student(s) as ${status}?`)) {
        return;
    }
    
    // In a real app, make API call to update multiple records
    showNotification(`Updating ${studentIds.length} students to ${status}...`, 'info');
    
    // Simulate API call
    setTimeout(() => {
        showNotification(`Successfully updated ${studentIds.length} students`, 'success');
        // Refresh the table
        location.reload();
    }, 1500);
}