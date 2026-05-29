"""Corpus data models (Phase 0)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AllowedUrl:
    url: str
    scheme_id: str
    document_type: str


@dataclass
class CitationRules:
    factual: str
    refusal_default_scheme_id: str


@dataclass
class Manifest:
    corpus_version: str
    policy: str
    citation_rules: CitationRules
    allowed_urls: list[AllowedUrl]


@dataclass
class Scheme:
    id: str
    name: str
    category: str
    groww_url: str
    aliases: list[str] = field(default_factory=list)


@dataclass
class SchemesRegistry:
    amc_name: str
    amc_website: str
    product_context: str
    schemes: list[Scheme]
