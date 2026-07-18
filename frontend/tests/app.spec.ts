import { expect, test } from '@playwright/test';

const session = {
  state: {
    accessToken: 'e2e-access-token',
    refreshToken: 'e2e-refresh-token',
    user: {
      id: 'runner-1',
      username: 'runner',
      role: 'user',
      isActive: true,
      createdAt: '2026-07-15T00:00:00Z',
    },
  },
  version: 0,
};

test.beforeEach(async ({ page }) => {
  await page.addInitScript((value) => {
    window.localStorage.setItem('runcanvas-session', JSON.stringify(value));
  }, session);
  await page.route('**/api/v1/saved-places*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: [] }),
    });
  });
  await page.route('**/api/v1/courses*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 'course-1',
            name: '잠실 하트 5K',
            shapeType: 'heart',
            targetDistanceM: 5000,
            actualDistanceM: 5120,
            status: 'ready',
            isFavorite: true,
            shareEnabled: false,
            savedPlaceId: null,
            isPregenerated: false,
            totalScore: 0.88,
            createdAt: '2026-07-15T00:00:00Z',
            updatedAt: '2026-07-15T00:00:00Z',
          },
        ],
        nextCursor: null,
      }),
    });
  });
});

test('authenticated user can open the dashboard', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: '도시 위에 남긴 선' })).toBeVisible();
  await expect(page.getByText('잠실 하트 5K')).toBeVisible();
  await expect(page.getByRole('link', { name: '새 코스', exact: true })).toBeVisible();
});

test('builder inputs survive a reload', async ({ page }) => {
  await page.goto('/#/builder');
  await page.getByPlaceholder('잠실종합운동장').fill('여의나루역');
  await page.getByLabel('목표 거리 (km)').fill('8');
  await page.getByText('고급 설정', { exact: true }).click();
  await page.getByLabel('한강·강변 강하게 선호').check();
  await expect
    .poll(() => page.evaluate(() => window.localStorage.getItem('runcanvas.builder-draft.v1')))
    .toContain('"preferRiverside":true');

  await page.reload();
  await expect(page.getByPlaceholder('잠실종합운동장')).toHaveValue('여의나루역');
  await expect(page.getByLabel('목표 거리 (km)')).toHaveValue('8');
  await expect(page.getByLabel('한강·강변 강하게 선호')).toBeChecked();
});
