# 🔍 cv_EasyScan: Tech Job Market Scanner & AI Synthesizer

A modern, high-performance toolkit to discover, crawl, normalize, and analyze tech and remote job postings across premier recruitment platforms and social networks (**ITviec**, **CareerViet**, **Remotive**, **TopCV**, **JoyWork**, **LinkedIn**, **Glassdoor**, **FlexJobs**, **Facebook**).

Equipped with an **embedded SQLite3 engine** featuring intelligent deduplication and accent-insensitive full-text search, an **AI Synthesizer powered by Google Gemini**, and a responsive **Web UI with full i18n support (English, Vietnamese, Russian)**.

---

## 🌟 Key Features

### 1. Multi-Source Crawler Engine
- **Remotive API**: 100% remote global tech jobs fetched via official JSON API with detailed tech stack tagging.
- **ITviec**: Deep scraping for software engineering roles (tech stack, salary range, company culture, benefits).
- **CareerViet** (formerly CareerBuilder Vietnam): Comprehensive enterprise, FDI, and tech listings.
- **LinkedIn Jobs**: Public guest postings via LinkedIn API with headless Playwright fallback.
- **JoyWork (`joywork.vn`)**: Direct integration with JoyWork's public JSON API.
- **TopCV**: Popular Vietnamese job board integration with strict guardrail filtering to discard irrelevant ads.
- **Glassdoor & FlexJobs**: International and remote job search with anti-bot challenge detection.
- **Facebook Fanpages / Groups**: Automated scraping via **Playwright** using a **Persistent Browser Profile** (login once, zero checkpoint risk), human-like scrolling with **random sleep delays up to 10 seconds**, and auto-expanding post bodies. Also supports safe offline JSON/HTML/TXT file imports.

### 2. Intelligent Guardrails & Deduplication
- **Strict Relevance Filter (`is_keyword_relevant`)**: Ensures only position-relevant jobs are collected. Automatically discards off-topic positions (e.g. debt collection, real estate, telesales, retail, F&B) when searching for engineering roles.
- **Adaptive Crawl Limit**: When requesting e.g. 50 jobs, if only 10 genuine matches exist, the crawler stops naturally at 10 without padding with irrelevant listings.
- **SQLite3 Local Storage with Deduplication**: Employs SHA-256 / composite hashing (`job_hash`) to avoid duplicate records while updating salary and description fields in-place.
- **Accent-Insensitive Search**: Custom SQLite normalization (`strip_accents`) allows seamless querying across Vietnamese and English (e.g. searching `ky su ai` or `AI Engineer` matches both `Kỹ sư AI` and `AI Engineer`).

### 3. AI Market Intelligence (Google Gemini)
- Automated statistical analysis of collected job listings:
  - **Salary Benchmarks**: Min, max, and median salary ranges segmented by seniority level.
  - **In-Demand Tech Stacks**: Most frequent programming languages, frameworks, cloud platforms, and AI tools.
  - **Geographic & Workplace Trends**: Onsite vs. Hybrid vs. 100% Remote opportunities.
  - **Actionable Candidate Advice**: Resume optimization tips, missing skill roadmaps, and interview preparation questions.
- Exports comprehensive Markdown reports directly to `reports/`.

### 4. Interactive Web UI with Multi-Language Support (i18n)
- **Modern Dark UI**: Built with Tailwind CSS and FontAwesome, providing live search with debouncing (350ms), interactive modals, and real-time background task status banners.
- **Rich Multi-Dimensional Filters**:
  - **Job Type**: Full-time, Intern / Fresher, Contract / Freelance, Part-time.
  - **Workplace Mode**: Remote / Online, Hybrid, On-site.
  - **Region / Location**: All, Hanoi & North, HCMC & South, Da Nang & Central, Global / Worldwide.
  - **Source Checklist**: Filter by recruitment portal, public salary flag, and remote toggle.
- **Tri-Lingual Switcher**: Instant switching between **English (Default)**, **Vietnamese (Tiếng Việt)**, and **Russian (Русский)** with persistent `localStorage` preference.

### 5. Blazing-Fast Environment Management with Astral `uv`
- Complete `pyproject.toml` and `uv.lock` support for sub-second dependency installation and reproducible runtime environments.

---

## 📁 Repository Structure

