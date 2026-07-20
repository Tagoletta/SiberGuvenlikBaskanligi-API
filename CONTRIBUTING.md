# Katkı Rehberi / Contributing Guidelines

## 🇹🇷 Türkçe

Katkıda bulunduğunuz için teşekkürler! Bu proje, T.C. Siber Güvenlik Başkanlığı'nın
genel API'sinden tehdit istihbaratı listelerini çeken açık kaynak bir araçtır.
Aşağıdaki kısa rehber, katkı sürecini herkes için kolaylaştırmayı amaçlar.

### Nasıl katkıda bulunabilirim?

* **Hata bildirimi:** Bir sorunla karşılaştıysanız önce [mevcut issue'ları][issues]
  kontrol edin. Yoksa "Bug report" şablonuyla yeni bir issue açın.
* **Özellik önerisi:** "Feature request" şablonunu kullanın ve önerinizin çözdüğü
  sorunu açıklayın.
* **Kod / dokümantasyon:** Küçük düzeltmeler için doğrudan bir Pull Request
  açabilirsiniz. Büyük değişikliklerden önce bir issue açıp tartışmanızı öneririz.

### Geliştirme ortamı

```bash
pip install -r scraper/requirements.txt
DATA_DIR=data python scraper/fetch.py
```

Değişikliklerinizi Docker ile de doğrulayabilirsiniz:

```bash
docker compose up -d --build
docker compose logs -f
```

### Pull Request kuralları

1. Değişikliklerinizi ana koddan ayrı bir dalda (branch) yapın.
2. Kodunuzun mevcut stile uyduğundan emin olun (Python için [PEP 8]).
3. `scraper/fetch.py` davranışını değiştiriyorsanız, ilgili ortam değişkenlerini
   ve `README.md`'yi güncelleyin.
4. Bir commit tek bir mantıksal değişikliği kapsasın; açıklayıcı commit mesajları
   yazın (`fix:`, `feat:`, `docs:`, `chore:` önekleri tercih edilir).
5. PR açıklamasında **ne** ve **neden** değiştirdiğinizi belirtin.

### Dikkat edilmesi gerekenler

* `data/` klasöründeki dosyalar (listeler ve `database-*.jsonl`) **otomatik olarak
  bot tarafından üretilir**. Bunları elle düzenleyip commit etmeyin.
* API'ye gönderilen isteklerin hızını (`MIN_DELAY`, `MAX_DELAY` vb.) düşürecek
  değişiklikler, kaynağa aşırı yük bindirebilir; lütfen makul gecikmeleri koruyun.
* Bu proje **savunma amaçlı** bir güvenlik aracıdır. Katkılar bu amaca uygun
  olmalıdır.

---

## 🇬🇧 English

Thanks for your interest in contributing! This project is an open-source tool
that pulls threat-intelligence blocklists from the public API of Turkey's
Cybersecurity Directorate. The short guide below aims to make contributing
smooth for everyone.

### How can I contribute?

* **Report a bug:** First check the [existing issues][issues]. If none match,
  open a new issue using the "Bug report" template.
* **Suggest a feature:** Use the "Feature request" template and describe the
  problem your idea solves.
* **Code / docs:** For small fixes, feel free to open a Pull Request directly.
  For larger changes, please open an issue to discuss first.

### Development setup

```bash
pip install -r scraper/requirements.txt
DATA_DIR=data python scraper/fetch.py
```

You can also verify changes with Docker:

```bash
docker compose up -d --build
docker compose logs -f
```

### Pull Request rules

1. Make your changes on a separate branch.
2. Keep your code consistent with the existing style ([PEP 8] for Python).
3. If you change `scraper/fetch.py` behavior, update the relevant environment
   variables and `README.md`.
4. Keep each commit to a single logical change; write descriptive commit
   messages (`fix:`, `feat:`, `docs:`, `chore:` prefixes are preferred).
5. In the PR description, explain **what** you changed and **why**.

### Things to keep in mind

* Files under `data/` (the lists and `database-*.jsonl`) are **generated
  automatically by the bot**. Do not hand-edit and commit them.
* Changes that reduce the request pacing (`MIN_DELAY`, `MAX_DELAY`, etc.) may
  overload the source; please keep reasonable delays.
* This is a **defensive** security tool. Contributions should serve that purpose.

[issues]: https://github.com/Tagoletta/SiberGuvenlikBaskanligi-API/issues
[PEP 8]: https://peps.python.org/pep-0008/
