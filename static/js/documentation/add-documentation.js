document.addEventListener('DOMContentLoaded', function () {
    initializeEventSelect();
    initializeFileUploads();
    initializeTallySystem();
});

function initializeEventSelect() {
    const eventsSelect = document.getElementById('documentation-events-id');

    eventsSelect.addEventListener('change', function () {
        const eventId = this.value;
        fetchRelatedForms(
            eventId,
            'documentation-activity-report-forms-id',
            'documentation-learning-journal-forms-id',
            document.getElementById('learning-journal-forms-checked-by')
        );
    });
}

async function fetchRelatedForms(eventId, activityReportSelectId, learningJournalSelectId, learningJournalCheckedBySelect) {
    try {
        const response = await fetch(`/get-related-forms/${eventId}`);
        const data = await response.json();

        // Use custom default text for each select
        updateSelectOptions(activityReportSelectId, data.activity_reports, 'activity_report_forms_id', 'events_name', 'Select activity report forms');
        updateSelectOptions(learningJournalSelectId, data.learning_journals, 'learning_journal_forms_id', 'events_name', 'Select learning journal forms');
        updateSignatoryOptions(learningJournalCheckedBySelect, data.signatories);
    } catch (error) {
        console.error('Error fetching related forms:', error);
    }
}

function updateSignatoryOptions(select, signatories) {
    select.innerHTML = '<option value="" disabled selected>Select Signatory</option>';
    signatories.forEach(signatory => {
        const option = document.createElement('option');
        option.value = signatory.signatory_id;
        option.textContent = `${signatory.signatory_first_name} ${signatory.signatory_last_name} - ${signatory.signatory_position}`;
        option.selected = true;
        select.appendChild(option);
    });
}

function addNewField(containerId, placeholder) {
    const container = document.getElementById(containerId);
    const newInput = document.createElement('input');
    newInput.type = 'text';
    newInput.name = containerId;
    newInput.placeholder = `Enter ${placeholder}`;
    container.appendChild(newInput);
}

function addNewTallyItem() {
    const tallyItemsContainer = document.querySelector('#tally-items tbody');
    const nameRow = tallyItemsContainer.querySelector('.tally-item-name').cloneNode(true);
    const ratingsRow = tallyItemsContainer.querySelector('.tally-item-ratings').cloneNode(true);

    // Clear input values
    nameRow.querySelectorAll('input').forEach(input => input.value = '');
    ratingsRow.querySelectorAll('input').forEach(input => {
        if (input.type === 'number') input.value = '0';
    });

    tallyItemsContainer.appendChild(nameRow);
    tallyItemsContainer.appendChild(ratingsRow);
}

function initializeFileUploads() {
    setupFileUpload('evaluation-images', 'evaluation-files-name', 'selected-files-list');
    setupFileUpload('attendance-images', 'attendance-files-name', 'attendance-files-list');
    setupFileUpload('photo-documentation-images', 'photo-doc-files-name', 'photo-doc-files-list', true);
    setupExcelUpload();
}

function setupFileUpload(inputId, nameSpanId, listId, includePreview = false) {
    const input = document.getElementById(inputId);
    const filesNameSpan = document.getElementById(nameSpanId);
    const filesList = document.getElementById(listId);

    input.addEventListener('change', function() {
        updateFileList(this, filesNameSpan, filesList, includePreview);
    });
}

function updateFileList(input, filesNameSpan, filesList, includePreview) {
    filesList.innerHTML = '';
    
    if (input.files.length > 0) {
        filesNameSpan.textContent = `${input.files.length} file(s) selected`;
        
        Array.from(input.files).forEach((file, index) => {
            const fileItem = createFileItem(file, index, input, includePreview);
            filesList.appendChild(fileItem);
        });
    } else {
        filesNameSpan.textContent = 'No files chosen';
    }
}

function createFileItem(file, index, input, includePreview) {
    const fileItem = document.createElement('div');
    fileItem.className = 'selected-file-item';
    
    const fileName = document.createElement('span');
    fileName.textContent = file.name;
    
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'remove-file-btn';
    removeBtn.textContent = '×';
    removeBtn.onclick = () => removeFile(index, input);
    
    fileItem.appendChild(fileName);
    
    if (includePreview && file.type.startsWith('image/')) {
        const preview = createImagePreview(file);
        fileItem.appendChild(preview);
    }
    
    fileItem.appendChild(removeBtn);
    return fileItem;
}

