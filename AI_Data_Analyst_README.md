AI Data Analyst

An AI-powered data analysis platform that allows users to upload one or
more CSV files and interact with their data using natural language.

The application combines LLM reasoning, Pandas, DuckDB, Plotly,
anomaly detection, data-quality checks, conversation memory, SQL
generation, and explainable analysis into a production-style workflow.

1. Project Goal

The goal is to build an AI Data Analyst that behaves like a data analyst
rather than a simple chatbot.

A user should be able to:

Upload one or more CSV files.

Automatically validate and profile the data.

Ask questions in natural language.

Let the AI determine the appropriate analysis.

Execute real Pandas or SQL operations against the uploaded data.

Generate charts automatically.

Detect and explain anomalies.

Generate SQL and/or Pandas code.

Maintain context across follow-up questions.

Explain the evidence and analysis steps used to produce the answer.

Export results and reports.

Review data-quality problems.

Use multiple datasets together when appropriate.

2. Complete User Workflow

                    USER
                      |
                      v
              +---------------+
              |   Web UI       |
              | Streamlit      |
              +-------+-------+
                      |
             Upload CSV / Ask Question
                      |
                      v
              +---------------+
              | FastAPI API    |
              +-------+-------+
                      |
        +-------------+-------------+
        |                           |
        v                           v
  Data Ingestion              Conversation
        |                       Context
        v                           |
  Validation & Profiling            |
        |                           |
        +-------------+-------------+
                      |
                      v
              +---------------+
              | AI Agent       |
              | Intent Router  |
              +-------+-------+
                      |
       +--------------+------------------+
       |         |          |            |
       v         v          v            v
    Pandas    DuckDB      Chart       Anomaly
     Tool      Tool       Tool          Tool
       |         |          |            |
       +---------+----------+------------+
                      |
                      v
              Actual Results
                      |
                      v
              +---------------+
              | Response LLM  |
              +-------+-------+
                      |
       +--------------+----------------+
       |              |                |
       v              v                v
    Answer          Chart          Analysis Trace
       |              |                |
       +--------------+----------------+
                      |
                      v
             Conversation Memory

3. Core Features

3.1 CSV Upload

The application supports:

Single CSV upload.

Multiple CSV uploads.

Drag-and-drop upload.

File extension validation.

File-size validation.

Empty-file validation.

Encoding handling.

Header validation.

Duplicate-column detection.

Automatic data-type inference.

Date-column detection.

Numeric-column detection.

Categorical-column detection.

Example:

Uploaded Files

sales_2025.csv       12.4 MB
customers.csv         4.7 MB
products.csv          2.1 MB

4. Data Validation

Every uploaded dataset passes through a validation pipeline.

CSV
 |
 v
File Validation
 |
 v
Schema Validation
 |
 v
Column Validation
 |
 v
Data Type Detection
 |
 v
Missing Value Analysis
 |
 v
Duplicate Detection
 |
 v
Data Quality Report

Validation checks include:

Empty rows.

Empty columns.

Duplicate column names.

Missing values.

Duplicate records.

Invalid numeric values.

Invalid dates.

Inconsistent data types.

Extremely high-cardinality columns.

Constant columns.

Potential identifier columns.

Suspicious outliers.

5. Data Profiling

After upload, the UI should display:

Dataset Overview

Rows:             125,430
Columns:              18
Missing Values:     1.82%
Duplicate Rows:       243
Numeric Columns:        7
Categorical Columns:   8
Date Columns:           3

For every column:

Column       Type        Missing     Unique
------------------------------------------------
order_id     integer       0%        125430
order_date   datetime      0%          812
region       string        0%            5
product      string      0.05%         124
sales        float        0.12%      54231
quantity     integer       0%            41

The profiling engine should calculate:

Mean.

Median.

Minimum.

Maximum.

Standard deviation.

Quantiles.

Unique count.

Missing percentage.

Duplicate count.

Cardinality.

Basic distributions.

6. Multi-File Analysis

Multiple files should be registered as separate logical tables.

Example:

sales.csv       -> sales
customers.csv   -> customers
products.csv    -> products

DuckDB can query them together.

