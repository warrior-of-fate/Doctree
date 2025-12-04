# DocTree.AI (pdf-topic-scanner-main)

A lightweight PDF topic scanner and hierarchy builder — FastAPI backend that runs a PDF parsing + heading-classification pipeline, and a Next.js frontend UI to upload PDFs and visualize the generated section tree.

Features
- Upload PDF files (up to 500MB in dev configuration)
- Extract headings and build hierarchical section tree
- Interactive tree viewer and raw JSON output

Quickstart (development)

1. Backend

```powershell
cd "d:\PDF 1\pdf-\pdf-topic-scanner-main"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000
```

2. Frontend

```powershell
cd frontend
npm ci
npm run dev
# Open http://localhost:3000
```

Docker (local)

Build and run both services with docker-compose (example files available in the repo):

```powershell
docker-compose up --build
```

Testing

```powershell
# from repo root
pytest -q
```

Repository structure (important files)
- `src/api/server.py` — FastAPI HTTP API exposing the pipeline
- `src/core/pdf_parser.py` — PDF parsing logic used by the pipeline
- `frontend/` — Next.js frontend (upload UI and viewer)
- `requirements.txt` — Python dependencies

Contributing
- See `CONTRIBUTING.md` for contribution guidelines, tests, and code style.

License
- MIT — see `LICENSE`

Contact
- Maintainer: `death-by-love` — bhaaveshdharamaraj@gmail.com
# pdf-topic-scanner
AI-powered PDF Hierarchy &amp; Topic Extraction System
