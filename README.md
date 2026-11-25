# HealthSync AI

A modern **Healthcare AI & Patient Management Dashboard** built with **Python**, **Streamlit**, **SQLite**, **Pandas**, and **Altair**.

---

## Features

- **Overview Dashboard**: Live SQLite metrics, Data Quality & AI Coverage progress cards, Altair biomarker charts (Glucose, Haemoglobin, Cholesterol), Duplicate Name/Email monitor, and Recent Activity.
- **Add Patient**: Validated registration form (`Full Name`, `Date of Birth` in `DD/MM/YYYY`, `Email`, `Glucose`, `Haemoglobin`, `Cholesterol`) with duplicate name/email prevention and optional automatic AI remarks.
- **Patient Records (CRUD)**: Search, filter, sort, view details, edit records, and delete records with confirmation.
- **Data Quality & Assignment Import**: Controlled import of the 10-record assignment dataset (preserving invalid/duplicate entries for audit), automatic validation error reporting, and a Duplicate Name & Email cleanup manager.
- **AI Health Insights**: Configurable OpenAI-compatible API integration that generates cautious, educational health observations and saves analysis history in SQLite.

---

## Tech Stack

- **Frontend / UI:** Streamlit + Custom CSS (`styles.py`)
- **Database:** SQLite (`database.py`)
- **Validation & Data Quality:** Python + `email-validator` (`validators.py`)
- **Analytics & Charts:** Pandas + Altair
- **AI Integration:** OpenAI-compatible Chat Completions API (`ai_service.py`)

---

## Setup & Run

1. **Clone the repository**
   ```bash
   git clone https://github.com/amangari115322/HealthSync_AI.git
   cd HealthSync_AI
   ```

2. **Create and activate a virtual environment**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables (optional for AI Insights)**
   Copy `.env.example` to `.env` and add your API details:
   ```env
   AI_API_KEY=your_api_key_here
   AI_API_URL=https://api.openai.com/v1/chat/completions
   AI_MODEL=gpt-4o-mini
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

---

## Project Structure

- `app.py` — Main Streamlit application (Overview, Add Patient, Patient Records, AI Health Insights)
- `styles.py` — Custom SaaS design system CSS, SVG icons, and startup splash screen
- `database.py` — SQLite schema, migrations, CRUD operations, and AI analysis history
- `validators.py` — Input validation, data quality checks, duplicate detection, and assignment dataset
- `ai_service.py` — External AI API integration and error handling
- `config.py` — App metadata and environment configuration
- `assets/` — Hero banner visual
- `.streamlit/config.toml` — Streamlit theme configuration
