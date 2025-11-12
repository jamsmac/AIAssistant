# Superadmin Panel - Complete Guide

## Overview

The AI Assistant Platform v3.0 now includes a comprehensive **Superadmin Panel** for managing all aspects of the system, including v3.0 components, users, settings, and audit logs.

## Access

**URL:** `http://localhost:3000/admin`

**Required Role:** `superadmin` or `admin`

---

## Dashboard

### Main Dashboard (`/admin`)

The main dashboard provides a comprehensive overview of the entire system:

#### Key Metrics

- **System Status**: Real-time health monitoring
  - Uptime tracking
  - Version information
  - Status indicator (healthy/warning/error)

- **User Statistics**
  - Total users
  - Active users today
  - New users this week

- **Agent Statistics**
  - Total agents (84 specialized agents)
  - Active agents
  - Tasks completed today
  - Success rate

- **v3.0 Components Status**
  - Plugin Registry: Number of registered plugins
  - Skills Registry: Total and active skills
  - LLM Router: Cost savings percentage (77%)
  - Agent Catalog: Specialized agents count

- **Performance Metrics**
  - Average response time
  - Requests today
  - Errors today
  - Uptime percentage

#### Quick Actions

Direct links to all management pages:
- Plugin Registry
- LLM Router
- Skills Manager
- User Management
- System Settings
- Audit Logs

#### Recent Activity

Real-time feed of recent system events and user actions.

---

## Plugin Registry (`/admin/plugins`)

Manage all plugins, agents, skills, and tools in the system.

### Features

#### Statistics
- Total plugins
- Total agents across all plugins
- Total skills
- Total tools

#### Plugin Management
- **Search**: Find plugins by name or description
- **Filter**: By category (core, development, finance, etc.)
- **View Details**: 
  - Version information
  - Author
  - Dependencies
  - Agent/skill/tool counts
- **Actions**:
  - Activate/Deactivate plugins
  - Configure plugin settings
  - Delete plugins

#### Add New Plugin
- Register new plugins
- Specify dependencies
- Configure plugin settings

#### Export/Import
- Export plugin configurations
- Import plugins from file

---

## LLM Router Configuration (`/admin/llm-router`)

Configure intelligent model routing with 77% cost reduction.

### Features

#### Statistics
- Total requests processed
- Cost saved (dollar amount and percentage)
- Actual cost spent
- Average cost per request

#### Task Distribution
Visual breakdown of task complexity:
- **Simple Tasks**: Basic queries (use haiku/gemini)
- **Moderate Tasks**: Standard tasks (use sonnet)
- **Complex Tasks**: Advanced tasks (use opus)
- **Expert Tasks**: Specialized tasks (use gpt-4)

#### Router Settings
- **Prefer Cost Efficiency**: Toggle to prioritize cheaper models

#### Model Configuration

Configure each model:
- **Enable/Disable**: Toggle model availability
- **Max Tokens**: Maximum output length
- **Temperature**: Creativity level (0-2)
- **Cost per 1K Input**: Input token cost
- **Cost per 1K Output**: Output token cost
- **Priority**: Model selection priority

**Supported Models:**
1. Haiku (Claude 3 Haiku)
2. Sonnet (Claude 3.5 Sonnet)
3. Opus (Claude 3 Opus)
4. GPT-4
5. GPT-3.5 Turbo
6. Gemini

---

## Skills Manager (`/admin/skills-manager`)

Manage Progressive Disclosure Skills System with 90% context savings.

### Features

#### Statistics
- Total skills
- Active skills
- Total usage count
- Context saved percentage (90%)

#### Skills Table

View all skills with:
- **Name & Description**
- **Category**: development, testing, security, etc.
- **Triggers**: Keywords that activate the skill
- **Usage Count**: How many times used
- **Token Estimates**: 
  - Level 1 (Metadata): ~50 tokens
  - Level 2 (Instructions): ~500 tokens
  - Level 3 (Resources): ~2000 tokens
- **Status**: Active/Inactive
- **Actions**: Edit, Delete

#### Progressive Disclosure Levels

**Level 1 - Metadata (Always Loaded)**
- Skill name and basic description
- Minimal token usage

**Level 2 - Instructions (Loaded on Activation)**
- Detailed instructions
- Usage guidelines

