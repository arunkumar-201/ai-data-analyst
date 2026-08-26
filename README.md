# AI Data Analyst

A full-stack AI-powered data analysis platform that allows users to upload CSV files, explore data quality, chat with their data using natural language, detect anomalies, generate visualizations, and export reports.

## Features

- **Multi-CSV Upload**: Drag-and-drop CSV files with validation and preview
- **Data Quality Dashboard**: Comprehensive profiling, validation, and quality scoring
- **Natural Language Chat**: Ask questions about your data in plain English
- **SQL/Pandas Code Generation**: LLM-powered query generation with execution
- **Interactive Visualizations**: Plotly charts (bar, line, scatter, histogram, pie, heatmap)
- **Anomaly Detection**: Z-score, IQR, and Isolation Forest methods with explanations
- **Conversation Memory**: Persistent chat sessions with context awareness
- **Export Capabilities**: CSV, Excel, JSON, PNG, HTML, PDF exports
- **Analysis Trace**: Full transparency into the analysis pipeline

## Tech Stack

### Frontend
- React 18 + TypeScript + Vite
- Tailwind CSS for styling
- Zustand for state management with localStorage persistence
- Plotly.js (react-plotly.js) for interactive charts
- Lucide React for icons
- Axios for API communication

### Backend
- FastAPI with async lifespan management
- DuckDB for analytical SQL queries
- Pandas for data manipulation
- OpenAI API for LLM integration (function calling)
- SciPy/Scikit-learn for anomaly detection
- Pydantic for validation

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- OpenAI API key

### Installation

1. **Clone and install dependencies**:
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

2. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

3. **Run the application**:

**Option A: Development mode (two terminals)**
```bash
# Terminal 1 - Backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

**Option B: Docker (production)**
```bash
docker-compose up --build
```

**Option C: Docker (development with hot reload)**
```bash
docker-compose --profile dev up --build
```

4. **Access the application**:
- Frontend: http://localhost:5173 (dev) or http://localhost:8000 (Docker)
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Project Structure

```
ai-data-analyst/
├── frontend/                 # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Page components (8 pages)
│   │   ├── services/        # API client
│   │   ├── stores/          # Zustand state management
│   │   └── types/           # TypeScript interfaces
│   └── package.json
├── backend/                  # FastAPI + Python
│   ├── api/                 # API route handlers
│   ├── agent/               # LLM agent orchestration
│   ├── data/                # Data loading, validation, profiling
│   ├── services/            # Core services (DuckDB, LLM, Memory, Export)
│   ├── tools/               # Tool implementations for LLM
│   └── utils/               # Utilities (errors, logging, security)
├── sample_data/             # Sample CSV datasets
├── data/                    # Runtime data (DuckDB, uploads)
├── exports/                 # Generated exports
├── requirements.txt         # Python dependencies
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## API Endpoints

### Upload
- `POST /api/upload` - Upload CSV files
- `POST /api/upload/preview` - Preview CSV without saving

### Datasets
- `GET /api/datasets` - List all datasets
- `GET /api/datasets/{id}` - Get dataset info
- `GET /api/datasets/{id}/preview` - Preview data
- `GET /api/datasets/{id}/schema` - Get schema
- `GET /api/datasets/{id}/profile` - Get data profile
- `DELETE /api/datasets/{id}` - Delete dataset

### Chat
- `POST /api/chat` - Send message to AI analyst
- `POST /api/sessions` - Create chat session
- `GET /api/sessions` - List sessions
- `GET /api/sessions/{id}` - Get session details
- `DELETE /api/sessions/{id}` - Delete session

### Anomalies
- `POST /api/anomalies/detect` - Detect univariate anomalies
- `POST /api/anomalies/multivariate` - Detect multivariate anomalies

### Charts
- `POST /api/charts/generate` - Generate chart from data
- `POST /api/charts/auto` - Auto-generate chart from dataset

### Quality
- `POST /api/quality/check` - Run quality checks
- `GET /api/quality/summary/{id}` - Get quality summary

### Export
- `POST /api/export/data` - Export dataset
- `POST /api/export/chart` - Export chart
- `POST /api/export/report` - Export session report

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `LLM_MODEL` | OpenAI model to use | `gpt-4o-mini` |
| `LLM_TEMPERATURE` | LLM temperature | `0.1` |
| `LLM_MAX_TOKENS` | Max tokens per request | `4096` |
| `LLM_REQUEST_TIMEOUT` | Request timeout (seconds) | `60` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:5173` |

## Usage Examples

### Chat with your data
```
"Show me total sales by region"
"What are the top 5 products by revenue?"
"Find anomalies in the profit column"
"Create a bar chart of sales by month"
"Compare average salary by department"
```

### Anomaly Detection
The system supports three methods:
- **Z-Score**: Statistical outliers beyond n standard deviations
- **IQR**: Interquartile range outliers
- **Isolation Forest**: ML-based anomaly detection

## Sample Data

The `sample_data/` directory includes:
- `sales_data.csv` - 50 rows of sales transactions
- `financial_transactions.csv` - 70 rows with fraud examples
- `employee_data.csv` - 40 rows of employee records

## Development

### Running Tests
```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend type checking
cd frontend
npx tsc --noEmit
```

### Code Quality
- TypeScript strict mode enabled
- ESLint + Prettier configured
- Python type hints throughout

## Security

- Read-only SQL validation (SELECT only)
- File type and size validation
- Path traversal prevention
- API keys never exposed to frontend
- CORS configured for specific origins

## License

MIT License - see LICENSE file for details.