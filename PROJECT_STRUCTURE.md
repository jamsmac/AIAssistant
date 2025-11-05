# PROJECT STRUCTURE - AI ASSISTANT PLATFORM

## Directory Tree Overview

```
autopilot-core/
├── api/                              # FastAPI Backend
│   ├── server.py                    # Main API server (3,908 lines)
│   └── routers/                     # API route modules
│       ├── blog_api.py             # Blog endpoints
│       └── fractal_api.py          # Fractal agent endpoints
│
├── agents/                           # Business Logic & AI Integration
│   ├── __init__.py
│   ├── ai_router.py                # Multi-model AI routing (787 lines)
│   ├── database.py                 # Data layer (1,454 lines)
│   ├── workflow_engine.py          # Workflow orchestration (631 lines)
│   ├── mcp_server.py               # Model Context Protocol (498 lines)
│   ├── monitoring.py               # Health & monitoring (427 lines)
│   ├── mcp_client.py               # MCP integration client
│   ├── auth.py                     # Authentication utilities
│   ├── rate_limiter.py             # Rate limiting (157 lines)
│   ├── csrf_protection.py          # CSRF protection (155 lines)
│   ├── two_factor_auth.py          # 2FA implementation
│   ├── oauth_providers.py          # OAuth integration
│   ├── ranking_collector.py        # HuggingFace/Arena scraper
│   ├── postgres_db.py              # PostgreSQL interface
│   │
│   ├── fractal/                    # Fractal Agent System
│   │   ├── __init__.py
│   │   ├── base_agent.py          # Base fractal agent
│   │   └── orchestrator.py         # Agent orchestrator
│   │
│   └── blog/                       # Blog Agents (Content Creation)
│       ├── __init__.py
│       ├── writer_agent.py         # Content writing
│       ├── editor_agent.py         # Content editing
│       ├── seo_agent.py            # SEO optimization
│       ├── image_agent.py          # Image sourcing
│       └── social_agent.py         # Social media adaptation
│
├── web-ui/                          # Next.js Frontend
│   ├── package.json                # Dependencies (React 19, Next 16)
│   ├── tsconfig.json               # TypeScript config (strict mode)
│   ├── next.config.ts              # Next.js configuration
│   ├── vercel.json                 # Vercel deployment config
│   ├── vitest.config.ts            # Unit test config
│   ├── playwright.config.ts        # E2E test config
│   │
│   ├── app/                        # Next.js App Router Pages
│   │   ├── layout.tsx              # Root layout
│   │   ├── page.tsx                # Dashboard
│   │   ├── loading.tsx             # Loading state
│   │   ├── not-found.tsx           # 404 page
│   │   │
│   │   ├── login/page.tsx          # Login form
│   │   ├── register/page.tsx       # Registration form
│   │   │
│   │   ├── chat/page.tsx           # Chat interface
│   │   ├── workflows/page.tsx      # Workflow management
│   │   ├── agents/page.tsx         # Agent network
│   │   ├── integrations/page.tsx   # Integration hub
│   │   │
│   │   ├── projects/               # Project management
│   │   │   ├── page.tsx           # Projects list
│   │   │   └── [id]/
│   │   │       ├── page.tsx       # Project details
│   │   │       └── databases/
│   │   │           └── [dbId]/page.tsx
│   │   │
│   │   ├── models-ranking/page.tsx # AI rankings
│   │   ├── project/page.tsx        # Project details
│   │   ├── history/page.tsx        # Chat history
│   │   │
│   │   ├── blog/                  # Blog pages
│   │   │   ├── page.tsx           # Blog listing
│   │   │   └── [slug]/page.tsx    # Blog post view
│   │   │
│   │   ├── admin/                 # Admin pages
│   │   │   ├── blog/
│   │   │   │   ├── page.tsx      # Blog management
│   │   │   │   └── new/page.tsx  # New post
│   │   │   ├── analytics/page.tsx # Analytics
│   │   │   └── monitoring/page.tsx # Monitoring
│   │   │
│   │   ├── api/                   # API routes
│   │   │   ├── chat/route.ts     # Chat endpoint
│   │   │   └── health/route.ts   # Health check
│   │   │
│   │   └── auth/
│   │       └── callback/page.tsx  # OAuth callback
│   │
│   ├── components/                # React Components
│   │   ├── Navigation.tsx         # Sidebar
│   │   ├── ErrorBoundary.tsx      # Error handling
│   │   ├── DashboardCharts.tsx    # Analytics charts
│   │   │
│   │   ├── chat/                 # Chat components
│   │   │   ├── ChatSidebar.tsx
│   │   │   ├── ChatMessages.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   └── ChatSettings.tsx
│   │   │
│   │   ├── workflows/            # Workflow components
│   │   │   ├── WorkflowCard.tsx
│   │   │   ├── WorkflowForm.tsx
│   │   │   └── WorkflowExecutionModal.tsx
│   │   │
│   │   ├── agents/               # Agent components
│   │   │   └── AgentNetworkGraph.tsx
│   │   │
│   │   ├── blog/                # Blog components
│   │   │   ├── RichTextEditor.tsx
│   │   │   └── CommentModeration.tsx
│   │   │
│   │   ├── auth/                # Auth components
│   │   │   └── OAuthButtons.tsx
│   │   │
│   │   └── ui/                  # UI components
│   │       └── Toast.tsx
│   │
│   ├── lib/                       # Utility libraries
│   │   ├── api.ts               # API client
│   │   ├── config.ts            # Configuration
│   │   ├── analytics.ts         # Analytics
│   │   ├── security.ts          # Security utils
│   │   └── useApi.ts            # API hook
│   │
│   ├── types/                     # TypeScript types
│   │   ├── api.ts               # API types
│   │   ├── workflows.ts         # Workflow types
│   │   ├── agents.ts            # Agent types
│   │   ├── database.ts          # Database types
│   │   └── charts.ts            # Chart types
│   │
│   ├── tests/                     # Test files
│   │   ├── app/
│   │   │   └── login.test.tsx
│   │   ├── components/
│   │   │   └── ui/Toast.test.tsx
│   │   ├── lib/
│   │   │   └── api.test.ts
│   │   ├── e2e/
│   │   │   ├── auth.spec.ts
│   │   │   └── workflows.spec.ts
│   │   ├── mocks/
│   │   │   ├── handlers.ts
│   │   │   └── server.ts
│   │   ├── security/
│   │   │   └── rls-isolation.test.ts
│   │   ├── utils/
│   │   │   └── test-utils.tsx
│   │   └── setup.ts
│   │
│   ├── public/                    # Static assets
│   │   └── favicon.ico
│   │
│   ├── .env.example               # Environment template
│   ├── .env.local                 # Local development
│   ├── .env.production            # Production
│   │
│   └── node_modules/              # NPM packages
│
├── tests/                          # Backend tests
│   ├── test_ai_router.py         # AI routing tests
│   ├── test_database.py          # Database tests
│   ├── test_auth.py              # Authentication tests
│   ├── test_fractal_system.py    # Fractal agent tests
│   └── security/
│       └── rls-isolation.test.ts # Security tests
│
├── scripts/                        # Utility scripts
│   ├── setup_scheduler.sh        # Scheduler setup
│   ├── update_rankings.py        # Ranking updates
│   ├── deploy.sh                 # Deployment
│   ├── init_agents.py            # Agent initialization
│   ├── init_blog_schema.sql      # Blog schema
│   └── init_fractal_schema.sql   # Fractal schema
│
├── docker-compose.yml             # Docker services
│   ├── PostgreSQL 16
│   ├── Redis
│   ├── Qdrant
│   ├── MinIO
│   └── N8N
│
├── .github/                        # GitHub configuration
│   └── workflows/
│       └── ci.yml                # CI/CD pipeline (9 jobs)
│
├── requirements.txt               # Python dependencies (57 packages)
├── railway.json                   # Railway deployment config
├── .env.example                   # Environment template
├── .cursorrules                   # Cursor AI rules
│
├── README.md                      # Project overview
├── TROUBLESHOOTING.md             # Common issues
└── Documentation (33K+ lines)
    ├── COMPREHENSIVE_CODEBASE_ANALYSIS.md
    ├── ANALYSIS_SUMMARY.md
    ├── DEVELOPMENT_ROADMAP.md
    ├── SECURITY_AUDIT_REPORT.md
    ├── PROJECT_AUDIT_REPORT.md
    └── ... (20+ more docs)
```

