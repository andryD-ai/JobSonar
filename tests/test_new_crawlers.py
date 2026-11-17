"""Unit tests for JoyWork, LinkedIn, FlexJobs, and Glassdoor crawler parsers."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crawlers.factory import crawler_factory
from crawlers.joywork import JoyWorkCrawler
from crawlers.linkedin import LinkedInCrawler
from crawlers.flexjobs import FlexJobsCrawler
from crawlers.glassdoor import GlassdoorCrawler


def test_factory_registration():
    sources = crawler_factory.get_available_sources()
    for name in ("itviec", "careerviet", "topcv", "joywork", "linkedin", "flexjobs", "glassdoor", "facebook"):
        assert name in sources, f"{name} missing from CrawlerFactory"
        assert crawler_factory.get_crawler(name).name == name


def test_joywork_parser():
    crawler = JoyWorkCrawler()
    sample_item = {
        "id": "job123",
        "title": "Senior AI Engineer",
        "slug": "senior-ai-engineer",
        "locations": ["ha-noi"],
        "workModes": ["HYBRID"],
        "currency": "VND",
        "salaryMin": 30000000,
        "salaryMax": 50000000,
        "experienceLevel": "Y3_5",
        "tags": ["Python", "LLM", "RAG"],
        "company": {"name": "TechCorp VN"},
        "tasks": "<p>Build LLM agents</p>",
        "skills": "<p>Python, FastAPI</p>",
        "benefitsIncome": "<p>13th month salary</p>",
        "createdAt": "2026-11-10T00:00:00Z",
    }
    job = crawler._parse_item(sample_item, "AI Engineer")
    assert job is not None
    assert job.source == "joywork"
    assert job.title == "Senior AI Engineer"
    assert job.company == "TechCorp VN"
    assert "Hà Nội" in job.location
    assert "Hybrid" in job.location
    assert job.salary_min == 30_000_000.0
    assert job.salary_max == 50_000_000.0
    assert "Python" in job.requirements
    assert job.job_url == "https://joywork.vn/jobs/senior-ai-engineer--job123"


def test_linkedin_parser():
    crawler = LinkedInCrawler()
    html = """
    <ul>
      <li>
        <div class="base-card">
          <a class="base-card__full-link" href="https://www.linkedin.com/jobs/view/12345?trk=test"></a>
          <h3 class="base-search-card__title">AI Engineer</h3>
          <h4 class="base-search-card__subtitle">Global AI Labs</h4>
          <span class="job-search-card__location">Hanoi, Vietnam</span>
          <span class="job-search-card__salary-info">$2,000 - $3,500</span>
          <time datetime="2026-11-11">1 day ago</time>
        </div>
      </li>
    </ul>
    """
    jobs = crawler._parse_cards(html, "AI Engineer")
    assert len(jobs) == 1
    assert jobs[0].source == "linkedin"
    assert jobs[0].title == "AI Engineer"
    assert jobs[0].company == "Global AI Labs"
    assert jobs[0].location == "Hanoi, Vietnam"
    assert jobs[0].salary_min == 2000.0
    assert jobs[0].salary_max == 3500.0
    assert jobs[0].job_url == "https://www.linkedin.com/jobs/view/12345"


def test_flexjobs_parser():
    crawler = FlexJobsCrawler()
    html = """
    <div data-testid="job-card">
      <a data-testid="job-title" href="/publicjobs/ai-engineer-123">Remote AI Engineer</a>
      <span data-testid="company-name">RemoteFirst Co</span>
      <span data-testid="job-location">Remote - Anywhere</span>
      <span data-testid="job-salary">$100,000 - $130,000</span>
      <p data-testid="job-description">Work on generative AI systems.</p>
    </div>
    """
    jobs = crawler.parse_html(html, "AI Engineer")
    assert len(jobs) == 1
    assert jobs[0].source == "flexjobs"
    assert jobs[0].title == "Remote AI Engineer"
    assert jobs[0].company == "RemoteFirst Co"
    assert jobs[0].location == "Remote - Anywhere"
    assert jobs[0].job_url == "https://www.flexjobs.com/publicjobs/ai-engineer-123"


def test_glassdoor_parser():
    crawler = GlassdoorCrawler()
    html = """
    <ul>
      <li data-test="jobListing">
        <a data-test="job-title" href="/job-listing/ai-eng-123.htm">Senior AI Engineer</a>
        <span data-test="employer-short-name">VN Fintech</span>
        <span data-test="emp-location">Ho Chi Minh City</span>
        <span data-test="detailSalary">$2,500 - $4,000</span>
        <div data-test="job-description-snippet">Build ML pipelines.</div>
      </li>
    </ul>
    """
    jobs = crawler.parse_html(html, "AI Engineer")
    assert len(jobs) == 1
    assert jobs[0].source == "glassdoor"
    assert jobs[0].title == "Senior AI Engineer"
    assert jobs[0].company == "VN Fintech"
    assert jobs[0].location == "Ho Chi Minh City"
    assert jobs[0].salary_min == 2500.0
    assert jobs[0].salary_max == 4000.0


from crawlers.remotive import RemotiveCrawler


def test_remotive_parser():
    crawler = RemotiveCrawler()
    sample_item = {
        "id": 1001,
        "title": "Senior AI & Python Engineer",
        "company_name": "Global AI Lab",
        "url": "https://remotive.com/remote-jobs/1001",
        "candidate_required_location": "Worldwide",
        "salary": "$80,000 - $120,000",
        "description": "<p>Build agentic AI workflows</p>",
        "tags": ["AI", "Python", "LLM"],
        "job_type": "full_time",
        "publication_date": "2026-11-12T00:00:00"
    }
    job = crawler._parse_item(sample_item, "AI Engineer")
    assert job is not None
    assert job.source == "remotive"
    assert job.title == "Senior AI & Python Engineer"
    assert job.company == "Global AI Lab"
    assert "Remote" in job.location
    assert job.is_remote is True
    assert job.salary_min == 80000.0
    assert job.salary_max == 120000.0


if __name__ == "__main__":
    test_factory_registration()
    test_joywork_parser()
    test_linkedin_parser()
    test_flexjobs_parser()
    test_glassdoor_parser()
    test_remotive_parser()
    print("All new crawler unit tests passed!")
