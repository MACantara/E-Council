import type { FieldConfig } from '@/components/forms/Field';
import type { CrudConfig } from '@/components/Crud/CrudList';

export const SEMESTER_OPTIONS = [
  { value: '1st Semester', label: '1st Semester' },
  { value: '2nd Semester', label: '2nd Semester' },
];

export const STATUS_OPTIONS = [
  { value: 'Upcoming', label: 'Upcoming' },
  { value: 'Postponed', label: 'Postponed' },
  { value: 'Done', label: 'Done' },
  { value: 'Cancelled', label: 'Cancelled' },
];

export const ROLE_OPTIONS = [
  { value: 'Student Council Officer', label: 'Student Council Officer' },
  { value: 'Faculty', label: 'Faculty' },
  { value: 'Staff', label: 'Staff' },
  { value: 'Admin', label: 'Admin' },
];

export interface ResourceDefinition extends CrudConfig {
  fields: FieldConfig[];
  contentType?: 'json' | 'multipart';
}

export const conceptPapers: ResourceDefinition = {
  title: 'Concept Paper',
  endpoint: '/api/v1/concept-papers',
  baseRoute: '/concept-papers',
  idField: 'concept_paper_forms_id',
  listFields: [
    { key: 'concept_paper_forms_subject', label: 'Subject' },
    { key: 'concept_paper_forms_status', label: 'Status', type: 'status' },
    { key: 'concept_paper_forms_semester', label: 'Semester' },
    { key: 'concept_paper_forms_academic_year', label: 'Academic Year' },
  ],
  statusField: 'concept_paper_forms_status',
  fields: [
    { name: 'concept_paper_forms_subject', label: 'Subject', required: true },
    { name: 'concept_paper_forms_semester', label: 'Semester', type: 'select', options: SEMESTER_OPTIONS },
    { name: 'concept_paper_forms_academic_year', label: 'Academic Year' },
    { name: 'concept_paper_forms_status', label: 'Status', type: 'select', options: STATUS_OPTIONS },
    { name: 'concept_paper_forms_location', label: 'Location' },
    { name: 'concept_paper_forms_event_start_date_and_time', label: 'Start Date & Time', type: 'datetime-local' },
    { name: 'concept_paper_forms_event_end_date_and_time', label: 'End Date & Time', type: 'datetime-local' },
    { name: 'concept_paper_forms_body', label: 'Body', type: 'textarea' },
    { name: 'concept_paper_forms_descriptions', label: 'Descriptions', type: 'textarea' },
    { name: 'concept_paper_forms_expected_number_of_participants', label: 'Expected Participants' },
    { name: 'concept_paper_forms_budget', label: 'Budget' },
  ],
};

export const events: ResourceDefinition = {
  title: 'Event',
  endpoint: '/api/v1/events',
  baseRoute: '/events',
  idField: 'events_id',
  listFields: [
    { key: 'events_name', label: 'Name' },
    { key: 'events_status', label: 'Status', type: 'status' },
    { key: 'events_venue', label: 'Venue' },
    { key: 'events_start_date_and_time', label: 'Starts', type: 'date' },
  ],
  statusField: 'events_status',
  fields: [
    { name: 'events_name', label: 'Name', required: true },
    { name: 'events_semester', label: 'Semester', type: 'select', options: SEMESTER_OPTIONS },
    { name: 'events_academic_year', label: 'Academic Year' },
    { name: 'events_status', label: 'Status', type: 'select', options: STATUS_OPTIONS },
    { name: 'events_venue', label: 'Venue' },
    { name: 'events_start_date_and_time', label: 'Start Date & Time', type: 'datetime-local' },
    { name: 'events_end_date_and_time', label: 'End Date & Time', type: 'datetime-local' },
    { name: 'events_budget', label: 'Budget' },
    { name: 'events_description', label: 'Description', type: 'textarea' },
    { name: 'events_remarks', label: 'Remarks', type: 'textarea' },
  ],
};