function createImagePreview(file) {
    const previewContainer = document.createElement('div');
    previewContainer.className = 'file-preview-container';
    
    const preview = document.createElement('img');
    preview.className = 'file-preview';
    preview.src = URL.createObjectURL(file);
    
    previewContainer.appendChild(preview);
    return previewContainer;
}

function removeFile(index, input) {
    const dt = new DataTransfer();
    const { files } = input;
    
    for (let i = 0; i < files.length; i++) {
        if (i !== index) {
            dt.items.add(files[i]);
        }
    }
    
    input.files = dt.files;
    input.dispatchEvent(new Event('change'));
}

function setupExcelUpload() {
    const input = document.getElementById('student-list-excel');
    input.addEventListener('change', handleExcelUpload);
}

async function handleExcelUpload(e) {
    const fileNameSpan = document.getElementById('excel-file-name');
    const preview = document.getElementById('student-list-preview');
    const namesList = document.getElementById('student-names-list');

    if (this.files.length > 0) {
        const file = this.files[0];
        fileNameSpan.textContent = file.name;

        const formData = new FormData();
        formData.append('excel_file', file);

        namesList.innerHTML = '<li>Loading...</li>';
        preview.style.display = 'block';

        try {
            const response = await fetch('/process-student-excel', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            });

            const data = await response.json();
            updateStudentList(data, namesList);
        } catch (error) {
            namesList.innerHTML = '<li class="error">Failed to process file</li>';
            console.error('Error:', error);
        }
    } else {
        fileNameSpan.textContent = 'No file chosen';
        preview.style.display = 'none';
    }
}

function updateStudentList(data, namesList) {
    namesList.innerHTML = '';
    if (data.success) {
        data.students.forEach(student => {
            const li = document.createElement('li');
            li.textContent = student;
            namesList.appendChild(li);
        });
    } else {
        namesList.innerHTML = `<li class="error">${data.error}</li>`;
    }
}

function initializeTallySystem() {
    const tallyTable = document.querySelector('.tally-table');
    
    syncTallyItems();
    
    tallyTable.addEventListener('input', e => {
        if (e.target.type === 'text') {
            syncTallyItems();
        }
    });
    
    document.querySelector('.add-tally-button')?.addEventListener('click', () => {
        setTimeout(syncTallyItems, 100);
    });
    
    document.querySelector('.evaluation-tally-table')?.addEventListener('change', e => {
        if (e.target.type === 'radio') {
            calculateOverallRating();
        }
    });
}

function syncTallyItems() {
    const tallyRows = document.querySelectorAll('.tally-table tbody tr');
    const evaluationTallyContainer = document.querySelector('.evaluation-tally-table tbody');
    
    evaluationTallyContainer.innerHTML = '';
    
    tallyRows.forEach((row, index) => {
        const nameInput = row.querySelector('input[type="text"]');
        if (nameInput) {
            addTallyItemToEvaluation(nameInput.value || `Item ${index + 1}`, index, evaluationTallyContainer);
        }
    });
}

function addTallyItemToEvaluation(itemName, index, container) {
    const nameRow = document.createElement('tr');
    const ratingsRow = document.createElement('tr');
    
    nameRow.innerHTML = `<td colspan="6" class="tally-item-name">${itemName}</td>`;
    ratingsRow.innerHTML = `
        <td><input type="radio" name="eval-tally-${index}" value="5" required></td>
        <td><input type="radio" name="eval-tally-${index}" value="4"></td>
        <td><input type="radio" name="eval-tally-${index}" value="3"></td>
        <td><input type="radio" name="eval-tally-${index}" value="2"></td>
        <td><input type="radio" name="eval-tally-${index}" value="1"></td>
    `;
    
    container.appendChild(nameRow);
    container.appendChild(ratingsRow);
}

function calculateOverallRating() {
    const rows = document.querySelectorAll('.evaluation-tally-table tbody tr:not(.tally-item-name)');
    let totalRating = 0;
    let totalItems = 0;
    
    rows.forEach(row => {
        const selectedRadio = row.querySelector('input[type="radio"]:checked');
        if (selectedRadio) {
            totalRating += parseInt(selectedRadio.value);
            totalItems++;
        }
    });
    
    const averageRating = totalItems > 0 ? Math.round((totalRating / totalItems) * 100) / 100 : 0;
    
    document.getElementById('calculated-rating-value').textContent = averageRating.toFixed(2);
    document.getElementById('documentation-rating').value = averageRating;
    
    const roundedRating = Math.round(averageRating);
    const radioButton = document.getElementById(`documentation-rating-${roundedRating}`);
    if (radioButton) {
        radioButton.checked = true;
    }
}
