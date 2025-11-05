/**
 * k6 Load Testing Script
 * Tests API performance under various load conditions
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const successRate = new Rate('success');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 10 },   // Ramp up to 10 users
    { duration: '1m', target: 10 },    // Stay at 10 users
    { duration: '30s', target: 50 },   // Ramp up to 50 users
    { duration: '2m', target: 50 },    // Stay at 50 users
    { duration: '30s', target: 100 },  // Ramp up to 100 users
    { duration: '3m', target: 100 },   // Stay at 100 users
    { duration: '1m', target: 0 },     // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'], // 95% of requests must complete below 1s
    http_req_failed: ['rate<0.05'],    // Error rate must be below 5%
    errors: ['rate<0.05'],              // Custom error rate below 5%
    success: ['rate>0.95'],             // Success rate above 95%
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:3000';

// Test data
const testUser = {
  email: 'loadtest@example.com',
  password: 'LoadTest123!',
};

// Helper function to get auth token
function authenticate() {
  const loginRes = http.post(
    `${BASE_URL}/api/auth/login`,
    JSON.stringify(testUser),
    {
      headers: { 'Content-Type': 'application/json' },
    }
  );

  if (loginRes.status === 200) {
    const body = JSON.parse(loginRes.body);
    return body.token;
  }
  return null;
}

// Setup function - runs once per VU
export function setup() {
  // Create test user if needed
  const registerRes = http.post(
    `${BASE_URL}/api/auth/register`,
    JSON.stringify(testUser),
    {
      headers: { 'Content-Type': 'application/json' },
    }
  );

  console.log(`Setup completed. Status: ${registerRes.status}`);
  return { token: authenticate() };
}

// Main test function - runs continuously for each VU
export default function (data) {
  const token = data.token;
  const headers = {
    'Content-Type': 'application/json',
    Authorization: token ? `Bearer ${token}` : '',
  };

  // Test 1: Health check endpoint
  const healthRes = http.get(`${BASE_URL}/api/health`);
  check(healthRes, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 500ms': (r) => r.timings.duration < 500,
  });
  errorRate.add(healthRes.status !== 200);
  successRate.add(healthRes.status === 200);

  sleep(1);

  // Test 2: Dashboard stats (authenticated)
  const statsRes = http.get(`${BASE_URL}/api/dashboard/stats`, { headers });
  check(statsRes, {
    'dashboard stats status is 200': (r) => r.status === 200,
    'dashboard stats has data': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.total_requests !== undefined;
      } catch {
        return false;
      }
    },
  });
  errorRate.add(statsRes.status !== 200);
  successRate.add(statsRes.status === 200);

  sleep(1);

  // Test 3: List workflows
  const workflowsRes = http.get(`${BASE_URL}/api/workflows`, { headers });
  check(workflowsRes, {
    'workflows status is 200': (r) => r.status === 200,
    'workflows returns array': (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body);
      } catch {
        return false;
      }
    },
  });
  errorRate.add(workflowsRes.status !== 200);
  successRate.add(workflowsRes.status === 200);

  sleep(1);

  // Test 4: Create and delete workflow (write operations)
  const newWorkflow = {
    name: `Load Test Workflow ${__VU}-${__ITER}`,
    description: 'Created by k6 load test',
    triggers: [{ type: 'manual', config: {} }],
    actions: [{ type: 'api_call', config: { url: 'https://example.com' } }],
  };

  const createRes = http.post(
    `${BASE_URL}/api/workflows`,
    JSON.stringify(newWorkflow),
    { headers }
  );

  if (createRes.status === 201) {
    const workflow = JSON.parse(createRes.body);

    // Delete the created workflow
    const deleteRes = http.del(
      `${BASE_URL}/api/workflows/${workflow.id}`,
      null,
      { headers }
    );

    check(deleteRes, {
      'workflow deletion successful': (r) => r.status === 204 || r.status === 200,
    });
  }

  check(createRes, {
    'workflow creation status is 201': (r) => r.status === 201,
    'workflow creation response time < 2s': (r) => r.timings.duration < 2000,
  });
  errorRate.add(createRes.status !== 201);
  successRate.add(createRes.status === 201);

  sleep(2);

  // Test 5: Search operations
  const searchRes = http.get(
    `${BASE_URL}/api/agents?search=test`,
    { headers }
  );
  check(searchRes, {
    'search status is 200': (r) => r.status === 200,
    'search response time < 1s': (r) => r.timings.duration < 1000,
  });

  sleep(1);

  // Test 6: Concurrent API calls
  const batch = http.batch([
    ['GET', `${BASE_URL}/api/health`, null, { headers }],
    ['GET', `${BASE_URL}/api/agents`, null, { headers }],
    ['GET', `${BASE_URL}/api/workflows`, null, { headers }],
  ]);

  batch.forEach((res) => {
    check(res, {
      'batch request successful': (r) => r.status === 200,
    });
    errorRate.add(res.status !== 200);
    successRate.add(res.status === 200);
  });

  sleep(2);
}

// Teardown function - runs once after all iterations
export function teardown(data) {
  console.log('Load test completed');

  // Generate summary
  console.log(`
    Load Test Summary:
    - Error Rate: ${errorRate.rate}
    - Success Rate: ${successRate.rate}
  `);
}