```text
cv_scan/
├── config/                  # App settings and dynamic sources configuration
│   ├── settings.py          # Environment loader, timeouts, default models
│   └── sources_config.py    # Recruitment sources metadata and toggle manager
├── crawlers/                # Multi-platform crawlers
│   ├── base.py              # Base crawler interface with HTTPX & Playwright
│   ├── careerviet.py        # CareerViet crawler
│   ├── facebook.py          # Facebook persistent browser crawler
│   ├── factory.py           # Crawler registry and factory
│   ├── flexjobs.py          # FlexJobs remote crawler
│   ├── glassdoor.py         # Glassdoor crawler
│   ├── itviec.py            # ITviec tech crawler
│   ├── joywork.py           # JoyWork JSON API crawler
│   ├── linkedin.py          # LinkedIn guest search crawler
│   ├── remotive.py          # Remotive 100% remote API crawler
│   └── topcv.py             # TopCV crawler with relevance guardrails
├── data/
│   ├── sources.json         # Default sources configuration
│   └── .gitkeep             # Local database directory (jobs.db ignored by git)
├── db/                      # SQLite3 database layer
│   ├── database.py          # SQLite connection manager with strip_accents UDF
│   ├── models.py            # Pydantic & dataclass schemas (JobItem, ReportItem)
│   └── repository.py        # CRUD repository, filtered pagination, deduplication
├── llm/                     # LLM synthesis engine
│   ├── client.py            # Google Gemini client (with OpenAI / Ollama fallbacks)
│   ├── prompts.py           # Analytical prompts for market synthesis
│   └── synthesizer.py       # Data aggregator and Markdown report exporter
├── reports/                 # Output directory for generated reports (.gitkeep)
├── tests/                   # Automated test suite
│   ├── sample_fb_posts.json # Mock Facebook posts for offline testing
│   └── test_new_crawlers.py # Unit tests for crawlers and filters
├── utils/                   # Shared utilities
│   ├── logger.py            # Rich color logging
│   └── text_cleaner.py      # Accent normalization, salary parsing, relevance filter
├── bin/                     # Convenience bash automation scripts
│   ├── setup_env.sh         # One-click environment bootstrap with uv
│   ├── common.sh            # Common script helpers and path discovery
│   ├── web.sh               # Launch local Web UI server
│   ├── crawl.sh             # Quick crawl runner
│   ├── menu.sh              # Interactive terminal dashboard
│   ├── report.sh            # Trigger AI market report
│   ├── run_all.sh           # End-to-end pipeline (crawl -> save -> report)
│   ├── stats.sh             # Display database statistics
│   ├── fb_login.sh          # One-time Facebook browser login
│   └── fb_crawl.sh          # Facebook Fanpage crawler
├── web/                     # Web application
│   ├── index.html           # Single-page application with EN/VI/RU i18n
│   └── server.py            # Lightweight Python HTTP server & REST API
├── cli.py                   # Command-line interface
├── main.py                  # Main entry point
├── pyproject.toml           # Project metadata & dependencies
├── requirements.txt         # Standard requirements file
├── uv.lock                  # Pinned dependencies lockfile
└── .env.example             # Environment template
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **uv** (recommended for blazing-fast package installation)

### 1. Installation

#### Method A: One-Click Setup with `uv` (Recommended)
```bash
# Clone the repository
git clone git@github.com:andryD-ai/cv_EasyScan.git
cd cv_EasyScan

# Run the automated setup script
./bin/setup_env.sh
```
This script automatically:
1. Detects or installs Astral `uv`.
2. Creates `.venv` using `uv venv`.
3. Installs dependencies in milliseconds via `uv pip install -r requirements.txt`.
4. Installs Playwright Chromium headless browser.
5. Prepares `.env` from `.env.example`.

#### Method B: Manual Setup with `uv`
```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv run playwright install chromium
```

#### Method C: Standard Python venv
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

---

### 2. Environment Configuration (`.env`)

Copy the template:
```bash
cp .env.example .env
```

Open `.env` and configure your **Google Gemini API Key** (obtain free at [Google AI Studio](https://aistudio.google.com/)):
```env
GEMINI_API_KEY=AIzaSy...your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
DEFAULT_LLM_PROVIDER=gemini
```

---

## 💻 Usage

### 1. Launch Interactive Web UI (Recommended)
```bash
# Using the helper script:
./bin/web.sh

# Or using uv run:
uv run python web/server.py 8000
```
Open your browser at **`http://localhost:8000`**. You can search, filter, trigger background crawlers, configure sources, and generate AI reports visually.

---

### 2. Terminal Interactive Dashboard
```bash
./bin/menu.sh
```
Opens an interactive ncurses-style terminal menu to execute all tasks with guided prompts.

---

### 3. Command-Line Interface (CLI)

#### A. Crawl Job Listings
```bash
# Crawl Python developer jobs from ITviec, CareerViet, and JoyWork (20 per source)
python main.py crawl --keyword "Python" --sources itviec,careerviet,joywork --limit 20

# Crawl AI Engineer jobs with location filtering (Hanoi, Da Nang)
python main.py crawl -k "AI Engineer" -s itviec,careerviet,joywork,linkedin --location "Ha Noi, Da Nang" -l 30

# Crawl 100% remote jobs using Remotive and LinkedIn Remote
python main.py crawl -k "Data Engineer" -s remotive,linkedin --location "Remote" -l 20
```

#### B. Search Local Database
```bash
# Search stored jobs by keyword
python main.py search --keyword "AI Engineer" --limit 10

# Filter by source and salary availability
python main.py search --keyword "Python" --source itviec --has-salary
```

#### C. Generate AI Market Intelligence Report
```bash
# Generate a comprehensive report for "AI Engineer"
python main.py report --keyword "AI Engineer"

# Generate and preview report directly in the terminal
python main.py report --keyword "Python" --preview

# Analyze up to 150 latest job listings
python main.py report -k "Data Engineer" -l 150
```
Generated reports are saved as Markdown in `reports/report_<keyword>_<timestamp>.md`.

#### D. End-to-End Pipeline
Executes the full pipeline in one command: **Crawl -> Deduplicate & Save -> Analyze with Gemini -> Export Markdown Report**:
```bash
python main.py run --keyword "AI Engineer" --sources itviec,careerviet,remotive --limit 20 --report
```

#### E. View Database Statistics
```bash
python main.py stats
```

#### F. Facebook Fanpage Scraper
```bash
# Step 1: One-time manual login to save persistent session profile
python main.py fb-login

# Step 2: Scrape posts from a recruitment group or page (with anti-bot random delays up to 10s)
python main.py fb-crawl --url "https://www.facebook.com/groups/itjobs.vietnam" --limit 15

# Step 3: Offline safe import from existing JSON/HTML file
python main.py fb-import --file tests/sample_fb_posts.json --keyword "Python"
```

---

## 🧪 Testing

Run automated unit and integration tests:
```bash
# Run crawler test suite
uv run python tests/test_new_crawlers.py
```

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
