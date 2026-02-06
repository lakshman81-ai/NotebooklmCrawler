#!/usr/bin/env python3
"""
Educational Content Searcher with Camoufox
Most undetectable browser automation in 2025

Camoufox advantages:
- Passes Cloudflare, DataDome, Pixelscan, Browserscan
- Firefox-based (less fingerprinting than Chrome)
- Automatic anti-detection (no manual configuration needed)
"""

from camoufox.sync_api import Camoufox
from urllib.parse import urlencode
from typing import List, Dict, Optional
import json
import time
from datetime import datetime
from pathlib import Path
import os


class CamoufoxEducationalSearcher:
    """
    Educational content searcher using Camoufox
    Most undetectable browser in 2025
    """

    # Educational platform definitions
    PLATFORMS = {
        'ncert': 'ncert.nic.in',
        'cbse': 'cbse.nic.in',
        'khan': 'khanacademy.org',
        'byjus': 'byjus.com',
        'vedantu': 'vedantu.com',
        'toppr': 'toppr.com',
        'meritnation': 'meritnation.com'
    }

    def __init__(self, headless: bool = True,
                 config_file: str = 'outputs/search_config.json',
                 cache_dir: str = 'outputs/search_cache'):
        """
        Initialize Camoufox searcher

        Args:
            headless: Run in headless mode (recommended for automation)
            config_file: Path to configuration file
            cache_dir: Directory for caching results
        """
        self.headless = headless
        self.config_file = Path(config_file)
        self.cache_dir = Path(cache_dir)

        # Ensure directories exist
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load configuration
        self.config = self.load_config()

        # Browser instance (created on-demand)
        self.browser = None
        self.context = None
        self.page = None
        self._camoufox_cm = None

    def load_config(self) -> Dict:
        """Load configuration from file"""
        default_config = {
            'trusted_domains': [
                'byjus.com', 'vedantu.com', 'khanacademy.org',
                'ncert.nic.in', 'toppr.com', 'meritnation.com', 'cbse.nic.in'
            ],
            'blocked_domains': [
                'youtube.com', 'facebook.com', 'twitter.com',
                'instagram.com', 'pinterest.com', 'linkedin.com', 'amazon.com'
            ],
            'use_trusted_only': False,
            'exclude_blocked': True,
            'max_results_per_platform': 10,
            'search_timeout': 30000,
            'rate_limit_delay': 2
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except:
                pass

        return default_config

    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    # ============================================================
    # DOMAIN FILTERING (same as before)
    # ============================================================

    def toggle_trusted_only(self, enabled: bool):
        """Toggle trusted-only mode"""
        self.config['use_trusted_only'] = enabled
        self.save_config()
        print(f"\n{'='*70}")
        print(f"TRUSTED DOMAINS ONLY: {'ENABLED' if enabled else 'DISABLED'}")
        print('='*70 + '\n')

    def toggle_exclude_blocked(self, enabled: bool):
        """Toggle exclude-blocked mode"""
        self.config['exclude_blocked'] = enabled
        self.save_config()
        print(f"\n{'='*70}")
        print(f"EXCLUDE BLOCKED DOMAINS: {'ENABLED' if enabled else 'DISABLED'}")
        print('='*70 + '\n')

    def add_trusted_domain(self, domain: str):
        """Add domain to trusted list"""
        if domain not in self.config['trusted_domains']:
            self.config['trusted_domains'].append(domain)
            self.save_config()
            print(f"✓ Added to trusted: {domain}")

    def add_blocked_domain(self, domain: str):
        """Add domain to blocked list"""
        if domain not in self.config['blocked_domains']:
            self.config['blocked_domains'].append(domain)
            self.save_config()
            print(f"✓ Added to blocked: {domain}")

    def build_query(self, base_query: str) -> tuple:
        """Build search query with domain filters"""
        query_parts = [base_query]
        filter_desc = []

        if self.config.get('use_trusted_only', False):
            trusted_sites = ' OR '.join([
                f'site:{domain}'
                for domain in self.config['trusted_domains']
            ])
            query_parts.append(f'({trusted_sites})')
            filter_desc.append(f"Trusted only ({len(self.config['trusted_domains'])} domains)")

        elif self.config.get('exclude_blocked', True):
            for domain in self.config['blocked_domains']:
                query_parts.append(f'-site:{domain}')
            filter_desc.append(f"Excluding {len(self.config['blocked_domains'])} domains")

        final_query = ' '.join(query_parts)
        description = '; '.join(filter_desc) if filter_desc else "No filters"

        return final_query, description

    # ============================================================
    # CAMOUFOX BROWSER AUTOMATION
    # ============================================================

    def start(self):
        """Start Camoufox browser"""
        if self.browser is not None:
            return

        print("Starting Camoufox (most undetectable browser)...")

        # Camoufox acts as a context manager.
        # To keep the browser open, we manually invoke enter.
        # Note: lang/locale should be set in new_page or extra_http_headers if init doesn't support it directly
        self._camoufox_cm = Camoufox(
            headless=self.headless,
            geoip=False
        )
        self.browser = self._camoufox_cm.__enter__()

        # Create page with strict locale settings
        # Some Camoufox/Playwright versions attach context to browser or allow creating new context
        self.context = self.browser.new_context(
            locale="en-US",
            timezone_id="America/New_York",
            permissions=["geolocation"],
            geolocation={"latitude": 40.7128, "longitude": -74.0060}, # NYC
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9"
            }
        )
        self.page = self.context.new_page()

        print("✓ Camoufox started (stealth mode active, US Locale)\n")

    def search_bing(self, query: str, **kwargs) -> List[Dict]:
        """
        Perform Bing search with Camoufox

        Args:
            query: Search query
            **kwargs: count, filetype, freshness
        """
        if not self.page:
            self.start()

        # Build filtered query
        filtered_query, filter_desc = self.build_query(query)

        # Add filetype filter
        if kwargs.get('filetype'):
            filtered_query += f" filetype:{kwargs['filetype']}"

        # Build URL
        # Add setmkt=en-US to enforce US market results
        params = {
            'q': filtered_query,
            'count': kwargs.get('count', self.config['max_results_per_platform']),
            'setmkt': 'en-US',
            'setlang': 'en-US',
            'cc': 'US'
        }

        if kwargs.get('freshness'):
            params['filters'] = f"ex1:\"ez5_{kwargs['freshness']}\""

        url = f"https://www.bing.com/search?{urlencode(params)}"

        print(f"Query: {query}")
        print(f"Filters: {filter_desc}")
        print(f"URL: {url[:100]}...")

        # Navigate (Camoufox handles anti-detection)
        try:
            self.page.goto(url, timeout=self.config['search_timeout'])
        except Exception as e:
            print(f"✗ Navigation error: {e}")
            return []

        # Wait for results
        try:
            self.page.wait_for_selector('.b_algo', timeout=10000)
        except:
            print("✗ No results found or timeout")
            return []

        # Extract results using JavaScript
        results = self.page.evaluate('''
            () => {
                const results = [];
                const items = document.querySelectorAll('.b_algo');

                items.forEach(item => {
                    const titleElem = item.querySelector('h2 a');
                    const snippetElem = item.querySelector('.b_caption p');

                    if (titleElem) {
                        results.push({
                            title: titleElem.textContent.trim(),
                            url: titleElem.href,
                            snippet: snippetElem ? snippetElem.textContent.trim() : ''
                        });
                    }
                });

                return results;
            }
        ''')

        print(f"✓ Found {len(results)} results\n")

        return results

    def search_platform(self, platform: str, grade: int,
                       subject: str, **kwargs) -> List[Dict]:
        """Search specific educational platform"""

        if platform.lower() not in self.PLATFORMS:
            raise ValueError(f"Unknown platform: {platform}")

        domain = self.PLATFORMS[platform.lower()]

        # Construct query
        if platform.lower() == 'khan':
            query = f"{subject}"
        elif platform.lower() in ['byjus', 'toppr', 'vedantu', 'meritnation']:
            query = f"class {grade} {subject}"
        else:
            query = f"grade {grade} {subject}"

        if kwargs.get('topic'):
            query += f" {kwargs['topic']}"

        # Add site restriction
        query = f"site:{domain} {query}"

        # Search
        results = self.search_bing(
            query,
            **{k: v for k, v in kwargs.items() if k != 'topic'}
        )

        # Add metadata
        for result in results:
            result['platform'] = platform
            result['domain'] = domain
            result['grade'] = grade
            result['subject'] = subject
            result['search_date'] = datetime.now().isoformat()

        return results

    def search_all_platforms(self, grade: int, subject: str,
                            platforms: Optional[List[str]] = None,
                            **kwargs) -> Dict[str, List[Dict]]:
        """Search across multiple platforms"""

        if platforms is None:
            platforms = list(self.PLATFORMS.keys())

        all_results = {}

        print("\n" + "="*70)
        print(f"SEARCHING: Grade {grade} - {subject.upper()}")
        if kwargs.get('topic'):
            print(f"Topic: {kwargs['topic']}")
        print("="*70 + "\n")

        for platform in platforms:
            print(f"Platform: {platform.upper()}")
            print("-" * 70)

            try:
                results = self.search_platform(platform, grade, subject, **kwargs)
                all_results[platform] = results

                # Rate limiting
                time.sleep(self.config['rate_limit_delay'])

            except Exception as e:
                print(f"✗ Error: {e}\n")
                all_results[platform] = []

        # Summary
        total = sum(len(r) for r in all_results.values())
        print("="*70)
        print(f"TOTAL RESULTS: {total}")
        print("="*70 + "\n")

        return all_results

    def save_results(self, results: Dict, filename: Optional[str] = None) -> Path:
        """Save results to JSON"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"search_results_{timestamp}.json"

        filepath = self.cache_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"✓ Results saved: {filepath}")
        return filepath

    def screenshot(self, filename: Optional[str] = None) -> Path:
        """Take screenshot"""
        if not self.page:
            print("✗ Browser not started")
            return None

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"screenshot_{timestamp}.png"

        filepath = self.cache_dir / filename

        self.page.screenshot(path=str(filepath))
        print(f"✓ Screenshot saved: {filepath}")
        return filepath

    def close(self):
        """Close browser"""
        if self.browser:
            self.browser.close()
            # Also exit the context manager if we stored it
            if hasattr(self, '_camoufox_cm') and self._camoufox_cm:
                try:
                    self._camoufox_cm.__exit__(None, None, None)
                except Exception:
                    pass

            self.browser = None
            self.context = None
            self.page = None
            self._camoufox_cm = None
            print("✓ Browser closed")


# Make it available under the expected name for compatibility
EducationalContentSearcher = CamoufoxEducationalSearcher


# ============================================================
# USAGE EXAMPLES
# ============================================================

if __name__ == "__main__":

    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║  Educational Content Searcher - Camoufox Edition             ║
    ║  Most Undetectable Browser Automation in 2025                ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    # Initialize
    searcher = CamoufoxEducationalSearcher(headless=True)

    try:
        # ========================================
        # EXAMPLE 1: Basic Search
        # ========================================
        print("\n" + "="*70)
        print("EXAMPLE 1: Basic Bing Search")
        print("="*70)

        searcher.start()

        results = searcher.search_bing("python tutorial", count=5)

        print(f"\nResults: {len(results)}")
        for i, result in enumerate(results[:3], 1):
            print(f"\n{i}. {result['title'][:60]}...")
            print(f"   {result['url']}")

        searcher.close()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if searcher.browser:
            searcher.close()
