# ☁️ CloudSense

> AI-powered AWS cost intelligence agent — monitor, query, and optimize your cloud spend in plain English.

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat-square&logo=react)
![AWS](https://img.shields.io/badge/AWS-Cost%20Explorer-FF9900?style=flat-square&logo=amazonaws)
![Gemini](https://img.shields.io/badge/Gemini-1.5%20Flash-4285F4?style=flat-square&logo=google)
![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-Jaeger-F5A800?style=flat-square)

CloudSense connects to your AWS account and lets you understand and control cloud costs through a dashboard and a natural language AI chat interface powered by Google Gemini (free tier).

**Ask it things like:**
- *"Why did my bill spike last week?"*
- *"Which service is costing the most right now?"*
- *"Are there any idle resources wasting money?"*
- *"What will my bill look like at end of month?"*

---

## Features

| Feature | Description |
|---|---|
| 💬 **AI chat** | Natural language queries over your live AWS cost data |
| 📊 **Cost dashboard** | Daily spend, service breakdown, anomaly detection |
| 🔍 **Idle resource scanner** | Unattached EBS volumes, unused Elastic IPs, stopped EC2s |
| 📈 **Forecasting** | Predict end-of-month spend from current trends |
| 📬 **Slack digest** | Daily AI-generated cost summary pushed to Slack |
| 🔭 **Distributed tracing** | Full OpenTelemetry instrumentation, Jaeger UI included |

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   CloudSense                    │
│                                                 │
│  ┌──────────┐   ┌────────────┐   ┌──────────┐  │
│  │  React   │──▶│  FastAPI   │──▶│   AWS    │  │
│  │ Frontend │   │  Backend   │   │   APIs   │  │
│  └──────────┘   └─────┬──────┘   └──────────┘  │
│                       │                         │
│                ┌──────▼──────┐                  │
│                │   Gemini    │                  │
│                │  AI Agent   │                  │
│                └─────┬───────┘                  │
│                      │                          │
│          ┌───────────┼───────────┐              │
│     ┌────▼────┐  ┌───▼───┐  ┌───▼───┐          │
│     │Postgres │  │Jaeger │  │ Slack │          │
│     │ (cache) │  │(trace)│  │ alerts│          │
│     └─────────┘  └───────┘  └───────┘          │
└─────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy, APScheduler |
| AI | Google Gemini 1.5 Flash (free tier) |
| Cloud data | AWS Cost Explorer API, EC2 API |
| Frontend | React 18, TypeScript, Recharts, TailwindCSS |
| Database | PostgreSQL |
| Observability | OpenTelemetry SDK, Jaeger |
| Notifications | Slack Webhooks |
| Infrastructure | Docker Compose |
| CI | GitHub Actions |

---

## Prerequisites

- Docker and Docker Compose
- An AWS account with Cost Explorer enabled
- A Google Gemini API key (free — see setup below)
- A read-only AWS IAM user (see setup below)

---

## Environment Setup

### 1. Get a Gemini API key (free)

1. Go to [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **Create API key**
4. Copy the key — you'll use it as `GEMINI_API_KEY`

Free tier: 1,500 requests/day, 1M tokens/minute. No credit card needed.

### 2. Create an AWS IAM user

CloudSense only needs **read-only** access. Create a dedicated IAM user:

1. Go to **IAM → Users → Create user** in the AWS Console
2. Attach the policy in `infra/iam-policy.json` directly, or use these managed policies:
   - `ReadOnlyAccess` (broad but simple for dev)
   - Or attach the custom policy below for least-privilege:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetCostForecast",
        "ce:GetDimensionValues",
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "ec2:DescribeAddresses",
        "ec2:DescribeRegions"
      ],
      "Resource": "*"
    }
  ]
}
```

3. Go to the user → **Security credentials → Create access key**
4. Choose **Application running outside AWS**
5. Copy the `Access key ID` and `Secret access key`

### 3. Enable AWS Cost Explorer

If this is a new AWS account, Cost Explorer may not be enabled:

1. Go to **Billing → Cost Explorer** in the AWS Console
2. Click **Enable Cost Explorer**
3. Wait up to 24 hours for data to populate (existing accounts have it immediately)

### 4. Configure environment

```bash
git clone https://github.com/yourusername/cloudsense.git
cd cloudsense
cp .env.example .env
```

Open `.env` and fill in your values:

```env
# AWS — read-only IAM user credentials
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1

# Gemini — free at aistudio.google.com
GEMINI_API_KEY=AIza...

# Slack — optional, for daily digest alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Observability
OTLP_ENDPOINT=http://localhost:4317
TRACING_ENABLED=true
```

---

## Running the Project

### With Docker (recommended)

```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend dashboard | http://localhost:3000 |
| Backend API + docs | http://localhost:8000/docs |
| Jaeger trace UI | http://localhost:16686 |

### Without Docker (local dev)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend** (separate terminal):
```bash
cd frontend
npm install
npm run dev
```

**Database** (requires PostgreSQL running locally):
```bash
# Update DATABASE_URL in .env to point to your local Postgres
# Tables are created automatically on first run
```

---

## Implementation Guide

The project is built across 5 phases, each corresponding to a set of commits. Work through them in order.

### Phase 1 — Project bootstrap

