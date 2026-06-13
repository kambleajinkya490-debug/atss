# ATS Resume Scorer 🎯

An AI-powered Applicant Tracking System (ATS) resume analyzer built with FastAPI, Claude AI, and a responsive web frontend — fully containerized with Docker.

## Features

- **Resume parsing**: PDF and DOCX support via `pdfplumber` and `python-docx`
- **Keyword analysis**: TF-IDF/cosine similarity against job description
- **AI deep analysis**: Claude `claude-sonnet-4-6` for semantic scoring and actionable recommendations
- **5-category scoring**: Keyword Match, Skills Match, Experience, Education, Formatting
- **Downloadable PDF reports** with full breakdown
- **Responsive UI**: Deep navy dashboard with animated score gauges

## Project Structure

```
ats-scorer/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py               # FastAPI app & routes
│   └── services/
│       ├── extractor.py      # PDF/DOCX text extraction
│       ├── scorer.py         # TF-IDF & keyword scoring
│       ├── ai_analyzer.py    # Claude AI integration
│       └── report_generator.py  # PDF report generation
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
│       └── index.html        # Full SPA dashboard
├── docker-compose.yml
├── .env.example
└── README.md
```

## Quick Start

### 1. Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- An [Anthropic API key](https://console.anthropic.com/)

### 2. Clone & Configure

```bash
# Clone the repo
git clone <your-repo-url>
cd ats-scorer

# Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
nano .env
```

### 3. Build & Run

```bash
docker compose up -d --build
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 4. Usage

1. Open http://localhost:3000
2. Upload your resume (PDF or DOCX)
3. Paste the job description
4. Click **Analyze Resume**
5. Review your ATS score, keyword gaps, and AI recommendations
6. Download your PDF report

## Score Breakdown

| Category | Weight | Description |
|---|---|---|
| Keyword Match | 30% | TF-IDF comparison of JD keywords vs resume |
| Skills Match | 25% | Technical & soft skills detection |
| Experience Relevance | 25% | Years + semantic content similarity |
| Education Match | 10% | Degree & certification requirements |
| Formatting & Readability | 10% | Structure, sections, length |

## Grade Scale

| Grade | Score | Meaning |
|---|---|---|
| A | 85–100% | Excellent ATS match |
| B | 70–84% | Good match, minor gaps |
| C | 55–69% | Fair, significant improvements needed |
| D | 0–54% | Weak match, major overhaul needed |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/analyze` | Analyze resume vs JD |
| POST | `/generate-report` | Generate PDF report |

## Development (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
ANTHROPIC_API_KEY=your_key uvicorn main:app --reload --port 8000

# Frontend — open in browser directly
open frontend/src/index.html
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes (for AI) | Your Claude API key |
| `APP_ENV` | No | `development` or `production` |
| `LOG_LEVEL` | No | Logging verbosity |

## License

MIT
