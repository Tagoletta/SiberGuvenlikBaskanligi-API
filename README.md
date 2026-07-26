<div align="center">

# 🛡️ SiberGüvenlik Başkanlığı — Blocklist API

**T.C. Siber Güvenlik Başkanlığı** tehdit istihbaratı listelerini otomatik çeken, zaman penceresine göre filtreleyen ve güvenlik duvarları için ham metin olarak yayınlayan açık kaynak araç.

An open-source tool that mirrors **Turkey's Cybersecurity Directorate** threat-intelligence feeds as firewall-ready blocklists — refreshed hourly, no server required.

[![Update blocklists](https://github.com/Tagoletta/SiberGuvenlikBaskanligi-API/actions/workflows/update-lists.yml/badge.svg)](https://github.com/Tagoletta/SiberGuvenlikBaskanligi-API/actions/workflows/update-lists.yml)
[![Last commit](https://img.shields.io/github/last-commit/Tagoletta/SiberGuvenlikBaskanligi-API/main?logo=github)](https://github.com/Tagoletta/SiberGuvenlikBaskanligi-API/commits/main)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Made with Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](scraper/fetch.py)

</div>

---

## 📑 İçindekiler / Table of Contents

- [🇹🇷 Türkçe](#-türkçe)
  - [Nedir?](#nedir)
  - [Canlı kayıt sayıları](#canlı-kayıt-sayıları)
  - [Çıktı dosyaları](#çıktı-dosyaları)
  - [Güvenlik duvarı kullanımı](#güvenlik-duvarı-kullanımı)
  - [Nasıl çalışır?](#nasıl-çalışır)
  - [Docker](#docker-ile-çalıştırma-isteğe-bağlı)
- [🇬🇧 English](#-english)
  - [What is this?](#what-is-this)
  - [Live record counts](#live-record-counts)
  - [Output files](#output-files)
  - [Firewall usage](#firewall-usage)
  - [How it works](#how-it-works)
  - [Configuration](#configuration)

---

## 🇹🇷 Türkçe

### Nedir?

`https://siberguvenlik.gov.tr/api/address/index` adresindeki genel API'den **5 farklı adres tipini** (domain, url, ip, ip6, ip6net) çeker; her kaydın tarihini veritabanında saklar ve her çalışmada zaman penceresine göre güncel listeler üretir.

**Sunucu gerekmez.** GitHub Actions saatlik olarak çalışır, listeleri `data/` klasörüne commit eder. Güvenlik duvarınız listeleri doğrudan ham GitHub URL'sinden çekebilir.

### Canlı kayıt sayıları

> Aşağıdaki tablo her bot commit'inde otomatik güncellenir — her zaman penceresindeki (`30/60/90/120 gün` ve `full`) yayınlanan listelerin gerçek, filtreleme sonrası satır sayılarını gösterir.

<!-- STATS-TR:START -->
| Tip | 30g | 60g | 90g | 120g | Full |
| --- | --: | --: | --: | --: | --: |
| 🌐 Domain | 4.305 | 9.057 | 14.476 | 19.505 | 461.772 |
| 🔗 URL | 0 | 0 | 0 | 0 | 6.927 |
| 📡 IPv4 | 281 | 713 | 1.046 | 1.245 | 15.027 |
| 🧭 IPv6 | 0 | 0 | 0 | 0 | 6 |
| 🕸️ IPv6 Ağ | 0 | 0 | 0 | 0 | 0 |
| **Toplam** | **4.586** | **9.770** | **15.522** | **20.750** | **483.732** |

_Son güncelleme: 2026-07-26 22:14 (UTC+3) — bot tarafından otomatik._
<!-- STATS-TR:END -->

### Çıktı dosyaları

Her adres tipi ayrı dosyada, her zaman penceresi için ayrı ayrı tutulur (`data/` klasörü):

| Pencere | Domainler | URL'ler | IPv4 | IPv6 | IPv6 Ağları |
| ------- | --------- | ------- | ---- | ---- | ----------- |
| Tüm zamanlar | `full-domains.txt` | `full-urls.txt` | `full-ips.txt` | `full-ip6.txt` | `full-ip6net.txt` |
| Son 30 gün | `days-30-domains.txt` | `days-30-urls.txt` | `days-30-ips.txt` | `days-30-ip6.txt` | `days-30-ip6net.txt` |
| Son 60 gün | `days-60-domains.txt` | `days-60-urls.txt` | `days-60-ips.txt` | `days-60-ip6.txt` | `days-60-ip6net.txt` |
| Son 90 gün | `days-90-domains.txt` | `days-90-urls.txt` | `days-90-ips.txt` | `days-90-ip6.txt` | `days-90-ip6net.txt` |
| Son 120 gün | `days-120-domains.txt` | `days-120-urls.txt` | `days-120-ips.txt` | `days-120-ip6.txt` | `days-120-ip6net.txt` |

Her dosya: satır başına bir kayıt, tırnak yok, boşluk yok, LF satır sonu. Domain'ler alfabetik, IP'ler sayısal sıralı.

> `database-*.jsonl` (250.000 kayıtlık parçalar) ve `_state.json` dahili kayıt dosyalarıdır; güvenlik duvarı bunları görmezden gelir.

### Güvenlik duvarı kullanımı

Listeleri doğrudan ham GitHub URL'sinden çekin:

```
https://raw.githubusercontent.com/Tagoletta/SiberGuvenlikBaskanligi-API/main/data/full-domains.txt
https://raw.githubusercontent.com/Tagoletta/SiberGuvenlikBaskanligi-API/main/data/days-30-domains.txt
https://raw.githubusercontent.com/Tagoletta/SiberGuvenlikBaskanligi-API/main/data/full-ips.txt
https://raw.githubusercontent.com/Tagoletta/SiberGuvenlikBaskanligi-API/main/data/full-urls.txt
```

pfSense, OPNsense, MikroTik, ipset, Pi-hole, Squid ve benzeri sistemlerle uyumludur.

### Nasıl çalışır?

- **İlk çalışma** (full liste yok): tüm tipler için tam tarama başlar. Her tip `per-page=1000` parametresiyle çekilir (~481 sayfa toplamda). Ortalama 5–12 s/sayfa ile ilk tarama **~1–2 saatte** tamamlanır.
- **Tam tarama sonrası**: her saatlik çalışmada yalnızca yeni sayfalar çekilir (incremental), listeler yeniden üretilir.
- **Her 7 günde bir**: kaynaktan silinen kayıtları yakalamak için tam yeniden tarama yapılır. Silinen kayıtlar `data/removed.log` dosyasına eklenir.

**Yaşlandırma mantığı:** Listeler her çalışmada veritabanı + güncel saatten türetilir. 31 günlük bir kayıt `days-30-*`'dan düşer ama `days-60-*`, `days-90-*`, `days-120-*` ve `full-*`'da kalmaya devam eder. Hiçbir kayıt geniş pencerelerden kaybolmaz.

### Docker ile çalıştırma (isteğe bağlı)

GitHub Actions kullanıyorsanız Docker gerekmez. Kendi sunucunuzda çalıştırmak için:

```bash
docker compose up -d --build
docker compose logs -f
```

Listeler `./data` klasöründe oluşur.

---

## 🇬🇧 English

### What is this?

An open-source tool that pulls **five address types** (domain, url, ip, ip6, ip6net) from the public API of Turkey's Cybersecurity Directorate (`siberguvenlik.gov.tr`), stores each record with its original date, and regenerates time-windowed blocklists on every run.

**No server required.** A GitHub Actions workflow runs hourly, commits the refreshed lists to `data/`, and your firewall can consume them directly from raw GitHub URLs.

### Live record counts

> The table below is regenerated automatically on every bot commit — it shows the real, post-filtering line counts of the published lists for each time window (`30/60/90/120 days` and `full`).

<!-- STATS-EN:START -->
| Type | 30d | 60d | 90d | 120d | Full |
| --- | --: | --: | --: | --: | --: |
| 🌐 Domain | 4,305 | 9,057 | 14,476 | 19,505 | 461,772 |
| 🔗 URL | 0 | 0 | 0 | 0 | 6,927 |
| 📡 IPv4 | 281 | 713 | 1,046 | 1,245 | 15,027 |
| 🧭 IPv6 | 0 | 0 | 0 | 0 | 6 |
| 🕸️ IPv6 Net | 0 | 0 | 0 | 0 | 0 |
| **Total** | **4,586** | **9,770** | **15,522** | **20,750** | **483,732** |

_Last updated: 2026-07-26 22:14 (UTC+3) — auto-generated by the bot._
<!-- STATS-EN:END -->

### Output files

Each address type is kept in its own file, per time window (`data/` directory):

| Window | Domains | URLs | IPv4 | IPv6 | IPv6 Nets |
| ------ | ------- | ---- | ---- | ---- | --------- |
| All time | `full-domains.txt` | `full-urls.txt` | `full-ips.txt` | `full-ip6.txt` | `full-ip6net.txt` |
| Last 30 days | `days-30-domains.txt` | `days-30-urls.txt` | `days-30-ips.txt` | `days-30-ip6.txt` | `days-30-ip6net.txt` |
| Last 60 days | `days-60-domains.txt` | `days-60-urls.txt` | `days-60-ips.txt` | `days-60-ip6.txt` | `days-60-ip6net.txt` |
| Last 90 days | `days-90-domains.txt` | `days-90-urls.txt` | `days-90-ips.txt` | `days-90-ip6.txt` | `days-90-ip6net.txt` |
| Last 120 days | `days-120-domains.txt` | `days-120-urls.txt` | `days-120-ips.txt` | `days-120-ip6.txt` | `days-120-ip6net.txt` |

One entry per line, no quotes, no surrounding whitespace, LF line endings. Domains sorted alphabetically, IPs sorted numerically.

> `database-*.jsonl` (split into 250,000-record shards) and `_state.json` are internal bookkeeping files; firewalls should ignore them.

### Firewall usage

Consume the lists straight from raw GitHub URLs:

```
https://raw.githubusercontent.com/Tagoletta/SiberGuvenlikBaskanligi-API/main/data/full-domains.txt
https://raw.githubusercontent.com/Tagoletta/SiberGuvenlikBaskanligi-API/main/data/days-30-domains.txt
https://raw.githubusercontent.com/Tagoletta/SiberGuvenlikBaskanligi-API/main/data/full-ips.txt
https://raw.githubusercontent.com/Tagoletta/SiberGuvenlikBaskanligi-API/main/data/full-urls.txt
```

Compatible with pfSense, OPNsense, MikroTik, ipset, Pi-hole, Squid, and similar systems.

### How it works

- **First run** (no full lists present): a full crawl begins for all types. Each type is fetched with `per-page=1000` (~481 pages total). At 5–12 s/page the initial seed completes in **~1–2 hours**.
- **After the full crawl**: each hourly run does a fast incremental update — only new pages per type are fetched — then lists are regenerated.
- **Every 7 days**: a full re-crawl runs to detect entries removed at the source. Removed records are appended to `data/removed.log`.

**Ageing logic:** Lists are derived from the database + current clock on every run. A record that turns 31 days old drops out of `days-30-*` but remains in `days-60-*`, `days-90-*`, `days-120-*`, and `full-*`. No entry is ever lost from the wider windows.

### Configuration

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `MIN_DELAY` / `MAX_DELAY` | `5` / `12` | Seconds between pages during the full crawl |
| `INC_MIN_DELAY` / `INC_MAX_DELAY` | `2` / `6` | Seconds between pages during incremental |
| `TIME_BUDGET_SECONDS` | `18000` | Checkpoint the full crawl after this many seconds |
| `FULL_RESYNC_DAYS` | `7` | Re-crawl everything this often to detect removals (`0` = off) |
| `INCREMENTAL_MAX_PAGES` | `50` | Safety cap for incremental pages per type per run |
| `PER_PAGE` | `1000` | Records per API page (max supported by the API) |
| `DATA_DIR` | `data` | Output directory |
| `USER_AGENT` | Chrome/138 | Request User-Agent |

### Docker (optional)

Not needed if you use GitHub Actions.

```bash
docker compose up -d --build
docker compose logs -f
```

Lists appear under `./data`. Override pacing via environment variables in `docker-compose.yml`.

### GitHub Actions

`.github/workflows/update-lists.yml` runs every hour. First runs perform the resumable full crawl; once complete, each hourly run is a fast incremental update and refreshes the live counts in this README.

> 💡 **Keep the repo public.** GitHub Actions is free and unlimited for public repos. Scheduled workflows pause after 60 days of inactivity — the hourly bot commits count as activity, keeping it alive.

### Local run (no Docker)

```bash
pip install -r scraper/requirements.txt
DATA_DIR=data python scraper/fetch.py
```

### API source

All data is sourced from the official public API:

```
GET https://siberguvenlik.gov.tr/api/address/index?type={domain|url|ip|ip6|ip6net}&page={n}&per-page=1000
```

API documentation: `https://siberguvenlik.gov.tr/api/openapi.yaml`

---

<div align="center">

Katkı için [CONTRIBUTING.md](CONTRIBUTING.md) · Güvenlik açığı bildirimi için [SECURITY.md](SECURITY.md) · [GPLv3](LICENSE)

</div>
