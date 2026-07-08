/**
 * Add Event Page JavaScript
 * Handles form field toggling based on creation method and academic year selection
 */

document.addEventListener('DOMContentLoaded', function () {
    initializeAddEventForm();
});

function initializeAddEventForm() {
    const academicYearSelect = document.getElementById('events-academic-year');
    const otherAcademicYearContainer = document.getElementById('other-academic-year-container');
    const creationMethodSelect = document.getElementById('creation-method');
    const conceptPaperContainer = document.getElementById('concept-paper-container');
    const fieldsToToggle = [
        'events-name',
        'events-semester',
        'events-academic-year',
        'events-start-date-and-time',
        'events-end-date-and-time',
        'events-venue',
        'events-budget',
        'events-description'
    ];

    // Toggle other academic year field
    if (academicYearSelect) {
        academicYearSelect.addEventListener('change', function () {
            if (academicYearSelect.value === 'Other') {
                otherAcademicYearContainer.style.display = 'flex';
            } else {
                otherAcademicYearContainer.style.display = 'none';
            }
        });
    }

    // Toggle form fields based on creation method
    if (creationMethodSelect) {
        creationMethodSelect.addEventListener('change', function () {
            if (creationMethodSelect.value === 'existing') {
                conceptPaperContainer.style.display = 'flex';
                fieldsToToggle.forEach(function (fieldId) {
                    const field = document.getElementById(fieldId);
                    if (field) {
                        field.closest('.input-pair').style.display = 'none';
                        field.required = false;
                    }
                });
            } else {
                conceptPaperContainer.style.display = 'none';
                fieldsToToggle.forEach(function (fieldId) {
                    const field = document.getElementById(fieldId);
                    if (field) {
                        field.closest('.input-pair').style.display = 'flex';
                        field.required = true;
                    }
                });
            }
        });
    }
}
