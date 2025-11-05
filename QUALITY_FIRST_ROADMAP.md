# 🎯 QUALITY-FIRST ROADMAP - AI Assistant Platform

**Выбранная стратегия:** Quality-First
**Цель:** Максимальное качество кода перед production
**Длительность:** 4 недели
**Статус:** 🚀 Ready to Start

---

## 📅 TIMELINE

```
Week 1: Security Fixes + CI/CD + Monitoring
Week 2-3: Type Safety + Component Tests
Week 4: Refactoring + API Layer
Final: Production Deployment
```

---

## 🗓️ WEEK 1: FOUNDATION (Security + Infrastructure)

### Day 1: Security Fixes 🔴 CRITICAL

#### Morning (3-4 hours): Apply Security Migrations

**Задача 1.1: Проверка текущего состояния**
```bash
# Check if Supabase is configured
cat .env | grep SUPABASE

# Check existing migrations
ls -la supabase/migrations/

# Verify database connection
npx supabase status
```

**Задача 1.2: Apply Migrations**
```bash
# Backup current database (if exists)
npx supabase db dump > backup_$(date +%Y%m%d).sql

# Apply all pending migrations
npx supabase db push

# Verify migrations applied
npx supabase migration list
```

**Expected Migrations:**
- `20251022000007_fix_insecure_rls_policies.sql` - Fix 18 insecure policies
- `20251027000002_fix_dynamic_tables_rls.sql` - Add RLS to dynamic tables
- `20251027000003_add_gdpr_compliance.sql` - GDPR compliance
- `20251027000004_encrypt_api_keys.sql` - Encrypt API keys

#### Afternoon (3-4 hours): Security Testing

**Задача 1.3: Create Security Test Suite**

File: `tests/security/rls-isolation.test.ts`
```typescript
import { describe, it, expect, beforeAll } from 'vitest'
import { createClient } from '@supabase/supabase-js'

describe('RLS Isolation Tests', () => {
  let userAClient: SupabaseClient
  let userBClient: SupabaseClient

  beforeAll(async () => {
    // Create test users
    userAClient = await createAuthenticatedClient('userA@test.com')
    userBClient = await createAuthenticatedClient('userB@test.com')
  })

  it('User A cannot access User B projects', async () => {
    // User A creates project
    const { data: projectA } = await userAClient
      .from('projects')
      .insert({ name: 'Project A' })
      .select()
      .single()

    // User B tries to access it
    const { data: projectsB } = await userBClient
      .from('projects')
      .select()

    expect(projectsB).not.toContainEqual(expect.objectContaining({
      id: projectA.id
    }))
  })

  it('User A cannot update User B data', async () => {
    // User B creates database
    const { data: dbB } = await userBClient
      .from('databases')
      .insert({ name: 'Database B', project_id: 'proj-b' })
      .select()
      .single()

    // User A tries to update it
    const { error } = await userAClient
      .from('databases')
      .update({ name: 'Hacked' })
      .eq('id', dbB.id)

    expect(error).toBeTruthy()
    expect(error?.message).toContain('permission')
  })

  it('User A cannot delete User B records', async () => {
    // Similar test for delete operations
  })
})
```

**Задача 1.4: Run Security Tests**
```bash
npm run test:security

# Expected: All tests should pass
# If any fail, investigate and fix RLS policies
```

**Success Criteria:**
- ✅ All 18 RLS policies fixed
- ✅ 100% data isolation between users
- ✅ All security tests passing
- ✅ No unauthorized access possible

---

### Day 2: CI/CD Pipeline 🟡

**Задача 2.1: Create GitHub Actions Workflow**

File: `.github/workflows/ci.yml`
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    name: Lint & Format Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: web-ui/package-lock.json

      - name: Install dependencies
        run: |
          cd web-ui
          npm ci

      - name: Run ESLint
        run: |
          cd web-ui
          npm run lint

      - name: Check TypeScript
        run: |
          cd web-ui
          npm run type-check

  test:
    name: Run Tests
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          cd web-ui
          npm ci

      - name: Run unit tests
        run: |
          cd web-ui
          npm run test:unit

      - name: Run integration tests
        run: |
          cd web-ui
          npm run test:integration
        env:
          VITE_SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          VITE_SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_ANON_KEY }}

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./web-ui/coverage/coverage-final.json

  build:
    name: Build Application
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          cd web-ui
          npm ci

      - name: Build
        run: |
          cd web-ui
          npm run build

      - name: Check bundle size
        run: |
          cd web-ui
          npm run bundlesize

  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    steps:
      - uses: actions/checkout@v4
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          scope: ${{ secrets.VERCEL_SCOPE }}

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
          scope: ${{ secrets.VERCEL_SCOPE }}
