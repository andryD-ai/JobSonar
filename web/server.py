"""Local Web UI server for Vietnam Job Market Scanner."""
import os
import sys
import json
import threading
from pathlib import Path
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
import urllib.parse
from datetime import datetime

# Add root directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import settings
from config.sources_config import sources_config
from db.repository import job_repo, report_repo
from crawlers.factory import crawler_factory
from llm.synthesizer import JobSynthesizer
from utils.logger import logger

# In-memory background task tracking
bg_tasks = []


def run_bg_task(task_type: str, target_func, *args, **kwargs):
    task_id = len(bg_tasks) + 1
    task_record = {
        "id": task_id,
        "type": task_type,
        "status": "running",
        "message": "Đang thực thi...",
        "created_at": datetime.now().strftime("%H:%M:%S")
    }
    bg_tasks.insert(0, task_record)

    def worker():
        try:
            result = target_func(*args, **kwargs)
            task_record["status"] = "success"
            task_record["message"] = f"Hoàn tất! {result if isinstance(result, str) else ''}"
        except Exception as e:
            logger.error(f"Background task {task_id} failed: {e}")
            task_record["status"] = "failed"
            task_record["message"] = f"Lỗi: {str(e)}"

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return task_record


class JobAPIHandler(BaseHTTPRequestHandler):
    def send_json(self, data, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str, ensure_ascii=False).encode("utf-8"))

    def send_file(self, file_path: Path, content_type: str = "text/html; charset=utf-8"):
        if not file_path.exists():
            self.send_error(404, "File not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        with open(file_path, "rb") as f:
            self.wfile.write(f.read())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Static Web UI frontend
        if path in ["/", "/index.html"]:
            html_file = Path(__file__).resolve().parent / "index.html"
            self.send_file(html_file, "text/html; charset=utf-8")
            return

        # API: Stats
        if path == "/api/stats":
            stats = job_repo.get_stats()
            reports = report_repo.list_reports(limit=5)
            stats["total_reports"] = len(reports)
            stats["recent_reports"] = [r.model_dump() for r in reports]
            all_srcs = sources_config.get_all()
            stats["total_sources"] = len(all_srcs)
            stats["enabled_sources"] = sum(1 for s in all_srcs if s.get("enabled"))
            self.send_json(stats)
            return

        # API: Jobs list with filter and pagination
        if path == "/api/jobs":
            keyword = query.get("keyword", [None])[0]
            source = query.get("source", [None])[0]
            location = query.get("location", [None])[0]
            job_type = query.get("job_type", [None])[0]
            workplace_mode = query.get("workplace_mode", [None])[0]
            region = query.get("region", [None])[0]
            has_salary = query.get("has_salary", ["0"])[0] in ["1", "true", "True"]
            is_remote = query.get("is_remote", ["0"])[0] in ["1", "true", "True"]
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])

            jobs, total = job_repo.search_jobs(
                keyword=keyword,
                source=source,
                location=location,
                job_type=job_type,
                workplace_mode=workplace_mode,
                region=region,
                has_salary_only=has_salary,
                is_remote_only=is_remote,
                page=page,
                limit=limit
            )
            data = {
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": max(1, (total + limit - 1) // limit),
                "jobs": [j.to_dict() for j in jobs]
            }
            self.send_json(data)
            return

        # API: Single Job
        if path.startswith("/api/jobs/"):
            try:
                job_id = int(path.split("/")[-1])
                with job_repo.db.get_connection() as conn:
                    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
                    if row:
                        self.send_json(job_repo._row_to_job(row).to_dict())
                        return
                self.send_error(404, "Job not found")
            except Exception as e:
                self.send_error(400, f"Invalid Job ID: {e}")
            return

        # API: Reports list
        if path == "/api/reports":
            reports = report_repo.list_reports(limit=30)
            self.send_json([r.model_dump() for r in reports])
            return

        # API: Single Report
        if path.startswith("/api/reports/"):
            try:
                rep_id = int(path.split("/")[-1])
                with report_repo.db.get_connection() as conn:
                    row = conn.execute("SELECT * FROM reports WHERE id = ?", (rep_id,)).fetchone()
                    if row:
                        self.send_json(dict(row))
                        return
                self.send_error(404, "Report not found")
            except Exception as e:
                self.send_error(400, f"Invalid Report ID: {e}")
            return

        # API: Sources config list
        if path == "/api/sources":
            self.send_json(sources_config.get_all())
            return

        # API: Background tasks status
        if path == "/api/tasks":
            self.send_json(bg_tasks[:10])
            return

        self.send_error(404, "API endpoint not found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        # API: Trigger Crawl
        if path == "/api/crawl":
            keyword = payload.get("keyword", "").strip()
            if not keyword:
                self.send_json({"error": "Keyword is required"}, status=400)
                return

            sources = payload.get("sources", "itviec,careerviet")
            limit = int(payload.get("limit", 20))
            location = payload.get("location") or None
            is_remote = bool(payload.get("is_remote", False))
            if is_remote and (not location or location.lower() == "all"):
                location = "Remote"

            def do_crawl():
                src_list = [s.strip().lower() for s in sources.split(",") if s.strip()]
                total_c = 0
                errors = []
                for s in src_list:
                    try:
                        c = crawler_factory.get_crawler(s)
                        items = c.search(keyword, limit=limit, location=location)
                        job_repo.save_jobs_batch(items)
                        total_c += len(items)
                    except Exception as e:
                        logger.error(f"Error crawling from '{s}': {e}")
                        errors.append(f"{s}: {str(e)[:50]}")
                msg = f"Đã cào {total_c} tin tuyển dụng cho '{keyword}'"
                if errors:
                    msg += f" (Cảnh báo: {', '.join(errors)})"
                return msg

            task = run_bg_task(f"Crawl: {keyword}", do_crawl)
            self.send_json(task)
            return

        # API: Trigger LLM Report
        if path == "/api/report":
            keyword = payload.get("keyword", "").strip()
            if not keyword:
                self.send_json({"error": "Keyword is required"}, status=400)
                return

            def do_report():
                synthesizer = JobSynthesizer()
                _, path = synthesizer.generate_report(keyword=keyword)
                return f"Báo cáo đã xuất tại {path.name}"

            task = run_bg_task(f"Report AI: {keyword}", do_report)
            self.send_json(task)
            return

        # API: Toggle source
        if path == "/api/sources/toggle":
            source_id = payload.get("id")
            enabled = payload.get("enabled", True)
            ok = sources_config.toggle(source_id, enabled)
            self.send_json({"success": ok, "id": source_id, "enabled": enabled})
            return

        # API: Add custom source
        if path == "/api/sources/add":
            try:
                new_src = sources_config.add_source(payload)
                self.send_json({"success": True, "source": new_src})
            except Exception as e:
                self.send_json({"error": str(e)}, status=400)
            return

        # API: Delete source
        if path == "/api/sources/delete":
            source_id = payload.get("id")
            ok = sources_config.delete_source(source_id)
            self.send_json({"success": ok, "id": source_id})
            return

        self.send_error(404, "API endpoint not found")

    def log_message(self, format, *args):
        # Clean logging
        logger.debug(f"[WebUI] {self.address_string()} - {format % args}")


def start_server(host: str = "0.0.0.0", port: int = 8000):
    server = ThreadingHTTPServer((host, port), JobAPIHandler)
    logger.info(f"[WebUI] Server running at: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("[WebUI] Server stopped.")
        server.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    host = sys.argv[2] if len(sys.argv) > 2 else "0.0.0.0"
    start_server(host, port)