---

## KEY STATISTICS

### Code Distribution

```
Backend (Python):
├── api/server.py                   3,908 lines  (Main API)
├── agents/database.py              1,454 lines  (Data layer)
├── agents/ai_router.py               787 lines  (Model routing)
├── agents/workflow_engine.py         631 lines  (Automation)
├── agents/mcp_server.py              498 lines  (MCP integration)
├── agents/monitoring.py              427 lines  (Monitoring)
└── Other agents & modules          1,200 lines
    Total Backend:               ~9,000 lines

Frontend (TypeScript/React):
├── Pages (app/)                   ~3,500 lines
├── Components (components/)       ~2,500 lines
├── Types & Libraries            ~2,000 lines
├── Tests & Config               ~1,500 lines
└── Configuration                   ~500 lines
    Total Frontend:              ~10,000 lines

Documentation:
├── Markdown Files                33,799 lines
└── Comments in Code              ~5,000 lines
    Total Documentation:          ~38,800 lines

Grand Total:                      ~57,800 lines
```

### Framework Versions
- Python: 3.11
- Node.js: 20
- FastAPI: 0.115.4
- React: 19.2.0
- Next.js: 16.0.1
- TypeScript: 5.9.3
- Tailwind CSS: 4.1.16

---

## IMPORTANT FILES REFERENCE

