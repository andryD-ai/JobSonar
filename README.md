# 🔍 Vietnam Job Market Scanner & LLM Synthesizer

Hệ thống tự động tìm kiếm, cào dữ liệu việc làm từ các trang tuyển dụng hàng đầu tại Việt Nam & quốc tế (**ITviec**, **CareerViet**, **TopCV**, **JoyWork**, **LinkedIn**, **FlexJobs**, **Glassdoor**, **Facebook Fanpage**), lưu trữ cơ sở dữ liệu cục bộ **SQLite3** có cơ chế khử trùng lặp (deduplication) và sử dụng **Google Gemini** để phân tích, tổng hợp báo cáo thị trường lao động chi tiết.

---

## 🌟 Tính năng nổi bật

1. **Bộ cào dữ liệu đa nguồn (Multi-source Crawler)**:
   - **ITviec**: Cào dữ liệu chuyên sâu cho ngành IT/Software (Tech stack, phổ lương, phúc lợi).
   - **CareerViet** (trước đây là CareerBuilder VN): Đa dạng ngành nghề và doanh nghiệp FDI.
   - **TopCV**: Hệ sinh thái tuyển dụng phổ biến nhất Việt Nam.
   - **JoyWork (`joywork.vn`)**: Nền tảng tuyển dụng minh bạch tại VN qua API JSON chính thức.
   - **LinkedIn**: Cào việc làm công khai qua LinkedIn Guest Jobs Search + Playwright fallback.
   - **FlexJobs & Glassdoor**: Hỗ trợ cào việc làm remote/quốc tế (có cơ chế phát hiện security/anti-bot gate rõ ràng).
   - **Facebook Fanpage / Group**: Mô phỏng trình duyệt thật qua **Playwright**, sử dụng **Persistent Browser Profile** (đăng nhập 1 lần, không lo checkpoint/khóa tài khoản), **nghỉ ngẫu nhiên lên đến 10 giây** giữa các lần cuộn để chống bot, tự động click nút *"Xem thêm"* để lấy toàn bộ mô tả công việc (JD).
   - Hỗ trợ **Import file Facebook offline** (JSON, HTML, TXT) an toàn tuyệt đối.

2. **Cơ sở dữ liệu cục bộ SQLite3**:
   - Gọn nhẹ, không cần cài đặt thêm server database (MySQL/PostgreSQL).
   - Khử trùng lặp tự động bằng hàm băm `job_hash` (dựa trên URL hoặc Source + Company + Title). Nếu đã có, hệ thống sẽ cập nhật thông tin mới nhất mà không tạo bản ghi rác.
   - Đánh index tăng tốc độ tìm kiếm theo từ khóa.

3. **Tổng hợp báo cáo thị trường thông minh với LLM (Google Gemini)**:
   - Tự động thống kê: **Phổ lương thực tế** (Min, Max, Median theo cấp bậc), **Top Tech Stack & Kỹ năng được săn đón**, **Phân bố địa lý** (HN, HCM, Remote), **Top nhà tuyển dụng**.
   - Đưa ra **Lời khuyên thực chiến cho ứng viên**: Tối ưu CV, lộ trình học kỹ năng thiếu hụt, chủ đề phỏng vấn.
   - Xuất file báo cáo chuẩn Markdown (`reports/report_*.md`).

4. **Giao diện dòng lệnh (CLI) đẹp mắt**:
   - Sử dụng thư viện `rich` với bảng biểu, highlight màu sắc và thanh thông báo trực quan.

---

## 📁 Cấu trúc thư mục

