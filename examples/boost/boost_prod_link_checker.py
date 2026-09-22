# check_links_production.py
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import csv
from datetime import datetime

# Production domains (treating these as equivalent)
PRODUCTION_DOMAINS = [
    "https://www.boost.org",
    "https://boost.org"
]

# Versions to spot-check (add/remove as needed)
VERSIONS_TO_CHECK = [
    "1_86_0",
    "1_87_0", 
    "1_88_0",
    "1_89_0",
    "1_90_0",
    "latest"
]

# Popular libraries to spot-check in each version
LIBRARIES_TO_SPOT_CHECK = [
    "asio",
    "beast",
    "filesystem",
    "test",
    "thread",
    "regex"
]

visited = set()
broken = []
redirects = []
skipped = 0
doc_pages_checked = 0
malformed_paths = []  # Track URLs with /libs/ but missing /doc/libs/

def normalize_url(url):
    """Normalize production URLs to a canonical form."""
    for domain in PRODUCTION_DOMAINS:
        if url.startswith(domain):
            return url.replace(domain, "https://www.boost.org")
    return url

def is_production_url(url):
    """Check if URL is on any production domain."""
    return any(url.startswith(domain) for domain in PRODUCTION_DOMAINS)

def is_doc_url(url):
    """Check if this is a library documentation URL."""
    return '/doc/libs/' in url

def should_deeply_crawl(url):
    """Determine if we should crawl all links on this page."""
    # Always deeply crawl non-doc pages (your Django pages)
    if not is_doc_url(url):
        return True
    
    # For doc pages, DON'T crawl their internal links
    # We just verify the doc pages exist, but don't check their internal links
    # (those are library maintainer issues, not site issues)
    return False

def should_skip_url(url):
    """Check if we should completely skip checking this URL."""
    # Skip anchors and non-http links
    if any(url.startswith(prefix) for prefix in ['#', 'mailto:', 'tel:', 'javascript:']):
        return True
    
    # Skip external OAuth/login URLs (GitHub, Google, etc.)
    external_domains = ['github.com', 'accounts.google.com', 'signin/v2', 'lifecycle/flows']
    if any(domain in url for domain in external_domains):
        return True
    
    # Skip external sites
    if not is_production_url(url):
        return True
    
    # Skip PDFs and downloads
    if any(ext in url for ext in ['.pdf', '.zip', '.tar.gz', '.tar.bz2', '.cpp', '.py', '.natvis']):
        return True
    
    return False

async def check_page(page, url, source_url="direct", depth=0):
    global skipped, doc_pages_checked, malformed_paths
    
    normalized_url = normalize_url(url)
    
    if normalized_url in visited:
        return
    visited.add(normalized_url)
    
    if should_skip_url(normalized_url):
        skipped += 1
        return
    
    # Check for malformed /libs/ paths (missing /doc/libs/)
    parsed = urlparse(normalized_url)
    if '/libs/' in parsed.path and '/doc/libs/' not in parsed.path:
        malformed_paths.append({
            'source': normalize_url(source_url),
            'url': normalized_url,
            'suggested_fix': normalized_url.replace('/libs/', '/doc/libs/latest/libs/')
        })
        print(f"⚠ Malformed path: {normalized_url}")
        return
    
    # Limit depth in doc pages to avoid crawling too deep
    is_doc = is_doc_url(normalized_url)
    if is_doc:
        doc_pages_checked += 1
        if depth > 2:  # Only go 2 levels deep in docs
            return
    
    try:
        # Add delay to be respectful to production (increased from 0.1s)
        await asyncio.sleep(0.3)
        
        response = await page.goto(normalized_url, wait_until="domcontentloaded", timeout=45000)
        status = response.status
        
        if status >= 400:
            broken.append({
                'source': normalize_url(source_url),
                'url': normalized_url,
                'status': status,
                'type': 'doc' if is_doc else 'site'
            })
            print(f"✗ [{status}] {normalized_url}")
            return
        elif status >= 300 and status < 400:
            redirects.append({
                'source': normalize_url(source_url),
                'url': normalized_url,
                'status': status
            })
            print(f"↪ [{status}] {normalized_url}")
        else:
            if len(visited) % 25 == 0:
                print(f"✓ Checked {len(visited)} pages ({doc_pages_checked} doc pages)...")
        
        # Decide whether to crawl links on this page
        should_crawl_links = should_deeply_crawl(normalized_url)
        
        if not should_crawl_links:
            return
        
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            if href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
                continue
            
            full_url = urljoin(normalized_url, href)
            
            if should_skip_url(full_url):
                continue
            
            normalized_link = normalize_url(full_url)
            if normalized_link not in visited:
                # Increase depth only for doc pages
                next_depth = depth + 1 if is_doc else depth
                await check_page(page, full_url, source_url=normalized_url, depth=next_depth)
                
    except Exception as e:
        print(f"✗ Error on {normalized_url}: {e}")
        broken.append({
            'source': normalize_url(source_url),
            'url': normalized_url,
            'status': 'error',
            'type': str(e)
        })

