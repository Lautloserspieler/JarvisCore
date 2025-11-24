from unittest import mock

from services.crawler_service.config import CrawlerConfig, NetworkConfig, ResourceLimits
from services.crawler_service.security_guard import SecurityGuard


def build_config(tmp_path):
    return CrawlerConfig(
        listen_host="127.0.0.1",
        listen_port=8090,
        api_key="test",
        data_dir=str(tmp_path),
        db_path=str(tmp_path / "crawler.db"),
        resource_limits=ResourceLimits(max_cpu_percent=90, max_memory_mb=4096, max_disk_write_mb_per_min=100),
        network=NetworkConfig(
            allowed_domains=["example.com", "wikipedia.org"],
            max_requests_per_minute=10,
            respect_robots_txt=True,
            user_agent="TestCrawler",
        ),
    )


def test_domain_whitelist_allows_subdomains(tmp_path):
    guard = SecurityGuard(build_config(tmp_path))
    assert guard.check_domain("https://www.example.com/page")
    assert guard.check_domain("https://docs.wikipedia.org/article")
    assert guard.check_domain("https://wikipedia.org/wiki/Test")
    assert not guard.check_domain("https://forbidden.org")


def test_robots_failure_is_permissive(tmp_path):
    guard = SecurityGuard(build_config(tmp_path))
    with mock.patch.object(SecurityGuard, "_get_robots_parser", return_value=None):
        assert guard.allowed_by_robots("https://example.com/page")