**Level 3 - Resources (Loaded on Use)**
- Complete documentation
- Examples and references
- Full context

---

## User Management (`/admin/users`)

Manage users, roles, and permissions.

### Features

#### Statistics
- Total users
- Active users
- Admin count
- Suspended users

#### Search & Filters
- Search by name or email
- Filter by role (superadmin/admin/user)

#### User Table

View all users with:
- **Name & Email**
- **Role**: 
  - `superadmin`: Full system access
  - `admin`: Management access
  - `user`: Standard access
- **Status**: active/suspended/pending
- **Tasks Count**: Number of tasks completed
- **Credits Used**: Total credits consumed
- **Last Login**: Last login timestamp
- **Actions**: Edit, Delete

#### User Actions
- **Create User**: Add new users
- **Edit User**: Update user information
- **Change Role**: Promote/demote users
- **Suspend/Activate**: Control user access
- **Delete User**: Remove users (with confirmation)

---

## System Settings (`/admin/settings`)

Configure system-wide settings and preferences.

### Settings Categories

#### 1. General Settings
- **Site Name**: Platform name
- **Site URL**: Base URL
- **Admin Email**: System admin email
- **Timezone**: System timezone

#### 2. API Keys
- **Anthropic API Key**: For Claude models
- **OpenAI API Key**: For GPT models
- **Gemini API Key**: For Gemini models
- **OpenBB API Key**: For financial data

#### 3. Database Settings
- **Host**: Database server host
- **Port**: Database port (default: 5432)
- **Database Name**: Database name
- **User**: Database user

#### 4. Security Settings
- **Two-Factor Authentication**: Require 2FA for all users
- **Strong Passwords**: Enforce complex password requirements
- **Session Timeout**: Session duration in seconds
- **Max Login Attempts**: Failed login limit

#### 5. Notification Settings
- **Email Notifications**: Enable/disable email alerts
- **Slack Webhook**: Slack integration URL
- **Discord Webhook**: Discord integration URL

#### 6. v3.0 Features
- **Plugin Registry**: Enable plugin system
- **LLM Router**: Enable intelligent routing (77% cost savings)
- **Progressive Disclosure**: Enable skills system (90% context savings)
- **Cost Efficiency Mode**: Prefer cheaper models

---

## Audit Logs (`/admin/audit-logs`)

Track all system activity and user actions.

### Features

#### Statistics
- Total events
- Successful operations
- Failures
- Warnings

#### Search & Filters
- **Search**: Find logs by action, user, or details
- **Status Filter**: success/failure/warning/info
- **Category Filter**: 
  - plugin
  - config
  - security
  - user
  - system
  - skill
  - analytics

#### Logs Table

View all logs with:
- **Timestamp**: When the action occurred
- **User**: Who performed the action
- **Action**: What was done
- **Resource**: What was affected
- **Details**: Additional information
- **IP Address**: Source IP
- **Status**: success/failure/warning/info

#### Export Logs
Export audit logs to CSV for external analysis.

---

## API Endpoints

All admin functionality is backed by REST API endpoints:

### Dashboard
- `GET /api/admin/dashboard` - Get dashboard statistics

### Plugin Registry
- `GET /api/admin/plugins` - List all plugins
- `POST /api/admin/plugins` - Register new plugin
- `PUT /api/admin/plugins/{name}/status` - Toggle plugin status
- `DELETE /api/admin/plugins/{name}` - Delete plugin

### LLM Router
- `GET /api/admin/llm-router/stats` - Get router statistics
- `GET /api/admin/llm-router/models` - Get model configurations
- `PUT /api/admin/llm-router/models` - Update model configurations

### Skills Registry
- `GET /api/admin/skills` - List all skills
- `POST /api/admin/skills` - Register new skill
- `DELETE /api/admin/skills/{name}` - Delete skill

### User Management
- `GET /api/admin/users` - List all users
- `POST /api/admin/users` - Create new user
- `PUT /api/admin/users/{id}` - Update user
- `DELETE /api/admin/users/{id}` - Delete user
- `PUT /api/admin/users/{id}/role` - Change user role
- `PUT /api/admin/users/{id}/status` - Change user status

### System Settings
- `GET /api/admin/settings` - Get system settings
- `PUT /api/admin/settings` - Update system settings