Example question:

Which customer segment generated the highest revenue?

The agent can determine that sales needs to be joined with
customers.

Example:

SELECT
    c.segment,
    SUM(s.revenue) AS total_revenue
FROM sales s
JOIN customers c
    ON s.customer_id = c.customer_id
GROUP BY c.segment
ORDER BY total_revenue DESC;

7. Natural Language Question Answering

The user can ask questions such as:

Which region generated the highest revenue?

Show monthly sales trends.

Which products are underperforming?

What are the top five customers?

What is the average order value?

Which month had the highest sales?

Compare sales between regions.

What percentage of revenue comes from the top 10 customers?

The system should never rely on the LLM to invent numerical results.

Instead:

Question
   |
   v
Intent Detection
   |
   v
Tool Selection
   |
   v
Real Data Execution
   |
   v
Actual Result
   |
   v
LLM Explanation

8. AI Agent / Reasoning Layer

The AI agent is responsible for selecting the correct operation.

Possible intents:

AGGREGATION
FILTERING
GROUPING
COMPARISON
TREND_ANALYSIS
DISTRIBUTION
CORRELATION
ANOMALY_DETECTION
DATA_QUALITY
SQL_GENERATION
PANDAS_GENERATION
VISUALIZATION
SUMMARY

Example:

User:
Which region generated the highest revenue?

Agent:
Intent = GROUP_BY_AGGREGATION
Tool = SQL/Pandas
Visualization = Bar Chart

9. Tool Calling

The agent should have controlled tools.

Recommended tools:

profile_dataset()
execute_sql()
execute_pandas()
generate_chart()
detect_anomalies()
run_data_quality_check()
generate_summary()
export_result()

Every tool should have:

Input validation.

Error handling.

Execution timeout where applicable.

Structured output.

Logging.

Clear error messages.

10. DuckDB SQL Engine

DuckDB is used for analytical SQL queries.

Advantages:

Fast analytical queries.

Works directly with data files.

Supports joins and aggregations.

Familiar SQL interface.

Easy local deployment.

Good fit for CSV analytics.

Example:

SELECT
    region,
    SUM(revenue) AS total_revenue
FROM sales
GROUP BY region
ORDER BY total_revenue DESC;

The result is returned as a DataFrame.

11. Pandas Analysis Engine

Pandas is used when Python-based analysis is more appropriate.

Example:

result = (
    df.groupby("region")["revenue"]
      .sum()
      .sort_values(ascending=False)
)

The application should show generated Pandas code when requested.

12. SQL Generation

The user can ask:

Generate SQL for this analysis.

The system should return the SQL used or generated for the analysis.

Example:

SELECT
    region,
    SUM(revenue) AS total_revenue
FROM sales
GROUP BY region
ORDER BY total_revenue DESC
LIMIT 5;

Recommended workflow:

Generate SQL
     |
     v
Validate SQL
     |
     v
Execute SQL
     |
     v
Compare Result
     |
     v
Return Answer

The system should not execute arbitrary destructive SQL.

Only read-only analytical operations should be allowed.

13. Visualization Engine

Charts should be generated automatically based on the result and
question.

Supported charts:

Bar.

Horizontal Bar.

Line.

Area.

Pie.

Scatter.

Histogram.

Box Plot.

Heatmap.

Chart selection rules:

Date + Numeric
    -> Line

Category + Numeric
    -> Bar

Two Numeric Columns
    -> Scatter

Single Numeric Column
    -> Histogram

Part-to-Whole
    -> Pie

Numeric Distribution
    -> Box Plot

Multiple Numeric Features
    -> Heatmap

Charts should be interactive using Plotly.

14. Example Visualization Workflow

User:

Show monthly sales trends.

System:

Detect date column
        |
        v
Detect sales column
        |
        v
Group by month
        |
        v
SUM(sales)
        |
        v
Plotly Line Chart

Result:

Monthly Sales

Jan   ███████
Feb   █████████
Mar   ███████████
Apr   █████████████
...

The UI should show:

Chart.

Chart title.

X-axis.

Y-axis.

Data table.

SQL.

Pandas code.