### Configuration Files
| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies |
| `web-ui/package.json` | Node.js dependencies |
| `.env.example` | Environment variables template |
| `docker-compose.yml` | Docker services |
| `railway.json` | Railway deployment |
| `web-ui/vercel.json` | Vercel deployment |
| `.github/workflows/ci.yml` | CI/CD pipeline |

### Main Entry Points
| File | Purpose |
|------|---------|
| `api/server.py` | FastAPI application |
| `web-ui/app/page.tsx` | Frontend dashboard |
| `agents/ai_router.py` | Model routing logic |
| `agents/database.py` | Database layer |
| `web-ui/lib/api.ts` | Frontend API client |

### Core Agents
| Module | Purpose | LOC |
|--------|---------|-----|
| `ai_router.py` | Model selection | 787 |
| `database.py` | Data persistence | 1,454 |
| `workflow_engine.py` | Task automation | 631 |
| `mcp_server.py` | Claude integration | 498 |
| `monitoring.py` | System health | 427 |
| `fractal/` | Agent network | 400+ |
| `blog/` | Content creation | 300+ |

---

## DEPLOYMENT STRUCTURE

### Frontend Deployment (Vercel)
```
web-ui/
├── .next/ (production build)
├── public/ (static assets)
└── Auto-deployed on main branch push
```

### Backend Deployment (Railway)
```
api/ + agents/
├── requirements.txt (dependencies)
├── railway.json (config)
└── Auto-deployed on main branch push
```

### Infrastructure (Docker)
```
docker-compose.yml provides:
├── PostgreSQL 16 (port 5432)
├── Redis (port 6379)
├── Qdrant (port 6333)
├── MinIO (port 9000)
└── N8N (port 5678)
```

---

## API ENDPOINTS SUMMARY

| Category | Count | Examples |
|----------|-------|----------|
| Authentication | 7 | login, register, 2fa, oauth |
| Chat & AI | 3 | chat, stream, history |
| Projects | 6 | create, list, get, update, delete |
| Databases | 8 | create, query, records |
| Sessions | 4 | create, get, delete |
| Workflows | 5+ | create, execute, history |
| Rankings | 4 | get, update, by category |
| Health & Stats | 3 | health, metrics, status |
| Integrations | 3+ | providers, connect |
| **Total** | **30+** | Fully documented |

---

## PAGES SUMMARY

| Section | Count | Examples |
|---------|-------|----------|
| Public Pages | 3 | login, register, home |
| User Pages | 5 | chat, projects, workflows |
| Content Pages | 4 | blog, models-ranking, integrations |
| Admin Pages | 3 | analytics, monitoring, blog management |
| **Total** | **17** | Fully functional |

---

## DEVELOPMENT WORKFLOW

### Local Setup
```bash
# Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn api.server:app --reload

# Frontend
cd web-ui
npm install
npm run dev

# Database
docker-compose up -d
```

### Testing
```bash
# Backend tests
pytest tests/ -v --cov

# Frontend tests
npm run test:unit
npm run test:e2e

# All tests
npm run test:coverage
```

### Deployment
```bash
# Automatic on git push to main
# Frontend: Vercel
# Backend: Railway
# Monitor at github.com/.../actions
```

---

## SECURITY IMPLEMENTATION

### Authentication
- JWT (HS256) with 24-hour expiration
- bcrypt password hashing (cost 12)
- 2FA support (TOTP)
- OAuth integration
- Session management

### Protection
- CSRF tokens (HMAC-SHA256)
- Rate limiting (3-tier)
- SQL injection prevention (parameterized)
- XSS protection (DOMPurify)
- CORS headers
- CSP headers
- Security headers middleware

### Data
- User isolation
- Request/response validation
- Error message obfuscation
- Request logging
- Suspicious activity alerts

---

**Last Updated**: November 5, 2025
**Maintainer**: Development Team
**Status**: Production Ready v1.0
