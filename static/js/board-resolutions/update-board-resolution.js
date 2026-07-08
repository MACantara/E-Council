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
    const otherAcademicYearInput = document.getElementById('other-academic-year-input');
    const otherAcademicYearLabel = document.getElementById('other-academic-year-label');
    if (academicYearSelect.value === 'Other') {
        otherAcademicYearInput.style.display = 'block';
        otherAcademicYearInput.required = true;
        otherAcademicYearLabel.style.display = 'block';
        otherAcademicYearLabel.required = true;
    } else {
        otherAcademicYearInput.style.display = 'none';
        otherAcademicYearInput.required = false;
        otherAcademicYearLabel.style.display = 'none';
        otherAcademicYearLabel.required = false;
    }
}
