"""Command-line interface (CLI) for JobSonar."""
import sys
import argparse
from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from config.settings import settings
from db.database import db
from db.repository import job_repo, report_repo
from crawlers.factory import crawler_factory
from crawlers.facebook import FacebookCrawler
from llm.synthesizer import JobSynthesizer
from utils.logger import logger

console = Console()


def show_banner():
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║       🔍 VIETNAM JOB MARKET SCANNER & LLM SYNTHESIZER        ║
    ║  ITviec • CareerViet • TopCV • JoyWork • LinkedIn • Glassdoor║
    ║      FlexJobs • Facebook  |  SQLite3  |  Google Gemini       ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    console.print(f"[bold cyan]{banner}[/bold cyan]")


def cmd_crawl(args):
    """Crawls jobs from specified sources and saves to SQLite."""
    show_banner()
    keyword = args.keyword
    sources: List[str] = [s.strip().lower() for s in args.sources.split(",") if s.strip()]
    limit = args.limit
    location = getattr(args, "location", None)
    if getattr(args, "remote", False):
        location = "Remote" if not location else f"{location}, Remote"

    console.print(f"[bold green]▶ Bắt đầu cào dữ liệu cho từ khóa:[/bold green] [bold yellow]'{keyword}'[/bold yellow]")
    if location:
        console.print(f"Khu vực ưu tiên: [bold cyan]{location}[/bold cyan]")
    console.print(f"Nguồn: {', '.join(sources)} | Giới hạn mỗi nguồn: {limit}\n")

    total_crawled = 0
    total_inserted = 0
    total_duplicates = 0

    results_table = Table(title=f"Kết quả cào tin tuyển dụng: '{keyword}'", show_header=True, header_style="bold magenta")
    results_table.add_column("Nguồn", style="cyan")
    results_table.add_column("Số tin cào được", justify="right")
    results_table.add_column("Mới thêm vào DB", justify="right", style="green")
    results_table.add_column("Trùng lặp / Cập nhật", justify="right", style="yellow")

    for src in sources:
        try:
            crawler = crawler_factory.get_crawler(src)
            jobs = crawler.search(keyword, limit=limit, location=location)
            inserted, duplicates = job_repo.save_jobs_batch(jobs)

            total_crawled += len(jobs)
            total_inserted += inserted
            total_duplicates += duplicates

            results_table.add_row(src.upper(), str(len(jobs)), str(inserted), str(duplicates))
        except Exception as e:
            console.print(f"[bold red]Lỗi khi cào nguồn {src}:[/bold red] {e}")
            results_table.add_row(src.upper(), "0 (Lỗi)", "0", "0")

    console.print(results_table)
    console.print(
        f"\n[bold green]✔ Hoàn tất:[/bold green] Tổng cào: [bold]{total_crawled}[/bold] | "
        f"Mới: [bold green]{total_inserted}[/bold green] | Trùng lặp: [bold yellow]{total_duplicates}[/bold yellow]\n"
    )


def cmd_fb_login(args):
    """Opens browser to log into Facebook once and save persistent session."""
    show_banner()
    fb = FacebookCrawler()
    fb.interactive_login()


def cmd_fb_crawl(args):
    """Crawls Facebook Fanpage or group posts with random delays up to 10s."""
    show_banner()
    url = args.url
    limit = args.limit
    min_delay = args.min_delay
    max_delay = args.max_delay
    keyword = args.keyword or "Facebook Fanpage"

    console.print(f"[bold green]▶ Bắt đầu cào Fanpage Facebook:[/bold green] [cyan]{url}[/cyan]")
    console.print(f"Giới hạn: {limit} bài | Nghỉ ngẫu nhiên: {min_delay}s - {max_delay}s mỗi lần cuộn\n")

    fb = FacebookCrawler()
    jobs = fb.crawl_fanpage(url, keyword=keyword, limit=limit, min_delay=min_delay, max_delay=max_delay)

    inserted, duplicates = job_repo.save_jobs_batch(jobs)
    console.print(
        f"\n[bold green]✔ Đã cào xong từ Facebook:[/bold green] {len(jobs)} bài | "
        f"Lưu mới: [bold green]{inserted}[/bold green] | Đã có: [bold yellow]{duplicates}[/bold yellow]"
    )


def cmd_fb_import(args):
    """Imports Facebook posts from a JSON, HTML, or TXT file."""
    show_banner()
    fb = FacebookCrawler()
    jobs = fb.import_from_file(args.file, keyword=args.keyword or "Facebook File Import")
    inserted, duplicates = job_repo.save_jobs_batch(jobs)
    console.print(
        f"[bold green]✔ Đã import:[/bold green] {len(jobs)} bài | "
        f"Lưu mới: [bold green]{inserted}[/bold green] | Đã có: [bold yellow]{duplicates}[/bold yellow]"
    )