Set up the repo skeleton before writing any logic.

```bash
git checkout -b develop
```

**Commits:**
```
feat: initialise repo structure
# Files: .gitignore, .env.example, README.md

chore: add docker-compose and Dockerfiles
# Files: docker-compose.yml, backend/Dockerfile, frontend/Dockerfile

chore: add requirements.txt and package.json
# Files: backend/requirements.txt, frontend/package.json,
#         frontend/vite.config.ts, frontend/tailwind.config.js
```

---

### Phase 2 — AWS data layer

Build the services that talk to AWS before wiring any API routes.

**Commits:**
```
feat: add AWS Cost Explorer service
# Files: backend/app/services/aws_cost.py
#         backend/app/utils/config.py

feat: add idle resource scanner
# Files: backend/app/services/aws_resources.py

feat: add database models and IAM policy
# Files: backend/app/models/database.py
#         infra/iam-policy.json

test: unit tests for cost anomaly detection
# Files: backend/tests/test_cost_service.py
#         backend/tests/__init__.py
```

Run the tests before moving on:
```bash
cd backend && pytest tests/test_cost_service.py -v
```

---

### Phase 3 — API and AI agent

Wire the AWS services into FastAPI routes, then add the Gemini agent on top.

**Commits:**
```
feat: add FastAPI app with cost endpoints
# Files: backend/app/main.py, backend/app/api/costs.py,
#         backend/app/api/resources.py, backend/app/api/alerts.py,
#         backend/app/api/__init__.py, backend/app/__init__.py

feat: add Gemini AI agent with live AWS context
# Files: backend/app/agents/cost_agent.py
#         backend/app/agents/__init__.py

feat: add chat endpoint and conversation starters
# Files: backend/app/api/chat.py

feat: add Slack daily digest with APScheduler
# Files: backend/app/services/slack.py
```

Test the API is working before building the frontend:
```bash
uvicorn app.main:app --reload
# Visit http://localhost:8000/docs
# Try GET /api/costs/daily and POST /api/chat/
```

---

### Phase 4 — Frontend

Build the React UI one page at a time.

**Commits:**
```
feat: scaffold React app with routing and nav
# Files: frontend/index.html, frontend/src/main.tsx,
#         frontend/src/index.css, frontend/src/App.tsx,
#         frontend/src/utils/api.ts

feat: add dashboard page with cost charts
# Files: frontend/src/pages/Dashboard.tsx

feat: add AI chat page
# Files: frontend/src/pages/Chat.tsx

feat: add idle resources page
# Files: frontend/src/pages/Resources.tsx
```

---

### Phase 5 — Observability, CI/CD, and polish

Add tracing, automate the pipeline, and make it demo-ready.

**Commits:**
```
feat: add OpenTelemetry distributed tracing with Jaeger
# Files: backend/app/observability/tracer.py,
#         backend/app/observability/decorators.py,
#         backend/app/observability/__init__.py,
#         backend/app/agents/cost_agent.py (updated),
#         backend/app/services/aws_cost.py (updated),
#         backend/app/main.py (updated),
#         backend/tests/test_observability.py,
#         docker-compose.yml (updated — Jaeger service added)

ci: add GitHub Actions workflow
# Files: .github/workflows/ci.yml

docs: write README with architecture and setup guide
# Files: README.md (final update)

chore: add mock data mode for demo without AWS
# Files: backend/app/services/mock_data.py (new),
#         backend/app/services/aws_cost.py (updated),
#         backend/app/services/aws_resources.py (updated),
#         .env.example (add USE_MOCK_DATA=false)
```

Open a PR from `develop` → `main` after Phase 5. Let GitHub Actions pass, then merge.

---

## Viewing Traces

With Docker Compose running, open **http://localhost:16686**.

1. Select service: `cloudsense`
2. Click **Find Traces**
3. Click any trace to see the full span waterfall

A single AI chat request will show:
```
POST /api/chat/                        (FastAPI — auto)
  └── agent.gemini.chat                (manual span)
        └── agent.build_context        (manual span)
        │     └── aws.cost_explorer.*  (manual spans)
        └── httpx → Gemini API         (auto span)
```

---

## Project Structure

```
cloudsense/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/               # Route handlers
│   │   ├── agents/            # Gemini AI agent
│   │   ├── services/          # AWS + Slack business logic
│   │   ├── models/            # SQLAlchemy models
│   │   ├── observability/     # OTel tracer + decorators
│   │   └── utils/             # Config, helpers
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/             # Dashboard, Chat, Resources
│       └── utils/             # API client
├── infra/
│   └── iam-policy.json
├── .github/workflows/ci.yml
├── docker-compose.yml
└── .env.example
```

---

## Running Cost

| Component | Monthly cost |
|---|---|
| AWS Cost Explorer API | ~$0.01/day |
| Google Gemini API | **$0** (free tier) |
| Self-hosted (Docker) | **$0** |
| **Total** | **< $1/month** |

---

## Roadmap

- [ ] Tag-based cost attribution by team / environment
- [ ] Multi-account AWS Organizations support
- [ ] Azure Cost Management integration
- [ ] Terraform plan cost estimation with PR comments
- [ ] Kubernetes namespace chargebacks via OpenCost

---

## License

MIT