### Audit Logs
- `GET /api/admin/audit-logs` - Get audit logs (with filters)
- `POST /api/admin/audit-logs` - Create audit log entry
- `GET /api/admin/audit-logs/export` - Export logs to CSV

### System Health
- `GET /api/admin/health` - Get system health status
- `GET /api/admin/metrics` - Get detailed system metrics

---

## Security

### Role-Based Access Control

**Superadmin**
- Full access to all features
- Can manage other admins
- Can modify critical settings
- Can view all audit logs

**Admin**
- Can manage users (except superadmins)
- Can configure plugins and skills
- Can view audit logs
- Cannot modify critical security settings

**User**
- No admin panel access
- Standard platform features only

### Authentication

- All admin endpoints require authentication
- Session-based authentication with JWT tokens
- Optional 2FA for enhanced security
- Automatic session timeout
- Failed login attempt tracking

### Audit Trail

All admin actions are logged:
- User identification
- Action performed
- Resource affected
- Timestamp
- IP address
- Success/failure status

---

## Best Practices

### 1. Regular Monitoring
- Check dashboard daily for system health
- Review audit logs for suspicious activity
- Monitor cost savings and performance metrics

### 2. User Management
- Assign roles based on least privilege principle
- Regularly review user access
- Suspend inactive accounts
- Enable 2FA for all admin accounts

### 3. Plugin Management
- Only install trusted plugins
- Keep plugins updated
- Review plugin dependencies
- Test plugins in staging before production

### 4. LLM Router Optimization
- Monitor cost savings regularly
- Adjust model priorities based on usage
- Enable cost efficiency mode
- Review task distribution

### 5. Skills Management
- Organize skills by category
- Use descriptive triggers
- Monitor context savings
- Deactivate unused skills

### 6. Security
- Use strong API keys
- Rotate keys regularly
- Enable 2FA
- Set appropriate session timeouts
- Review audit logs regularly

### 7. Backup & Recovery
- Regular database backups
- Export plugin configurations
- Document custom settings
- Test recovery procedures

---

## Troubleshooting

### Cannot Access Admin Panel

**Problem**: 403 Forbidden or redirect to login

**Solution**:
1. Verify user has `superadmin` or `admin` role
2. Check authentication token is valid
3. Clear browser cache and cookies
4. Re-login to get fresh token

### Plugin Not Activating

**Problem**: Plugin status won't change

**Solution**:
1. Check plugin dependencies are met
2. Verify no conflicts with other plugins
3. Review audit logs for error details
4. Check plugin is properly registered

### LLM Router Not Routing

**Problem**: All requests use same model

**Solution**:
1. Verify LLM Router is enabled in settings
2. Check model configurations are correct
3. Ensure API keys are valid
4. Review router statistics for errors

### Skills Not Loading

**Problem**: Skills not activating on triggers

**Solution**:
1. Verify Progressive Disclosure is enabled
2. Check skill triggers are correct
3. Ensure skill is marked as active
4. Review skill usage statistics

### Audit Logs Not Showing

**Problem**: Recent actions not appearing

**Solution**:
1. Check audit log creation is enabled
2. Verify database connection
3. Clear filters and search
4. Check user permissions

---

## Screenshots

### Main Dashboard
![Dashboard Overview](docs/screenshots/admin-dashboard.png)

### Plugin Registry
![Plugin Management](docs/screenshots/admin-plugins.png)

### LLM Router
![Router Configuration](docs/screenshots/admin-llm-router.png)

### Skills Manager
![Skills Management](docs/screenshots/admin-skills.png)

### User Management
![User Management](docs/screenshots/admin-users.png)

### System Settings
![System Settings](docs/screenshots/admin-settings.png)

### Audit Logs
![Audit Logs](docs/screenshots/admin-audit-logs.png)

---

## Future Enhancements

### Planned Features

- [ ] Real-time notifications
- [ ] Advanced analytics dashboard
- [ ] Bulk user operations
- [ ] Plugin marketplace
- [ ] Automated backups
- [ ] Performance profiling
- [ ] Custom dashboards
- [ ] Mobile app
- [ ] Multi-language support
- [ ] Dark mode

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/jamsmac/AIAssistant/issues
- Documentation: See README_v3.md
- Email: admin@example.com

---

**Version:** 3.0.0  
**Last Updated:** November 12, 2025  
**Status:** ✅ Production Ready