```text
cv_scan/
├── config/
│   ├── __init__.py
│   └── settings.py          # Cấu hình đường dẫn, API key, timeout, user-agent
├── crawlers/
│   ├── base.py              # Interface chuẩn cho mọi crawler
│   ├── itviec.py            # Module cào ITviec
│   ├── careerviet.py        # Module cào CareerViet
│   ├── topcv.py             # Module cào TopCV (Playwright + HTTP)
│   ├── joywork.py           # Module cào JoyWork (joywork.vn API)
│   ├── linkedin.py          # Module cào LinkedIn Jobs
│   ├── flexjobs.py          # Module cào FlexJobs
│   ├── glassdoor.py         # Module cào Glassdoor
│   ├── facebook.py          # Module cào Fanpage Facebook (Persistent Profile + Random Sleep)
│   └── factory.py           # Quản lý và gọi crawler theo tên
├── data/
│   ├── jobs.db              # File SQLite database tự động khởi tạo
│   └── browser_profile/     # Lưu session đăng nhập Facebook an toàn
├── db/
│   ├── database.py          # Kết nối SQLite & khởi tạo bảng
│   ├── models.py            # Schema dữ liệu JobItem & ReportItem
│   └── repository.py        # Các hàm CRUD, deduplication, search
├── llm/
│   ├── client.py            # Kết nối Google Gemini (hỗ trợ OpenAI & Ollama)
│   ├── prompts.py           # Prompt chuyên gia phân tích thị trường
│   └── synthesizer.py       # Gom dữ liệu từ DB, gọi LLM và xuất báo cáo
├── reports/                 # Thư mục lưu các file báo cáo Markdown sinh ra
├── utils/
│   ├── logger.py            # Rich logging
│   └── text_cleaner.py      # Làm sạch HTML, regex trích xuất lương, tạo hash
├── cli.py                   # Giao diện dòng lệnh CLI
├── main.py                  # Điểm khởi chạy chính
├── requirements.txt         # Thư viện phụ thuộc
└── .env.example             # Mẫu biến môi trường
```

---

## 🚀 Cài đặt & Cấu hình

### 1. Chuẩn bị môi trường Python

Yêu cầu: **Python 3.10+**.

```bash
# Di chuyển vào thư mục dự án
cd cv_scan

# --- CÁCH 1: Khởi tạo tự động 1 lệnh bằng UV (Khuyến nghị) ---
./bin/setup_env.sh

# --- CÁCH 2: Cài đặt thủ công bằng UV (Astral) ---
# 1. Tạo môi trường ảo
uv venv .venv

# 2. Kích hoạt môi trường ảo
source .venv/bin/activate

# 3. Cài đặt các thư viện cần thiết cực nhanh bằng uv pip
uv pip install -r requirements.txt

# 4. Cài đặt Chromium cho Playwright (dùng cho LinkedIn, Glassdoor, Facebook)
uv run playwright install chromium

# --- CÁCH 3: Cài đặt truyền thống bằng python3-venv & pip ---
# python3 -m venv .venv
# source .venv/bin/activate
# pip install -r requirements.txt
# playwright install chromium
```

### 2. Cấu hình biến môi trường (`.env`)

Tạo file `.env` từ file mẫu `.env.example`:

```bash
cp .env.example .env
```

