# AI Data Analyst

> An AI-powered natural language data analysis platform that transforms CSV datasets into actionable insights using LLM-powered reasoning, SQL/Pandas analysis, interactive visualizations, anomaly detection, and data-quality intelligence.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-TypeScript-61DAFB?logo=react&logoColor=black)
![DuckDB](https://img.shields.io/badge/DuckDB-Analytics-FFF000?logo=duckdb&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-Frontend-646CFF?logo=vite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 🚀 Live Application

### 🌐 Frontend

**Live Application:**

https://ai-data-analyst-1-oj15.onrender.com

The frontend is deployed as a Render Static Site and communicates with the production FastAPI backend.

### ⚙️ Backend API

**Production Backend:**

https://ai-data-analyst-pre1.onrender.com

### ❤️ Health Check

https://ai-data-analyst-pre1.onrender.com/health

### 📚 Swagger API Documentation

https://ai-data-analyst-pre1.onrender.com/docs

### 📖 ReDoc API Documentation

https://ai-data-analyst-pre1.onrender.com/redoc

### 💻 GitHub Repository

https://github.com/arunkumar-201/ai-data-analyst

---

# 📌 Overview

**AI Data Analyst** is a full-stack AI application designed to allow users to analyze structured datasets using natural language.

Instead of manually writing SQL, Python, or Pandas operations, users can upload CSV files and ask questions such as:

- Which region generated the highest revenue?
- Show the monthly sales trend.
- What are the top five products?
- Which customers are underperforming?
- Generate SQL for this analysis.
- Detect anomalies in the dataset.
- Give me a summary of this dataset.
- What insights can you find from the data?

The application combines an LLM-powered reasoning layer with deterministic data-analysis tools to produce useful and explainable results.

---

# ✨ Key Features

## 1. CSV Upload & Dataset Management

- Upload CSV datasets through the web interface
- Support for multiple datasets
- CSV validation before processing
- Automatic dataset registration
- Dataset metadata and profiling
- Row and column statistics
- Dataset activation and management
- Dataset search and organization

---

## 2. Natural Language Data Analysis

Users can interact with datasets using conversational questions.

### Example

```text
Which region generated the highest revenue?

The system determines the appropriate analysis strategy and executes the required data operation.

3. LLM-Powered Data Analysis

The AI agent acts as an orchestration layer between the user and analysis tools.

The system can determine whether a request requires:

SQL
Pandas
Statistical analysis
Visualization
Anomaly detection
Data profiling
Data-quality analysis

This allows the application to go beyond simple chatbot responses.

4. SQL Generation & Execution

The platform can generate SQL queries based on natural-language questions.

Example
SELECT
    region,
    SUM(revenue) AS total_revenue
FROM sales
GROUP BY region
ORDER BY total_revenue DESC;

Generated queries can be displayed as part of the analysis trace.

5. Pandas Analysis

For operations better suited to Python/Pandas, the system can generate and execute Pandas-based analysis.

Example
df.groupby("region")["revenue"].sum().sort_values(ascending=False)

This provides flexibility for statistical and dataframe-oriented operations.

6. Interactive Visualizations

The application supports data visualization for analytical questions.

Supported visualization types include:

Bar charts
Line charts
Pie charts
Scatter plots
Other analytical visualizations

Charts are generated dynamically based on the dataset and user request.

7. Anomaly Detection

The platform provides anomaly detection capabilities for identifying unusual observations.

Supported approaches include:

Z-score analysis
IQR-based detection
Isolation Forest

Detected anomalies are presented with contextual explanations to help users understand why a record may have been flagged.

8. Data Quality Analysis

The application performs dataset-quality checks including:

Missing values
Column statistics
Data types
Duplicate records
Potential data inconsistencies
Dataset quality scoring

This helps users understand the reliability of their data before performing analysis.

9. Dataset Profiling

Each uploaded dataset can be profiled to provide information such as:

Number of rows
Number of columns
Column names
Data types
Missing values
Basic statistics
Dataset quality indicators
10. Conversation Context

The application maintains conversation context within a session.

Example
User:
What is the average revenue?

AI:
The average revenue is ₹82,450.

User:
Which region has the highest value?

AI:
The South region has the highest total revenue.

The second question can use the context established by the previous interaction.

11. Analysis Trace

The platform provides an analysis trace to make AI-assisted analysis more transparent.

The trace can expose stages such as:

User Question
      ↓
AI Agent
      ↓
Tool Selection
      ↓
SQL / Pandas Generation
      ↓
Tool Execution
      ↓
Results
      ↓
Explanation

This makes the system easier to understand and debug compared with a black-box chatbot.

12. Query Results

Analysis results can be displayed in structured tables.

Example
Region	Revenue
South	950000
West	820000
North	710000
East	640000
13. Reports & Exports

The application provides export capabilities for analytical results and reports.

Supported workflows include:

JSON exports
CSV exports
Analysis results
Data-quality information
Anomaly information
14. Chat History

Previous analysis sessions can be retained and restored.

Users can:

View previous conversations
Reopen sessions
Continue previous analysis
Navigate to specific sessions
Maintain dataset-related context
15. Dashboard

The dashboard provides a high-level overview of uploaded datasets.

Example metrics include:

Total Datasets
Total Rows
Total Columns
Total Data Size

The dashboard provides a quick entry point into the analytical workspace.

🏗️ Architecture

The application follows a modular full-stack architecture.

                         ┌─────────────────────────┐
                         │          User           │
                         └────────────┬────────────┘
                                      │
                                      ▼
                     ┌───────────────────────────────┐
                     │ React + TypeScript + Tailwind │
                     │           Frontend            │
                     └──────────────┬────────────────┘
                                    │ HTTP/REST
                                    ▼
                     ┌───────────────────────────────┐
                     │           FastAPI             │
                     │         Backend API           │
                     └──────────────┬────────────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ▼                  ▼                  ▼
        ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
        │ CSV Upload & │   │ Dataset      │   │ Conversation │
        │ Validation   │   │ Profiling    │   │ Memory       │
        └──────────────┘   └──────────────┘   └──────────────┘
                 │                  │
                 └──────────┬───────┘
                            ▼
                     ┌───────────────┐
                     │    DuckDB     │
                     │  Analytics DB │
                     └───────┬───────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ AI Agent /           │
                  │ Orchestration Layer  │
                  └──────────┬───────────┘
                             │
                             ▼
                     ┌───────────────┐
                     │      LLM      │
                     │ Gemini / LLM  │
                     └───────┬───────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Analysis Tool Layer  │
                  ├──────────────────────┤
                  │ SQL Analysis         │
                  │ Pandas Analysis      │
                  │ Visualization        │
                  │ Anomaly Detection    │
                  │ Data Profiling       │
                  │ Data Quality         │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Results + Explanation│
                  │ + Visualization      │
                  └──────────────────────┘
🧩 Architecture Components
Frontend

The frontend provides the user interface for:

Dataset upload
Dataset management
Natural-language chat
Data quality analysis
Anomaly detection
Visualizations
Reports
History
Settings

Technology:

React
TypeScript
Vite
Tailwind CSS
Axios
Plotly
Zustand
Backend

The backend provides:

REST APIs
Dataset management
CSV processing
DuckDB analytics
LLM integration
Agent orchestration
SQL execution
Pandas execution
Chart generation
Anomaly detection
Data quality analysis
Export functionality

Technology:

Python
FastAPI
Uvicorn
Pandas
DuckDB
Pydantic
AI Layer

The AI layer provides:

LLM-powered reasoning
Tool selection
Natural-language-to-SQL
Natural-language-to-Pandas
Analysis explanations
Conversation context
🛠️ Technology Stack
Frontend
React
TypeScript
Tailwind CSS
Vite
Plotly
Zustand
Axios
Backend
Python
FastAPI
Uvicorn
Pandas
DuckDB
Pydantic
AI
Gemini / LLM
LLM-powered agent
Tool/function orchestration
Natural-language-to-SQL
Natural-language-to-Pandas
Analysis explanations
Data & Analytics
DuckDB
Pandas
SQL
Statistical analysis
Anomaly detection
Data profiling
Data quality analysis
DevOps
Docker
Docker Compose
GitHub
Render
📁 Project Structure
AI DATA ANALYST/
│
├── backend/
│   ├── agent/
│   │   ├── prompts.py
│   │   ├── router.py
│   │   └── state.py
│   │
│   ├── api/
│   │   ├── anomalies.py
│   │   ├── charts.py
│   │   ├── chat.py
│   │   ├── datasets.py
│   │   ├── export.py
│   │   ├── quality.py
│   │   └── upload.py
│   │
│   ├── data/
│   │   ├── loader.py
│   │   ├── profiler.py
│   │   ├── registry.py
│   │   └── validator.py
│   │
│   ├── services/
│   │   ├── duckdb_service.py
│   │   ├── export_service.py
│   │   ├── llm_service.py
│   │   └── memory_service.py
│   │
│   ├── tools/
│   │   ├── anomaly_tool.py
│   │   ├── chart_tool.py
│   │   ├── pandas_tool.py
│   │   ├── profiling_tool.py
│   │   ├── quality_tool.py
│   │   └── sql_tool.py
│   │
│   ├── utils/
│   │   ├── errors.py
│   │   ├── json_response.py
│   │   ├── logger.py
│   │   └── security.py
│   │
│   ├── tests/
│   │   ├── test_anomalies.py
│   │   ├── test_chat.py
│   │   ├── test_profiling.py
│   │   ├── test_sql.py
│   │   ├── test_upload.py
│   │   └── test_validation.py
│   │
│   └── main.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AnalysisTrace.tsx
│   │   │   ├── AnomalyCard.tsx
│   │   │   ├── Chart.tsx
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── DatasetCard.tsx
│   │   │   ├── Layout.tsx
│   │   │   ├── QualityDashboard.tsx
│   │   │   ├── Table.tsx
│   │   │   └── UploadZone.tsx
│   │   │
│   │   ├── pages/
│   │   │   ├── Anomalies.tsx
│   │   │   ├── Chat.tsx
│   │   │   ├── Datasets.tsx
│   │   │   ├── History.tsx
│   │   │   ├── Home.tsx
│   │   │   ├── Quality.tsx
│   │   │   ├── Reports.tsx
│   │   │   └── Settings.tsx
│   │   │
│   │   ├── services/
│   │   │   └── api.ts
│   │   │
│   │   ├── stores/
│   │   │   └── useAppStore.ts
│   │   │
│   │   └── types/
│   │       └── index.ts
│   │
│   ├── package.json
│   ├── vite.config.ts
│   └── .env.production
│
├── sample_data/
│   ├── employee_data.csv
│   ├── financial_transactions.csv
│   └── sales_data.csv
│
├── data/
│
├── docs/
│   └── architecture.png
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
⚙️ Getting Started
Prerequisites

Make sure the following are installed:

Python 3.11+
Node.js 18+
npm
Git
Docker (optional)
💻 Local Development
1. Clone the Repository
git clone https://github.com/arunkumar-201/ai-data-analyst.git
cd ai-data-analyst
2. Backend Setup

Create a Python virtual environment.

Windows
python -m venv .venv
.venv\Scripts\activate
Linux / macOS
python3 -m venv .venv
source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt
3. Configure Environment Variables

Create a .env file in the project root.

Example:

GEMINI_API_KEY=your_gemini_api_key_here

LLM_MODEL=gemini-2.5-flash
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4096
LLM_REQUEST_TIMEOUT=60

CORS_ORIGINS=http://localhost:5173,http://localhost:3000

Never commit API keys or .env files to GitHub.

4. Start the Backend

From the project root:

uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

Backend:

http://localhost:8000

Health check:

http://localhost:8000/health

Swagger:

http://localhost:8000/docs

ReDoc:

http://localhost:8000/redoc
5. Start the Frontend

Open another terminal:

cd frontend
npm install
npm run dev

Frontend:

http://localhost:5173
🌍 Production Frontend Configuration

The production frontend uses the deployed FastAPI backend.

Create:

frontend/.env.production

Add:

VITE_API_URL=https://ai-data-analyst-pre1.onrender.com

The frontend API service uses the production backend URL for deployed requests.

After changing the production environment configuration:

cd frontend
npm run build
🐳 Docker Deployment

The project includes Docker support for reproducible deployment.

Build and start the application:

docker compose up --build

Run in detached mode:

docker compose up -d --build

Stop the application:

docker compose down

View logs:

docker compose logs -f
☁️ Render Deployment

The application is deployed using Render.

The deployment consists of:

                         Internet
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
       Render Static Site           Render Web Service
              │                           │
              ▼                           ▼
        React Frontend              FastAPI Backend
              │                           │
              └─────────────┬─────────────┘
                            │
                            ▼
                         DuckDB
                            │
                            ▼
                      Gemini / LLM
Frontend Deployment

The frontend is deployed as a Render Static Site.

Production URL:

https://ai-data-analyst-1-oj15.onrender.com

Typical Render configuration:

Root Directory:
frontend

Build Command:
npm install && npm run build

Publish Directory:
frontend/dist

Depending on the Render configuration, the root directory can be set to frontend, in which case:

Build Command:
npm install && npm run build

Publish Directory:
dist

Production environment variable:

VITE_API_URL=https://ai-data-analyst-pre1.onrender.com
Backend Deployment

The backend is deployed as a Render Web Service.

Production URL:

https://ai-data-analyst-pre1.onrender.com

Health endpoint:

https://ai-data-analyst-pre1.onrender.com/health

Swagger:

https://ai-data-analyst-pre1.onrender.com/docs

ReDoc:

https://ai-data-analyst-pre1.onrender.com/redoc

The backend runs on the Render-provided port.

The application binds to:

0.0.0.0

and supports the Render PORT environment variable when configured by the deployment environment.

🔌 API Overview

The FastAPI backend exposes APIs for the main application workflows.

Health
GET /health
Datasets
GET    /api/datasets
GET    /api/datasets/{id}
GET    /api/datasets/{id}/profile
GET    /api/datasets/{id}/quality
GET    /api/datasets/{id}/preview
GET    /api/datasets/{id}/schema
DELETE /api/datasets/{id}
GET    /api/schema
Upload
POST /api/upload
POST /api/upload/preview
Chat
POST   /api/chat
POST   /api/sessions
GET    /api/sessions
GET    /api/sessions/{id}
GET    /api/sessions/{id}/history
DELETE /api/sessions/{id}
Charts
POST /api/charts/generate
POST /api/charts/auto
GET  /api/charts/types
Anomalies
POST /api/anomalies/detect
POST /api/anomalies/detect-multivariate
GET  /api/anomalies/methods
Quality
GET /api/quality/{dataset_id}
GET /api/quality/{dataset_id}/summary
Export
POST /api/export/data
POST /api/export/chart
POST /api/export/report
GET  /api/export/formats
📚 API Documentation

Once the backend is running, FastAPI automatically provides API documentation.

Local Swagger
http://localhost:8000/docs
Production Swagger

https://ai-data-analyst-pre1.onrender.com/docs

Local ReDoc
http://localhost:8000/redoc
Production ReDoc

https://ai-data-analyst-pre1.onrender.com/redoc

🔄 Example Workflow

A typical user workflow looks like this:

1. Upload CSV
       ↓
2. Validate Dataset
       ↓
3. Profile Dataset
       ↓
4. Store Dataset in DuckDB
       ↓
5. Ask Natural Language Question
       ↓
6. AI Agent Determines Required Tool
       ↓
7. Generate SQL / Pandas
       ↓
8. Execute Analysis
       ↓
9. Generate Results
       ↓
10. Generate Explanation
       ↓
11. Display Table / Chart / Insight
💬 Example Questions

The following questions can be used to demonstrate the application.

Dataset Summary
Give me a summary of this dataset.
Aggregation
Which region generated the highest revenue?
Ranking
Show me the top five customers by revenue.
Trend Analysis
Show monthly sales trends.
Product Analysis
Which products are underperforming?
SQL Generation
Generate SQL for the top five customers.
Anomaly Detection
Detect anomalies in the dataset and explain why they were flagged.
Data Quality
What are the major data quality issues in this dataset?
🧪 Testing

The backend includes automated tests covering important application components.

Run the complete test suite:

pytest

Run with verbose output:

pytest -v

Example validation result:

85 passed

The project also validates API responses to ensure non-finite floating-point values such as:

NaN
Infinity
-Infinity

do not break JSON serialization.

These values are safely sanitized before being returned through the API.

🔍 Validation

The application has been validated through backend and frontend checks.

Current validation includes:

Backend automated tests
Frontend TypeScript diagnostics
Frontend production build
CSV upload smoke tests
Dataset API smoke tests
JSON serialization validation
Health endpoint validation

Example backend validation:

85 passed

Frontend production build:

cd frontend
npm run build

Expected output:

vite building for production...
modules transformed
dist/index.html
dist/assets/...
🛡️ Error Handling

The application includes defensive handling for common failure scenarios including:

Invalid CSV files
Empty datasets
Unsupported data formats
Missing columns
Invalid analysis requests
LLM failures
Tool execution failures
Invalid generated SQL
Dataset-not-found errors
JSON serialization issues
Backend API failures

The frontend surfaces errors to the user rather than silently failing.

🔐 Security Considerations

The project follows basic security practices for an AI-enabled data application.

API Keys

API credentials are stored through environment variables.

Never commit:

.env

or API keys to the repository.

Generated Code

LLM-generated SQL and Pandas operations should be treated as untrusted input and validated before execution.

Data Isolation

Uploaded datasets are processed through the backend data layer and associated with application-level dataset/session state.

CORS

The backend supports configurable CORS origins through:

CORS_ORIGINS=http://localhost:5173

For production, configure the allowed frontend origin appropriately.

📊 Data Processing

The application uses DuckDB and Pandas for deterministic data processing.

The LLM is primarily responsible for:

Natural Language
      ↓
Reasoning
      ↓
Tool Selection
      ↓
SQL / Pandas Plan

The actual computation is handled by analytical tools.

SQL Tool
Pandas Tool
Chart Tool
Anomaly Tool
Profiling Tool
Quality Tool

This approach reduces the risk of relying on the LLM to perform numerical calculations directly.

🤖 AI Agent

The AI agent acts as the orchestration layer.

The general flow is:

User Question
      ↓
Agent Router
      ↓
Understand Intent
      ↓
Select Tool
      ↓
Execute Tool
      ↓
Validate Result
      ↓
Generate Explanation
      ↓
Return Response

Available tools include:

SQL Tool
Pandas Tool
Chart Tool
Anomaly Tool
Profiling Tool
Quality Tool
🧠 Deterministic Analysis

The system separates AI reasoning from deterministic computation.

For example:

User:
Which region generated the highest revenue?

The AI can determine that an aggregation is required.

It can generate:

SELECT
    region,
    SUM(revenue) AS total_revenue
FROM sales
GROUP BY region
ORDER BY total_revenue DESC;

DuckDB then executes the actual query.

The result is returned to the AI layer for explanation.

This architecture provides a better balance between:

AI reasoning
Data accuracy
Explainability
Reproducibility
📈 Anomaly Detection

The application supports multiple anomaly-detection approaches.

Z-Score

Useful for identifying values that are statistically far from the mean.

IQR

Uses the interquartile range to identify statistical outliers.

Isolation Forest

Useful for detecting anomalies using machine-learning-based isolation.

🧹 Data Quality

The quality analysis module evaluates datasets for issues such as:

Missing Values
      ↓
Duplicate Records
      ↓
Data Types
      ↓
Column Statistics
      ↓
Potential Inconsistencies
      ↓
Quality Score
📊 Dataset Profiling

Dataset profiling provides information such as:

Dataset dimensions
Column names
Data types
Missing values
Numerical statistics
Categorical information
Quality indicators
📦 Sample Datasets

Sample datasets are included in:

sample_data/

Available examples include:

employee_data.csv
financial_transactions.csv
sales_data.csv

These datasets can be used to demonstrate:

Aggregation
Filtering
Ranking
Trend analysis
Anomaly detection
Data profiling
Data quality analysis
Visualization
🖼️ Screenshots

Application screenshots can be stored in:

docs/screenshots/

Recommended screenshots:

docs/screenshots/dashboard.png
docs/screenshots/datasets.png
docs/screenshots/chat.png
docs/screenshots/analysis.png
docs/screenshots/anomalies.png
docs/screenshots/data-quality.png
Dashboard

Natural Language Analysis

Dataset Management

Anomaly Detection

🎥 Demo

A short demonstration should showcase the core workflow:

CSV Upload
    ↓
Dataset Selection
    ↓
Natural Language Question
    ↓
AI Analysis
    ↓
Generated Result
    ↓
Visualization / Anomaly Detection
Live Demo

https://ai-data-analyst-1-oj15.onrender.com

🚀 Production Deployment
Frontend
Platform: Render Static Site

URL:
https://ai-data-analyst-1-oj15.onrender.com
Backend
Platform: Render Web Service

URL:
https://ai-data-analyst-pre1.onrender.com
Backend Health
https://ai-data-analyst-pre1.onrender.com/health
Swagger
https://ai-data-analyst-pre1.onrender.com/docs
ReDoc
https://ai-data-analyst-pre1.onrender.com/redoc
🏛️ Deployment Architecture
                    ┌─────────────────────┐
                    │       User          │
                    └──────────┬──────────┘
                               │
                               ▼
              ┌────────────────────────────┐
              │     Render Static Site     │
              │      React Frontend        │
              └──────────────┬─────────────┘
                             │
                             │ HTTPS / REST API
                             ▼
              ┌────────────────────────────┐
              │     Render Web Service     │
              │       FastAPI Backend      │
              └──────────────┬─────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
          ┌────────┐    ┌──────────┐   ┌─────────┐
          │ DuckDB │    │ AI Agent │   │ Pandas  │
          └────────┘    └────┬─────┘   └─────────┘
                             │
                             ▼
                       ┌───────────┐
                       │ Gemini /  │
                       │    LLM    │
                       └───────────┘
🧰 Development Commands
Backend

Create environment:

python -m venv .venv

Activate on Windows:

.venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Run backend:

uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

Run tests:

pytest -v
Frontend

Install dependencies:

cd frontend
npm install

Development server:

npm run dev

Production build:

npm run build

Preview production build:

npm run preview
🐳 Docker Commands

Build:

docker compose build

Start:

docker compose up

Start in background:

docker compose up -d

Rebuild:

docker compose up --build

Stop:

docker compose down

Logs:

docker compose logs -f
🧱 Design Principles
Modular Architecture

Responsibilities are separated into:

API layer
Agent layer
Data layer
Service layer
Tool layer
Frontend components
Tool-Based AI

The LLM does not need to perform all analytical operations itself.

Instead, it can select specialized tools such as:

SQL Tool
Pandas Tool
Chart Tool
Anomaly Tool
Profiling Tool
Quality Tool

This improves reliability and makes the system easier to extend.

Deterministic Data Processing

Actual dataset calculations are delegated to analytical engines such as:

DuckDB
Pandas

rather than relying on the LLM to calculate everything directly.

Explainability

The application exposes analysis steps and generated operations where appropriate so users can understand how an answer was produced.

Extensibility

The architecture allows additional capabilities to be added without rewriting the entire application.

🔮 Future Extensions

Potential future extensions include:

Multi-file joins
Forecasting
Authentication
Role-based access control
Cloud object storage
Redis caching
Streaming responses
Advanced statistical analysis
Semantic search
RAG pipelines
Agent evaluation
Scheduled reports
Email/Slack notifications
Production observability
Kubernetes deployment
⚠️ Known Limitations

The current implementation is primarily designed as an AI data-analysis demonstration and can be extended further for enterprise-scale deployment.

Potential production improvements include:

Persistent cloud database
Object storage for large datasets
Authentication and authorization
Stronger sandboxing for generated code
Distributed task processing
Rate limiting
Advanced monitoring
Automated LLM evaluation
Multi-user data isolation
📋 Project Validation

The application has been validated through backend and frontend checks.

Current validation includes:

Backend automated tests
Frontend TypeScript diagnostics
Frontend production build
CSV upload smoke tests
Dataset API smoke tests
JSON serialization validation
Health endpoint validation

Example:

Backend Tests: 85 passed
Frontend Build: Successful
CSV Upload Smoke Test: Successful
Dataset API Smoke Test: Successful
Health Endpoint: Successful
💡 Engineering Highlights

This project demonstrates practical implementation of an AI-powered application rather than simply connecting an LLM API.

Key engineering areas include:

Full-stack application architecture
REST API development
LLM orchestration
Tool-based AI workflows
SQL generation
Pandas-based analysis
Data visualization
Statistical anomaly detection
Data profiling
Data quality analysis
Dataset lifecycle management
Conversation memory
Error handling
JSON serialization safety
Automated testing
Docker containerization
Render deployment
🗺️ Future Roadmap
Phase 1 — Core Analytics
CSV upload
Dataset validation
Dataset profiling
Natural language analysis
SQL analysis
Pandas analysis
Visualization
Anomaly detection
Phase 2 — AI Intelligence
AI agent orchestration
Tool selection
Analysis trace
Conversation context
Result explanations
Phase 3 — Production Readiness
Automated testing
Error handling
Docker support
Export functionality
Authentication
Cloud object storage
Distributed processing
Advanced observability
Phase 4 — Advanced Analytics
Forecasting
Multi-dataset joins
Semantic search
RAG
Automated dashboards
Scheduled reports
Advanced agent evaluation
🤝 Contributing

Contributions are welcome.

1. Clone the Repository
git clone https://github.com/arunkumar-201/ai-data-analyst.git
cd ai-data-analyst
2. Create a Feature Branch
git checkout -b feature/your-feature
3. Make Your Changes
git add .
4. Commit
git commit -m "Add your feature"
5. Push
git push origin feature/your-feature

Then open a Pull Request.

🔗 Important Links
Resource	Link
🌐 Live Application	https://ai-data-analyst-1-oj15.onrender.com
⚙️ Backend API	https://ai-data-analyst-pre1.onrender.com
❤️ Health Check	https://ai-data-analyst-pre1.onrender.com/health
📚 Swagger	https://ai-data-analyst-pre1.onrender.com/docs
📖 ReDoc	https://ai-data-analyst-pre1.onrender.com/redoc
💻 GitHub	https://github.com/arunkumar-201/ai-data-analyst
👤 GitHub Profile	https://github.com/arunkumar-201
📄 License

This project is licensed under the MIT License.

See the LICENSE file for details.
👨‍💻 Author
Arun Kumar Danda

AI Data Analyst — Full-Stack AI Data Analysis Platform

GitHub

https://github.com/arunkumar-201

Repository

https://github.com/arunkumar-201/ai-data-analyst
