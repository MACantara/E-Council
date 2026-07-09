document.addEventListener('DOMContentLoaded', function () {
    initializeEventSelect();
    initializeFileUploads();
    initializeTallySystem();

    // Initialize add field buttons
    document.getElementById('add-strength-btn')?.addEventListener('click', function () {
        addNewField('activity-strengths', 'Activity Strength');
    });
    document.getElementById('add-weakness-btn')?.addEventListener('click', function () {
        addNewField('activity-weaknesses', 'Activity Weakness');
    });
    document.getElementById('add-recommendation-btn')?.addEventListener('click', function () {
        addNewField('activity-recommendations', 'Activity Recommendation');
    });
    document.getElementById('add-learning-btn')?.addEventListener('click', function () {
        addNewField('learnings', 'Learning');
    });
    document.getElementById('add-observation-btn')?.addEventListener('click', function () {
        addNewField('observations', 'Observation');
    });
    document.getElementById('add-tally-item-btn')?.addEventListener('click', addNewTallyItem);
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

    const div = document.createElement('div');
    div.className = 'flex items-center gap-2';

    const newInput = document.createElement('input');
    newInput.type = 'text';
    newInput.name = containerId;
    newInput.placeholder = `Enter ${placeholder}`;
    newInput.required = true;
    newInput.className = 'w-full rounded-lg border border-edge bg-surface px-3.5 py-2.5 text-sm text-ink placeholder:text-ink-3 transition-colors focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent';

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'remove-item-btn inline-flex shrink-0 items-center rounded-lg border border-danger px-3 py-2.5 text-sm font-medium text-danger transition-colors hover:bg-danger hover:text-white';
    removeBtn.textContent = 'Delete';
    removeBtn.addEventListener('click', function () {
        div.remove();
    });

    div.appendChild(newInput);
    div.appendChild(removeBtn);
    container.appendChild(div);
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
    fileItem.className = 'selected-file-item flex items-center justify-between gap-3 rounded-lg border border-edge bg-surface-lowered px-3.5 py-2.5';

    const fileInfo = document.createElement('div');
    fileInfo.className = 'flex items-center gap-3 min-w-0';

    if (includePreview && file.type.startsWith('image/')) {
        const preview = createImagePreview(file);
        fileInfo.appendChild(preview);
    }

    const fileName = document.createElement('span');
    fileName.textContent = file.name;
    fileName.className = 'truncate text-sm text-ink';
    fileInfo.appendChild(fileName);

    fileItem.appendChild(fileInfo);

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'remove-file-btn inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-danger text-sm font-medium text-danger transition-colors hover:bg-danger hover:text-white';
    removeBtn.textContent = '×';
    removeBtn.addEventListener('click', () => removeFile(index, input));

    fileItem.appendChild(removeBtn);
    return fileItem;
}

function createImagePreview(file) {
    const previewContainer = document.createElement('div');
    previewContainer.className = 'file-preview-container h-10 w-10 shrink-0 overflow-hidden rounded-lg';

    const preview = document.createElement('img');
    preview.className = 'file-preview h-full w-full object-cover';
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

        namesList.innerHTML = '<li class="text-sm text-ink-2">Loading...</li>';
        preview.classList.remove('hidden');

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
            namesList.innerHTML = '<li class="text-sm text-danger">Failed to process file</li>';
            console.error('Error:', error);
        }
    } else {
        fileNameSpan.textContent = 'No file chosen';
        preview.classList.add('hidden');
    }
}

function updateStudentList(data, namesList) {
    namesList.innerHTML = '';
    if (data.success) {
        data.students.forEach(student => {
            const li = document.createElement('li');
            li.textContent = student;
            li.className = 'text-sm text-ink-2';
            namesList.appendChild(li);
        });
    } else {
        namesList.innerHTML = `<li class="text-sm text-danger">${data.error}</li>`;
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

    nameRow.className = 'tally-item-name bg-surface-lowered';
    nameRow.innerHTML = `<td colspan="6" class="border-b border-edge px-4 py-2 text-sm font-medium text-ink">${itemName}</td>`;

    const radioClass = 'h-4 w-4 border-edge text-accent focus:ring-accent';
    ratingsRow.innerHTML = `
        <td class="border-b border-edge px-3 py-2 text-center"><input type="radio" class="${radioClass}" name="eval-tally-${index}" value="5" required></td>
        <td class="border-b border-edge px-3 py-2 text-center"><input type="radio" class="${radioClass}" name="eval-tally-${index}" value="4"></td>
        <td class="border-b border-edge px-3 py-2 text-center"><input type="radio" class="${radioClass}" name="eval-tally-${index}" value="3"></td>
        <td class="border-b border-edge px-3 py-2 text-center"><input type="radio" class="${radioClass}" name="eval-tally-${index}" value="2"></td>
        <td class="border-b border-edge px-3 py-2 text-center"><input type="radio" class="${radioClass}" name="eval-tally-${index}" value="1"></td>
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
