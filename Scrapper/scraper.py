#!/usr/bin/env python3
"""
Web Content Scraper CLI Script
Supporting Playwright & Selenium with custom CSS selectors and Markdown export.
"""

import argparse
import csv
import os
import re
import sys
import time
from urllib.parse import urlparse
from typing import Dict, List, Tuple, Optional


def normalize_url_key(url_str: str) -> str:
    """Normalize URL/domain for matching dictionary key."""
    url_str = url_str.strip()
    # Remove protocol if present
    url_no_proto = re.sub(r'^https?://', '', url_str, flags=re.IGNORECASE)
    # Remove trailing slash
    return url_no_proto.rstrip('/').lower()


def load_css_paths(csv_file_path: str) -> Dict[str, str]:
    """
    Load mapping of URL/Domain to css_path from CSV file.
    Supports ';' or ',' as delimiter.
    """
    mapping: Dict[str, str] = {}
    if not os.path.isfile(csv_file_path):
        print(f"[Error] File css-paths '{csv_file_path}' tidak ditemukan.")
        sys.exit(1)

    with open(csv_file_path, mode='r', encoding='utf-8-sig') as f:
        # Sample to determine delimiter
        first_line = f.readline()
        f.seek(0)
        delimiter = ';' if ';' in first_line else ','
        
        reader = csv.DictReader(f, delimiter=delimiter)
        # Normalize column names
        field_map = {}
        if reader.fieldnames:
            for field in reader.fieldnames:
                clean_field = field.strip().lower()
                if clean_field in ['url', 'urls', 'domain']:
                    field_map['url'] = field
                elif clean_field in ['css_path', 'csspath', 'css', 'selector']:
                    field_map['css_path'] = field

        if 'url' not in field_map or 'css_path' not in field_map:
            # Fallback for headerless or custom headers: first col = url, second = css_path
            f.seek(0)
            raw_reader = csv.reader(f, delimiter=delimiter)
            for row in raw_reader:
                if len(row) >= 2:
                    u_key = normalize_url_key(row[0])
                    mapping[u_key] = row[1].strip()
        else:
            for row in reader:
                url_val = row.get(field_map['url'], '').strip()
                css_val = row.get(field_map['css_path'], '').strip()
                if url_val and css_val:
                    u_key = normalize_url_key(url_val)
                    mapping[u_key] = css_val

    return mapping


def get_css_selector_for_url(
    url: str,
    css_paths_map: Optional[Dict[str, str]],
    default_css_path: str
) -> Tuple[str, bool]:
    """
    Returns (css_path, is_defined).
    If css_paths_map is given but URL is not found, print log message and return default_css_path.
    """
    if css_paths_map is None:
        return default_css_path, True

    parsed = urlparse(url if url.startswith(('http://', 'https://')) else f"https://{url}")
    domain = parsed.netloc.lower()
    full_url_norm = normalize_url_key(url)

    # Check exact full URL match first
    if full_url_norm in css_paths_map:
        return css_paths_map[full_url_norm], True

    # Check domain match (e.g. www.kompas.com or kompas.com)
    domain_norm = normalize_url_key(domain)
    if domain_norm in css_paths_map:
        return css_paths_map[domain_norm], True

    # Check domain without www prefix
    domain_no_www = domain_norm.replace('www.', '')
    if domain_no_www in css_paths_map:
        return css_paths_map[domain_no_www], True

    # Substring match check
    for key, selector in css_paths_map.items():
        if key in full_url_norm or key in domain_norm:
            return selector, True

    # Not defined in css_paths_map
    print(f"css-path url '{url}' tidak didefinisikan, menggunakan default path")
    return default_css_path, False


def extract_content_js() -> str:
    """JavaScript snippet executed in browser context."""
    return """
    (cssPath) => {
        let elementText = document.querySelectorAll(cssPath);
        let scrapped = '';
        elementText.forEach(el => {
            scrapped = `${scrapped}\\n${el.innerText}`;
        });
        return scrapped;
    }
    """


