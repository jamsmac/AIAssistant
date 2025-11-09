# AI Assistant OS – Production Documentation

## 1. Platform Overview
- **Stack**: FastAPI backend (`api/server_refactored.py`), Next.js 16 frontend (`web-ui`), SQLite cache, PostgreSQL primary DB, MCP server (12 tools).
- **Key Capabilities**: Smart AI router with caching, JWT auth via httpOnly cookies, async connection pooling, role-based workflows, visual workflow builder, monitoring endpoints, analytics dashboards.

## 2. Architecture Summary
- **Backend Services**: FastAPI app composed of modular routers (`api/routers/*`). Startup initializes `asyncpg` connection pool and cache cleanup scheduler (`agents/db_pool.py`, `agents/cache_manager.py`).
- **Frontend**: App Router (Next.js) using React 19, Zustand store for workflow builder, TailwindCSS. Heavy components (ReactFlow, charts) loaded dynamically to keep bundle lean.
- **MCP Integration**: `agents/mcp_server.py` exposes 12 tools (projects, databases, chat, workflows, analytics). Configured via `.cursor/mcp.json`. Run tests with `python test_mcp_server.py`.
- **Security Layers**: Strict CORS validation, security headers, bcrypt password hashing, JWT cookies (`secure`, `SameSite=Lax`, `HttpOnly`), input validation with Pydantic, rate limiting.

## 3. Environment & Configuration
- Copy `.env.example` → `.env`; never commit secrets.
- **Required Vars**: `DATABASE_URL`, `SECRET_KEY`, `CACHE_DB_PATH`, `ENVIRONMENT`, provider API keys (Anthropic, OpenAI, etc.), Sentry credentials (optional), MCP endpoints.
- Generate strong `SECRET_KEY` with `python scripts/generate_secret_key.py 64`. Production requires ≥64 bytes, mixed charset; startup validation blocks weak keys.
- **CORS**: Configure `CORS_ORIGINS` env with comma-separated origins. Validation rejects `http` origins in production and dangerous patterns.

## 4. Backend Setup
1. Create virtual environment (`python -m venv venv && source venv/bin/activate`).
2. Install deps: `pip install -r requirements.txt`.
3. Run migrations or schema setup (see `DATABASE_SETUP.md`).
4. Launch API: `python api/server_refactored.py` (defaults to `0.0.0.0:8000`). Uvicorn reload can be used for dev: `uvicorn api.server_refactored:app --reload`.
5. **Connection Pool**: Tuned via env (`DB_POOL_MIN`, `DB_POOL_MAX`, `DB_MAX_QUERIES`). Metrics exposed under `/api/monitoring/pool`.
6. **Cache**: Persistent SQLite file (`data/autopilot_cache.db`). TTL per task-type, cleanup scheduled via APScheduler.

## 5. Frontend Setup & Performance
1. `cd web-ui && npm install`.
2. Development server: `npm run dev` (Next.js 16 with Turbopack).
3. Production build: `npm run build`; start: `npm run start`.
4. **Bundle Analysis**: `npm run analyze` (wraps `ANALYZE=true npm run build`) opens static report; see `BUNDLE_ANALYSIS_GUIDE.md` for interpretation. Large vendor chunks (ReactFlow, Recharts, Tiptap) are dynamically imported.
5. Styling exclusively via Tailwind (per repo policy). Avoid inline styles.

## 6. Authentication & Security Requirements
- Login/register endpoints set `auth_token` cookie (httpOnly, secure, SameSite=Lax). Frontend relies on cookies; do **not** store tokens in localStorage.
- Ensure HTTPS in production so cookies use `Secure` flag correctly.
- Rate limiting enforced for anonymous/authenticated/premium tiers (`agents/rate_limiter.py`).
- Security headers defined in Next.js (`web-ui/next.config.ts`) and FastAPI middlewares.
- Audit logs & alerting via monitoring module (`monitoring` package) – integrate with external observability stack if available.

## 7. MCP Server Usage
- Start server: `./start_mcp_server.sh` (ensures Python deps available).
- Tools: project CRUD, database schema management, chat routing, workflow execution, analytics fetch.
- Test suite: `python test_mcp_server.py` (validates 12 tools & auth constraints).

## 8. Testing Strategy
- **Unit Tests**: `pytest` (backend), `npm run test:unit` (frontend via Vitest). Coverage target 90%+ enforced by `pytest.ini` (`--cov-fail-under=80` currently; adjust when all suites stable).
- **Integration Tests**: Backend scenarios in `tests/test_integration.py` cover cache persistence, monitoring endpoints, auth cookie flow.
- **E2E Tests**: Playwright (`npm run test:e2e`) includes auth and workflow builder coverage. Ensure Playwright browsers installed (`npx playwright install`).
- **Security Tests**: `python tests/security/rls-isolation.test.ts` (if applicable) and `npm run test:security` for frontend.
- **Smoke/Automation**: `python scripts/smoke_test.py` for high-level API sanity.

## 9. Deployment Checklist
- Backend: Deploy FastAPI (Gunicorn/Uvicorn workers) behind reverse proxy with HTTPS termination. Provide environment secrets, configure systemd or container orchestration.
- Frontend: Deploy Next.js (Vercel or custom). Ensure environment variables in Vercel dashboard (API URLs, Sentry DSN, etc.).
- Database: Provision managed PostgreSQL; update `DATABASE_URL`. Apply migrations.
- Secrets: Rotate `SECRET_KEY`, API keys, and set `ENVIRONMENT=production`.
- Monitoring: Configure Sentry (optional but recommended), hook `/api/monitoring/health` and `/api/monitoring/pool` into uptime dashboards.
- Caching: Verify `CACHE_DB_PATH` directory writable by service user.

## 10. Operations & Runbook
- **Health Checks**: `/api/monitoring/health` returns status for services (DB pool, cache). `/api/monitoring/system` exposes CPU/memory metrics if enabled.
- **Cache Maintenance**: `/api/cache/stats`, `/api/cache/cleanup`, `/api/cache` (DELETE) for manual purge.
- **Rate Limit Monitoring**: extend `monitoring_router` endpoints if deeper introspection needed.
- **Log Retention**: Ensure backend logs shipped to centralized storage; default logging via Python `logging` (see `LOG_LEVEL` env).

## 11. Documentation Map
- Quick reference: `START_HERE.md`
- Security specifics: `SECURITY_ACTIONS_COMPLETED.md`, `JWT_COOKIE_MIGRATION.md`
- MCP reference: `MCP_README.md`, `MCP_SETUP_GUIDE.md`
- Workflow Builder details: `PHASE_2_1_COMPLETE.md`, `web-ui/components/workflows/*`
- Deployment details: `DEPLOYMENT_GUIDE.md`, `PRODUCTION_CHECKLIST.md`

Maintain this document alongside feature phases. Update sections when introducing new services, modifying security posture, or changing deployment pipelines.
