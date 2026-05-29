"""Phase 1.1 — Allowlist-gated HTTP fetcher for Groww scheme pages."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import httpx

from app.config import INGESTION_RAW_DIR
from app.corpus.loader import _normalize_url, is_url_allowlisted, load_manifest

logger = logging.getLogger(__name__)

ALLOWLIST_REJECT = "ALLOWLIST_REJECT"
DEFAULT_TIMEOUT_SEC = 30.0
DEFAULT_RATE_LIMIT_SEC = 1.0
DEFAULT_MAX_RETRIES = 3
RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
USER_AGENT = (
    "Mozilla/5.0 (compatible; MF-FAQ-Assistant/0.1; +https://github.com/edu/milestone2)"
)


class AllowlistRejectedError(Exception):
    """Raised when a URL is not in corpus/manifest.yaml."""

    code = ALLOWLIST_REJECT

    def __init__(self, url: str, message: str | None = None) -> None:
        self.url = url
        super().__init__(message or f"{ALLOWLIST_REJECT}: URL not in manifest allowlist: {url}")


class FetchError(Exception):
    """Raised when fetch fails after retries or redirect validation."""

    def __init__(self, url: str, reason: str) -> None:
        self.url = url
        self.reason = reason
        super().__init__(f"Fetch failed for {url}: {reason}")


@dataclass
class FetchResult:
    scheme_id: str
    source_url: str
    final_url: str
    status_code: int
    content_length: int
    fetched_at: str
    html_path: Path
    meta_path: Path
    skipped: bool = False


def assert_url_allowlisted(url: str) -> str:
    """Return canonical URL or raise AllowlistRejectedError."""
    canonical = _normalize_url(url)
    if not is_url_allowlisted(canonical):
        raise AllowlistRejectedError(url)
    return canonical


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _validate_final_url(expected_canonical: str, response: httpx.Response) -> str:
    final = _normalize_url(str(response.url))
    if final != expected_canonical:
        raise FetchError(
            expected_canonical,
            f"redirect final URL mismatch: got {final}",
        )
    return final


def _write_atomic(path: Path, content: str | bytes, *, binary: bool = False) -> None:
    """Write only on success; avoid leaving partial files as complete."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        if binary:
            tmp.write_bytes(content)  # type: ignore[arg-type]
        else:
            tmp.write_text(content, encoding="utf-8")
        tmp.replace(path)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise


def fetch_one(
    scheme_id: str,
    url: str,
    *,
    raw_dir: Path | None = None,
    timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    max_retries: int = DEFAULT_MAX_RETRIES,
    force: bool = False,
    client_factory: Callable[[], httpx.Client] | None = None,
) -> FetchResult:
    """
    Fetch a single allowlisted URL and persist HTML + sidecar metadata.

    Raises AllowlistRejectedError if url is not in manifest.
    Raises FetchError on redirect mismatch or exhausted retries.
    """
    canonical = assert_url_allowlisted(url)
    raw_dir = raw_dir or INGESTION_RAW_DIR
    html_path = raw_dir / f"{scheme_id}.html"
    meta_path = raw_dir / f"{scheme_id}.meta.json"

    if html_path.exists() and meta_path.exists() and not force:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        logger.info("Skipping %s (already fetched at %s)", scheme_id, meta.get("fetched_at"))
        return FetchResult(
            scheme_id=scheme_id,
            source_url=canonical,
            final_url=meta.get("final_url", canonical),
            status_code=meta.get("status_code", 0),
            content_length=meta.get("content_length", 0),
            fetched_at=meta["fetched_at"],
            html_path=html_path,
            meta_path=meta_path,
            skipped=True,
        )

    last_error: str | None = None
    for attempt in range(max_retries):
        try:
            if client_factory:
                with client_factory() as client:
                    response = _get_with_retry_status(client, canonical, timeout_sec)
            else:
                with httpx.Client(
                    follow_redirects=True,
                    timeout=timeout_sec,
                    headers={"User-Agent": USER_AGENT},
                ) as client:
                    response = _get_with_retry_status(client, canonical, timeout_sec)

            final_url = _validate_final_url(canonical, response)
            body = response.content
            if not body:
                raise FetchError(canonical, "empty response body")

            fetched_at = _iso_utc_now()
            _write_atomic(html_path, body, binary=True)

            meta = {
                "scheme_id": scheme_id,
                "source_url": canonical,
                "final_url": final_url,
                "fetched_at": fetched_at,
                "status_code": response.status_code,
                "content_length": len(body),
            }
            _write_atomic(meta_path, json.dumps(meta, indent=2) + "\n")

            logger.info(
                "Fetched %s (%s bytes, HTTP %s)",
                scheme_id,
                len(body),
                response.status_code,
            )
            return FetchResult(
                scheme_id=scheme_id,
                source_url=canonical,
                final_url=final_url,
                status_code=response.status_code,
                content_length=len(body),
                fetched_at=fetched_at,
                html_path=html_path,
                meta_path=meta_path,
            )
        except AllowlistRejectedError:
            raise
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            last_error = str(exc)
            logger.warning("Attempt %s/%s network error for %s: %s", attempt + 1, max_retries, scheme_id, exc)
        except FetchError as exc:
            last_error = exc.reason
            logger.warning("Attempt %s/%s failed for %s: %s", attempt + 1, max_retries, scheme_id, exc.reason)
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            last_error = f"HTTP {status}"
            if status not in RETRYABLE_STATUS:
                raise FetchError(canonical, last_error) from exc
            logger.warning(
                "Attempt %s/%s HTTP %s for %s",
                attempt + 1,
                max_retries,
                status,
                scheme_id,
            )

        if attempt < max_retries - 1:
            backoff = 2**attempt
            time.sleep(backoff)

    raise FetchError(canonical, last_error or "unknown error")


def _get_with_retry_status(client: httpx.Client, url: str, timeout_sec: float) -> httpx.Response:
    response = client.get(url, timeout=timeout_sec)
    if response.status_code >= 400:
        response.raise_for_status()
    return response


def fetch_all_from_manifest(
    *,
    raw_dir: Path | None = None,
    rate_limit_sec: float = DEFAULT_RATE_LIMIT_SEC,
    force: bool = False,
    scheme_id: str | None = None,
) -> list[FetchResult]:
    """Fetch all (or one) entries from corpus/manifest.yaml."""
    manifest = load_manifest()
    entries = manifest.allowed_urls
    if scheme_id:
        entries = [e for e in entries if e.scheme_id == scheme_id]
        if not entries:
            raise ValueError(f"scheme_id not in manifest: {scheme_id}")

    results: list[FetchResult] = []
    for i, entry in enumerate(entries):
        if i > 0 and rate_limit_sec > 0:
            time.sleep(rate_limit_sec)
        results.append(
            fetch_one(
                entry.scheme_id,
                entry.url,
                raw_dir=raw_dir,
                force=force,
            )
        )
    return results


def count_raw_html_files(raw_dir: Path | None = None) -> int:
    raw_dir = raw_dir or INGESTION_RAW_DIR
    if not raw_dir.exists():
        return 0
    return len(list(raw_dir.glob("*.html")))
