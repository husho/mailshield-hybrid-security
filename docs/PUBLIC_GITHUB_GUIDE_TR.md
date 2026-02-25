# Public GitHub Yayin Rehberi (Gercek Log Olmadan)

## Hedef
Projeyi public acarken gercek musteri verisi ve hassas loglar disarida kalmali, ama calisan bir demo akisi korunmali.

## Uygulanan Yapi
- Gercek loglar repoya alinmiyor (`Logs/` ve `Logs.zip` ignore edildi).
- Sentetik log ureteci eklendi: `mailshield-generate-synth`
- Egitim, API ve degerlendirme komutlari sentetik veriyle de calisabilir.

## Public Repo Icerigi
- Kaynak kod
- README ve calistirma adimlari
- Sentetik veri uretim komutu
- Model egitim/degerlendirme scriptleri
- Ornek cikti dosyalari (kucuk boyutlu)

## Public Repo Disinda Kalacaklar
- Gercek log dosyalari
- Ham PII iceren herhangi bir ara cikti
- Sirket ici IP/domain listeleri
- Uretim sirlari veya konfigurasyonlari

## One-shot Demo Akisi
1. Sentetik log uret:
```bash
mailshield-generate-synth --output-dir ./sample_data/synthetic-logs --hosts 3 --days 14 --events-per-day 1000
```

2. Model egit:
```bash
mailshield-train --logs-dir ./sample_data/synthetic-logs --output-dir ./artifacts/public-demo --epochs 3 --window-minutes 15 --seq-len 8
```

3. API calistir:
```bash
mailshield-api --model-dir ./artifacts/public-demo --host 0.0.0.0 --port 8000
```

4. Baseline karsilastirmasi:
```bash
mailshield-eval --logs-dir ./sample_data/synthetic-logs --model-dir ./artifacts/public-demo --output-dir ./artifacts/public-demo/eval
```

## GitHub'a Public Yayin (CLI ile)
1. Ilk commit'i olustur:
```bash
git add .
git commit -m "Initial public release"
```

2. Public repo olustur ve push et:
```bash
./scripts/publish_github.sh mailshield-hybrid-security public
```

3. Alternatif (elle):
```bash
gh repo create mailshield-hybrid-security --public --source . --remote origin --push
```

## README Icin Kisa Aciklama Onerisi
"Bu repoda veri gizliligi nedeniyle gercek uretim loglari paylasilmamaktadir. Calistirilabilirlik ve tekrar uretilebilirlik icin sentetik MailEnable-benzeri log uretim araci dahil edilmistir."
