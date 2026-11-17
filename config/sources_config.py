"""Sources configuration manager for job crawling."""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from config.settings import settings
from utils.logger import logger

SOURCES_JSON_PATH = settings.DATA_DIR / "sources.json"

DEFAULT_SOURCES = [
    {
        "id": "itviec",
        "name": "ITviec",
        "category": "Tech VN",
        "badge_color": "red",
        "enabled": True,
        "recommended": True,
        "requires_vpn": False,
        "requires_login": False,
        "description": "Nền tảng việc làm CNTT & Phần mềm hàng đầu VN (Tech stack, phúc lợi rõ ràng)"
    },
    {
        "id": "careerviet",
        "name": "CareerViet",
        "category": "Đa ngành VN",
        "badge_color": "blue",
        "enabled": True,
        "recommended": True,
        "requires_vpn": False,
        "requires_login": False,
        "description": "Doanh nghiệp lớn, Khối Ngân hàng, Tài chính & FDI tại Việt Nam"
    },
    {
        "id": "joywork",
        "name": "JoyWork",
        "category": "Startup & Culture VN",
        "badge_color": "teal",
        "enabled": True,
        "recommended": True,
        "requires_vpn": False,
        "requires_login": False,
        "description": "Nền tảng việc làm văn hóa tốt, tích hợp API JSON chính thức cực kỳ ổn định"
    },
    {
        "id": "linkedin",
        "name": "LinkedIn",
        "category": "Quốc tế & VN",
        "badge_color": "sky",
        "enabled": True,
        "recommended": True,
        "requires_vpn": True,
        "requires_login": False,
        "description": "Mạng xã hội nghề nghiệp toàn cầu (Nên bật VPN nếu truy cập từ Việt Nam)"
    },
    {
        "id": "glassdoor",
        "name": "Glassdoor",
        "category": "Quốc tế & Remote",
        "badge_color": "emerald",
        "enabled": True,
        "recommended": False,
        "requires_vpn": False,
        "requires_login": False,
        "description": "Việc làm quốc tế, các vị trí Remote trả USD và đánh giá công ty"
    },
    {
        "id": "topcv",
        "name": "TopCV",
        "category": "Đa ngành VN",
        "badge_color": "amber",
        "enabled": False,
        "recommended": False,
        "requires_vpn": False,
        "requires_login": False,
        "description": "Nền tảng tuyển dụng phổ biến (Có lọc chặt chẽ tiêu đề để tránh tin rác quảng cáo)"
    },
    {
        "id": "facebook",
        "name": "Facebook Fanpage",
        "category": "Mạng xã hội",
        "badge_color": "indigo",
        "enabled": True,
        "recommended": False,
        "requires_vpn": False,
        "requires_login": True,
        "description": "Cào bài tuyển dụng Fanpage/Group qua Playwright (Cần chạy fb-login 1 lần trước)"
    },
    {
        "id": "remotive",
        "name": "Remotive",
        "category": "Remote Global 100%",
        "badge_color": "emerald",
        "enabled": True,
        "recommended": True,
        "requires_vpn": False,
        "requires_login": False,
        "description": "Nền tảng việc làm Remote & Online toàn cầu cho IT/Dev/AI (API chính thức, 100% Remote, lương USD)"
    },
    {
        "id": "flexjobs",
        "name": "FlexJobs",
        "category": "Remote Global",
        "badge_color": "purple",
        "enabled": False,
        "recommended": False,
        "requires_vpn": True,
        "requires_login": False,
        "description": "Nền tảng việc làm Remote & Freelance chuyên nghiệp quốc tế"
    }
]


class SourcesConfigManager:
    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = file_path or SOURCES_JSON_PATH
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_SOURCES, f, ensure_ascii=False, indent=2)

    def get_all(self) -> List[Dict[str, Any]]:
        self._ensure_file()
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading sources config: {e}")
            return DEFAULT_SOURCES

    def get_enabled(self) -> List[Dict[str, Any]]:
        return [s for s in self.get_all() if s.get("enabled", False)]

    def get_enabled_ids(self) -> List[str]:
        return [s["id"] for s in self.get_enabled()]

    def toggle(self, source_id: str, enabled: bool) -> bool:
        sources = self.get_all()
        found = False
        for s in sources:
            if s.get("id") == source_id:
                s["enabled"] = bool(enabled)
                found = True
                break
        if found:
            self._save(sources)
        return found

    def add_source(self, data: Dict[str, Any]) -> Dict[str, Any]:
        sources = self.get_all()
        source_id = data.get("id", "").strip().lower()
        if not source_id:
            raise ValueError("Mã nguồn (ID) không được để trống")

        for s in sources:
            if s.get("id") == source_id:
                raise ValueError(f"Nguồn tuyển dụng với mã '{source_id}' đã tồn tại!")

        new_source = {
            "id": source_id,
            "name": data.get("name", source_id.title()),
            "category": data.get("category", "Tùy chỉnh"),
            "badge_color": data.get("badge_color", "teal"),
            "enabled": bool(data.get("enabled", True)),
            "recommended": bool(data.get("recommended", False)),
            "requires_vpn": bool(data.get("requires_vpn", False)),
            "requires_login": bool(data.get("requires_login", False)),
            "description": data.get("description", ""),
            "custom_url": data.get("custom_url", "")
        }
        sources.append(new_source)
        self._save(sources)
        return new_source

    def delete_source(self, source_id: str) -> bool:
        sources = self.get_all()
        new_sources = [s for s in sources if s.get("id") != source_id]
        if len(new_sources) != len(sources):
            self._save(new_sources)
            return True
        return False

    def _save(self, sources: List[Dict[str, Any]]) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(sources, f, ensure_ascii=False, indent=2)


sources_config = SourcesConfigManager()