def cmd_report(args):
    """Synthesizes a market report using LLM."""
    show_banner()
    keyword = args.keyword
    provider = args.provider or settings.DEFAULT_LLM_PROVIDER
    api_key = args.api_key or None
    limit = args.limit

    console.print(f"[bold green]▶ Đang tạo báo cáo thị trường cho vị trí:[/bold green] [bold yellow]'{keyword}'[/bold yellow]")
    console.print(f"Mô hình LLM: [cyan]{provider.upper()}[/cyan] | Số tin phân tích tối đa: {limit}\n")

    try:
        synthesizer = JobSynthesizer(provider=provider, api_key=api_key)
        report_md, report_path = synthesizer.generate_report(keyword=keyword, limit=limit)

        console.print(Panel(
            f"[bold green]✔ Báo cáo đã được tạo và lưu thành công![/bold green]\n"
            f"Đường dẫn file: [bold cyan]{report_path}[/bold cyan]",
            title="Báo cáo hoàn tất",
            border_style="green"
        ))

        if args.preview:
            console.print("\n" + "=" * 60)
            console.print(Markdown(report_md))
            console.print("=" * 60 + "\n")
    except Exception as e:
        console.print(f"[bold red]Lỗi khi tạo báo cáo:[/bold red] {e}")


def cmd_run(args):
    """End-to-end: Crawl -> Store in SQLite -> Synthesize LLM Report."""
    cmd_crawl(args)
    if args.report:
        cmd_report(args)


def cmd_web(args):
    """Starts the local Web UI server."""
    from web.server import start_server
    port = args.port
    console.print(f"[bold green]▶ Khởi động Web UI tại:[/bold green] [bold yellow]http://{args.host}:{port}[/bold yellow] (Local: http://127.0.0.1:{port})")
    start_server(host=args.host, port=port)


def cmd_stats(args):
    """Displays SQLite database statistics."""
    show_banner()
    stats = job_repo.get_stats()
    reports = report_repo.list_reports(limit=5)

    console.print(Panel(f"Tổng số tin tuyển dụng đang lưu trong SQLite: [bold green]{stats['total_jobs']}[/bold green]", title="Database Overview"))

    source_table = Table(title="Phân bố theo nguồn dữ liệu", header_style="bold magenta")
    source_table.add_column("Nguồn", style="cyan")
    source_table.add_column("Số lượng", justify="right")
    for src, cnt in stats["by_source"].items():
        source_table.add_row(src.upper(), str(cnt))
    console.print(source_table)

    if stats["top_companies"]:
        comp_table = Table(title="Top nhà tuyển dụng nhiều nhất", header_style="bold magenta")
        comp_table.add_column("Công ty", style="green")
        comp_table.add_column("Số tin", justify="right")
        for item in stats["top_companies"]:
            for comp, cnt in item.items():
                comp_table.add_row(comp, str(cnt))
        console.print(comp_table)

    if reports:
        rep_table = Table(title="Lịch sử các báo cáo LLM gần nhất", header_style="bold magenta")
        rep_table.add_column("ID", justify="right")
        rep_table.add_column("Từ khóa", style="yellow")
        rep_table.add_column("Số jobs phân tích", justify="right")
        rep_table.add_column("Mô hình", style="cyan")
        rep_table.add_column("Ngày tạo")
        for r in reports:
            rep_table.add_row(str(r.id), r.keyword, str(r.total_jobs_analyzed), r.llm_model, str(r.created_at))
        console.print(rep_table)