def scrape_with_playwright(
    urls: List[str],
    css_paths_map: Optional[Dict[str, str]],
    default_css_path: str,
    headless: bool = True,
    timeout: int = 30
) -> List[Dict[str, str]]:
    """Scrape web pages using Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[Error] Package 'playwright' belum terinstal. Install dengan: pip install playwright && playwright install")
        sys.exit(1)

    results = []
    print(f"[*] Starting Playwright (headless={headless})...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for idx, raw_url in enumerate(urls, 1):
            url = raw_url if raw_url.startswith(('http://', 'https://')) else f"https://{raw_url}"
            css_path, _ = get_css_selector_for_url(raw_url, css_paths_map, default_css_path)

            print(f"[{idx}/{len(urls)}] Opening {url} (CSS Path: '{css_path}')...")
            scrapped_text = ""
            status = "SUCCESS"

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
                # Wait briefly for dynamic elements if any
                page.wait_for_timeout(1000)

                # Execute JS extraction logic
                js_code = """
                (cssPath) => {
                    let cssPath = arguments[0] || cssPath;
                    let elementText = document.querySelectorAll(cssPath);
                    let scrapped = '';
                    elementText.forEach(el => {
                        scrapped = `${scrapped}\\n${el.innerText}`;
                    });
                    return scrapped;
                }
                """
                scrapped_text = page.evaluate(
                    """(cssPath) => {
                        let elementText = document.querySelectorAll(cssPath);
                        let scrapped = '';
                        elementText.forEach(el => {
                            scrapped = `${scrapped}\\n${el.innerText}`;
                        });
                        return scrapped;
                    }""",
                    css_path
                )
            except Exception as e:
                status = f"ERROR: {str(e)}"
                print(f"    -> Gagal mengekstrak {url}: {e}")

            results.append({
                "url": url,
                "raw_url": raw_url,
                "css_path": css_path,
                "content": scrapped_text.strip(),
                "status": status
            })

        browser.close()

    return results


def scrape_with_selenium(
    urls: List[str],
    css_paths_map: Optional[Dict[str, str]],
    default_css_path: str,
    headless: bool = True,
    timeout: int = 30
) -> List[Dict[str, str]]:
    """Scrape web pages using Selenium."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
    except ImportError:
        print("[Error] Package 'selenium' belum terinstal. Install dengan: pip install selenium")
        sys.exit(1)

    results = []
    print(f"[*] Starting Selenium (headless={headless})...")

    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(timeout)

    try:
        for idx, raw_url in enumerate(urls, 1):
            url = raw_url if raw_url.startswith(('http://', 'https://')) else f"https://{raw_url}"
            css_path, _ = get_css_selector_for_url(raw_url, css_paths_map, default_css_path)

            print(f"[{idx}/{len(urls)}] Opening {url} (CSS Path: '{css_path}')...")
            scrapped_text = ""
            status = "SUCCESS"

            try:
                driver.get(url)
                time.sleep(1)

                js_script = """
                let cssPath = arguments[0];
                let elementText = document.querySelectorAll(cssPath);
                let scrapped = '';
                elementText.forEach(el => {
                    scrapped = `${scrapped}\\n${el.innerText}`;
                });
                return scrapped;
                """
                scrapped_text = driver.execute_script(js_script, css_path)
            except Exception as e:
                status = f"ERROR: {str(e)}"
                print(f"    -> Gagal mengekstrak {url}: {e}")

            results.append({
                "url": url,
                "raw_url": raw_url,
                "css_path": css_path,
                "content": scrapped_text.strip() if scrapped_text else "",
                "status": status
            })
    finally:
        driver.quit()

    return results


