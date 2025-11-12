# 🤖 AI Assistant Platform v3.0 (Fractal + Multi-Agent Hybrid)

A cutting-edge, full-stack platform for orchestrating AI agents, managing complex workflows, and integrating a vast ecosystem of tools and models. This version introduces a powerful hybrid architecture combining Fractal Agents with a multi-agent system, a modular plugin registry, and advanced financial analytics capabilities.

## ✨ Key Features

### 🚀 Hybrid Agent Architecture
- **Fractal Agents**: Retains the proven hierarchical structure for task decomposition and context propagation.
- **Multi-Agent System**: Integrates 84 specialized agents from a catalog, dynamically loaded for specific tasks.
- **LangGraph Integration**: Manages complex, stateful workflows for sophisticated operations like financial analysis and security hardening.

### 🔌 Modular Plugin & Skills System
- **Plugin Registry**: A centralized, type-safe registry for managing agents, skills, and tools with dependency and conflict resolution.
- **Progressive Disclosure**: A three-tiered skills system that conserves up to 90% of context by loading skill instructions and resources on demand.

### 🧠 Intelligent Routing & Orchestration
- **LLM Router**: Intelligently selects the best AI model (e.g., Haiku, Sonnet, Opus) based on task complexity analysis, reducing costs by up to 77%.
- **Workflow Engine**: Orchestrates multi-step processes involving different agents and tools.

### 💰 Financial Analytics Module
- **OpenBB Integration**: Provides a comprehensive suite of financial analysis tools.
- **Multi-Agent Workflows**: Executes complex financial analysis tasks using dedicated agents for technical and fundamental analysis.

### 🎨 Modern UI/UX & Developer Experience
- **Modular Routers**: A refactored FastAPI backend with modular, scalable API endpoints.
- **Enhanced UI**: New frontend components for managing agents, workflows, skills, and financial dashboards.
- **Prompt Library**: A collection of 57 pre-built templates for various workflows and tools.

## 🏗️ New Architecture (Hybrid)

The v3.0 architecture is designed for modularity, scalability, and efficiency, integrating the existing Fractal Agent system with a new catalog of specialized agents and a robust set of orchestration and integration layers.

```
agents/
├── fractal/                     # Existing Fractal Agent code (preserved)
│   ├── base.py                  # Base Fractal Agent
│   ├── blog_agents.py           # Existing Blog Agents
│   └── enhanced_agent.py        # NEW: Enhanced with new integrations
│
├── catalog/                     # NEW: 84 specialized agents
│   ├── __init__.py
│   ├── catalog_generated.py    # Auto-generated from .md files
│   └── agent_loader.py          # Dynamic agent loading
│
├── skills/                      # NEW: Progressive Disclosure mechanism
│   ├── registry.py              # Skills registry
│   ├── metadata/                # Level 1: Always in memory
│   ├── instructions/            # Level 2: Load on activation
│   └── resources/               # Level 3: Load on use
│
├── orchestration/               # NEW: LangGraph for complex workflows
│   ├── langgraph_node.py        # Wrapper for LangGraph
│   └── workflows/               # Complex workflow definitions
│       ├── financial_analysis.py
│       ├── full_stack_feature.py
│       └── security_hardening.py
│
├── routing/                     # NEW: Intelligent LLM routing
│   ├── llm_router.py            # Model selection by complexity
│   └── complexity_analyzer.py   # Task complexity analysis
│
├── financial/                   # NEW: Financial analytics module
│   ├── analytics.py             # OpenBB integration
│   ├── technical.py             # Technical indicators
│   ├── fundamental.py           # Fundamental analysis
│   └── workflows.py             # Multi-agent financial workflows
│
├── prompts/                     # NEW: Template library
│   ├── library.py               # PromptLibrary class
│   ├── workflows/               # 15 workflow templates
│   └── tools/                   # 42 tool templates
│
└── registry/                    # NEW: Plugin system
    ├── plugin_registry.py       # Centralized registry
    ├── validator.py             # Schema validation
    └── models.py                # Pydantic models

api/
├── main.py                      # NEW: Slim entry point
├── routers/                     # NEW: Modular routers
│   ├── auth.py
│   ├── chat.py
│   ├── agents.py                # Agent management
│   ├── workflows.py             # Workflow execution
│   └── financial.py             # Financial endpoints
├── dependencies.py              # Shared dependencies
└── middleware.py                # CORS, rate limiting

web-ui/app/
├── agents/                      # NEW: Agent catalog UI
│   ├── page.tsx                 # Agent list
│   ├── [id]/                    # Agent details
│   └── chat/                    # Agent-specific chat
├── workflows/                   # NEW: Workflow builder UI
│   └── page.tsx
├── financial/                   # NEW: Financial dashboard UI
│   └── page.tsx
└── skills/                      # NEW: Skills manager UI
    └── page.tsx
```
## 🔑 Key New Components