```

**Задача 2.2: Setup Pre-commit Hooks**

```bash
# Install Husky
npm install -D husky lint-staged

# Initialize Husky
npx husky-init

# Create pre-commit hook
npx husky add .husky/pre-commit "npm run lint-staged"
```

File: `package.json` (add)
```json
{
  "lint-staged": {
    "*.{ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{json,md}": [
      "prettier --write"
    ]
  }
}
```

**Задача 2.3: Configure Branch Protection**

GitHub Settings → Branches → Add rule:
- ✅ Require pull request reviews
- ✅ Require status checks to pass (lint, test, build)
- ✅ Require branches to be up to date
- ✅ Restrict push to main

**Success Criteria:**
- ✅ CI runs on every PR
- ✅ Tests must pass before merge
- ✅ Auto-deploy to staging/production
- ✅ Pre-commit hooks prevent bad code

---

### Day 3-4: Monitoring & Error Boundaries 🟡

**Задача 3.1: Activate Sentry**

File: `src/lib/sentry.ts`
```typescript
import * as Sentry from '@sentry/react'
import { useEffect } from 'react'
import {
  createRoutesFromChildren,
  matchRoutes,
  useLocation,
  useNavigationType
} from 'react-router-dom'

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.MODE,

  // Performance Monitoring
  tracesSampleRate: import.meta.env.PROD ? 0.1 : 1.0,

  // Session Replay
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,

  integrations: [
    new Sentry.BrowserTracing({
      routingInstrumentation: Sentry.reactRouterV6Instrumentation(
        useEffect,
        useLocation,
        useNavigationType,
        createRoutesFromChildren,
        matchRoutes
      ),
    }),
    new Sentry.Replay({
      maskAllText: true,
      blockAllMedia: true,
    }),
  ],

  beforeSend(event, hint) {
    // Filter sensitive data
    if (event.request) {
      delete event.request.cookies
      delete event.request.headers?.Authorization
    }

    // Don't send in development
    if (import.meta.env.DEV) {
      console.error('Sentry Event:', event, hint)
      return null
    }

    return event
  },
})

// Custom context
export const setSentryUser = (user: { id: string; email: string }) => {
  Sentry.setUser({ id: user.id, email: user.email })
}

export const addBreadcrumb = (message: string, category: string, data?: Record<string, any>) => {
  Sentry.addBreadcrumb({
    message,
    category,
    level: 'info',
    data,
  })
}
```

**Задача 3.2: Add Error Boundaries**

File: `src/components/ErrorBoundary.tsx`
```typescript
import { Component, ErrorInfo, ReactNode } from 'react'
import * as Sentry from '@sentry/react'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  level?: 'global' | 'section' | 'component'
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)

    Sentry.captureException(error, {
      contexts: {
        react: {
          componentStack: errorInfo.componentStack,
        },
      },
      level: this.props.level === 'global' ? 'fatal' : 'error',
    })
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-50 p-4">
          <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
            <div className="flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mx-auto mb-4">
              <AlertTriangle className="w-8 h-8 text-red-600" />
            </div>

            <h1 className="text-2xl font-bold text-center text-gray-900 mb-2">
              {this.props.level === 'global' ? 'Application Error' : 'Something went wrong'}
            </h1>

            <p className="text-gray-600 text-center mb-6">
              {this.props.level === 'global'
                ? 'The application encountered an unexpected error.'
                : 'This section encountered an error. You can try refreshing.'}
            </p>

            {import.meta.env.DEV && this.state.error && (
              <div className="bg-gray-100 rounded-lg p-4 mb-6 overflow-auto max-h-40">
                <pre className="text-xs text-red-600">
                  {this.state.error.toString()}
                </pre>
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={this.handleReset}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Try Again
              </button>

              {this.props.level === 'global' && (
                <button
                  onClick={() => window.location.href = '/'}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <Home className="w-4 h-4" />
                  Go Home
                </button>
              )}
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

// Convenient HOC
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  level: Props['level'] = 'component'
) {
  return function WithErrorBoundary(props: P) {
    return (
      <ErrorBoundary level={level}>
        <Component {...props} />
      </ErrorBoundary>
    )
  }
}
```

**Задача 3.3: Wrap Application**

File: `src/App.tsx`
```typescript
import { ErrorBoundary } from './components/ErrorBoundary'

function App() {
  return (
    <ErrorBoundary level="global">
      <Suspense fallback={<LoadingScreen />}>
        <DatabaseProvider>
          <ErrorBoundary level="section">
            <Router />
          </ErrorBoundary>
        </DatabaseProvider>
      </Suspense>
    </ErrorBoundary>
  )
}
```

**Success Criteria:**
- ✅ Sentry capturing errors
- ✅ User sees friendly error messages
- ✅ Errors don't crash entire app
- ✅ Monitoring dashboard setup

---

### Day 5: Bundle Optimization 🟡

**Задача 4.1: Analyze Current Bundle**

```bash
# Build with analysis
cd web-ui
npm run build

# Use bundle analyzer
npm install -D rollup-plugin-visualizer
npx vite-bundle-visualizer
```

**Задача 4.2: Split Large Chunks**

File: `vite.config.ts`
```typescript
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Split file parsers (950KB → 3x ~300KB)
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-ui': ['lucide-react', 'recharts'],
          'vendor-supabase': ['@supabase/supabase-js'],
          'file-parser-csv': ['papaparse'],
          'file-parser-excel': ['xlsx'],
          'file-parser-pdf': ['pdfjs-dist'],
          'charts': ['recharts'],
        },
      },
    },
    chunkSizeWarningLimit: 500,
  },
})
```

**Задача 4.3: Add Bundle Size Monitoring**

File: `package.json`
```json
{
  "scripts": {
    "bundlesize": "bundlesize"
  },
  "bundlesize": [
    {
      "path": "./dist/assets/*.js",
      "maxSize": "500 KB",
      "compression": "gzip"
    }
  ],
  "devDependencies": {
    "bundlesize": "^0.18.2"
  }
}
```

Add to CI: `.github/workflows/ci.yml`
```yaml
- name: Check bundle size
  run: |
    cd web-ui
    npm run build
    npm run bundlesize