def read_url_list(urls_file: str) -> List[str]:
    """Read list of URLs from file."""
    if not os.path.isfile(urls_file):
        print(f"[Error] File daftar URL '{urls_file}' tidak ditemukan.")
        sys.exit(1)

    urls = []
    with open(urls_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Skip header line if present (e.g., 'url')
            if line.lower() in ['url', 'urls', 'link', 'links']:
                continue
            urls.append(line)

    if not urls:
        print(f"[Warning] Tidak ada URL yang ditemukan pada file '{urls_file}'.")

    return urls


def sanitize_filename(name: str) -> str:
    """Sanitize string for filename use."""
    sub = re.sub(r'[^\w\-_\. ]', '_', name)
    return re.sub(r'_+', '_', sub).strip('_')


def save_output(results: List[Dict[str, str]], output_target: str, output_mode: str):
    """Save clean scraped content to Markdown file(s) for training dataset."""
    valid_items = [item for item in results if item.get('content') and item['content'].strip()]
    failed_items = [item for item in results if not item.get('content') or not item['content'].strip()]

    # Determine log file path and output directory
    if output_mode == 'merge':
        out_dir = os.path.dirname(output_target)
        if not out_dir:
            out_dir = '.'
        base_name = os.path.splitext(os.path.basename(output_target))[0]
        log_file = os.path.join(out_dir, f"{base_name}.log")
    else:
        out_dir = output_target
        if output_target.endswith('.md') or output_target.endswith('.txt'):
            out_dir = os.path.splitext(output_target)[0]
        log_file = os.path.join(out_dir, "scraper.log")

    os.makedirs(out_dir, exist_ok=True)

    # Log failure / empty extraction details if any exist
    if failed_items:
        with open(log_file, 'w', encoding='utf-8') as log_f:
            log_f.write(f"=== SCRAPING LOG / FAILURE REPORT ({time.strftime('%Y-%m-%d %H:%M:%S')}) ===\n")
            log_f.write(f"Total URL diproses: {len(results)}\n")
            log_f.write(f"Total Berhasil: {len(valid_items)}\n")
            log_f.write(f"Total Gagal / Kosong: {len(failed_items)}\n\n")
            for item in failed_items:
                log_f.write(f"- URL: {item['url']}\n")
                log_f.write(f"  CSS Path: {item['css_path']}\n")
                log_f.write(f"  Status: {item['status']}\n\n")

        print(f"[INFO] {len(failed_items)} URL gagal/kosong diekstrak. Detail dicatat di log: {os.path.abspath(log_file)}")

    # Save clean dataset Markdown file(s)
    if output_mode == 'merge':
        clean_contents = [item['content'].strip() for item in valid_items]
        merged_text = "\n\n---\n\n".join(clean_contents)
        if merged_text:
            merged_text += "\n"

        with open(output_target, 'w', encoding='utf-8') as f:
            f.write(merged_text)

        print(f"[OK] {len(valid_items)} konten bersih berhasil digabungkan ke: {os.path.abspath(output_target)}")

    elif output_mode == 'each':
        for idx, item in enumerate(valid_items, 1):
            parsed = urlparse(item['url'])
            domain_slug = sanitize_filename(parsed.netloc or "url")
            filename = f"scraped_{idx:03d}_{domain_slug}.md"
            filepath = os.path.join(out_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(item['content'].strip() + "\n")

        print(f"[OK] Scrapping selesai. {len(valid_items)} file clean dataset tersimpan pada folder: {os.path.abspath(out_dir)}")


def main():
    parser = argparse.ArgumentParser(
        description="Web Content Scraper - Ekstraksi isi konten URL ke file Markdown."
    )
    parser.add_argument(
        "--urls", "-u",
        required=True,
        help="Path ke file yang berisi daftar URL (misal: --urls=Windows/output/crawler_url.txt)"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Path lokasi output file/folder hasil scrapping"
    )
    parser.add_argument(
        "--output-mode",
        choices=["each", "merge"],
        default="merge",
        help="Mode simpan output: 'each' (1 file per URL) atau 'merge' (gabung semua ke 1 file). Default: merge"
    )
    parser.add_argument(
        "--css-path",
        default="body p",
        help="Default CSS Path selector ekstraksi elemen text. Default: 'body p'"
    )
    parser.add_argument(
        "--css-paths",
        default=None,
        help="Path ke file CSV pemetaan URL ke CSS Path (contoh header: url;css_path)"
    )
    parser.add_argument(
        "--engine",
        choices=["playwright", "selenium"],
        default="playwright",
        help="Engine scraping yang digunakan: 'playwright' atau 'selenium'. Default: playwright"
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Jalankan browser dengan UI visual (non-headless mode)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout waktu tunggu loading halaman dalam detik. Default: 30"
    )

    args = parser.parse_args()

    # 1. Read URL list
    urls = read_url_list(args.urls)
    if not urls:
        print("[!] Tidak ada URL yang valid untuk diproses.")
        sys.exit(0)

    # 2. Load CSS path mapping if provided
    css_paths_map = None
    if args.css_paths:
        css_paths_map = load_css_paths(args.css_paths)

    # 3. Perform scraping
    headless_mode = not args.no_headless
    if args.engine == "playwright":
        results = scrape_with_playwright(
            urls=urls,
            css_paths_map=css_paths_map,
            default_css_path=args.css_path,
            headless=headless_mode,
            timeout=args.timeout
        )
    else:
        results = scrape_with_selenium(
            urls=urls,
            css_paths_map=css_paths_map,
            default_css_path=args.css_path,
            headless=headless_mode,
            timeout=args.timeout
        )

    # 4. Save results to markdown
    save_output(results, args.output, args.output_mode)


if __name__ == "__main__":
    main()
