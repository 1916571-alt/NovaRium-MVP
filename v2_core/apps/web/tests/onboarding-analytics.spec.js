const { test, expect } = require("@playwright/test");

function json(route, status, payload) {
  route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(payload)
  });
}

test("home onboarding flow smoke with mocked API", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("nr_access_token", "mock-token");
  });

  await page.route("**/v2/**", async (route) => {
    const req = route.request();
    const url = new URL(req.url());
    const path = url.pathname.replace(/^\/v2/, "");
    const method = req.method();

    if (method === "GET" && path === "/auth/me") return json(route, 200, { user_id: "u1", email: "u1@test.local" });
    if (method === "GET" && path === "/portfolio/me") return json(route, 200, { summary: { experiments_total: 0, experiments_adopted: 0, sql_accuracy: 0, journey_events_total: 0 } });
    if (method === "GET" && path === "/projects") return json(route, 200, { items: [], count: 0 });
    if (method === "GET" && path === "/analytics/templates") {
      return json(route, 200, {
        items: [
          {
            key: "commerce",
            label: "Commerce Funnel",
            description: "commerce template",
            default_user_count: 2400,
            default_control_purchase_rate: 0.22,
            default_test_purchase_rate: 0.27,
            preset_defaults: {
              beginner: { user_count: 1320, control_purchase_rate: 0.209, test_purchase_rate: 0.318 },
              standard: { user_count: 2400, control_purchase_rate: 0.22, test_purchase_rate: 0.27 },
              advanced: { user_count: 4560, control_purchase_rate: 0.22, test_purchase_rate: 0.2525 }
            }
          }
        ],
        count: 1
      });
    }
    if (method === "POST" && path === "/workspaces") return json(route, 201, { id: "ws1", owner_user_id: "u1", name: "ws", my_role: "owner", created_at: "now" });
    if (method === "POST" && path === "/projects") return json(route, 201, { id: "p1", workspace_id: "ws1", name: "p", my_role: "owner", created_at: "now" });
    if (method === "POST" && path === "/analytics/projects/p1/bootstrap") {
      return json(route, 201, {
        project_id: "p1",
        experiment_id: "e1",
        run_id: "r1",
        template: "commerce",
        seed_preset: "standard",
        user_count: 2400,
        assignments_inserted: 2400,
        events_inserted: 14000,
        control_users: 1200,
        test_users: 1200,
        control_purchase_rate: 0.22,
        test_purchase_rate: 0.27,
        sql_challenges_seeded: 2
      });
    }
    return json(route, 200, {});
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Quick Onboarding" })).toBeVisible();
  await page.getByPlaceholder("workspace name").fill("ws-smoke");
  await page.getByPlaceholder("project name").fill("p-smoke");
  await page.getByRole("button", { name: "Create + Bootstrap" }).click();
  await expect(page.getByText("Onboarding completed")).toBeVisible();
  await expect(page.getByText("Latest Bootstrap Summary")).toBeVisible();
  await expect(page.getByRole("link", { name: "Go Analytics" })).toBeVisible();
});

test("analytics bootstrap and funnel flow smoke with mocked API", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("nr_access_token", "mock-token");
  });

  await page.route("**/v2/**", async (route) => {
    const req = route.request();
    const url = new URL(req.url());
    const path = url.pathname.replace(/^\/v2/, "");
    const method = req.method();

    if (method === "GET" && path === "/projects") {
      return json(route, 200, { items: [{ id: "p1", workspace_id: "ws1", name: "p1", my_role: "owner", created_at: "now" }], count: 1 });
    }
    if (method === "GET" && path === "/analytics/templates") {
      return json(route, 200, {
        items: [
          {
            key: "commerce",
            label: "Commerce Funnel",
            description: "commerce template",
            default_user_count: 2400,
            default_control_purchase_rate: 0.22,
            default_test_purchase_rate: 0.27,
            preset_defaults: {
              beginner: { user_count: 1320, control_purchase_rate: 0.209, test_purchase_rate: 0.318 },
              standard: { user_count: 2400, control_purchase_rate: 0.22, test_purchase_rate: 0.27 },
              advanced: { user_count: 4560, control_purchase_rate: 0.22, test_purchase_rate: 0.2525 }
            }
          }
        ],
        count: 1
      });
    }
    if (method === "POST" && path === "/analytics/projects/p1/bootstrap") {
      return json(route, 201, {
        project_id: "p1",
        experiment_id: "e1",
        run_id: "r1",
        template: "commerce",
        seed_preset: "standard",
        user_count: 2400,
        assignments_inserted: 2400,
        events_inserted: 14000,
        control_users: 1200,
        test_users: 1200,
        control_purchase_rate: 0.22,
        test_purchase_rate: 0.27,
        sql_challenges_seeded: 2
      });
    }
    if (method === "GET" && path === "/analytics/projects/p1/funnel") {
      return json(route, 200, {
        project_id: "p1",
        run_id: "r1",
        experiment_id: "e1",
        template: "commerce",
        total_users: 2400,
        bottleneck_step: "click_cta",
        steps: [
          { step_index: 0, step_name: "session_start", users_count: 2400, conversion_rate: 1.0, dropoff_rate: 0.0 },
          { step_index: 1, step_name: "view_home", users_count: 2200, conversion_rate: 0.9167, dropoff_rate: 0.0833 },
          { step_index: 2, step_name: "view_detail", users_count: 1700, conversion_rate: 0.7083, dropoff_rate: 0.2273 },
          { step_index: 3, step_name: "click_cta", users_count: 1000, conversion_rate: 0.4167, dropoff_rate: 0.4118 },
          { step_index: 4, step_name: "add_to_cart", users_count: 780, conversion_rate: 0.325, dropoff_rate: 0.22 },
          { step_index: 5, step_name: "start_checkout", users_count: 600, conversion_rate: 0.25, dropoff_rate: 0.2308 },
          { step_index: 6, step_name: "purchase", users_count: 540, conversion_rate: 0.225, dropoff_rate: 0.1 }
        ]
      });
    }
    return json(route, 200, {});
  });

  await page.goto("/analytics?project_id=p1&experiment_id=e1&run_id=r1&template=commerce");
  await expect(page.getByRole("heading", { name: "Analytics" })).toBeVisible();
  await page.getByRole("button", { name: "Bootstrap" }).click();
  await expect(page.getByText("Simulation bootstrap completed")).toBeVisible();
  await page.getByRole("button", { name: "Load Funnel" }).click();
  await expect(page.getByText("Funnel Overview")).toBeVisible();
  await expect(page.getByText("bottleneck: click_cta")).toBeVisible();
});
