# MailShield Hybrid Security

Deep-learning tabanli hibrit bir e-posta guvenlik sistemi: hosting ortamlarindaki loglardan `normal / anomaly / spam` siniflandirmasi yapar.

## Akademik Baglam
Bu repository, yuksek lisans tez calismasi kapsaminda gelistirilmistir:

**"Web hosting ortamlarinda e-posta trafigi uzerinden anomali ve spam tespiti icin derin ogrenme tabanli bir hibrit guvenlik modeli gelistirilmesi ve performans analizi."**

Tez gereksinimi nedeniyle model cekirdegi derin ogrenme tabanlidir:
- Zamansal davranis kolu: `GRU`
- Yapisal/istatistiksel ozellik kolu: `MLP`
- Hibrit karar: iki kolun birlestirilmis ciktilari

## Proje Kapsami
- Gercek hosting log formatlari ile uyumlu parser (`SMTP`, `MTA`, `MTAFILTER`)
- Egitim, degerlendirme ve REST API cikisi
- Tez icin otomatik performans grafik uretimi
- Gercek loglarin acik paylasilmadigi durumlar icin sentetik veri uretici

## Kurulum
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Hizli Kullanim
Egitim:
```bash
mailshield-train \
  --logs-dir "./Logs" \
  --output-dir "./artifacts/latest" \
  --window-minutes 15 \
  --seq-len 8 \
  --epochs 5
```

Degerlendirme:
```bash
mailshield-eval \
  --logs-dir ./Logs \
  --model-dir ./artifacts/full-20260225 \
  --output-dir ./artifacts/full-20260225/eval
```

Tez grafikleri:
```bash
pip install -e .[report]
mailshield-thesis-figures \
  --eval-dir ./artifacts/full-20260225/eval-xgb \
  --train-summary ./artifacts/full-20260225/training_summary.json \
  --output-dir ./artifacts/full-20260225/figures
```

API:
```bash
mailshield-api --model-dir ./artifacts/latest --host 0.0.0.0 --port 8000
```

## Veri ve Gizlilik
- Gercek uretim loglari bu repoda bilincli olarak yer almaz.
- Acik repoda tekrar uretilebilirlik icin sentetik log uretici bulunur:
```bash
mailshield-generate-synth \
  --output-dir ./sample_data/synthetic-logs \
  --hosts 3 \
  --days 14 \
  --events-per-day 1000
```
- Hassas alanlar (email/domain/IP) hashlenerek islenir.

## Dokumantasyon
- Tez sonuclari taslagi: [docs/THESIS_RESULTS_DRAFT_TR.md](docs/THESIS_RESULTS_DRAFT_TR.md)
- Sekil aciklamalari: [docs/THESIS_FIGURE_TEXT_TR.md](docs/THESIS_FIGURE_TEXT_TR.md)
- Public repo rehberi: [docs/PUBLIC_GITHUB_GUIDE_TR.md](docs/PUBLIC_GITHUB_GUIDE_TR.md)

## Lisans
Bu proje `MIT License` ile lisanslanmistir. Ayrintilar icin [LICENSE](LICENSE) dosyasina bakin.