Explanation.

15. Anomaly Detection

Anomaly detection should be performed using actual statistical or ML
methods.

Recommended methods:

Z-Score

z = (x - mean) / standard_deviation

Default threshold:

|z| > 3

IQR

IQR = Q3 - Q1

Lower Bound = Q1 - 1.5 * IQR
Upper Bound = Q3 + 1.5 * IQR

Isolation Forest

For multi-dimensional anomaly detection.

The user can select:

Method:
- Z-Score
- IQR
- Isolation Forest

16. Anomaly Explanation

Do not only show:

Anomaly detected.

Explain why.

Example:

Anomaly #1

Date: 2026-03-17
Region: West
Revenue: $187,200

Reason:
Revenue is 4.21 standard deviations above
the normal daily revenue level.

Expected range:
$32,000 - $71,000

Severity:
High

The explanation is generated from actual statistical results.

17. Data Quality Dashboard

The Data Quality page should show:

Completeness     98.18%
Validity         99.23%
Consistency      97.91%
Uniqueness       99.61%

Checks:

Missing values.

Duplicate records.

Invalid dates.

Invalid numeric values.

Duplicate IDs.

Constant columns.

High-cardinality columns.

Unexpected data types.

Each problem should include:

Column
Issue
Count
Percentage
Severity
Recommendation

18. Conversation Memory

The system should remember the current session.

Example:

User:
Which region generated the highest revenue?

AI:
West generated the highest revenue.

User:
Show its monthly trend.

AI:
Here is the monthly trend for West.

The system resolves:

"its" -> "West"

Conversation state should contain:

{
    "dataset": "sales",
    "last_intent": "aggregation",
    "last_result": "...",
    "entities": {
        "region": "West"
    }
}

19. Analysis Trace

Instead of exposing private chain-of-thought, show a concise auditable
trace.

Example:

Analysis Trace

1. Question
   Which region generated the highest revenue?

2. Dataset
   sales.csv

3. Detected operation
   Group by region and sum revenue

4. Execution
   DuckDB

5. Query
   SELECT region, SUM(revenue)
   FROM sales
   GROUP BY region

6. Result
   West = $2.43M

7. Visualization
   Bar chart

This gives the user transparency without exposing hidden model
reasoning.

20. Dashboard / Home Page

The dashboard should contain:

AI Data Analyst

+ Upload CSV

Recent Datasets
-------------------------
sales.csv
customers.csv
products.csv

Quick Actions
-------------------------
Ask a Question
Data Quality
Detect Anomalies
Generate Dashboard

21. Uploaded Files Page

Display:

Uploaded Files

sales_2026.csv
Rows: 125,430
Columns: 18
Quality: 98.2%

customers.csv
Rows: 21,432
Columns: 9
Quality: 99.1%

Actions:

Preview
Profile
Analyze
Delete
Download

22. Chat / Ask Question Page

Layout:

+----------------------------------------------------+
| AI Data Analyst                                    |
+----------------------------------------------------+
|                                                    |
| User: Which region has the highest revenue?        |
|                                                    |
| AI: West generated the highest revenue.            |
|                                                    |
| [Bar Chart]                                        |
|                                                    |
| Explanation                                        |
| West generated $2.43M, which is ...                |
|                                                    |
| Analysis Trace                                    |
| GROUP BY region -> SUM(revenue)                    |
|                                                    |
+----------------------------------------------------+
| Ask a question about your data...           [Send] |
+----------------------------------------------------+

23. Answer Page

Each answer can contain:

Answer
Chart
Key Metrics
Explanation
SQL Query
Pandas Code
Analysis Trace
Download

Example:

The West region generated the highest revenue.

Revenue:
$2.43M

Compared with:
East: $2.05M
Central: $1.72M
South: $1.41M
North: $1.22M

24. Conversation History

Store previous questions.

Example:

Conversation History

Which region generated the highest revenue?
Today, 10:30 AM

Show monthly sales trends.
Today, 10:32 AM

Which products are underperforming?
Today, 10:35 AM

Detect anomalies in the dataset.
Today, 10:36 AM

Users can reopen a conversation.

25. Export

