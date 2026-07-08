/**
 * Add Financial Report Page JavaScript
 * Handles academic year toggle and auto-populating title from event selection
 */

document.addEventListener('DOMContentLoaded', function () {
    initializeAddFinancialReportForm();
});

function initializeAddFinancialReportForm() {
    const academicYearSelect = document.getElementById('financial-reports-academic-year');
    const otherAcademicYearInput = document.getElementById('other-academic-year');
    const eventSelect = document.getElementById('financial-reports-events-id');
    const titleInput = document.getElementById('financial-reports-title');

    // Academic year toggle
    if (academicYearSelect) {
        academicYearSelect.addEventListener('change', function () {
            if (this.value === 'Other') {
                otherAcademicYearInput.style.display = 'block';
                otherAcademicYearInput.required = true;
            } else {
                otherAcademicYearInput.style.display = 'none';
                otherAcademicYearInput.required = false;
            }
        });
    }

    // Auto-populate title from event selection
    if (eventSelect && titleInput) {
        eventSelect.addEventListener('change', function () {
            const selectedOption = this.options[this.selectedIndex];
            const eventName = selectedOption.getAttribute('data-event-name');
            if (eventName) {
                titleInput.value = `${eventName} Financial Report`;
            } else {
                titleInput.value = '';
            }
        });
    }
}
