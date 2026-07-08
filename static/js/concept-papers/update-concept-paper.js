/**
 * Update Concept Paper Page JavaScript
 * Handles dynamic form field additions and conditional field toggling
 */

document.addEventListener('DOMContentLoaded', function () {
    initializeUpdateConceptPaperForm();
});

function initializeUpdateConceptPaperForm() {
    // Remove inline onclick handlers and replace with event listeners
    const addObjectiveButton = document.querySelector('button[onclick="addObjective()"]');
    const addLearningOutcomeButton = document.querySelector('button[onclick="addLearningOutcome()"]');
    const addStrengthButton = document.querySelector('button[onclick="addStrength()"]');
    const addWeaknessButton = document.querySelector('button[onclick="addWeakness()"]');
    const addRecommendationButton = document.querySelector('button[onclick="addRecommendation()"]');
    const addObservationButton = document.querySelector('button[onclick="addObservation()"]');
    const addLearningButton = document.querySelector('button[onclick="addLearning()"]');

    if (addObjectiveButton) {
        addObjectiveButton.removeAttribute('onclick');
        addObjectiveButton.addEventListener('click', addObjective);
    }

    if (addLearningOutcomeButton) {
        addLearningOutcomeButton.removeAttribute('onclick');
        addLearningOutcomeButton.addEventListener('click', addLearningOutcome);
    }

    if (addStrengthButton) {
        addStrengthButton.removeAttribute('onclick');
        addStrengthButton.addEventListener('click', addStrength);
    }

    if (addWeaknessButton) {
        addWeaknessButton.removeAttribute('onclick');
        addWeaknessButton.addEventListener('click', addWeakness);
    }

    if (addRecommendationButton) {
        addRecommendationButton.removeAttribute('onclick');
        addRecommendationButton.addEventListener('click', addRecommendation);
    }

    if (addObservationButton) {
        addObservationButton.removeAttribute('onclick');
        addObservationButton.addEventListener('click', addObservation);
    }

    if (addLearningButton) {
        addLearningButton.removeAttribute('onclick');
        addLearningButton.addEventListener('click', addLearning);
    }

    // Handle academic year toggle
    const academicYearSelect = document.getElementById('concept-paper-academic-year');
    if (academicYearSelect) {
        academicYearSelect.removeAttribute('onchange');
        academicYearSelect.addEventListener('change', toggleOtherAcademicYear);
    }
}

// ============================================
// Conditional Field Toggling
// ============================================

function toggleOtherAcademicYear() {
    const academicYearSelect = document.getElementById('concept-paper-academic-year');
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

// ============================================
// Dynamic Field Addition Functions
// ============================================

function addObjective() {
    const container = document.getElementById('concept-paper-objectives');
    const input = document.createElement('input');
    input.type = 'text';
    input.name = 'concept-paper-objectives';
    input.placeholder = 'Enter Objective';
    input.required = true;
    container.appendChild(input);
}

function addLearningOutcome() {
    const container = document.getElementById('concept-paper-learning-outcomes');
    const input = document.createElement('input');
    input.type = 'text';
    input.name = 'concept-paper-learning-outcomes';
    input.placeholder = 'Enter Learning Outcome';
    input.required = true;
    container.appendChild(input);
}

function addStrength() {
    const container = document.getElementById('activity-strengths');
    const input = document.createElement('input');
    input.type = 'text';
    input.name = 'activity-strengths';
    input.placeholder = 'Enter Strength';
    input.required = true;
    container.appendChild(input);
}

function addWeakness() {
    const container = document.getElementById('activity-weaknesses');
    const input = document.createElement('input');
    input.type = 'text';
    input.name = 'activity-weaknesses';
    input.placeholder = 'Enter Weakness';
    input.required = true;
    container.appendChild(input);
}

function addRecommendation() {
    const container = document.getElementById('activity-recommendations');
    const input = document.createElement('input');
    input.type = 'text';
    input.name = 'activity-recommendations';
    input.placeholder = 'Enter Recommendation';
    input.required = true;
    container.appendChild(input);
}

function addObservation() {
    const container = document.getElementById('learning-journal-observations');
    const input = document.createElement('input');
    input.type = 'text';
    input.name = 'learning-journal-observations';
    input.placeholder = 'Enter Observation';
    input.required = true;
    container.appendChild(input);
}

function addLearning() {
    const container = document.getElementById('learning-journal-learnings');
    const input = document.createElement('input');
    input.type = 'text';
    input.name = 'learning-journal-learnings';
    input.placeholder = 'Enter Learning';
    input.required = true;
    container.appendChild(input);
}