Allow users to export:

CSV results.

Excel results.

PNG charts.

HTML charts.

PDF report.

Analysis summary.

A report can contain:

Dataset Summary
Questions Asked
Answers
Charts
SQL
Pandas Code
Anomalies
Data Quality
Recommendations

26. Error Handling

Errors should be user-friendly.

Bad:

KeyError: 'revenue'

Good:

I couldn't find a column related to revenue.

Available numeric columns:
sales
profit
quantity
discount

Other errors:

Unsupported file type.
CSV contains no rows.
Unable to detect a valid header.
Query could not be executed.
The requested column does not exist.
There is not enough data for anomaly detection.

27. Security

The application should:

Validate uploaded file types.

Restrict maximum file size.

Sanitize file names.

Never execute arbitrary shell commands.

Restrict generated SQL to read-only operations.

Avoid arbitrary Python execution.

Keep API keys in environment variables.

Never expose API keys in frontend code.

Validate LLM-generated tool arguments.

Add execution timeouts.

Log security-relevant errors.

28. LLM Prompt Strategy

The LLM should receive metadata rather than blindly receiving the entire
CSV.

Example metadata:

Dataset: sales

Columns:
- order_date: datetime
- region: categorical
- product: categorical
- quantity: integer
- revenue: float

Rows: 125430

The agent then decides which tool to call.

For large datasets:

User Question
     |
     v
Schema/Metadata
     |
     v
Tool Selection
     |
     v
Database/Pandas
     |
     v
Small Result
     |
     v
LLM Explanation

This reduces token usage and improves reliability.

29. Recommended Backend API

Upload

POST /api/upload

List datasets

GET /api/datasets

Dataset profile

GET /api/datasets/{dataset_id}/profile

Ask question

POST /api/chat

Example:

{
  "dataset_id": "sales",
  "message": "Which region generated the highest revenue?"
}

Generate chart

POST /api/chart

Detect anomalies

POST /api/anomalies

Data quality

GET /api/datasets/{dataset_id}/quality

Conversation history

GET /api/conversations

Export

POST /api/export

30. Recommended Project Structure

ai-data-analyst/
│
├── backend/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── upload.py
│   │   ├── chat.py
│   │   ├── datasets.py
│   │   ├── anomalies.py
│   │   ├── charts.py
│   │   └── export.py
│   │
│   ├── agent/
│   │   ├── router.py
│   │   ├── state.py
│   │   ├── prompts.py
│   │   └── planner.py
│   │
│   ├── tools/
│   │   ├── pandas_tool.py
│   │   ├── sql_tool.py
│   │   ├── chart_tool.py
│   │   ├── anomaly_tool.py
│   │   ├── quality_tool.py
│   │   └── profiling_tool.py
│   │
│   ├── data/
│   │   ├── loader.py
│   │   ├── validator.py
│   │   ├── profiler.py
│   │   └── registry.py
│   │
│   ├── services/
│   │   ├── llm.py
│   │   ├── memory.py
│   │   ├── duckdb.py
│   │   └── export.py
│   │
│   ├── models/
│   │   ├── requests.py
│   │   └── responses.py
│   │
│   └── utils/
│       ├── logger.py
│       ├── errors.py
│       └── security.py
│
├── frontend/
│   ├── app.py
│   ├── pages/
│   │   ├── home.py
│   │   ├── datasets.py
│   │   ├── chat.py
│   │   ├── quality.py
│   │   ├── anomalies.py
│   │   └── history.py
│   │
│   └── components/
│       ├── charts.py
│       ├── tables.py
│       ├── sidebar.py
│       └── analysis_trace.py
│
├── data/
│   └── sample_sales.csv
│
├── tests/
│   ├── test_upload.py
│   ├── test_validation.py
│   ├── test_profiling.py
│   ├── test_sql.py
│   ├── test_anomalies.py
│   └── test_chat.py
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── README.md
└── .gitignore

31. Technology Stack

Layer                      Technology