async def main():
    print(f"{'='*80}")
    print(f"🚀 PRODUCTION LINK CHECKER - boost.org")
    print(f"{'='*80}")
    print(f"⚠️  WARNING: Running against PRODUCTION site")
    print(f"⚠️  Using respectful delays (0.3s between requests)")
    print(f"Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Strategy: Deep check Django pages, spot-check library docs")
    print(f"Versions to check: {', '.join(VERSIONS_TO_CHECK)}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (compatible; BoostLinkChecker/1.0; +https://boost.org)'
        )
        page = await context.new_page()
        
        # Django pages - check thoroughly
        start_urls = [
            "https://www.boost.org/",
            "https://www.boost.org/libraries/",
            "https://www.boost.org/docs/",
            "https://www.boost.org/releases/",
            "https://www.boost.org/news/",
            "https://www.boost.org/community/",
        ]
        
        print("Checking main site pages...")
        for url in start_urls:
            await check_page(page, url)
        
        # Spot-check library docs for each version
        print("\nSpot-checking library documentation...")
        for version in VERSIONS_TO_CHECK:
            version_url = f"https://www.boost.org/doc/libs/{version}/"
            print(f"\n  Checking version {version}...")
            
            # Check the version index
            await check_page(page, version_url)
            
            # Spot-check a few popular libraries
            for lib in LIBRARIES_TO_SPOT_CHECK:
                lib_url = f"https://www.boost.org/doc/libs/{version}/libs/{lib}/"
                await check_page(page, lib_url, depth=0)
        
        await browser.close()
    
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    
    # Separate broken links by type
    site_broken = [b for b in broken if b.get('type') == 'site']
    doc_broken = [b for b in broken if b.get('type') == 'doc']
    
    # Save reports
    if broken:
        filename = f'broken-links-production-{timestamp}.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['source', 'url', 'status', 'type'])
            writer.writeheader()
            writer.writerows(broken)
        print(f"\n❌ Broken links saved to: {filename}")
    
    # Save malformed paths report
    if malformed_paths:
        filename = f'malformed-paths-production-{timestamp}.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['source', 'url', 'suggested_fix'])
            writer.writeheader()
            writer.writerows(malformed_paths)
        print(f"⚠ Malformed paths saved to: {filename}")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY - PRODUCTION CHECK")
    print(f"{'='*80}")
    print(f"✓ Total unique pages checked: {len(visited)}")
    print(f"📚 Documentation pages checked: {doc_pages_checked}")
    print(f"⊘ Skipped (OAuth, external, etc.): {skipped}")
    print(f"⚠ Malformed paths (/libs/ instead of /doc/libs/): {len(malformed_paths)}")
    print(f"✗ Total broken links: {len(broken)}")
    print(f"  - Site pages (Django): {len(site_broken)}")
    print(f"  - Doc pages (libraries): {len(doc_broken)}")
    print(f"↪ Redirects: {len(redirects)}")
    
    if malformed_paths:
        print(f"\n⚠ MALFORMED PATHS (Fix in Django templates):")
        print(f"These are using /libs/ instead of /doc/libs/latest/libs/")
        for i, link in enumerate(malformed_paths[:10], 1):
            print(f"  {i}. {link['url']}")
            print(f"      Found on: {link['source']}")
            print(f"      Should be: {link['suggested_fix']}")
    
    if broken:
        print(f"\nBroken links by status:")
        status_counts = {}
        for link in broken:
            status = str(link['status'])
            status_counts[status] = status_counts.get(status, 0) + 1
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count}")
        
        # Show site broken links first (most important)
        if site_broken:
            print(f"\n🚨 BROKEN SITE LINKS (Priority):")
            for i, link in enumerate(site_broken[:10], 1):
                print(f"  {i}. [{link['status']}] {link['url']}")
                print(f"      Found on: {link['source']}")
        
        # Then doc broken links
        if doc_broken:
            print(f"\n📚 BROKEN DOC LINKS (Spot Check Results):")
            for i, link in enumerate(doc_broken[:10], 1):
                print(f"  {i}. [{link['status']}] {link['url']}")
                print(f"      Found on: {link['source']}")
    else:
        print(f"\n🎉 No broken links found!")
    
    print(f"\nCompleted at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())