Mở file `.env` và điền **Google Gemini API Key** của bạn (Lấy miễn phí tại: [Google AI Studio](https://aistudio.google.com/)):

```env
GEMINI_API_KEY=AIzaSy...your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
DEFAULT_LLM_PROVIDER=gemini
```

---

## 📖 Hướng dẫn sử dụng

### 1. Cào tin tuyển dụng từ các trang web (`crawl`)
Cào từ các trang ITviec, CareerViet, TopCV:

```bash
# Cào vị trí Python từ ITviec và CareerViet (mỗi nguồn 20 tin)
python main.py crawl --keyword "Python" --sources itviec,careerviet --limit 20

# Cào vị trí Golang từ tất cả các trang
python main.py crawl -k "Golang" -s itviec,careerviet,topcv -l 30

# Cào vị trí Data Engineer
python main.py crawl -k "Data Engineer" -s itviec,careerviet
```

---

### 2. Cào bài viết từ Facebook Fanpage (`fb-login` & `fb-crawl`)

Để hạn chế tối đa bị checkpoint hoặc khóa tài khoản, hệ thống dùng cơ chế **Persistent Profile**:

#### Bước 2.1: Đăng nhập Facebook 1 lần duy nhất
```bash
python main.py fb-login
```
- Trình duyệt sẽ mở ra trang Facebook.
- Bạn đăng nhập tài khoản của mình (khuyên dùng nick phụ/clone).
- Sau khi vào Newsfeed thành công, quay lại terminal nhấn `[ENTER]`. Session đăng nhập sẽ được lưu vĩnh viễn trong `data/browser_profile/`.

#### Bước 2.2: Cào bài từ Fanpage
```bash
# Cào 15 bài từ một Fanpage/Group tuyển dụng bất kỳ
python main.py fb-crawl --url "https://www.facebook.com/groups/itjobs.vietnam" --limit 15

# Tùy chỉnh khoảng nghỉ ngẫu nhiên (chống bot, mặc định 2s - 10s)
python main.py fb-crawl --url "https://www.facebook.com/ten_fanpage" --limit 20 --min-delay 3.0 --max-delay 10.0
```

#### Bước 2.3: Import bài viết Facebook từ file (Chế độ an toàn / Offline)
Nếu bạn đã xuất sẵn bài viết ra file JSON, HTML hoặc TXT:
```bash
python main.py fb-import --file tests/sample_fb_posts.json --keyword "Python"
```

---

### 3. Dùng Gemini tổng hợp báo cáo thị trường (`report`)
Đọc dữ liệu đã cào trong database SQLite và yêu cầu LLM phân tích chuyên sâu:

```bash
# Tạo báo cáo cho vị trí Python
python main.py report --keyword "Python"

# Tạo báo cáo và in trực tiếp toàn bộ nội dung lên màn hình Terminal
python main.py report --keyword "Python" --preview

# Phân tích tới 150 tin gần nhất
python main.py report -k "Golang" -l 150
```

*File báo cáo định dạng Markdown sẽ được lưu tự động vào thư mục `reports/` (ví dụ: `reports/report_python_20261111_165500.md`).*

---

### 4. Chạy toàn trình 1 lệnh duy nhất (`run`)
Lệnh này sẽ tự động thực hiện: **Cào dữ liệu -> Khử trùng lặp & lưu vào SQLite -> Gọi Gemini phân tích -> Xuất file báo cáo Markdown**:

```bash
python main.py run --keyword "Python" --sources itviec,careerviet --limit 25 --report
```

---

### 5. Xem thống kê dữ liệu trong SQLite (`stats`)
Kiểm tra số lượng việc làm đã thu thập, nguồn dữ liệu và các báo cáo đã tạo:

```bash
python main.py stats
```

---

## 🗄️ Cấu trúc bảng SQLite (`data/jobs.db`)

- **Bảng `jobs`**:
  - `id`: Khóa chính tự tăng.
  - `source`: Tên nguồn (`itviec`, `careerviet`, `topcv`, `facebook`).
  - `job_hash`: Chuỗi băm duy nhất để chống lưu trùng lặp.
  - `title`: Tiêu đề công việc.
  - `company`: Tên công ty/nhà tuyển dụng.
  - `location`: Địa điểm làm việc (Hà Nội, TP.HCM, Remote...).
  - `salary_raw`, `salary_min`, `salary_max`, `salary_currency`: Thông tin mức lương.
  - `job_description`, `requirements`, `benefits`: Chi tiết JD.
  - `job_url`: Đường link bài tuyển dụng gốc.
  - `keyword_searched`: Từ khóa đã dùng để tìm kiếm.

- **Bảng `reports`**:
  - `id`: Khóa chính.
  - `keyword`: Vị trí phân tích.
  - `total_jobs_analyzed`: Số lượng tin đã đưa vào LLM.
  - `llm_model`: Mô hình LLM đã dùng (`gemini-2.5-flash`...).
  - `summary_markdown`: Nội dung báo cáo đầy đủ.
  - `created_at`: Thời gian xuất báo cáo.

---

## 💡 Mở rộng

- **Đổi sang OpenAI hoặc Ollama**: Chỉ cần thay đổi trong `.env` (`DEFAULT_LLM_PROVIDER=openai` hoặc `ollama`).
- **Thêm nguồn cào mới**: Kế thừa lớp `BaseCrawler` trong `crawlers/base.py` và đăng ký vào `crawlers/factory.py`.
