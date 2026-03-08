# Panduan Penggunaan AITF Crawler Engine

Dokumen ini berisi panduan **khusus penggunaan binary** di Windows, Linux, dan macOS.

## 1. Instalasi (Dependencies)

### Windows 10/11 (PowerShell)
```powershell
# install Chrome + ChromeDriver
.\windows-installer.ps1

# Aktifkan profile di shell baru
. $PROFILE
```

### Linux (Ubuntu/Debian)
```bash
chmod +x linux-installer.sh
./linux-installer.sh
```
Aktifkan profile shell:
```bash
source ~/.bashrc
```

### macOS
```bash
chmod +x macos-installer.sh
./macos-installer.sh
```
Aktifkan profile shell:
```bash
source ~/.zshrc
```

## 2. Cara menjalankan crawler engine
### Masuk ke salah satu folder engine terlebih dahulu (linux / macos / windows)
```bash
# Untuk os Linux
cd Linux
# Untuk os MacOS
cd MacOS
# untuk windows harap tunggu update...
# ditunggu ya...
```

### Cek Help
```bash
aitf-engine --help
```

## 3. Crawling Google Search
```bash
./aitf-engine crawl -k "Rumah Layak Huni" --keyword-type=keywords --token={YOUR_TOKEN}
```

Contoh dengan keyword dari file `daftar_keyword.txt` (default --keyword-type=keywords_file):
```bash
./aitf-engine crawl --token={YOUR_TOKEN}
```

Mode Crawling Images:
```bash
./aitf-engine crawl -k "Rumah rusak" --search-image-mode=True --token={YOUR_TOKEN}
```

## 4. Extract Text
```bash
./aitf-engine extract-text --token={YOUR_TOKEN}
```

Jika file daftar input URL berbeda:
```bash
./aitf-engine extract-text -f output/crawler_url.txt --token={YOUR_TOKEN}
```

## 5. Extract / Download Gambar
```bash
./aitf-engine extract-image --token={YOUR_TOKEN}
```

Output gambar disimpan di:
```
output/extracted_image_{timestamp}
```

## 6. Autentikasi Program
Binary membutuhkan token untuk aktivasi

Gunakan salah satu, masukan flag --token:
```bash
aitf-engine crawl --token={YOUR_TOKEN}
```

atau set sebagai env os variable (bisa langsung eksekusi tanpa flag --token):
```bash
export CRAWLER_ENGINE_TOKEN=PASTE_TOKEN
./aitf-engine crawl
```

Jika token tidak valid:
```
Invalid token, please contact administrator
```
