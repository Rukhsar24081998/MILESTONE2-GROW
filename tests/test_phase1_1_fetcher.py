"""Phase 1.1 tests — allowlist fetcher."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from ingestion.fetcher import (
    ALLOWLIST_REJECT,
    AllowlistRejectedError,
    FetchError,
    assert_url_allowlisted,
    fetch_one,
)
from app.corpus.loader import EXPECTED_URL_COUNT, load_manifest

SAMPLE_HTML = b"<html><body><h1>HDFC Test Fund</h1><p>Expense ratio 0.73%</p></body></html>"
MID_CAP_URL = "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
BAD_URL = "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"


class _MockClient:
    """Minimal httpx client stand-in for tests."""

    def __init__(self, response: httpx.Response) -> None:
        self._response = response

    def __enter__(self) -> _MockClient:
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def get(self, url: str, timeout: float | None = None) -> httpx.Response:
        return self._response


def _mock_factory(response: httpx.Response):
    def factory() -> _MockClient:
        return _MockClient(response)

    return factory


def test_assert_url_allowlisted_rejects_unknown_groww_url():
    with pytest.raises(AllowlistRejectedError) as exc_info:
        assert_url_allowlisted(BAD_URL)
    assert exc_info.value.code == ALLOWLIST_REJECT


def test_assert_url_allowlisted_accepts_manifest_url():
    canonical = assert_url_allowlisted(MID_CAP_URL)
    assert canonical == MID_CAP_URL


def test_fetch_one_writes_html_and_meta(tmp_path: Path):
    response = httpx.Response(200, content=SAMPLE_HTML, request=httpx.Request("GET", MID_CAP_URL))
    result = fetch_one(
        "hdfc-mid-cap-direct-growth",
        MID_CAP_URL,
        raw_dir=tmp_path,
        client_factory=_mock_factory(response),
    )

    assert result.skipped is False
    assert result.html_path.exists()
    assert result.meta_path.exists()
    assert result.html_path.read_bytes() == SAMPLE_HTML

    meta = json.loads(result.meta_path.read_text(encoding="utf-8"))
    assert meta["scheme_id"] == "hdfc-mid-cap-direct-growth"
    assert meta["source_url"] == MID_CAP_URL
    assert meta["status_code"] == 200
    assert meta["content_length"] == len(SAMPLE_HTML)
    assert meta["fetched_at"].endswith("Z")
    assert "T" in meta["fetched_at"]


def test_fetch_one_rejects_non_allowlisted_before_http(tmp_path: Path):
    with pytest.raises(AllowlistRejectedError):
        fetch_one(
            "fake-scheme",
            BAD_URL,
            raw_dir=tmp_path,
            client_factory=_mock_factory(
                httpx.Response(200, content=SAMPLE_HTML, request=httpx.Request("GET", BAD_URL))
            ),
        )


def test_fetch_one_redirect_mismatch_fails(tmp_path: Path):
    wrong_final = "https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth"
    response = httpx.Response(
        200,
        content=SAMPLE_HTML,
        request=httpx.Request("GET", wrong_final),
    )
    with pytest.raises(FetchError, match="redirect final URL mismatch"):
        fetch_one(
            "hdfc-mid-cap-direct-growth",
            MID_CAP_URL,
            raw_dir=tmp_path,
            client_factory=_mock_factory(response),
        )


def test_fetch_one_skips_when_cached(tmp_path: Path):
    scheme_id = "hdfc-mid-cap-direct-growth"
    factory = _mock_factory(
        httpx.Response(200, content=SAMPLE_HTML, request=httpx.Request("GET", MID_CAP_URL))
    )

    first = fetch_one(scheme_id, MID_CAP_URL, raw_dir=tmp_path, client_factory=factory)
    assert first.skipped is False

    second = fetch_one(scheme_id, MID_CAP_URL, raw_dir=tmp_path, client_factory=factory)
    assert second.skipped is True


def test_fetch_one_force_refetches(tmp_path: Path):
    scheme_id = "hdfc-mid-cap-direct-growth"
    calls: list[str] = []

    class CountingClient(_MockClient):
        def get(self, url: str, timeout: float | None = None) -> httpx.Response:
            calls.append(url)
            return httpx.Response(200, content=SAMPLE_HTML, request=httpx.Request("GET", url))

    def factory() -> CountingClient:
        return CountingClient(
            httpx.Response(200, content=SAMPLE_HTML, request=httpx.Request("GET", MID_CAP_URL))
        )

    fetch_one(scheme_id, MID_CAP_URL, raw_dir=tmp_path, client_factory=factory)
    fetch_one(scheme_id, MID_CAP_URL, raw_dir=tmp_path, force=True, client_factory=factory)
    assert len(calls) == 2


def test_fetch_all_test_reject_cli():
    from ingestion.fetch_all import main

    assert main(["--test-reject", BAD_URL]) == 0
    assert main(["--test-reject", MID_CAP_URL]) == 1


def test_manifest_has_five_entries():
    manifest = load_manifest()
    assert len(manifest.allowed_urls) == EXPECTED_URL_COUNT
