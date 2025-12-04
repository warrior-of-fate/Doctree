# 🚀 Quick Setup & Running Guide

## Running the Application

### ✅ CORRECT WAY

Always navigate to the **project root directory** (where `main.py` is located):

```bash
cd "d:\PDF 1\pdf-\pdf-topic-scanner-main"
```

Then run from there:

```bash
# For Streamlit UI
streamlit run src/ui/streamlit_app.py

# For CLI
python main.py tests/sample_pdfs/simple_doc.pdf --stats

# For tests
pytest tests/test_small_pipeline.py -v
```

### ❌ WRONG WAY (This causes the import error)

```bash
cd d:\PDF 1\pdf-
streamlit run pdf-topic-scanner-main/src/ui/streamlit_app.py  # ❌ Wrong!
```

---

## 📁 Project Structure

```
d:\PDF 1\pdf-\
└── pdf-topic-scanner-main/        ← Always cd here first!
    ├── main.py                      ← Entry point
    ├── src/
    │   ├── core/
    │   │   └── pdf_parser.py
    │   ├── features/
    │   │   └── feature_engineer.py
    │   ├── hierarchy/
    │   │   ├── heading_classifier.py
    │   │   └── tree_builder.py
    │   └── ui/
    │       └── streamlit_app.py
    ├── tests/
    └── utils/
```

---

## 🔧 Fix Applied

I've updated both `main.py` and `src/ui/streamlit_app.py` to automatically adjust Python's import paths. This means they should now work from any directory, but it's still **best practice** to run from the project root.

### What was fixed:
```python
# Added this to both files:
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
```

---

## ✅ Verify Installation

```bash
# Navigate to correct directory
cd "d:\PDF 1\pdf-\pdf-topic-scanner-main"

# Verify imports work
python -c "from src.core.pdf_parser import parse_pdf; print('✅ All imports working')"

# Run tests
pytest tests/test_small_pipeline.py -v

# Try CLI
python main.py tests/sample_pdfs/simple_doc.pdf --stats
```

---

## 🎯 Quick Start Commands

```bash
# 1. Navigate to project root
cd "d:\PDF 1\pdf-\pdf-topic-scanner-main"

# 2. Run the UI (opens at http://localhost:8501)
streamlit run src/ui/streamlit_app.py

# 3. Or run the CLI
python main.py tests/sample_pdfs/simple_doc.pdf --stats
```

---

## 📝 Alternative: Create a Batch Script

Create `run_streamlit.bat` in the project root:

```batch
@echo off
cd /d "%~dp0"
streamlit run src/ui/streamlit_app.py
pause
```

Then just double-click it to run!

---

**Status:** ✅ Fixed - App should now run correctly!