```

**Success Criteria:**
- ✅ fileParser chunk < 300KB
- ✅ Total bundle < 400KB gzipped
- ✅ CI monitors bundle size
- ✅ Lighthouse score > 90

---

## 🗓️ WEEKS 2-3: QUALITY IMPROVEMENTS

### Type Safety Improvements (2-3 weeks)

**Phase 1: Create Type Definitions**

File: `src/types/database.types.ts`
```typescript
export interface Database {
  id: string
  project_id: string
  name: string
  description: string | null
  schema: DatabaseSchema
  created_at: string
  updated_at: string
  user_id: string
}

export interface DatabaseSchema {
  columns: Column[]
  indexes?: Index[]
  constraints?: Constraint[]
}

export interface Column {
  id: string
  name: string
  type: ColumnType
  required: boolean
  unique: boolean
  default_value?: any
  options?: ColumnOptions
}

export type ColumnType =
  | 'text'
  | 'number'
  | 'boolean'
  | 'date'
  | 'select'
  | 'multi-select'
  | 'url'
  | 'email'
  | 'phone'
  | 'formula'
  | 'lookup'
  | 'rollup'

export interface ColumnOptions {
  choices?: string[]
  min?: number
  max?: number
  formula?: string
  lookup_database_id?: string
  lookup_column_id?: string
  rollup_function?: 'sum' | 'avg' | 'count' | 'min' | 'max'
}

// Type guards
export function isDatabase(value: unknown): value is Database {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'project_id' in value &&
    'name' in value &&
    'schema' in value
  )
}

export function isColumn(value: unknown): value is Column {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'name' in value &&
    'type' in value
  )
}
```

**Phase 2: Replace 'any' Systematically**

Strategy:
1. Start with most-used types (Database, Project, Record)
2. Work outward from core to UI
3. Use type guards where dynamic typing needed
4. Aim for <50 'any' instances (90% reduction)

Example transformation:
```typescript
// Before
function updateRecord(database: any, recordId: any, values: any) {
  // ...
}

// After
function updateRecord(
  database: Database,
  recordId: string,
  values: Record<string, unknown>
): Promise<DatabaseRecord> {
  // Type-safe implementation
}
```

**Phase 3: Strict TypeScript Config**

File: `tsconfig.json`
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "noImplicitThis": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

**Success Metrics:**
- Week 2 end: 435 → 200 'any' (50% reduction)
- Week 3 end: 200 → 50 'any' (90% reduction)
- ✅ Full IDE autocomplete
- ✅ Type errors caught at compile time

---

### Component Testing (2-3 weeks)

**Phase 1: Test Infrastructure Setup**

```bash
npm install -D @testing-library/react @testing-library/user-event @testing-library/jest-dom
npm install -D vitest @vitest/ui happy-dom
npm install -D msw
```

File: `vitest.config.ts`
```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      lines: 80,
      functions: 80,
      branches: 75,
      statements: 80,
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.config.ts',
        '**/*.d.ts',
      ],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

