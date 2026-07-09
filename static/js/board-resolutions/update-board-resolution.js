/**
 * Update Board Resolution Page JavaScript
 * Handles conditional field toggling for academic year
 */

document.addEventListener('DOMContentLoaded', function () {
    initializeUpdateBoardResolutionForm();
});

function initializeUpdateBoardResolutionForm() {
    const academicYearSelect = document.getElementById('board-resolutions-academic-year');
    if (academicYearSelect) {
        academicYearSelect.removeAttribute('onchange');
        academicYearSelect.addEventListener('change', toggleOtherAcademicYear);
    }
}

function toggleOtherAcademicYear() {
    const academicYearSelect = document.getElementById('board-resolutions-academic-year');
    const otherAcademicYearContainer = document.getElementById('other-academic-year-container');
    const otherAcademicYearInput = document.getElementById('other-academic-year-input');
    if (academicYearSelect.value === 'Other') {
        if (otherAcademicYearContainer) otherAcademicYearContainer.style.display = 'block';
        if (otherAcademicYearInput) otherAcademicYearInput.required = true;
    } else {
        if (otherAcademicYearContainer) otherAcademicYearContainer.style.display = 'none';
        if (otherAcademicYearInput) otherAcademicYearInput.required = false;
    }
}