Frontend                   Streamlit
Backend                    FastAPI
Data Processing            Pandas
SQL Analytics              DuckDB
Visualization              Plotly
LLM                        OpenAI API
Agent                      LangGraph or custom tool router
Anomaly Detection          Scikit-learn / SciPy
Validation                 Pandera / custom validation
Testing                    Pytest
Containerization           Docker
Logging                    Python logging
Storage                    SQLite / DuckDB
Optional Semantic Search   FAISS

32. Testing Strategy

Tests should cover:

Upload

valid CSV
invalid extension
empty CSV
large CSV
duplicate columns

Profiling

row count
column count
missing values
data types
duplicates

SQL

aggregation
filtering
grouping
joins
invalid column

Anomaly Detection

normal data
outlier data
empty data
single-value column

Chat

simple question
follow-up question
unknown column
unsupported question

33. Observability

Log:

Request ID
Dataset ID
User question
Detected intent
Selected tool
Execution time
Query execution time
LLM latency
Result size
Errors

Example:

[INFO]
request_id=abc123
dataset=sales
intent=aggregation
tool=duckdb
execution_ms=143
llm_ms=842

Do not log API keys or sensitive uploaded data.

34. Caching

Cache:

Dataset profiles.

Repeated SQL queries.

Repeated chart calculations.

Frequently requested summaries.

Example:

Question
   |
   v
Normalize Question
   |
   v
Cache Lookup
   |
   +---- Hit ----> Return Cached Result
   |
   +---- Miss ---> Execute Analysis

35. Production-Style Improvements

Optional production features:

Authentication.

User workspaces.

Persistent conversations.

Redis caching.

PostgreSQL metadata storage.

Background jobs for large files.

Streaming LLM responses.

OpenTelemetry.

Prometheus metrics.

Rate limiting.

Role-based access control.

Cloud object storage.

Model evaluation.

36. Docker

The application should be runnable with:

docker compose up --build

Recommended services:

frontend
backend
database

For the initial assignment, frontend and backend can also run in one
container if simplicity is preferred.

37. Environment Variables

Create .env.example:

OPENAI_API_KEY=your_api_key_here

LLM_MODEL=your_model

MAX_FILE_SIZE_MB=200

DATABASE_PATH=./data/app.db

DUCKDB_PATH=./data/analytics.duckdb

LOG_LEVEL=INFO

Never commit .env.

38. Example Questions

The application should support:

Which region generated the highest revenue?

Show monthly sales trends.

Which products are underperforming?

What are the top five customers?

Generate SQL for this analysis.

Detect anomalies in the dataset.

What is the average order value?

Which product has the highest profit margin?

Compare revenue between regions.

Which customers have declining purchases?

What percentage of revenue comes from the top 10 customers?

Show the distribution of order values.

Is there a correlation between quantity and revenue?

Which month had the largest growth?

Summarize the dataset.

What data-quality issues exist?

39. Example End-to-End Analysis

User:

Which region generated the highest revenue?

Agent:

Intent:
Aggregation

Dataset:
sales.csv

Tool:
DuckDB

Generated SQL:

SELECT
    region,
    SUM(revenue) AS total_revenue
FROM sales
GROUP BY region
ORDER BY total_revenue DESC;

Execution:

West       $2,430,000
East       $2,050,000
Central    $1,720,000
South      $1,410,000
North      $1,220,000

Response:

The West region generated the highest revenue at $2.43M.

It was approximately 18.5% higher than the East region.

Chart:

Revenue by Region
       |
2.5M   | █
2.0M   | █ █
1.5M   | █ █ █
1.0M   | █ █ █ █
0.5M   | █ █ █ █ █
       +----------------
         W E C S N

40. Recommended UI Pages

The final UI should contain:

Dashboard
│
├── Home
│
├── New Chat
│
├── Datasets
│   ├── Upload
│   ├── Preview
│   └── Profile
│
├── Conversations
│
├── Data Quality
│
├── Anomaly Detection
│
├── Reports / Exports
│
├── Settings
│
└── Help

41. Final UI Flow