**Phase 2: Test Critical Components**

Priority list:
1. DatabaseView (highest usage)
2. RecordForm (complex logic)
3. ColumnEditor (many edge cases)
4. VirtualTable (performance critical)
5. AdvancedColumnTypes (complex)

Example: `tests/components/DatabaseView.test.tsx`
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DatabaseView } from '@/components/DatabaseView'
import { DatabaseProvider } from '@/contexts/DatabaseContext'

const mockDatabase: Database = {
  id: 'db-1',
  project_id: 'proj-1',
  name: 'Test Database',
  schema: {
    columns: [
      { id: 'col-1', name: 'Name', type: 'text', required: true },
      { id: 'col-2', name: 'Age', type: 'number', required: false },
    ],
  },
  created_at: '2025-01-01',
  updated_at: '2025-01-01',
  user_id: 'user-1',
}

function setup(props = {}) {
  const user = userEvent.setup()
  const utils = render(
    <DatabaseProvider>
      <DatabaseView database={mockDatabase} {...props} />
    </DatabaseProvider>
  )
  return { user, ...utils }
}

describe('DatabaseView', () => {
  it('renders database table', () => {
    setup()
    expect(screen.getByRole('table')).toBeInTheDocument()
    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Age')).toBeInTheDocument()
  })

  it('handles column sorting', async () => {
    const { user } = setup()
    const nameColumn = screen.getByText('Name')

    await user.click(nameColumn)

    // Should sort ascending first
    expect(nameColumn).toHaveAttribute('aria-sort', 'ascending')

    await user.click(nameColumn)

    // Should toggle to descending
    expect(nameColumn).toHaveAttribute('aria-sort', 'descending')
  })

  it('opens record form on add button click', async () => {
    const { user } = setup()
    const addButton = screen.getByRole('button', { name: /add record/i })

    await user.click(addButton)

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })
  })

  it('filters records by search query', async () => {
    const { user } = setup()
    const searchInput = screen.getByPlaceholderText(/search/i)

    await user.type(searchInput, 'test query')

    await waitFor(() => {
      // Check that filter was applied
      expect(mockFetchRecords).toHaveBeenCalledWith(
        expect.objectContaining({
          search: 'test query'
        })
      )
    })
  })
})
```

**Phase 3: Test Custom Hooks**

Example: `tests/hooks/useDatabase.test.ts`
```typescript
import { describe, it, expect, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useDatabase } from '@/hooks/useDatabase'

describe('useDatabase', () => {
  it('fetches database on mount', async () => {
    const { result } = renderHook(() => useDatabase('db-1'))

    expect(result.current.loading).toBe(true)

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
      expect(result.current.database).toBeDefined()
    })
  })

  it('handles errors gracefully', async () => {
    // Mock error
    vi.mocked(supabase.from).mockReturnValue({
      select: () => Promise.reject(new Error('Network error'))
    })

    const { result } = renderHook(() => useDatabase('db-1'))

    await waitFor(() => {
      expect(result.current.error).toBeDefined()
      expect(result.current.error?.message).toBe('Network error')
    })
  })
})
```

**Success Metrics:**
- Week 2: 16% → 40% coverage
- Week 3: 40% → 80% coverage
- ✅ All critical paths tested
- ✅ CI fails if coverage drops

---

## 🗓️ WEEK 4: REFACTORING

### Refactor DatabaseContext

**Goal:** Split 723-line god object into 3 focused contexts

**Before:**
```typescript
// DatabaseContext.tsx (723 lines, 40+ state variables)
export const DatabaseContext = createContext({
  // Data
  databases, records, projects, users, ...
  // UI State
  selectedView, filters, sorting, selectedRows, ...
  // Operations
  createDatabase, updateDatabase, deleteDatabase, ...
  // 40+ more variables
})
```

**After:**
```typescript
// contexts/database/DataContext.tsx
export const DatabaseDataContext = createContext({
  databases: Database[]
  records: Record[]
  projects: Project[]
})

// contexts/database/UIContext.tsx
export const DatabaseUIContext = createContext({
  selectedView: ViewType
  filters: FilterState
  sorting: SortState
  selectedRows: Set<string>
})

