/**
 * Update Financial Report Page JavaScript
 * Handles academic year toggle
 */

document.addEventListener('DOMContentLoaded', function () {
    initializeUpdateFinancialReportForm();
});

function initializeUpdateFinancialReportForm() {
    const academicYearSelect = document.getElementById('financial-reports-academic-year');
    const otherAcademicYearInput = document.getElementById('other-academic-year');

    if (academicYearSelect) {
        academicYearSelect.addEventListener('change', function () {
            if (this.value === 'Other') {
                otherAcademicYearInput.classList.remove('hidden');
                otherAcademicYearInput.required = true;
            } else {
                otherAcademicYearInput.classList.add('hidden');
                otherAcademicYearInput.required = false;
            }
        });
    }
}
