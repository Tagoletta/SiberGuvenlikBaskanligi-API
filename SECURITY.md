# Güvenlik Politikası / Security Policy

## 🇹🇷 Türkçe

### Desteklenen sürümler

Bu proje sürekli olarak `main` dalından yayımlanır. Güvenlik güncellemeleri
yalnızca `main` dalının en güncel hâline uygulanır.

| Sürüm | Destekleniyor |
| ----- | ------------- |
| `main` (en güncel) | ✅ |
| Eski commit'ler | ❌ |

### Güvenlik açığı bildirimi

Bir güvenlik açığı bulduğunuzu düşünüyorsanız, lütfen bunu **herkese açık bir
issue olarak açmayın**. Bunun yerine ayrıntıları doğrudan e-posta ile bildirin:

**info@tagmachan.com**

Bildiriminize mümkünse şunları ekleyin:

* Açığın türü ve etkilediği bileşen (ör. `scraper/fetch.py`, GitHub Actions
  yapılandırması, Docker imajı)
* Sorunu yeniden üretmek için adımlar
* Olası etki ve varsa önerilen çözüm

**Yanıt süresi:** Bildiriminizi aldıktan sonra 72 saat içinde onay vermeyi ve
doğrulanan açıklar için makul bir sürede düzeltme yayımlamayı hedefliyoruz.

### Kapsam

Bu araç yalnızca herkese açık resmî API'den veri çeker; kimlik bilgisi veya
kişisel veri işlemez. Güvenlik değerlendirmeleri özellikle şu alanlarda önem
taşır:

* GitHub Actions iş akışlarındaki izinler ve gizli anahtar (secret) kullanımı
* Bağımlılıklardaki (requirements) bilinen açıklar
* Docker imajının yapılandırması

---

## 🇬🇧 English

### Supported versions

This project is released continuously from the `main` branch. Security updates
are applied only to the latest state of `main`.

| Version | Supported |
| ------- | --------- |
| `main` (latest) | ✅ |
| Older commits | ❌ |

### Reporting a vulnerability

If you believe you have found a security vulnerability, please **do not open a
public issue**. Instead, report the details privately by email:

**info@tagmachan.com**

Where possible, include:

* The type of vulnerability and the affected component (e.g. `scraper/fetch.py`,
  the GitHub Actions configuration, the Docker image)
* Steps to reproduce the issue
* Potential impact and, if known, a suggested fix

**Response time:** We aim to acknowledge your report within 72 hours and to
release a fix for confirmed vulnerabilities within a reasonable timeframe.

### Scope

This tool only fetches data from a public official API; it does not process
credentials or personal data. Security assessments are especially relevant for:

* Permissions and secret usage in the GitHub Actions workflows
* Known vulnerabilities in dependencies (requirements)
* Configuration of the Docker image
