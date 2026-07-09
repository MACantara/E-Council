/**
 * Update Concept Paper Page JavaScript
 * Handles dynamic form field additions and conditional field toggling
 */

document.addEventListener('DOMContentLoaded', function () {
    initializeUpdateConceptPaperForm();
});

function initializeUpdateConceptPaperForm() {
    // Attach click listeners to add-field buttons
    const addObjectiveButton = document.getElementById('add-objective-btn');
    const addLearningOutcomeButton = document.getElementById('add-learning-outcome-btn');
    const addStrengthButton = document.getElementById('add-strength-btn');
    const addWeaknessButton = document.getElementById('add-weakness-btn');
    const addRecommendationButton = document.getElementById('add-recommendation-btn');
    const addObservationButton = document.getElementById('add-observation-btn');
    const addLearningButton = document.getElementById('add-learning-btn');

    if (addObjectiveButton) {
        addObjectiveButton.addEventListener('click', addObjective);
    }

    if (addLearningOutcomeButton) {
        addLearningOutcomeButton.addEventListener('click', addLearningOutcome);
    }

    if (addStrengthButton) {
        addStrengthButton.addEventListener('click', addStrength);
    }

    if (addWeaknessButton) {
        addWeaknessButton.addEventListener('click', addWeakness);
    }

    if (addRecommendationButton) {
        addRecommendationButton.addEventListener('click', addRecommendation);
    }

    if (addObservationButton) {
        addObservationButton.addEventListener('click', addObservation);
    }

    if (addLearningButton) {
        addLearningButton.addEventListener('click', addLearning);
    }

    // Handle academic year toggle
    const academicYearSelect = document.getElementById('concept-paper-academic-year');
    if (academicYearSelect) {
        academicYearSelect.addEventListener('change', toggleOtherAcademicYear);
    }

    // Initialize existing remove buttons and set initial visibility for Other A.Y.
    initializeRemoveButtons();
    toggleOtherAcademicYear();
}

function initializeRemoveButtons() {
    document.querySelectorAll('.remove-item-btn').forEach(button => {
        button.addEventListener('click', function () {
            this.parentElement.remove();
        });
    });
}

// ============================================
// Conditional Field Toggling
// ============================================

function toggleOtherAcademicYear() {
    const academicYearSelect = document.getElementById('concept-paper-academic-year');
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

// ============================================
// Dynamic Field Addition Functions
// ============================================

function addDynamicField(containerId, name, placeholder) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const div = document.createElement('div');
    div.className = 'flex items-center gap-2';

    const input = document.createElement('input');
    input.type = 'text';
    input.name = name;
    input.placeholder = placeholder;
    input.required = true;
    input.className = 'w-full rounded-lg border border-edge bg-surface px-3.5 py-2.5 text-sm text-ink placeholder:text-ink-3 transition-colors focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent';

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'remove-item-btn inline-flex shrink-0 items-center rounded-lg border border-danger px-3 py-2.5 text-sm font-medium text-danger transition-colors hover:bg-danger hover:text-white';
    removeBtn.textContent = 'Delete';
    removeBtn.addEventListener('click', function () {
        div.remove();
    });

    div.appendChild(input);
    div.appendChild(removeBtn);
    container.appendChild(div);
}

function addObjective() {
    addDynamicField('concept-paper-objectives', 'concept-paper-objectives', 'Enter Objective');
}

function addLearningOutcome() {
    addDynamicField('concept-paper-learning-outcomes', 'concept-paper-learning-outcomes', 'Enter Learning Outcome');
}

function addStrength() {
    addDynamicField('activity-strengths', 'activity-strengths', 'Enter Strength');
}

function addWeakness() {
    addDynamicField('activity-weaknesses', 'activity-weaknesses', 'Enter Weakness');
}

function addRecommendation() {
    addDynamicField('activity-recommendations', 'activity-recommendations', 'Enter Recommendation');
}

function addObservation() {
    addDynamicField('learning-journal-observations', 'learning-journal-observations', 'Enter Observation');
}

function addLearning() {
    addDynamicField('learning-journal-learnings', 'learning-journal-learnings', 'Enter Learning');
}