HOME
 |
 +--> Upload CSV
 |       |
 |       v
 |   Validation
 |       |
 |       v
 |   Data Profile
 |
 +--> New Chat
         |
         v
    User Question
         |
         v
    AI Agent
         |
         v
    Tool Selection
         |
    +----+----+----+----+
    |    |    |    |    |
 Pandas SQL Chart Anomaly Quality
    |    |    |    |    |
    +----+----+----+----+
         |
         v
    Actual Result
         |
         v
    Answer + Chart
         |
         +--> SQL
         |
         +--> Pandas
         |
         +--> Explanation
         |
         +--> Analysis Trace
         |
         +--> Export
         |
         v
    Conversation Memory

42. Assignment Requirements Mapping

Assignment Requirement       Implementation

Upload CSV                   CSV ingestion module
Validate CSV                 Validation pipeline
Natural language questions   AI agent
Business insights            Insight generation
Charts                       Plotly
SQL generation               DuckDB + SQL generator
Pandas code                  Pandas tool
Anomaly detection            Z-score/IQR/Isolation Forest
Explain anomalies            Statistical evidence + LLM
Explain responses            Analysis Trace
Conversation context         Session memory
Multi-file                   Dataset registry + DuckDB joins
Dashboard                    Streamlit dashboard
Data quality                 Quality engine
Forecasting                  Optional time-series module
Agentic workflow             Tool-based agent
Tool calling                 Analysis tools
Semantic search              Optional FAISS
Caching                      Query/profile cache
Authentication               Optional auth layer
Export reports               CSV/XLSX/PDF/HTML
Streaming                    Optional streaming
Logging                      Structured application logs
Evaluation                   Automated test/evaluation suite
Docker                       Dockerfile + Compose
Documentation                README

43. MVP vs Final Version

MVP

Build first:

CSV Upload
    +
Validation
    +
Profiling
    +
Natural Language Chat
    +
Pandas/DuckDB
    +
Plotly
    +
Anomaly Detection
    +
Conversation Context

Final Submission

Then add:

Multi-file analysis
SQL generation
Pandas code generation
Data quality dashboard
Analysis trace
Export reports
Caching
Logging
Tests
Docker
Evaluation

44. Definition of Done

The project is considered complete when a reviewer can:

Upload a CSV.

See its data profile.

Ask a natural-language question.

Receive an answer based on actual data.

See an automatically generated chart.

Inspect SQL/Pandas code.

See a concise analysis trace.

Ask a follow-up question without repeating context.

Detect anomalies.

Understand why anomalies were flagged.

Review data-quality issues.

Analyze multiple datasets.

Export results.

Run the project locally.

Run the project using Docker.

Understand the architecture from the README.

45. Demo Scenario

Use a sample sales dataset with columns such as:

order_id
order_date
customer_id
region
product
category
quantity
sales
profit
discount

Demo:

1. Upload sales.csv

2. Show:
   125,430 rows
   18 columns
   98.18% completeness

3. Ask:
   "Which region generated the highest revenue?"

4. Display:
   Answer
   Bar chart
   SQL
   Pandas
   Analysis Trace

5. Ask:
   "Show its monthly trend."

6. Display:
   Monthly line chart

7. Ask:
   "Detect anomalies."

8. Display:
   Anomaly chart
   Anomaly table
   Explanation

9. Open:
   Data Quality

10. Open:
    Conversation History

This gives the reviewer a complete view of the application's
capabilities in approximately 20--30 seconds.

46. Architecture Principle

The most important design principle is:

The LLM should decide what analysis to perform, but the data engine
should perform the actual computation.

Therefore:

LLM = Understand + Plan + Explain

Pandas/DuckDB = Compute

Plotly = Visualize

Statistics/ML = Detect

Memory = Maintain Context

This architecture makes the application more reliable, explainable,
testable, and production-oriented than an application where the LLM
directly guesses answers from uploaded CSV data.

47. Future Improvements

Potential future extensions:

Natural-language dashboard generation.

Forecasting.

What-if analysis.

Automated executive reports.

Scheduled reports.

Voice-based analysis.

RAG over business documentation.

Enterprise authentication.

Cloud deployment.

Data lineage.

Model evaluation.

Human approval for generated queries.

Fine-tuned domain-specific models.

License

This project is intended as an AI Engineer assignment and portfolio
project.