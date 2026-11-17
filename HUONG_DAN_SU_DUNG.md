# 📖 HƯỚNG DẪN SỬ DỤNG NHANH (QUICK START GUIDE)
## Hệ Thống Cào Dữ Liệu Tuyển Dụng & Phân Tích Thị Trường Bằng AI (Gemini)

---

### 1. Kích hoạt môi trường và Cấu hình

Nếu bạn mới clone dự án về máy mới, chỉ cần chạy 1 lệnh để tự động tạo môi trường bằng **uv** (Astral):

```bash
# Khởi tạo tự động môi trường và cài đặt thư viện bằng uv
./bin/setup_env.sh
```

Hoặc kích hoạt môi trường ảo `.venv` đã có:

```bash
# Kích hoạt môi trường ảo
source .venv/bin/activate
```

#### Cấu hình Gemini API Key:
1. Lấy API key miễn phí tại: [Google AI Studio](https://aistudio.google.com/)
2. Tạo file `.env` từ file mẫu:
   ```bash
   cp .env.example .env
   ```
3. Mở file `.env` và điền key của bạn:
   ```env
   GEMINI_API_KEY=AIzaSy...your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   DEFAULT_LLM_PROVIDER=gemini
   ```

---

### 2. Chạy nhanh qua các kịch bản Bash trong `./bin` (Khuyên dùng ⭐)

Hệ thống đã viết sẵn các kịch bản bash trong thư mục [`./bin`](file:///home/candhn/Documents/cv_scan/bin/), tự động nhận diện và kích hoạt môi trường `.venv`:

| Tệp Script | Chức năng | Cách dùng mẫu |
| :--- | :--- | :--- |
| [`./bin/setup_env.sh`](file:///home/candhn/Documents/cv_scan/bin/setup_env.sh) | **Khởi tạo môi trường ảo & cài đặt thư viện bằng `uv`** | `./bin/setup_env.sh` |
| [`./bin/web.sh`](file:///home/candhn/Documents/cv_scan/bin/web.sh) | **Khởi chạy Local Web UI trực quan (Cổng 8000)** | `./bin/web.sh` |
| [`./bin/menu.sh`](file:///home/candhn/Documents/cv_scan/bin/menu.sh) | **Menu điều khiển tương tác trực quan** | `./bin/menu.sh` |
| [`./bin/crawl.sh`](file:///home/candhn/Documents/cv_scan/bin/crawl.sh) | Cào việc làm từ Web (ITviec, CareerViet, TopCV) | `./bin/crawl.sh "Python" itviec,careerviet 20` |
| [`./bin/fb_login.sh`](file:///home/candhn/Documents/cv_scan/bin/fb_login.sh) | Đăng nhập Facebook 1 lần để lưu Profile | `./bin/fb_login.sh` |
| [`./bin/fb_crawl.sh`](file:///home/candhn/Documents/cv_scan/bin/fb_crawl.sh) | Cào bài Fanpage (Delay ngẫu nhiên tới 10s) | `./bin/fb_crawl.sh "https://fb.com/..." 15 2.0 10.0` |
| [`./bin/report.sh`](file:///home/candhn/Documents/cv_scan/bin/report.sh) | Dùng Gemini tổng hợp báo cáo thị trường | `./bin/report.sh "Python" 100` |
| [`./bin/run_all.sh`](file:///home/candhn/Documents/cv_scan/bin/run_all.sh) | Chạy toàn trình: Cào Web -> SQLite -> Báo cáo AI | `./bin/run_all.sh "Python"` |
| [`./bin/stats.sh`](file:///home/candhn/Documents/cv_scan/bin/stats.sh) | Xem thống kê cơ sở dữ liệu SQLite | `./bin/stats.sh` |

*(Bạn có thể chạy các file script trên mà không cần truyền tham số, script sẽ tự động hỏi bạn từng bước!)*

---

### 3. Các lệnh sử dụng trực tiếp qua Python CLI

#### Lệnh 1: Cào dữ liệu từ các trang tuyển dụng (Web)
Hỗ trợ các nguồn: `itviec`, `careerviet`, `topcv`, `joywork`, `linkedin`, `flexjobs`, `glassdoor`.

```bash
# Cào vị trí Python từ ITviec, CareerViet và JoyWork (mỗi nguồn 20 tin)
python main.py crawl --keyword "Python" --sources itviec,careerviet,joywork --limit 20

# Cào vị trí AI Engineer từ các nguồn VN & quốc tế tại Hà Nội, Đà Nẵng
python main.py crawl -k "AI Engineer" -s itviec,careerviet,joywork,linkedin --location "Ha Noi, Da Nang" -l 30

# Cào vị trí Data Engineer
python main.py crawl -k "Data Engineer" -s itviec,careerviet
```

---

#### Lệnh 2: Thu thập bài viết từ Facebook Fanpage / Group

Cơ chế sử dụng **Playwright với Persistent Context** kết hợp **khoảng dừng ngẫu nhiên lên đến 10 giây** để chống checkpoint/khóa tài khoản tối đa:

##### Bước 2.1: Đăng nhập 1 lần duy nhất để lưu Session
```bash
python main.py fb-login
```
- Trình duyệt Chromium sẽ mở ra trang Facebook.
- Đăng nhập tài khoản của bạn (khuyên dùng nick phụ/clone).
- Khi đã vào trang chủ Facebook thành công, quay lại terminal nhấn `[ENTER]`.
- Toàn bộ session đăng nhập sẽ được lưu an toàn tại thư mục `data/browser_profile/` cho các lần chạy sau.

##### Bước 2.2: Cào bài viết Fanpage
```bash
# Cào 15 bài từ Fanpage hoặc Group tuyển dụng
python main.py fb-crawl --url "https://www.facebook.com/groups/itjobs.vietnam" --limit 15

# Tùy chỉnh khoảng nghỉ ngẫu nhiên (chống bot, mặc định 2s - 10s)
python main.py fb-crawl --url "https://www.facebook.com/ten_fanpage" --limit 20 --min-delay 3.0 --max-delay 10.0
```
*Tính năng:* Tự động cuộn trang theo hành vi người dùng thật, tự động bấm vào nút *"Xem thêm"* để đọc trọn vẹn mô tả JD.

##### Bước 2.3: Import bài viết Facebook từ file (Chế độ an toàn / Không cần mở mạng)
Nếu bạn đã xuất sẵn bài đăng ra file JSON, HTML hoặc TXT:
```bash
python main.py fb-import --file tests/sample_fb_posts.json --keyword "Python"
```

---

#### Lệnh 3: Dùng Gemini tổng hợp báo cáo thị trường
Đọc các bài tuyển dụng đã lưu trong SQLite cục bộ và yêu cầu Google Gemini phân tích chuyên sâu:

```bash
# Tạo báo cáo cho vị trí Python
python main.py report --keyword "Python"

# Tạo báo cáo và in trực tiếp toàn bộ nội dung lên màn hình Terminal
python main.py report --keyword "Python" --preview

# Phân tích tới 150 tin gần nhất
python main.py report -k "Golang" -l 150
```

*Kết quả:* File báo cáo Markdown hoàn chỉnh được lưu tự động tại thư mục `reports/` (Ví dụ: `reports/report_python_20261111_165500.md`).

---

#### Lệnh 4: Chạy toàn trình 1 lệnh duy nhất (End-to-End)
Tự động làm từ A-Z: **Cào dữ liệu -> Khử trùng lặp & lưu vào SQLite -> Gọi Gemini phân tích -> Xuất file báo cáo Markdown**:

```bash
python main.py run --keyword "Python" --sources itviec,careerviet --limit 25 --report
```

---

#### Lệnh 5: Xem thống kê cơ sở dữ liệu SQLite
Xem tổng số tin tuyển dụng đang có, phân bố theo nguồn và lịch sử các báo cáo đã tạo:

```bash
python main.py stats
```

---

#### Lệnh 6: Khởi chạy Local Web UI trực quan trên Trình duyệt ⭐
Giao diện Web UI hiện đại (Dark theme) để trực quan hóa toàn bộ dữ liệu cào được:
```bash
# Cách 1: Chạy bằng bash script
./bin/web.sh

# Cách 2: Chạy bằng python CLI
python main.py web
```
Sau đó mở trình duyệt truy cập: **`http://127.0.0.1:8000`**

---

### 4. Vị trí các tệp dữ liệu & Kết quả
- **Cơ sở dữ liệu SQLite**: `data/jobs.db`
- **File session Facebook**: `data/browser_profile/`
- **Thư mục báo cáo xuất ra**: `reports/` (định dạng Markdown tiêu chuẩn, có thể mở bằng bất kỳ trình đọc Markdown, VS Code hoặc import vào Notion)
