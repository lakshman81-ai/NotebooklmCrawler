#!/usr/bin/env python3
"""
edu_search.py — Educational Content Retrieval Engine v2

Programmatic Bing search pipeline for K-12 educational content.
Replaces DuckDuckGo with Firefox + Bing via Playwright.

Usage:
    from discovery.edu_search_pipeline import EduSearchPipeline, setup_logger

    setup_logger(level=logging.DEBUG)  # Call once at startup
    pipeline = EduSearchPipeline()
    results = pipeline.search(
        grade=8, subject="Physics", topic="Vectors",
        subtopic="Transformation",
        content_types=["concept_explainer", "material_visual"],
    )

CLI:
    python discovery/edu_search_pipeline.py --grade 8 --subject Physics --topic Vectors --json
"""

import time
import random
import logging
import json
import sys
from urllib.parse import urlparse
from dataclasses import dataclass, field
from discovery.bing_search import EducationalContentSearcher

# ═══════════════════════════════════════════════════════
#  LOGGING
# ═══════════════════════════════════════════════════════

def setup_logger(
    name: str = "edu_search",
    level: int = logging.INFO,
    log_file: str | None = None,
) -> logging.Logger:
    """
    Call once at startup. Without this, you get Python's default
    WARNING-only logger and miss all useful pipeline telemetry.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    logger.addHandler(console)

    if log_file:
        fh = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


logger = logging.getLogger("edu_search")


# ═══════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════

CONTENT_TYPE_KEYWORDS: dict[str, list[str]] = {
    "concept_explainer": ["tutorial", "lesson", "explained", "introduction"],
    "reasoning":         ["derivation", "proof", "worked-example", "step-by-step"],
    "material_visual":   ["flowchart", "diagram", "infographic", "chart"],
    "material_equation": ["equation", "formula", "calculation"],
    "practice":          ["worksheet", "exercise", "quiz", "practice-problems"],
    "video":             ["video", "lecture"],
    "simulation":        ["simulation", "interactive", "virtual-lab"],
    "printable":         ["filetype:pdf", "worksheet", "printable"],
}

GRADE_EXCLUSIONS: dict[str, str] = {
    "K-4":  '-college -university -"high school" -"AP " -calculus -thesis',
    "5-8":  '-college -university -"AP " -thesis -doctoral',
    "9-12": '-"elementary school" -kindergarten -"grade 3" -"grade 2"',
}

TRUSTED_DOMAINS_CORE: list[str] = [
    "khanacademy.org", "ck12.org", "education.com",
    "pbslearningmedia.org", "byjus.com", "openstax.org",
    "brilliant.org", "britannica.com",
]

TRUSTED_DOMAINS_BY_BAND: dict[str, dict[str, list[str]]] = {
    "K-4": {
        "math":           ["abcya.com", "coolmath4kids.com", "mathseeds.com"],
        "science":        ["kids.nationalgeographic.com", "sciencebob.com"],
        "social_studies": ["ducksters.com", "pbskids.org"],
        "language_arts":  ["starfall.com", "readworks.org", "storylineonline.net"],
        "reference":      ["kids.britannica.com", "ducksters.com", "infoplease.com"],
    },
    "5-8": {
        "math":      ["ixl.com", "mathway.com", "desmos.com"],
        "science":   ["byjus.com", "ck12.org"],
        "reference": ["kids.britannica.com", "infoplease.com"],
    },
    "9-12": {
        "math":      ["desmos.com", "brilliant.org"],
        "science":   ["biointeractive.org", "labxchange.org", "ck12.org"],
        "history":   ["crashcourse.com", "bighistoryproject.com"],
        "reference": ["scholarpedia.org", "citizendium.org", "openstax.org"],
    },
}

URL_EXCLUDE_PATTERNS = [
    "/login", "/signup", "/pricing", "/cart", "/checkout",
    "/subscribe", "/premium", "/app-download", "/trial",
]

BLOCK_DOMAINS = [
    "bing.com", "google.com", "googleadservices.com",
    "encrypted", "gstatic.com", "microsoft.com",
    "youtube.com", "facebook.com", "twitter.com", "instagram.com"
]

MAX_RETRIES = 3
BASE_DELAY = 2.0
INTER_REQUEST_DELAY = 1.5


# ═══════════════════════════════════════════════════════
#  EXCEPTIONS
# ═══════════════════════════════════════════════════════

class SearchError(Exception):
    """All retry attempts and backend fallbacks exhausted."""
    pass


# ═══════════════════════════════════════════════════════
#  DATA
# ═══════════════════════════════════════════════════════

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    domain: str = ""
    is_trusted: bool = False

    def to_dict(self) -> dict:
        return {
            "title": self.title, "url": self.url, "snippet": self.snippet,
            "domain": self.domain, "is_trusted": self.is_trusted,
        }


# ═══════════════════════════════════════════════════════
#  PIPELINE
# ═══════════════════════════════════════════════════════

class EduSearchPipeline:
    """
    End-to-end educational content retrieval pipeline using Bing + Firefox.

    Design:
        Each step (resolve → build → fetch → filter) is a public method
        that can be called independently. The search() method orchestrates
        them. This lets you swap or skip steps as needed.
    """

    def __init__(
        self,
        core_domains: list[str] | None = None,
        band_domains: dict | None = None,
        content_keywords: dict | None = None,
    ):
        self.core_domains = core_domains or TRUSTED_DOMAINS_CORE
        self.band_domains = band_domains or TRUSTED_DOMAINS_BY_BAND
        self.content_keywords = content_keywords or CONTENT_TYPE_KEYWORDS

        # Initialize the Bing searcher
        self.searcher = EducationalContentSearcher(
            headless=True,
            config_file='outputs/search_config.json',
            cache_dir='outputs/search_cache'
        )

    # ── Helpers ──────────────────────────────────────

    @staticmethod
    def _get_grade_band(grade: int) -> str:
        if grade <= 4:   return "K-4"
        if grade <= 8:   return "5-8"
        return "9-12"

    @staticmethod
    def _build_site_filter(domains: list[str]) -> str:
        """Bing syntax: (site:a OR site:b OR ...)"""
        if not domains:      return ""
        if len(domains) == 1: return f"site:{domains[0]}"
        return "(" + " OR ".join(f"site:{d}" for d in domains) + ")"

    # ── Step 1: Domain Resolution ────────────────────

    def resolve_domains(
        self, grade: int, subject: str, extra_domains: list[str] | None = None,
    ) -> list[str]:
        """
        Merge core + grade-band + subject-specific + extra domains.
        Returns deduplicated list preserving insertion order.
        """
        domains = list(self.core_domains)
        try:
             grade_int = int(grade)
        except ValueError:
             # Default to middle band if grade parsing fails
             grade_int = 8

        band = self._get_grade_band(grade_int)
        band_map = self.band_domains.get(band, {})

        # Fuzzy match subject to band keys
        subject_lower = subject.lower()
        matched = False
        for key, domain_list in band_map.items():
            if key in subject_lower or subject_lower in key:
                domains.extend(domain_list)
                matched = True
                break

        if not matched:
            logger.debug(
                f"No subject-specific domains for '{subject}' in band {band}. "
                f"Using core domains only."
            )

        # Always include reference alternatives for the band
        if "reference" in band_map:
            domains.extend(band_map["reference"])

        if extra_domains:
            domains.extend(extra_domains)

        # Deduplicate preserving order
        result = list(dict.fromkeys(domains))
        logger.debug(f"Resolved {len(result)} domains for Grade {grade} {subject}")
        return result

    # ── Step 2: Query Construction ───────────────────

    def build_query(
        self,
        grade: int,
        subject: str,
        topic: str,
        subtopic: str | None = None,
        content_types: list[str] | None = None,
        domains: list[str] | None = None,
    ) -> str:
        """
        Construct optimized Bing query string.

        Structure:
          "Grade N" "Subject" "Topic" ["Subtopic"]
          keyword1 keyword2
          -exclusion1 -exclusion2
          (site:a OR site:b OR ...)
        """
        parts = [f'"Grade {grade}"', f'"{subject}"', f'"{topic}"']
        if subtopic:
            parts.append(f'"{subtopic}"')

        if content_types:
            for ct in content_types:
                kws = self.content_keywords.get(ct, [])
                parts.extend(kws[:2])  # Max 2 per type

        try:
             grade_int = int(grade)
        except ValueError:
             grade_int = 8

        band = self._get_grade_band(grade_int)
        excl = GRADE_EXCLUSIONS.get(band, "")
        if excl:
            parts.append(excl)

        if domains:
            site_str = self._build_site_filter(domains)
            if site_str:
                parts.append(site_str)

        query = " ".join(parts)

        logger.debug(f"Built query: {query}")
        return query

    # ── Step 3: Fetch ────────────────────────────────

    def fetch(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[dict]:
        """
        Execute Bing search using EducationalContentSearcher.

        Returns raw result dicts with keys: title, url, snippet.
        """
        try:
            self.searcher.start()
            results = self.searcher.search_bing(query, count=max_results)
            return results
        except Exception as e:
            logger.error(f"Bing search failed: {e}")
            raise SearchError(f"Bing search failed: {e}")
        finally:
            self.searcher.close()

    # ── Step 4: Filter ───────────────────────────────

    def filter_results(
        self,
        raw_results: list[dict],
        trusted_domains: list[str],
        blocked_domains: list[str] | None = None,
        strict: bool = False,
    ) -> list[SearchResult]:
        """
        Deduplicate, validate, and rank results.
        Implements Parent/Child deduplication and Blocklist filtering.

        strict=False (default): All results returned, trusted sorted first.
        strict=True: Only trusted-domain results returned.
        """
        output: list[SearchResult] = []
        candidates: list[dict] = []

        # Prepare Blocklist
        active_blocks = set(BLOCK_DOMAINS)
        if blocked_domains:
            active_blocks.update(d.lower() for d in blocked_domains if d)

        # 1. Basic Filtering & Normalization
        for r in raw_results:
            url = r.get("url", "")
            if not url:
                continue

            # Remove tracking params but keep path
            norm = url.split("?")[0].split("#")[0]

            # Domain Check
            try:
                domain = urlparse(url).netloc.lower().replace("www.", "")
                full_url_lower = url.lower()
            except:
                continue

            # Blocklist Check
            if any(bd in domain or bd in full_url_lower for bd in active_blocks):
                continue

            if any(pat in full_url_lower for pat in URL_EXCLUDE_PATTERNS):
                continue

            is_trusted = any(td in domain for td in trusted_domains)

            if strict and not is_trusted:
                continue

            candidates.append({
                "data": r,
                "norm_url": norm,
                "domain": domain,
                "is_trusted": is_trusted
            })

        # 2. Parent/Child Deduplication
        # If we have 'site.com' and 'site.com/page', keep only 'site.com/page'.
        final_candidates = []

        # Sort candidates so we have a consistent order (optional but helpful)
        # We process O(N^2) so N should be small (~20-50 max from search)

        for i, parent_cand in enumerate(candidates):
            parent_url = parent_cand["norm_url"]
            is_parent = False

            # Ensure trailing slash for robust prefix checking
            p_check = parent_url if parent_url.endswith('/') else parent_url + '/'

            for j, child_cand in enumerate(candidates):
                if i == j:
                    continue

                child_url = child_cand["norm_url"]
                c_check = child_url if child_url.endswith('/') else child_url + '/'

                # If child starts with parent (and is longer), then 'parent_cand' is indeed a parent
                # Example: P=site.com/, C=site.com/page/ -> C starts with P -> P is parent
                if c_check.startswith(p_check) and len(c_check) > len(p_check):
                    is_parent = True
                    break

            if not is_parent:
                final_candidates.append(parent_cand)

        # 3. Construction & Deduplication (Set)
        seen_urls = set()
        for cand in final_candidates:
            if cand["norm_url"] in seen_urls:
                continue
            seen_urls.add(cand["norm_url"])

            r = cand["data"]
            output.append(SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""), # Keep original URL with params if needed, or use norm? Usually keep original.
                snippet=r.get("snippet", ""),
                domain=cand["domain"],
                is_trusted=cand["is_trusted"],
            ))

        # 4. Sorting & Limiting
        # Sort trusted first
        output.sort(key=lambda x: (0 if x.is_trusted else 1))

        # Limit to Top 15 (as requested)
        output = output[:15]

        logger.info(
            f"Filtered: {len(raw_results)} raw → {len(output)} results "
            f"({sum(1 for r in output if r.is_trusted)} trusted)"
        )
        return output

    # ── Orchestrator ─────────────────────────────────

    def search(
        self,
        grade: int,
        subject: str,
        topic: str,
        subtopic: str | None = None,
        content_types: list[str] | None = None,
        extra_domains: list[str] | None = None,
        blocked_domains: list[str] | None = None,
        region: str = "us-en",
        safesearch: str = "moderate",
        max_results: int = 10,
        strict_domain_filter: bool = False,
    ) -> list[SearchResult]:
        """
        Full pipeline: resolve → build → fetch → filter.
        Includes automatic fallback if strict domain filtering yields no results.
        """
        logger.info(
            f"Starting search: Grade {grade} {subject} > {topic}"
            + (f" > {subtopic}" if subtopic else "")
        )

        # 1. Try Strict/Trusted Search
        domains = self.resolve_domains(grade, subject, extra_domains)
        query = self.build_query(
            grade, subject, topic, subtopic, content_types, domains
        )

        try:
            # Note: region/safesearch are not currently passed to EducationalContentSearcher
            # as it relies on default browser settings or would need logic updates
            raw = self.fetch(query, max_results)
            results = self.filter_results(raw, domains, blocked_domains, strict_domain_filter)
        except Exception as e:
            logger.warning(f"Primary search failed: {e}")
            results = []

        # 2. Fallback: Relaxed Search (No site: filters) if no results
        if not results:
            logger.info("No results from strict search. Attempting fallback (no site filters)...")

            # Rebuild query WITHOUT domains
            fallback_query = self.build_query(
                grade, subject, topic, subtopic, content_types, domains=None
            )

            try:
                raw_fallback = self.fetch(fallback_query, max_results)
                results = self.filter_results(raw_fallback, domains, blocked_domains, strict=strict_domain_filter)

                if results:
                    logger.info(f"Fallback successful: {len(results)} results found.")
                else:
                    logger.warning("Fallback search also returned no results.")
            except Exception as e:
                logger.error(f"Fallback search failed: {e}")

        logger.info(
            f"Search complete: {len(results)} results for "
            f"Grade {grade} {subject} > {topic}"
        )
        return results


# ═══════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Educational Content Search via Bing (Firefox+Playwright)"
    )
    parser.add_argument("--grade", type=int, required=True)
    parser.add_argument("--subject", type=str, required=True)
    parser.add_argument("--topic", type=str, required=True)
    parser.add_argument("--subtopic", type=str, default=None)
    parser.add_argument(
        "--content-types", nargs="*", default=None,
        choices=list(CONTENT_TYPE_KEYWORDS.keys()),
    )
    parser.add_argument("--max-results", type=int, default=10)
    parser.add_argument("--region", type=str, default="us-en")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--log-file", type=str, default=None)

    args = parser.parse_args()

    setup_logger(
        level=logging.DEBUG if args.debug else logging.INFO,
        log_file=args.log_file,
    )

    pipeline = EduSearchPipeline()
    results = pipeline.search(
        grade=args.grade,
        subject=args.subject,
        topic=args.topic,
        subtopic=args.subtopic,
        content_types=args.content_types,
        max_results=args.max_results,
        region=args.region,
        strict_domain_filter=args.strict,
    )

    if args.json:
        print(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        print(f"\n{'=' * 60}")
        print(f"Grade {args.grade} {args.subject} — {args.topic}")
        print(f"{'=' * 60}")
        for i, r in enumerate(results, 1):
            trust = "✓" if r.is_trusted else "○"
            print(f"\n  [{trust}] {i}. {r.title}")
            print(f"      {r.url}")
            if r.snippet:
                print(f"      {r.snippet[:120]}...")
