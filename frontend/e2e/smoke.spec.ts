import { test, expect } from '@playwright/test';

const unique = (prefix: string) => `${prefix}-${Date.now()}`;

test('login redirects to dashboard', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveURL('/');
  await expect(page.locator('text=E-Council')).toBeVisible();
});

test('create concept paper', async ({ page }) => {
  const name = unique('E2E Concept');
  await page.goto('/concept-papers/create');
  await page.fill('input[name="concept_paper_forms_subject"]', name);
  await page.selectOption('select[name="concept_paper_forms_semester"]', '1st Semester');
  await page.fill('input[name="concept_paper_forms_academic_year"]', '2025-2026');
  await page.selectOption('select[name="concept_paper_forms_status"]', 'Upcoming');
  await page.click('button[type="submit"]');
  await page.waitForURL('/concept-papers');
  await expect(page.locator('text=' + name)).toBeVisible();
});

test('create event', async ({ page }) => {
  const name = unique('E2E Event');
  await page.goto('/events/create');
  await page.fill('input[name="events_name"]', name);
  await page.selectOption('select[name="events_semester"]', '1st Semester');
  await page.fill('input[name="events_academic_year"]', '2025-2026');
  await page.selectOption('select[name="events_status"]', 'Upcoming');
  await page.fill('input[name="events_start_date_and_time"]', '2025-06-01T10:00');
  await page.fill('input[name="events_end_date_and_time"]', '2025-06-01T12:00');
  await page.click('button[type="submit"]');
  await page.waitForURL('/events');
  await expect(page.locator('text=' + name)).toBeVisible();
});

test('create meeting', async ({ page }) => {
  const name = unique('E2E Meeting');
  await page.goto('/meetings/create');
  await page.fill('input[name="minutes_of_the_meeting_agenda"]', name);
  await page.selectOption('select[name="minutes_of_the_meeting_semester"]', '1st Semester');
  await page.fill('input[name="minutes_of_the_meeting_academic_year"]', '2025-2026');
  await page.selectOption('select[name="minutes_of_the_meeting_status"]', 'Upcoming');
  await page.fill('input[name="minutes_of_the_meeting_presiding_officer"]', 'E2E Officer');
  await page.fill('input[name="minutes_of_the_meeting_date"]', '2025-06-01T10:00');
  await page.click('button[type="submit"]');
  await page.waitForURL('/meetings');
  await expect(page.locator('text=' + name)).toBeVisible();
});

test('create board resolution', async ({ page }) => {
  const name = unique('E2E Resolution');
  await page.goto('/board-resolutions/create');
  await page.fill('input[name="board_resolutions_title"]', name);
  await page.selectOption('select[name="board_resolutions_semester"]', '1st Semester');
  await page.fill('input[name="board_resolutions_academic_year"]', '2025-2026');
  await page.selectOption('select[name="board_resolutions_status"]', 'Upcoming');
  await page.fill('input[name="board_resolutions_date"]', '2025-06-01T10:00');
  await page.click('button[type="submit"]');
  await page.waitForURL('/board-resolutions');
  await expect(page.locator('text=' + name)).toBeVisible();
});

test('admin user management', async ({ page }) => {
  await page.goto('/admin/users');
  await expect(page.locator('text=e2eadmin')).toBeVisible();
});
