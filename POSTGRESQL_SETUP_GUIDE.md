# 🐘 PostgreSQL Setup Guide for Production

Since Railway's CLI no longer supports adding PostgreSQL directly, here are your options:

## Option 1: Railway Dashboard (Recommended)

1. **Go to Railway Dashboard**
   - Visit [railway.app](https://railway.app)
   - Open your AIAssistant project

2. **Add PostgreSQL Service**
   - Click "New Service"
   - Select "Database"
   - Choose "Add PostgreSQL"
   - Railway will provision it automatically

3. **Get Connection String**
   - Click on the PostgreSQL service
   - Go to "Connect" tab
   - Copy the `DATABASE_URL`

4. **Run Deployment**
   ```bash
   # Set the DATABASE_URL from Railway
   railway variables --set DATABASE_URL="<your-postgres-url-from-railway>"

   # Deploy
   railway up --detach
   ```

## Option 2: Supabase (Free Tier Available)

1. **Create Supabase Account**
   - Go to [supabase.com](https://supabase.com)
   - Create free project

2. **Get Database Credentials**
   - Settings → Database
   - Connection string → URI
   - Copy the connection string

3. **Configure Railway**
   ```bash
   # Set Supabase PostgreSQL URL
   railway variables --set DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"
   ```

## Option 3: Neon (Serverless PostgreSQL)

1. **Create Neon Account**
   - Go to [neon.tech](https://neon.tech)
   - Create free project

2. **Get Connection String**
   - Dashboard → Connection Details
   - Copy the connection string

3. **Configure Railway**
   ```bash
   railway variables --set DATABASE_URL="<neon-connection-string>"
   ```

## Option 4: Local Development First

For immediate testing, deploy with SQLite first:

```bash
# Deploy with SQLite
railway variables --set \
  DATABASE_URL="sqlite:///./data/production.db" \
  JWT_SECRET="$(openssl rand -hex 32)" \
  CSRF_SECRET="$(openssl rand -hex 32)" \
  ENVIRONMENT="production" \
  PYTHON_VERSION="3.11"

railway up --detach
```

---

## 🚀 Quick Deployment (After PostgreSQL Setup)

Once you have a PostgreSQL URL from any provider:

```bash
# 1. Set all production variables
railway variables --set \
  DATABASE_URL="your-postgresql-url" \
  JWT_SECRET="$(openssl rand -hex 32)" \
  CSRF_SECRET="$(openssl rand -hex 32)" \
  ENVIRONMENT="production" \
  PYTHON_VERSION="3.11" \
  HOST="0.0.0.0" \
  PORT="8000" \
  WORKERS="4" \
  RATE_LIMIT_PER_MINUTE="60" \
  ENABLE_OAUTH="true" \
  ENABLE_CSRF="true"

# 2. Add OAuth credentials (optional)
railway variables --set \
  GOOGLE_CLIENT_ID="your-google-client-id" \
  GOOGLE_CLIENT_SECRET="your-google-secret" \
  GITHUB_CLIENT_ID="your-github-client-id" \
  GITHUB_CLIENT_SECRET="your-github-secret"

# 3. Deploy
railway up --detach --service AIAssistant

# 4. Get your deployment URL
railway domain
```

---

## 📝 Migration Steps

After PostgreSQL is connected:

```bash
# 1. Test connection locally
export DATABASE_URL="your-postgresql-url"
python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('$DATABASE_URL'))"

# 2. Run migrations
python api/database/run_migrations.py

# 3. Verify tables
psql $DATABASE_URL -c "\dt"
```

---

## 🔧 Alternative: Use Existing Database

If you already have a PostgreSQL database elsewhere:

```bash
# Format: postgresql://user:password@host:port/database
railway variables --set DATABASE_URL="postgresql://user:password@your-host:5432/your-db"
```

---

## ✅ Verification

After deployment, test the security features:

```bash
# Get your Railway URL
DEPLOY_URL=$(railway domain | grep -o 'https://[^ ]*' | head -1)

# Test the deployment
python test_security_features.py $DEPLOY_URL
```

---

## 🎯 Next Steps

1. **Choose PostgreSQL Provider** (Railway Dashboard, Supabase, or Neon)
2. **Get DATABASE_URL**
3. **Set environment variables** using the commands above
4. **Deploy** with `railway up`
5. **Test** security features

Your application code is already configured for PostgreSQL with:
- ✅ Connection pooling
- ✅ Migrations
- ✅ OAuth support
- ✅ CSRF protection
- ✅ All security features

Just need to connect a PostgreSQL database!