- **Plugin Registry**: A central hub for managing all agents, skills, and tools, ensuring type safety and easy extensibility.
- **Enhanced Fractal Agent**: An upgraded version of the Fractal Agent, now integrated with the new plugin and skill systems.
- **LangGraphFractalNode**: A wrapper that enables the use of Fractal Agents within stateful LangGraph workflows.
- **LLM Router**: An intelligent router that analyzes task complexity to select the most appropriate and cost-effective language model.
- **Skills Registry**: Implements a Progressive Disclosure mechanism to manage and load skills efficiently, saving context space.
- **Financial Module**: A powerful new module for business analytics, integrated with OpenBB for comprehensive financial data analysis.
- **Prompt Library**: A curated collection of 57 ready-to-use prompt templates for a wide range of tasks.

## 📦 Plugin Registry

The Plugin Registry is the cornerstone of the new modular architecture. It uses Pydantic models to enforce a strict schema for all plugins, ensuring consistency and reliability.

### Plugin Metadata

All plugins must conform to the `PluginMetadata` schema, which includes fields for name, version, description, category, dependencies, and more. This structured approach allows for robust validation and management of the entire plugin ecosystem.

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class PluginMetadata(BaseModel):
    name: str = Field(..., regex="^[a-z0-9-]+$")
    version: str = Field(..., regex="^\\d+\\.\\d+\\.\\d+$")
    description: str = Field(..., min_length=10, max_length=500)
    category: str
    author: str = Field(default="wshobson")
    agents: List[str] = Field(default=[])
    skills: List[str] = Field(default=[])
    tools: List[str] = Field(default=[])
    requires: List[str] = Field(default=[])
    conflicts: List[str] = Field(default=[])
    python_requires: str = Field(default=">=3.11")
    preferred_model: Optional[str] = Field(default=None)
    enabled: bool = Field(default=True)
```

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm/pnpm

### Backend Setup

```bash
# Navigate to the project directory
cd AIAssistant

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Then, edit the .env file to add your API keys and a new SECRET_KEY

# Run the database migrations (if any)
# python -m alembic upgrade head

# Start the FastAPI server
uvicorn api.main:app --reload
```

### Frontend Setup

```bash
# Navigate to the web UI directory
cd web-ui

# Install dependencies
npm install

# Start the development server
npm run dev
```

## 🛠️ Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **Pydantic**: Data validation and settings management
- **SQLAlchemy**: SQL toolkit and Object-Relational Mapper
- **LangGraph**: Building stateful, multi-agent applications
- **OpenBB**: Open-source financial analysis platform

### Frontend
- **Next.js**: React framework for production
- **TypeScript**: Statically typed JavaScript
- **Tailwind CSS**: A utility-first CSS framework
- **React Flow**: For building node-based UIs and editors

## 🤝 Contributing

Contributions are welcome! Please fork the repository, create a feature branch, and open a pull request with your changes.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