def main():
    parser = argparse.ArgumentParser(
        description="Vietnam Job Market Scanner & LLM Report Synthesizer",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Lệnh chức năng")

    # Command: crawl
    crawl_parser = subparsers.add_parser("crawl", help="Cào tin tuyển dụng từ các trang web")
    crawl_parser.add_argument("-k", "--keyword", required=True, help="Từ khóa / Vị trí tuyển dụng (VD: 'Python', 'Golang')")
    crawl_parser.add_argument("-s", "--sources", default="itviec,careerviet,joywork", help="Các nguồn cào, phân tách bởi dấu phẩy (hỗ trợ: itviec,careerviet,topcv,joywork,linkedin,flexjobs,glassdoor,remotive,facebook)")
    crawl_parser.add_argument("-l", "--limit", type=int, default=25, help="Số lượng tin tối đa mỗi nguồn (mặc định: 25)")
    crawl_parser.add_argument("--location", "-loc", default=None, help="Khu vực làm việc cần lọc (VD: 'Ha Noi, Da Nang')")
    crawl_parser.add_argument("--remote", action="store_true", default=False, help="Chỉ tìm kiếm việc làm Remote / Làm việc từ xa (Online)")
    crawl_parser.set_defaults(func=cmd_crawl)

    # Command: run (crawl + report)
    run_parser = subparsers.add_parser("run", help="Chạy toàn trình: Cào dữ liệu -> Lưu SQLite -> Xuất báo cáo LLM")
    run_parser.add_argument("-k", "--keyword", required=True, help="Từ khóa / Vị trí tuyển dụng")
    run_parser.add_argument("-s", "--sources", default="itviec,careerviet,joywork", help="Các nguồn cào (hỗ trợ: itviec,careerviet,topcv,joywork,linkedin,flexjobs,glassdoor,remotive,facebook)")
    run_parser.add_argument("-l", "--limit", type=int, default=25, help="Số lượng tin tối đa mỗi nguồn")
    run_parser.add_argument("--location", "-loc", default=None, help="Khu vực làm việc cần lọc (VD: 'Ha Noi, Da Nang')")
    run_parser.add_argument("--remote", action="store_true", default=False, help="Chỉ tìm kiếm việc làm Remote / Làm việc từ xa (Online)")
    run_parser.add_argument("--report", action="store_true", default=True, help="Tự động tạo báo cáo LLM sau khi cào xong")
    run_parser.add_argument("--provider", default="gemini", help="LLM provider: gemini | openai | ollama")
    run_parser.add_argument("--api-key", default=None, help="Google Gemini hoặc OpenAI API Key")
    run_parser.add_argument("--preview", action="store_true", help="Hiển thị toàn bộ báo cáo trên Terminal sau khi tạo")
    run_parser.set_defaults(func=cmd_run)

    # Command: report
    report_parser = subparsers.add_parser("report", help="Dùng LLM tổng hợp báo cáo từ dữ liệu đã có trong SQLite")
    report_parser.add_argument("-k", "--keyword", required=True, help="Từ khóa vị trí cần tổng hợp báo cáo")
    report_parser.add_argument("--provider", default="gemini", help="Nhà cung cấp LLM: gemini | openai | ollama (mặc định: gemini)")
    report_parser.add_argument("--api-key", default=None, help="API key của LLM nếu chưa lưu trong .env")
    report_parser.add_argument("-l", "--limit", type=int, default=100, help="Số lượng tin lấy ra phân tích (mặc định: 100)")
    report_parser.add_argument("--preview", action="store_true", help="In toàn bộ báo cáo lên Terminal")
    report_parser.set_defaults(func=cmd_report)

    # Command: fb-login
    fb_login_parser = subparsers.add_parser("fb-login", help="Đăng nhập tài khoản Facebook 1 lần duy nhất để lưu session profile")
    fb_login_parser.set_defaults(func=cmd_fb_login)

    # Command: fb-crawl
    fb_crawl_parser = subparsers.add_parser("fb-crawl", help="Cào bài viết từ một Fanpage/Group Facebook cụ thể")
    fb_crawl_parser.add_argument("-u", "--url", required=True, help="URL của Fanpage hoặc Group Facebook cần cào")
    fb_crawl_parser.add_argument("-k", "--keyword", default="Facebook Fanpage", help="Từ khóa nhãn phân loại")
    fb_crawl_parser.add_argument("-l", "--limit", type=int, default=15, help="Số lượng bài viết cần cào (mặc định: 15)")
    fb_crawl_parser.add_argument("--min-delay", type=float, default=2.0, help="Thời gian nghỉ tối thiểu giữa các lần cuộn (giây)")
    fb_crawl_parser.add_argument("--max-delay", type=float, default=10.0, help="Thời gian nghỉ tối đa giữa các lần cuộn (giây, mặc định: 10s)")
    fb_crawl_parser.set_defaults(func=cmd_fb_crawl)

    # Command: fb-import
    fb_import_parser = subparsers.add_parser("fb-import", help="Import bài viết Facebook từ file JSON, HTML hoặc TXT")
    fb_import_parser.add_argument("-f", "--file", required=True, help="Đường dẫn tới file chứa bài viết")
    fb_import_parser.add_argument("-k", "--keyword", default="Facebook Import", help="Từ khóa vị trí")
    fb_import_parser.set_defaults(func=cmd_fb_import)

    # Command: stats
    stats_parser = subparsers.add_parser("stats", help="Xem thống kê tổng quan dữ liệu trong cơ sở dữ liệu SQLite")
    stats_parser.set_defaults(func=cmd_stats)

    # Command: web
    web_parser = subparsers.add_parser("web", help="Khởi chạy Web UI trực quan trên trình duyệt")
    web_parser.add_argument("-p", "--port", type=int, default=8000, help="Cổng chạy Web UI (mặc định: 8000)")
    web_parser.add_argument("--host", default="0.0.0.0", help="Địa chỉ host lắng nghe (mặc định: 0.0.0.0)")
    web_parser.set_defaults(func=cmd_web)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
