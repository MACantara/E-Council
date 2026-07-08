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

// Set the current date and time as the default value for the datetime-local input
document.addEventListener('DOMContentLoaded', function () {
    const dateInput = document.getElementById('concept-paper-date');
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const formattedDate = `${year}-${month}-${day}T${hours}:${minutes}`;
    dateInput.value = formattedDate;
});

async function generateContent(endpoint, data, targetId) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    if (!csrfToken) {
        console.error('CSRF token not found');
        alert('CSRF token is missing. Please refresh the page.');
        return;
    }

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken.getAttribute('content')
            },
            body: JSON.stringify(data),
            credentials: 'same-origin'
        });

        console.log('Response status:', response.status);
        console.log('Response headers:', Object.fromEntries(response.headers.entries()));

        let responseData;
        const contentType = response.headers.get('content-type');
        console.log('Content-Type:', contentType);

        if (contentType && contentType.includes('application/json')) {
            responseData = await response.json();
        } else {
            const responseText = await response.text();
            console.error('Non-JSON response:', responseText);
            throw new Error('Server returned non-JSON response');
        }

        if (!response.ok) {
            throw new Error(responseData.error || `Server error: ${response.status}`);
        }

        if (responseData.content) {
            document.getElementById(targetId).value = responseData.content;
        } else {
            console.error('No content in response:', responseData);
            throw new Error('No content in server response');
        }
    } catch (error) {
        console.error('Error in generateContent:', error);
        alert(`Error generating content: ${error.message}`);
    }
}

async function generateBody() {
    const subject = document.getElementById('concept-paper-subject').value;
    const startDate = document.getElementById('concept-paper-event-start-date-and-time').value;
    const endDate = document.getElementById('concept-paper-event-end-date-and-time').value;
    const location = document.getElementById('concept-paper-location').value;

    await generateContent('/generate-concept-body', {
        subject,
        start_date: startDate,
        end_date: endDate,
        location
    }, 'concept-paper-body');
}

async function generateDescriptions() {
    const subject = document.getElementById('concept-paper-subject').value;
    await generateContent('/generate-concept-descriptions', {
        subject
    }, 'concept-paper-descriptions');
}

function addObjective() {
    const container = document.getElementById('concept-paper-objectives');
    const div = document.createElement('div');
    div.className = 'input-group';
    div.innerHTML = `
    <input type="text" name="concept-paper-objectives" placeholder="Enter Objective" required>
    <button type="button" class="delete-btn" onclick="this.parentElement.remove()">Delete</button>
`;
    container.appendChild(div);
}

async function generateObjectives() {
    const subject = document.getElementById('concept-paper-subject').value;
    const generateButton = event.target;
    const originalText = generateButton.textContent;
    generateButton.textContent = 'Generating...';
    generateButton.disabled = true;

    try {
        const response = await fetch('/generate-concept-objectives', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token() }}'
            },
            body: JSON.stringify({ subject }),
            credentials: 'same-origin'
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const responseData = await response.json();
        if (responseData.content) {
            // Split the bullet points into separate objectives
            const objectives = responseData.content
                .split('\n')
                .filter(line => line.trim())
                .map(line => line.replace(/^[•\-\*]\s*/, '')); // Remove bullet points

            // Clear existing objectives except the first input
            const container = document.getElementById('concept-paper-objectives');
            while (container.children.length > 1) {
                container.removeChild(container.lastChild);
            }

            // Set first objective in existing input
            if (objectives.length > 0) {
                container.querySelector('input').value = objectives[0];
            }

            // Add additional objectives
            for (let i = 1; i < objectives.length; i++) {
                const div = document.createElement('div');
                div.className = 'input-group';
                div.innerHTML = `
                <input type="text" name="concept-paper-objectives" value="${objectives[i]}" required>
                <button type="button" class="delete-btn" onclick="this.parentElement.remove()">Delete</button>
            `;
                container.appendChild(div);
            }
        }
    } catch (error) {
        console.error('Error:', error);
        alert(`Error: ${error.message || 'Failed to generate objectives. Please try again.'}`);
    } finally {
        generateButton.textContent = originalText;
        generateButton.disabled = false;
    }
}

async function generateLearningOutcomes() {
    const subject = document.getElementById('concept-paper-subject').value;
    const generateButton = event.target;
    const originalText = generateButton.textContent;
    generateButton.textContent = 'Generating...';
    generateButton.disabled = true;

    try {
        const response = await fetch('/generate-concept-learning-outcomes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token() }}'
            },
            body: JSON.stringify({ subject }),
            credentials: 'same-origin'
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const responseData = await response.json();
        if (responseData.content) {
            // Split the bullet points into separate outcomes
            const outcomes = responseData.content
                .split('\n')
                .filter(line => line.trim())
                .map(line => line.replace(/^[•\-\*]\s*/, '')); // Remove bullet points

            // Clear existing outcomes except the first input
            const container = document.getElementById('concept-paper-learning-outcomes');
            while (container.children.length > 1) {
                container.removeChild(container.lastChild);
            }

            // Set first outcome in existing input
            if (outcomes.length > 0) {
                container.querySelector('input').value = outcomes[0];
            }

            // Add additional outcomes
            for (let i = 1; i < outcomes.length; i++) {
                const div = document.createElement('div');
                div.className = 'input-group';
                div.innerHTML = `
                <input type="text" name="concept-paper-learning-outcomes" value="${outcomes[i]}" required>
                <button type="button" class="delete-btn" onclick="this.parentElement.remove()">Delete</button>
            `;
                container.appendChild(div);
            }
        }
    } catch (error) {
        console.error('Error:', error);
        alert(`Error: ${error.message || 'Failed to generate learning outcomes. Please try again.'}`);
    } finally {
        generateButton.textContent = originalText;
        generateButton.disabled = false;
    }
}

// Update the existing addLearningOutcome function
function addLearningOutcome() {
    const container = document.getElementById('concept-paper-learning-outcomes');
    const div = document.createElement('div');
    div.className = 'input-group';
    div.innerHTML = `
    <input type="text" name="concept-paper-learning-outcomes" placeholder="Enter Learning Outcome" required>
    <button type="button" class="delete-btn" onclick="this.parentElement.remove()">Delete</button>
`;
    container.appendChild(div);
}

async function generateExpectedParticipants() {
    const subject = document.getElementById('concept-paper-subject').value;
    await generateContent('/generate-concept-participants', {
        subject
    }, 'concept-paper-expected-number-of-participants');
}

async function generateConsentContent() {
    const subject = document.getElementById('concept-paper-subject').value;
    const startDate = document.getElementById('concept-paper-event-start-date-and-time').value;
    const endDate = document.getElementById('concept-paper-event-end-date-and-time').value;
    const location = document.getElementById('concept-paper-location').value;

    await generateContent('/generate-concept-consent', {
        subject,
        start_date: startDate,
        end_date: endDate,
        location
    }, 'parent-guardian-consent-content');
}