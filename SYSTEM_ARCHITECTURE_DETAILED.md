# 🏗️ Детальная Архитектура и Взаимодействие Компонентов Autopilot Core

## 📋 Содержание
1. [Общая Архитектура](#общая-архитектура)
2. [Поток Данных](#поток-данных)
3. [Детальное Описание Модулей](#детальное-описание-модулей)
4. [Взаимодействие Компонентов](#взаимодействие-компонентов)
5. [Технические Детали](#технические-детали)

---

## 🎯 Общая Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                   │
├─────────────────────────────────────────────────────────┤
│  React Components │ State Management │ UI/UX Layer      │
├─────────────────────────────────────────────────────────┤
│                    API Routes Layer                      │
├─────────────────────────────────────────────────────────┤
│  Business Logic  │  Services  │  Middleware             │
├─────────────────────────────────────────────────────────┤
│                  Database (Supabase)                     │
├─────────────────────────────────────────────────────────┤
│  PostgreSQL  │  Real-time  │  Auth  │  Storage          │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Поток Данных

### 1. **Жизненный Цикл Запроса**

```mermaid
User Action → React Component → API Call → Route Handler
    → Service Layer → Database → Response → UI Update
```

**Пример: Создание нового проекта**

```typescript
// 1. User clicks "New Project" button
// Component: /components/projects/ProjectList.tsx
const handleCreateProject = async () => {
  const projectData = {
    name: "My Project",
    description: "Description",
    status: "active"
  };

  // 2. API call through client
  const response = await apiClient.post('/api/projects', projectData);

  // 3. Update local state
  setProjects([...projects, response.data]);
};

// 4. API Route Handler: /app/api/projects/route.ts
export async function POST(request: NextRequest) {
  const body = await request.json();

  // 5. Validate data
  const validated = projectSchema.parse(body);

  // 6. Call Supabase
  const { data, error } = await supabase
    .from('projects')
    .insert(validated)
    .select()
    .single();

  // 7. Return response
  return NextResponse.json(data);
}
```

---

## 📦 Детальное Описание Модулей

### 1. **FractalAgents System** 🤖

#### Как работает:

**Иерархия агентов:**
```
Root Agent (Координатор)
    ├── Specialist Agent 1 (Frontend Expert)
    ├── Specialist Agent 2 (Backend Expert)
    └── Specialist Agent 3 (Database Expert)
        ├── Worker Agent 1
        └── Worker Agent 2
```

**Процесс обработки задачи:**

```typescript
// 1. Задача поступает в систему
const task = {
  id: "task-001",
  type: "complex",
  description: "Build a full-stack feature",
  requirements: ["frontend", "backend", "database"]
};

// 2. Root Agent анализирует задачу
class RootAgent {
  async analyzeTask(task: Task) {
    // Определяет необходимые навыки
    const requiredSkills = this.extractSkills(task);

    // Находит подходящих агентов
    const agents = await this.findAgents(requiredSkills);

    // Распределяет подзадачи
    return this.distributeSubtasks(task, agents);
  }
}

// 3. Specialist Agents получают подзадачи
class SpecialistAgent {
  async processSubtask(subtask: Subtask) {
    // Использует свою экспертизу
    const solution = await this.applySkilledApproach(subtask);

    // Может создать worker агентов
    if (this.needsWorkers(subtask)) {
      const workers = await this.spawnWorkers(subtask);
      return this.coordinateWorkers(workers);
    }

    return solution;
  }
}

// 4. Коллективная память обновляется
class CollectiveMemory {
  async updateFromExperience(task: Task, solution: Solution) {
    // Сохраняет успешные паттерны
    await this.storePattern({
      taskType: task.type,
      solution: solution,
      successRate: solution.metrics.success,
      timestamp: new Date()
    });

    // Обновляет trust levels агентов
    await this.updateAgentTrust(solution.agents);
  }
}
```

**База данных агентов:**

```sql
-- Таблица agents
CREATE TABLE agents (
  id UUID PRIMARY KEY,
  agent_name VARCHAR(255),
  agent_type ENUM('root', 'specialist', 'worker'),
  skills JSONB,
  parent_id UUID REFERENCES agents(id),
  trust_level FLOAT DEFAULT 0.5,
  success_rate FLOAT DEFAULT 0.0,
  task_count INTEGER DEFAULT 0
);

-- Таблица agent_connectors (связи между агентами)
CREATE TABLE agent_connectors (
  id UUID PRIMARY KEY,
  from_agent_id UUID REFERENCES agents(id),
  to_agent_id UUID REFERENCES agents(id),
  connector_type VARCHAR(50),
  strength FLOAT DEFAULT 0.5,
  trust FLOAT DEFAULT 0.5,
  last_interaction TIMESTAMP
);

-- Таблица collective_memory
CREATE TABLE collective_memory (
  id UUID PRIMARY KEY,
  pattern_type VARCHAR(100),
  pattern_data JSONB,
  success_rate FLOAT,
  usage_count INTEGER DEFAULT 0,
  created_by UUID REFERENCES agents(id)
);
```

---

### 2. **Workflow Automation System** ⚡

#### Как работает:

**Структура Workflow:**

```typescript
interface Workflow {
  id: string;
  name: string;
  triggers: Trigger[];
  actions: Action[];
  conditions: Condition[];
  status: 'active' | 'paused' | 'completed';
}

interface Trigger {
  type: 'schedule' | 'webhook' | 'event' | 'manual';
  config: {
    schedule?: string; // cron expression
    webhook?: { url: string; secret: string };
    event?: { source: string; eventType: string };
  };
}

interface Action {
  id: string;
  type: 'api_call' | 'database' | 'ai_task' | 'email';
  config: any;
  dependsOn?: string[]; // IDs других actions
  condition?: Condition;
}
```

**Execution Engine:**

```typescript
class WorkflowExecutor {
  private queue: Queue;
  private activeExecutions: Map<string, Execution>;

  async execute(workflow: Workflow, trigger: TriggerEvent) {
    // 1. Создаём execution context
    const execution = new Execution(workflow, trigger);
    this.activeExecutions.set(execution.id, execution);

    // 2. Проверяем условия запуска
    if (!await this.checkConditions(workflow.conditions, trigger)) {
      return execution.skip('Conditions not met');
    }

    // 3. Выполняем actions по порядку или параллельно
    const actionGraph = this.buildActionGraph(workflow.actions);

    for (const actionLayer of actionGraph.layers) {
      // Параллельное выполнение независимых actions
      await Promise.all(
        actionLayer.map(action => this.executeAction(action, execution))
      );
    }

    // 4. Сохраняем результаты
    await this.saveExecutionResult(execution);

    return execution;
  }

  private async executeAction(action: Action, execution: Execution) {
    try {
      switch (action.type) {
        case 'api_call':
          return await this.executeApiCall(action.config);
        case 'database':
          return await this.executeDatabaseQuery(action.config);
        case 'ai_task':
          return await this.executeAiTask(action.config);
        case 'email':
          return await this.sendEmail(action.config);
      }
    } catch (error) {
      await this.handleActionError(action, error, execution);
    }
  }
}
```

**Scheduler Service:**

```typescript
class WorkflowScheduler {
  private cronJobs: Map<string, CronJob>;

  async scheduleWorkflow(workflow: Workflow) {
    const scheduleTriggers = workflow.triggers.filter(t => t.type === 'schedule');

    for (const trigger of scheduleTriggers) {
      const job = new CronJob(trigger.config.schedule!, async () => {
        await this.executor.execute(workflow, {
          type: 'scheduled',
          timestamp: new Date()
        });
      });

      this.cronJobs.set(`${workflow.id}-${trigger.id}`, job);
      job.start();
    }
  }
}
```

---

### 3. **Real-time Monitoring System** 📊

#### Как работает:

**Metrics Collection:**

```typescript
class MetricsCollector {
  private metrics: Map<string, Metric[]> = new Map();
  private websocket: WebSocket;

  // Собирает метрики из разных источников
  async collectSystemMetrics() {
    const metrics = {
      cpu: await this.getCpuUsage(),
      memory: await this.getMemoryUsage(),
      disk: await this.getDiskUsage(),
      network: await this.getNetworkStats(),
      timestamp: Date.now()
    };

    // Сохраняет в памяти для агрегации
    this.addMetric('system', metrics);

    // Отправляет в real-time клиентам
    this.broadcast('metrics:system', metrics);

    // Сохраняет в базу для истории
    await this.persistMetrics(metrics);
  }

  // Агрегация для графиков
  getAggregatedMetrics(type: string, period: string) {
    const rawMetrics = this.metrics.get(type) || [];

    switch (period) {
      case '1h':
        return this.aggregateByMinute(rawMetrics, 60);
      case '24h':
        return this.aggregateByHour(rawMetrics, 24);
      case '7d':
        return this.aggregateByDay(rawMetrics, 7);
    }
  }
}
```

**WebSocket для Real-time Updates:**

```typescript
// Server side
class MonitoringWebSocket {
  handleConnection(ws: WebSocket) {
    // Подписка на метрики
    ws.on('subscribe', (channels: string[]) => {
      channels.forEach(channel => {
        this.subscriptions.add(ws, channel);
      });
    });

    // Отправка обновлений
    this.metricsCollector.on('update', (data) => {
      const subscribers = this.subscriptions.getSubscribers(data.channel);
      subscribers.forEach(ws => ws.send(JSON.stringify(data)));
    });
  }
}

// Client side (React)
function useRealtimeMetrics(channel: string) {
  const [metrics, setMetrics] = useState([]);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:3000/monitoring');

    ws.onopen = () => {
      ws.send(JSON.stringify({
        action: 'subscribe',
        channels: [channel]
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMetrics(prev => [...prev.slice(-99), data]);
    };

    return () => ws.close();
  }, [channel]);

  return metrics;
}
```

---

### 4. **AI Chat System** 💬

#### Как работает:

**Message Processing Pipeline:**

```typescript
class ChatProcessor {
  private context: ConversationContext;
  private aiClient: AIClient;

  async processMessage(message: UserMessage) {
    // 1. Анализ контекста
    const enrichedContext = await this.enrichContext(message);

    // 2. Определение intent
    const intent = await this.detectIntent(message, enrichedContext);

    // 3. Выбор подходящей модели
    const model = this.selectModel(intent);

    // 4. Формирование промпта
    const prompt = this.buildPrompt({
      message: message.content,
      context: enrichedContext,
      intent: intent,
      systemInstructions: this.getSystemPrompt(intent)
    });

    // 5. Получение ответа от AI
    const response = await this.aiClient.complete({
      model: model,
      prompt: prompt,
      temperature: this.getTemperature(intent),
      maxTokens: 2000
    });

    // 6. Пост-обработка
    const processed = await this.postProcess(response, intent);

    // 7. Сохранение в историю
    await this.saveToHistory(message, processed);

    return processed;
  }

  private async enrichContext(message: UserMessage) {
    // Получаем релевантную информацию
    const recentMessages = await this.getRecentMessages(message.sessionId);
    const userProfile = await this.getUserProfile(message.userId);
    const projectContext = await this.getProjectContext(message.projectId);

    // Векторный поиск похожих вопросов
    const similarQuestions = await this.vectorSearch(message.content);

    return {
      recentMessages,
      userProfile,
      projectContext,
      similarQuestions
    };
  }
}
```

**Streaming Responses:**

```typescript
class StreamingChat {
  async *streamResponse(prompt: string): AsyncGenerator<string> {
    const stream = await this.aiClient.streamComplete({
      model: 'gpt-4',
      prompt: prompt,
      stream: true
    });

    let buffer = '';
    for await (const chunk of stream) {
      buffer += chunk;

      // Отправляем по предложениям
      if (buffer.includes('.') || buffer.includes('!') || buffer.includes('?')) {
        const sentences = buffer.split(/[.!?]+/);
        const complete = sentences.slice(0, -1).join('. ') + '.';
        buffer = sentences[sentences.length - 1];

        yield complete;
      }
    }

    // Отправляем остаток
    if (buffer.trim()) {
      yield buffer;
    }
  }
}
```

---

### 5. **Project Management System** 📁

#### Как работает:

**Project Structure:**

```typescript
class Project {
  id: string;
  name: string;
  databases: Database[];
  apis: APIEndpoint[];
  environments: Environment[];
  deployments: Deployment[];

  // Управление жизненным циклом
  async initialize() {
    // Создаём структуру директорий
    await this.createDirectoryStructure();

    // Инициализируем git репозиторий
    await this.initGitRepo();

    // Создаём базовые файлы
    await this.createBaseFiles();

    // Настраиваем окружения
    await this.setupEnvironments();
  }

  async addDatabase(config: DatabaseConfig) {
    // Создаём схему
    const schema = await this.generateSchema(config);

    // Применяем миграции
    await this.runMigrations(schema);

    // Настраиваем connection pool
    await this.setupConnectionPool(config);

    // Добавляем в проект
    this.databases.push(new Database(config, schema));
  }
}
```

**Resource Manager:**

```typescript
class ResourceManager {
  private resources: Map<string, Resource>;
  private quotas: Map<string, Quota>;

  async allocateResource(projectId: string, type: ResourceType, amount: number) {
    // Проверяем квоты
    if (!await this.checkQuota(projectId, type, amount)) {
      throw new QuotaExceededError();
    }

    // Выделяем ресурс
    const resource = await this.provision(type, amount);

    // Регистрируем
    this.resources.set(`${projectId}-${resource.id}`, resource);

    // Обновляем счётчики
    await this.updateUsage(projectId, type, amount);

    return resource;
  }

  async scaleResource(resourceId: string, newAmount: number) {
    const resource = this.resources.get(resourceId);

    if (newAmount > resource.current) {
      // Scale up
      await this.scaleUp(resource, newAmount);
    } else {
      // Scale down
      await this.scaleDown(resource, newAmount);
    }

    resource.current = newAmount;
  }
}
```

---

## 🔗 Взаимодействие Компонентов

### 1. **Chat → Agents → Workflow**

```typescript
// Пользователь спрашивает в чате
User: "Create a new API endpoint for user authentication"

// Chat система определяет intent
ChatProcessor → Intent: CREATE_API_ENDPOINT

// Передаёт задачу FractalAgents
ChatProcessor → RootAgent: {
  task: "create_api",
  details: "user authentication endpoint"
}

// Root Agent распределяет подзадачи
RootAgent → BackendSpecialist: "Create auth endpoint"
RootAgent → DatabaseSpecialist: "Setup user tables"
RootAgent → SecuritySpecialist: "Implement JWT"

// Специалисты создают workflow
Specialists → WorkflowBuilder: {
  actions: [
    { type: "create_file", path: "/api/auth/route.ts" },
    { type: "database_migration", schema: "users_table" },
    { type: "generate_code", template: "jwt_auth" },
    { type: "run_tests", suite: "auth" }
  ]
}

// Workflow выполняется
WorkflowExecutor → Results

// Результаты возвращаются в чат
Results → ChatProcessor → User: "✅ Authentication endpoint created successfully"
```

### 2. **Monitoring → Analytics → Alerts**

```typescript
// Monitoring собирает метрики
MetricsCollector.collect() → {
  cpu: 85%,
  memory: 92%,
  responseTime: 1500ms
}

// Analytics анализирует тренды
AnalyticsEngine.analyze(metrics) → {
  trend: "increasing",
  anomaly: true,
  severity: "high"
}

// Alert система реагирует
AlertManager.process(analysis) → {
  sendEmail("admin@example.com", "High resource usage detected"),
  scaleUp("web-server", 2),
  createIncident("HIGH_RESOURCE_USAGE")
}
```

---

## 🔧 Технические Детали

### Database Schema

```sql
-- Projects
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  status VARCHAR(50) DEFAULT 'active',
  owner_id UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  settings JSONB DEFAULT '{}'::jsonb
);

-- Workflows
CREATE TABLE workflows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id),
  name VARCHAR(255),
  triggers JSONB,
  actions JSONB,
  conditions JSONB,
  status VARCHAR(50) DEFAULT 'active'
);

-- Executions
CREATE TABLE workflow_executions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id UUID REFERENCES workflows(id),
  trigger_type VARCHAR(50),
  started_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP,
  status VARCHAR(50),
  result JSONB,
  error TEXT
);

-- Chat Sessions
CREATE TABLE chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  project_id UUID REFERENCES projects(id),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Messages
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES chat_sessions(id),
  role VARCHAR(50), -- 'user', 'assistant', 'system'
  content TEXT,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### API Structure

```typescript
// API Routes
/api/
  ├── auth/
  │   ├── login/
  │   ├── logout/
  │   └── register/
  ├── projects/
  │   ├── [id]/
  │   │   ├── databases/
  │   │   ├── apis/
  │   │   └── deployments/
  ├── agents/
  │   ├── spawn/
  │   ├── tasks/
  │   └── memory/
  ├── workflows/
  │   ├── [id]/
  │   │   ├── execute/
  │   │   └── history/
  ├── chat/
  │   ├── messages/
  │   └── sessions/
  └── monitoring/
      ├── metrics/
      └── logs/
```

### State Management

```typescript
// Zustand Store Structure
interface AppStore {
  // User
  user: User | null;
  setUser: (user: User | null) => void;

  // Projects
  projects: Project[];
  currentProject: Project | null;
  selectProject: (id: string) => void;

  // Chat
  messages: Message[];
  addMessage: (message: Message) => void;

  // Agents
  agents: Agent[];
  agentConnections: Connection[];
  updateAgentStatus: (id: string, status: AgentStatus) => void;

  // Workflows
  workflows: Workflow[];
  executions: Execution[];

  // Real-time
  websocket: WebSocket | null;
  connectWebSocket: () => void;
}
```

---

## 🎯 Ключевые Особенности Взаимодействия

1. **Event-Driven Architecture** - Компоненты общаются через события
2. **Microservices Ready** - Каждый модуль может быть выделен в отдельный сервис
3. **Real-time Updates** - WebSocket для мгновенных обновлений
4. **Queue System** - Асинхронная обработка тяжёлых задач
5. **Caching Layer** - Redis/In-memory для быстрого доступа
6. **Horizontal Scaling** - Легко масштабируется горизонтально

---

*Это детальное описание того, как все компоненты системы работают и взаимодействуют друг с другом на техническом уровне.*