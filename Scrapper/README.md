# Web Content Scraper CLI (Clean Dataset Generator)

Script Python untuk melakukan scraping/ekstraksi teks dari daftar URL dan menyimpannya ke dalam file Markdown bersih yang siap dipakai sebagai **dataset training**.

## Fitur Utama
- **Clean Training Dataset**: Markdown hasil scraping hanya berisi teks murni hasil ekstraksi tanpa metadata header (`# Scraped Web Content`, `## URL`, dll.) dan tanpa teks penjelasan kegagalan.
- **Separator Mode Merge**: Pada `--output-mode=merge`, antar konten dipisahkan menggunakan pembatas horizontal `\n---\n`.
- **Log Pelaporan Kegagalan (`.log`)**: Keterangan URL yang gagal diekstrak atau bernilai kosong tidak masuk ke file markdown, melainkan dicatat ke file `.log` (misal `hasil_scrapping.log` atau `scraper.log`) serta diinformasikan via terminal.
- **Multi Engine**: Mendukung Playwright (default) dan Selenium.
- **Custom CSS Path**: Ekstraksi elemen teks berdasarkan CSS Selector (default `"body p"`).
- **CSS Paths Mapping (CSV)**: Pemetaan CSS Path spesifik per URL/domain via file CSV (pemisah `;` atau `,`).
- **Peringatan Auto-fallback**: Menampilkan log terminal jika URL tidak terdaftar pada file CSV mapping:
  `css-path url 'x' tidak didefinisikan, menggunakan default path`

---

## Instalasi Dependencies

1. Install package Python:
   ```bash
   pip install -r Scrapper/requirements.txt
   ```

2. Install browser binary Playwright:
   ```bash
   python -m playwright install
   ```

---

## Parameter CLI

| Parameter | Alias | Deskripsi | Default |
|---|---|---|---|
| `--urls` | `-u` | Path file daftar URL (misal: `Windows/output/crawler_url.txt`) | *Wajib* |
| `--output` | `-o` | Path file/folder output Markdown | *Wajib* |
| `--output-mode` | - | Mode penyimpanan: `merge` atau `each` | `merge` |
| `--css-path` | - | Default CSS Path selector jika tidak ditemukan di mapping | `"body p"` |
| `--css-paths` | - | Path file CSV mapping `url;css_path` | `None` |
| `--engine` | - | Browser engine: `playwright` atau `selenium` | `playwright` |
| `--no-headless` | - | Tampilkan UI browser (non-headless) | `False` |
| `--timeout` | - | Timeout loading halaman (dalam detik) | `30` |

---

## Contoh Penggunaan

### 1. Mode Merge (Clean Dataset Output)
Menggabungkan seluruh teks bersih dari setiap URL yang berhasil diekstrak ke 1 file Markdown dengan separator `\n---\n`:
```bash
python Scrapper/scraper.py --urls=Windows/output/crawler_url.txt --output=Scrapper/output/hasil_scrapping.md --output-mode=merge
```
*Jika ada URL yang gagal/kosong, detailnya dicatat di `Scrapper/output/hasil_scrapping.log`.*

### 2. Mode Each (Separate Clean File per URL)
Menyimpan teks bersih tiap URL ke dalam file Markdown tersendiri pada folder `Scrapper/output/hasil/`:
```bash
python Scrapper/scraper.py --urls=Windows/output/crawler_url.txt --output=Scrapper/output/hasil --output-mode=each
```

### 3. Menggunakan CSV Mapping `--css-paths`
Format CSV (`css_paths.csv`):
```csv
url;css_path
www.suaradewata.com;"body p"
www.kompas.com;"div.read__article p"
```

Eksekusi CLI:
```bash
python Scrapper/scraper.py --urls=Windows/output/crawler_url.txt --output=Scrapper/output/hasil_merge.md --css-paths=Scrapper/css_paths.csv
```