export const meetings: ResourceDefinition = {
  title: 'Meeting',
  endpoint: '/api/v1/meetings',
  contentType: 'multipart',
  baseRoute: '/meetings',
  idField: 'minutes_of_the_meeting_id',
  listFields: [
    { key: 'minutes_of_the_meeting_agenda', label: 'Agenda' },
    { key: 'minutes_of_the_meeting_status', label: 'Status', type: 'status' },
    { key: 'minutes_of_the_meeting_date', label: 'Date', type: 'date' },
    { key: 'minutes_of_the_meeting_presiding_officer', label: 'Presiding Officer' },
  ],
  statusField: 'minutes_of_the_meeting_status',
  fields: [
    { name: 'minutes_of_the_meeting_agenda', label: 'Agenda', required: true },
    { name: 'minutes_of_the_meeting_semester', label: 'Semester', type: 'select', options: SEMESTER_OPTIONS },
    { name: 'minutes_of_the_meeting_academic_year', label: 'Academic Year' },
    { name: 'minutes_of_the_meeting_status', label: 'Status', type: 'select', options: STATUS_OPTIONS },
    { name: 'minutes_of_the_meeting_presiding_officer', label: 'Presiding Officer' },
    { name: 'minutes_of_the_meeting_date', label: 'Date', type: 'datetime-local' },
    { name: 'minutes_of_the_meeting_notes', label: 'Notes', type: 'textarea' },
  ],
};

export const boardResolutions: ResourceDefinition = {
  title: 'Board Resolution',
  endpoint: '/api/v1/board-resolutions',
  baseRoute: '/board-resolutions',
  idField: 'board_resolutions_id',
  listFields: [
    { key: 'board_resolutions_title', label: 'Title' },
    { key: 'board_resolutions_status', label: 'Status', type: 'status' },
    { key: 'board_resolutions_date', label: 'Date', type: 'date' },
    { key: 'board_resolutions_total_amount', label: 'Total Amount' },
  ],
  statusField: 'board_resolutions_status',
  fields: [
    { name: 'board_resolutions_title', label: 'Title', required: true },
    { name: 'board_resolutions_description', label: 'Description', type: 'textarea' },
    { name: 'board_resolutions_semester', label: 'Semester', type: 'select', options: SEMESTER_OPTIONS },
    { name: 'board_resolutions_academic_year', label: 'Academic Year' },
    { name: 'board_resolutions_status', label: 'Status', type: 'select', options: STATUS_OPTIONS },
    { name: 'board_resolutions_date', label: 'Date', type: 'datetime-local' },
    { name: 'board_resolutions_total_amount', label: 'Total Amount' },
  ],
};

export const financialReports: ResourceDefinition = {
  title: 'Financial Report',
  endpoint: '/api/v1/financial',
  baseRoute: '/financial-reports',
  idField: 'financial_reports_id',
  listFields: [
    { key: 'financial_reports_title', label: 'Title' },
    { key: 'financial_reports_status', label: 'Status', type: 'status' },
    { key: 'financial_reports_date', label: 'Date', type: 'date' },
    { key: 'financial_reports_semester', label: 'Semester' },
  ],
  statusField: 'financial_reports_status',
  fields: [
    { name: 'financial_reports_title', label: 'Title', required: true },
    { name: 'financial_reports_semester', label: 'Semester', type: 'select', options: SEMESTER_OPTIONS },
    { name: 'financial_reports_academic_year', label: 'Academic Year' },
    { name: 'financial_reports_status', label: 'Status', type: 'select', options: STATUS_OPTIONS },
    { name: 'financial_reports_date', label: 'Date', type: 'datetime-local' },
  ],
};

export const documentation: ResourceDefinition = {
  title: 'Documentation',
  endpoint: '/api/v1/documentation',
  contentType: 'multipart',
  baseRoute: '/documentation',
  idField: 'documentation_id',
  listFields: [
    { key: 'documentation_type', label: 'Type' },
    { key: 'documentation_status', label: 'Status', type: 'status' },
    { key: 'documentation_semester', label: 'Semester' },
    { key: 'documentation_date_of_submission', label: 'Submitted', type: 'date' },
  ],
  statusField: 'documentation_status',
  fields: [
    { name: 'documentation_type', label: 'Type', type: 'select', options: [
      { value: 'Activity Report', label: 'Activity Report' },
      { value: 'After Documentation', label: 'After Documentation' },
    ]},
    { name: 'documentation_semester', label: 'Semester', type: 'select', options: SEMESTER_OPTIONS },
    { name: 'documentation_academic_year', label: 'Academic Year' },
    { name: 'documentation_status', label: 'Status', type: 'select', options: STATUS_OPTIONS },
    { name: 'documentation_date_of_submission', label: 'Date of Submission', type: 'datetime-local' },
    { name: 'documentation_rating', label: 'Rating', type: 'number' },
    { name: 'documentation_comments_suggestions', label: 'Comments / Suggestions', type: 'textarea' },
  ],
};

export const resources = {
  conceptPapers,
  events,
  meetings,
  boardResolutions,
  financialReports,
  documentation,
};