// contexts/database/OperationsContext.tsx
export const DatabaseOperationsContext = createContext({
  createDatabase: (data: CreateDatabaseInput) => Promise<Database>
  updateDatabase: (id: string, data: UpdateDatabaseInput) => Promise<void>
  deleteDatabase: (id: string) => Promise<void>
})
```

**Migration Strategy:**
1. Create 3 new contexts
2. Migrate one page at a time
3. Test after each migration
4. Remove old context when done

---

### Create API Abstraction Layer

**Goal:** Remove tight coupling with Supabase

**Structure:**
```
src/api/
├── base.ts          # Base API client
├── databases.ts     # Database operations
├── projects.ts      # Project operations
├── records.ts       # Record operations
├── workflows.ts     # Workflow operations
└── index.ts         # Public API
```

**Implementation:**

File: `src/api/base.ts`
```typescript
import { SupabaseClient } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'

export class ApiError extends Error {
  constructor(
    message: string,
    public code?: string,
    public status?: number
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export class ApiClient {
  constructor(private client: SupabaseClient = supabase) {}

  async get<T>(
    table: string,
    options?: {
      select?: string
      where?: Record<string, any>
      order?: { column: string; ascending: boolean }
      limit?: number
    }
  ): Promise<T[]> {
    let query = this.client.from(table).select(options?.select || '*')

    if (options?.where) {
      Object.entries(options.where).forEach(([key, value]) => {
        query = query.eq(key, value)
      })
    }

    if (options?.order) {
      query = query.order(options.order.column, {
        ascending: options.order.ascending
      })
    }

    if (options?.limit) {
      query = query.limit(options.limit)
    }

    const { data, error } = await query

    if (error) {
      throw new ApiError(error.message, error.code, error.status)
    }

    return data as T[]
  }

  async create<T>(table: string, data: Partial<T>): Promise<T> {
    const { data: result, error } = await this.client
      .from(table)
      .insert(data)
      .select()
      .single()

    if (error) {
      throw new ApiError(error.message, error.code, error.status)
    }

    return result as T
  }

  // ... update, delete methods
}

export const apiClient = new ApiClient()
```

File: `src/api/databases.ts`
```typescript
import { apiClient } from './base'
import type { Database, CreateDatabaseInput, UpdateDatabaseInput } from '@/types'

export const databasesApi = {
  list: (projectId: string) =>
    apiClient.get<Database>('databases', {
      where: { project_id: projectId },
      order: { column: 'created_at', ascending: false },
    }),

  get: (id: string) =>
    apiClient.get<Database>('databases', {
      where: { id },
    }).then(results => results[0]),

  create: (data: CreateDatabaseInput) =>
    apiClient.create<Database>('databases', data),

  update: (id: string, data: UpdateDatabaseInput) =>
    apiClient.update<Database>('databases', id, data),

  delete: (id: string) =>
    apiClient.delete('databases', id),
}
```

**Usage in components:**
```typescript
// Before
const { data } = await supabase.from('databases').select('*')

// After
const databases = await databasesApi.list(projectId)
```

---

## ✅ FINAL: PRODUCTION DEPLOYMENT

### Pre-deployment Checklist

- [ ] All security tests passing
- [ ] CI/CD pipeline working
- [ ] Monitoring active
- [ ] Error boundaries in place
- [ ] Bundle size optimized
- [ ] Type safety >90%
- [ ] Test coverage >80%
- [ ] DatabaseContext refactored
- [ ] API layer abstracted

### Deployment Steps

1. **Final Security Audit**
2. **Performance Testing**
3. **Staging Deployment**
4. **User Acceptance Testing**
5. **Production Deployment**
6. **Post-deployment Monitoring**

---

## 📊 SUCCESS METRICS

### Week 1:
- ✅ Security: 0 vulnerabilities
- ✅ CI/CD: Pipeline working
- ✅ Monitoring: Sentry active
- ✅ Bundle: <400KB gzipped

### Week 2-3:
- ✅ Type Safety: <50 'any' (90% improvement)
- ✅ Test Coverage: >80%
- ✅ Code Quality: A rating

### Week 4:
- ✅ DatabaseContext: 3 focused contexts
- ✅ API Layer: Full abstraction
- ✅ Production: Ready to deploy

---

**Время начала:** Сейчас
**Estimated completion:** 4 недели
**Risk level:** LOW (quality-first approach)
**Next step:** Apply Security Migrations

Готовы начать? 🚀
