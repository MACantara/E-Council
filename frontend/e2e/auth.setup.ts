import { test as setup, expect } from '@playwright/test';

const authFile = 'e2e/storageState.json';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.fill('input[name="users_username_or_email"]', 'e2eadmin');
  await page.fill('input[name="users_password"]', 'Password123');
  await page.click('button[type="submit"]');

  await page.waitForURL('/');
  await expect(page).toHaveURL('/');

  await page.context().storageState({ path: authFile });
});
