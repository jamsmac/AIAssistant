/**
 * MSW Request Handlers
 */

import { http, HttpResponse } from 'msw';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const handlers = [
  // Auth endpoints
  http.post(`${API_URL}/api/auth/login`, async ({ request }) => {
    const body = await request.json() as { email: string; password: string };

    if (body.email === 'test@example.com' && body.password === 'password123') {
      return HttpResponse.json({
        token: 'mock-jwt-token',
        user: {
          id: '1',
          email: 'test@example.com',
          name: 'Test User',
          role: 'user',
        },
      });
    }

    return HttpResponse.json(
      { message: 'Invalid credentials' },
      { status: 401 }
    );
  }),

  http.post(`${API_URL}/api/auth/register`, async ({ request }) => {
    const body = await request.json() as { email: string; password: string };

    if (body.email && body.password) {
      return HttpResponse.json({
        token: 'mock-jwt-token',
        user: {
          id: '2',
          email: body.email,
          name: 'New User',
          role: 'user',
        },
      });
    }

    return HttpResponse.json(
      { message: 'Registration failed' },
      { status: 400 }
    );
  }),

  // Dashboard stats
  http.get(`${API_URL}/api/dashboard/stats`, () => {
    return HttpResponse.json({
      total_requests: 15234,
      active_agents: 8,
      workflows_run: 342,
      success_rate: 94.5,
      trends: {
        requests: 12.5,
        agents: 25.0,
        workflows: -5.2,
        success: 2.1,
      },
    });
  }),

  // Agents endpoints
  http.get(`${API_URL}/api/agents`, () => {
    return HttpResponse.json([
      {
        id: 'agent-1',
        name: 'Code Reviewer',
        type: 'specialist',
        status: 'active',
        capabilities: ['code-review', 'best-practices'],
        config: { model: 'gpt-4', temperature: 0.3 },
        task_count: 152,
        success_rate: 96.5,
      },
      {
        id: 'agent-2',
        name: 'Data Analyst',
        type: 'specialist',
        status: 'idle',
        capabilities: ['data-analysis', 'visualization'],
        config: { model: 'gpt-4', temperature: 0.5 },
        task_count: 89,
        success_rate: 92.3,
      },
    ]);
  }),

  http.post(`${API_URL}/api/agents`, async ({ request }) => {
    const body = await request.json() as any;

    return HttpResponse.json({
      id: 'new-agent',
      ...body,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }, { status: 201 });
  }),

  // Workflows endpoints
  http.get(`${API_URL}/api/workflows`, () => {
    return HttpResponse.json([
      {
        id: 'workflow-1',
        name: 'Daily Report',
        description: 'Generate daily performance report',
        triggers: [{ type: 'schedule', config: { schedule: '0 9 * * *' } }],
        actions: [
          {
            type: 'api_call',
            config: {
              api_url: 'https://api.example.com/report',
              api_method: 'POST',
            },
          },
        ],
        status: 'active',
        run_count: 30,
        success_count: 28,
        error_count: 2,
      },
    ]);
  }),

  http.post(`${API_URL}/api/workflows/:id/execute`, ({ params }) => {
    return HttpResponse.json({
      id: 'run-1',
      workflow_id: params.id,
      status: 'running',
      started_at: new Date().toISOString(),
    });
  }),

  // Projects endpoints
  http.get(`${API_URL}/api/projects`, () => {
    return HttpResponse.json([
      {
        id: 'project-1',
        name: 'E-Commerce Platform',
        description: 'Main e-commerce application',
        status: 'active',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-15T00:00:00Z',
      },
      {
        id: 'project-2',
        name: 'Analytics Dashboard',
        description: 'Business intelligence dashboard',
        status: 'active',
        created_at: '2024-01-05T00:00:00Z',
        updated_at: '2024-01-20T00:00:00Z',
      },
    ]);
  }),

  // Databases endpoints
  http.get(`${API_URL}/api/projects/:projectId/databases`, ({ params }) => {
    return HttpResponse.json([
      {
        id: 'db-1',
        project_id: params.projectId,
        name: 'Production DB',
        type: 'postgresql',
        tables: [
          {
            id: 'table-1',
            name: 'users',
            columns: [
              { name: 'id', type: 'uuid', primary_key: true },
              { name: 'email', type: 'varchar', unique: true },
              { name: 'created_at', type: 'timestamp' },
            ],
          },
        ],
      },
    ]);
  }),

  // Analytics endpoints
  http.get(`${API_URL}/api/analytics/usage`, () => {
    return HttpResponse.json({
      daily: [
        { date: '2024-01-01', requests: 1234 },
        { date: '2024-01-02', requests: 1456 },
        { date: '2024-01-03', requests: 1678 },
      ],
      by_model: [
        { model: 'GPT-4', count: 5678 },
        { model: 'GPT-3.5', count: 3456 },
        { model: 'Claude', count: 2345 },
      ],
    });
  }),

  // Chat endpoints
  http.post(`${API_URL}/api/chat`, async ({ request }) => {
    const body = await request.json() as { message: string };

    return HttpResponse.json({
      response: `Echo: ${body.message}`,
      timestamp: new Date().toISOString(),
    });
  }),

  // Integrations endpoints
  http.get(`${API_URL}/api/integrations`, () => {
    return HttpResponse.json([
      {
        id: 'int-1',
        name: 'GitHub',
        type: 'version-control',
        status: 'connected',
        config: { org: 'my-org' },
      },
      {
        id: 'int-2',
        name: 'Slack',
        type: 'communication',
        status: 'connected',
        config: { channel: '#dev' },
      },
    ]);
  }),

  // Settings endpoints
  http.get(`${API_URL}/api/settings`, () => {
    return HttpResponse.json({
      theme: 'dark',
      notifications: true,
      language: 'en',
      timezone: 'UTC',
    });
  }),

  http.patch(`${API_URL}/api/settings`, async ({ request }) => {
    const body = await request.json() as Record<string, any>;

    return HttpResponse.json({
      ...body,
      updated_at: new Date().toISOString(),
    });
  }),

  // Blog endpoints
  http.get(`${API_URL}/api/blog/posts`, () => {
    return HttpResponse.json({
      posts: [
        {
          id: 'post-1',
          title: 'Introduction to AI Agents',
          slug: 'intro-to-ai-agents',
          excerpt: 'Learn about AI agents and how they work.',
          author: { name: 'John Doe', avatar: '/avatar.jpg' },
          published_at: '2024-01-01T00:00:00Z',
          view_count: 1234,
          like_count: 56,
        },
      ],
      total: 1,
      page: 1,
      per_page: 10,
    });
  }),

  // Error testing endpoints
  http.get(`${API_URL}/api/error/500`, () => {
    return HttpResponse.json(
      { message: 'Internal server error' },
      { status: 500 }
    );
  }),

  http.get(`${API_URL}/api/error/404`, () => {
    return HttpResponse.json(
      { message: 'Resource not found' },
      { status: 404 }
    );
  }),

  // Catch-all handler for unhandled requests
  http.get('*', ({ request }) => {
    console.warn(`Unhandled GET request: ${request.url}`);
    return HttpResponse.json({ message: 'Not found' }, { status: 404 });
  }),

  http.post('*', ({ request }) => {
    console.warn(`Unhandled POST request: ${request.url}`);
    return HttpResponse.json({ message: 'Not found' }, { status: 404 });
  }),
];