# 📖 JobSonar User Guide & Quickstart Reference

Comprehensive guide to executing crawlers, filtering jobs, generating AI market reports, and configuring sources.

---

## 1. Environment Setup with `uv`

If you are setting up on a fresh machine or cloned repo, initialize the environment with one command:

```bash
# Automated setup (installs uv if needed, creates .venv, installs packages, sets up Playwright)
./bin/setup_env.sh
```

Alternatively, manually initialize using Astral's `uv`:

```bash
# 1. Create virtual environment
uv venv .venv

# 2. Activate environment
source .venv/bin/activate

# 3. Install packages
uv pip install -r requirements.txt

# 4. Install headless browser
uv run playwright install chromium
```

### Configure Google Gemini API Key

1. Obtain a free API key at [Google AI Studio](https://aistudio.google.com/).
2. Copy the `.env.example` template:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env`:
   ```env
   GEMINI_API_KEY=AIzaSy...your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   DEFAULT_LLM_PROVIDER=gemini
   ```

---

## 2. Fast Execution via Shell Scripts (`./bin`)

The `./bin` directory provides standalone bash scripts that auto-detect and activate `.venv`:

| Script File | Purpose | Example Command |
| :--- | :--- | :--- |
| [`./bin/setup_env.sh`](bin/setup_env.sh) | **Bootstrap virtual environment & install libraries via `uv`** | `./bin/setup_env.sh` |
| [`./bin/web.sh`](bin/web.sh) | **Start Local Web UI server (Default port 8000)** | `./bin/web.sh` |
| [`./bin/menu.sh`](bin/menu.sh) | **Interactive ncurses-style CLI control dashboard** | `./bin/menu.sh` |
| [`./bin/crawl.sh`](bin/crawl.sh) | Crawl job postings from web platforms | `./bin/crawl.sh "Python" itviec,careerviet 20` |
| [`./bin/report.sh`](bin/report.sh) | Synthesize AI market report with Gemini | `./bin/report.sh "Python" 100` |
| [`./bin/run_all.sh`](bin/run_all.sh) | Full pipeline: Crawl Web -> SQLite -> AI Report | `./bin/run_all.sh "Python"` |
| [`./bin/stats.sh`](bin/stats.sh) | Display SQLite database storage statistics | `./bin/stats.sh` |
| [`./bin/fb_login.sh`](bin/fb_login.sh) | Login to Facebook once to save session profile | `./bin/fb_login.sh` |
| [`./bin/fb_crawl.sh`](bin/fb_crawl.sh) | Scrape recruitment fanpage/group with random sleep | `./bin/fb_crawl.sh "https://fb.com/..." 15 2.0 10.0` |

*(Scripts can also be executed without arguments to run interactively with prompted inputs).*

---

## 3. Direct Python CLI Usage

### A. Crawl Job Listings (`crawl`)
Supported sources: `itviec`, `careerviet`, `topcv`, `joywork`, `linkedin`, `remotive`, `glassdoor`, `flexjobs`.

```bash
# Crawl Python positions from ITviec, CareerViet, and JoyWork (20 per source)
python main.py crawl --keyword "Python" --sources itviec,careerviet,joywork --limit 20

# Crawl AI Engineer positions with multi-city location filtering
python main.py crawl -k "AI Engineer" -s itviec,careerviet,joywork,linkedin --location "Ha Noi, Da Nang" -l 30

# Crawl 100% remote jobs using Remotive and LinkedIn Remote
python main.py crawl -k "Data Engineer" -s remotive,linkedin --location "Remote" -l 20
```

---

### B. Facebook Fanpage & Group Scraper (`fb-login` & `fb-crawl`)

Uses **Playwright Persistent Context** with human-like scrolling and **random sleep intervals up to 10 seconds** to avoid bot detection:

#### Step 1: One-time login to save session
```bash
python main.py fb-login
```
- A Chromium browser opens Facebook.
- Log in with your secondary/testing account.
- Once logged in, return to the terminal and press `[ENTER]`.
- Session cookies and storage are saved permanently in `data/browser_profile/`.

#### Step 2: Scrape Fanpage or Group
```bash
# Scrape 15 posts from a recruitment group
python main.py fb-crawl --url "https://www.facebook.com/groups/itjobs.vietnam" --limit 15

# Customize random delays (2s to 10s)
python main.py fb-crawl --url "https://www.facebook.com/fanpage_name" --limit 20 --min-delay 3.0 --max-delay 10.0
```

#### Step 3: Offline Safe Import
```bash
python main.py fb-import --file tests/sample_fb_posts.json --keyword "Python"
```

---

### C. Synthesize AI Market Reports (`report`)
Analyzes stored job records in SQLite and invokes Google Gemini:

```bash
# Generate report for "AI Engineer"
python main.py report --keyword "AI Engineer"

# Generate report and print full Markdown directly in terminal
python main.py report --keyword "Python" --preview

# Analyze up to 150 latest job listings
python main.py report -k "Data Engineer" -l 150
```

Generated reports are saved in `reports/` (e.g. `reports/report_ai_engineer_20261117_153215.md`).

---

### D. End-to-End Pipeline (`run`)
Automatically runs the complete workflow in a single command:
**Crawl data -> Deduplicate & store in SQLite -> Analyze with Gemini -> Export Markdown report**:

```bash
python main.py run --keyword "AI Engineer" --sources itviec,careerviet,remotive --limit 25 --report
```

---

### E. Database Statistics (`stats`)
Displays total stored jobs, source distribution, and report generation history:

```bash
python main.py stats
```

---

### F. Launch Web UI (`web`)
```bash
# Method 1: Bash helper
./bin/web.sh

# Method 2: Python CLI
python main.py web
```
Navigate to: **`http://localhost:8000`**

---

## 4. Storage & Artifact Locations
- **SQLite Database**: `data/jobs.db` (auto-created on first run, ignored in git)
- **Browser Profile**: `data/browser_profile/` (persistent session storage, ignored in git)
- **Market Reports**: `reports/` (standard GitHub-flavored Markdown, ignored in git)
- **Sources Configuration**: `data/sources.json` (versioned configuration file)
