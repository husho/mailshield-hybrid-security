# Tez Tamamlama Planı (Tutarsızlık Analizi + Bölüm Bazlı Ekleme Rehberi)

Bu doküman, mevcut tez metnindeki proje-sonrası tutarsızlıkları tespit etmek ve tezi savunmaya hazır hale getirmek için hangi bölüme ne eklenmesi gerektiğini netleştirir.

## 1. Tespit Edilen Tutarsızlıklar

### 1.1 Kritik (Savunma öncesi mutlaka düzeltilmeli)

1. Kapak/ön sayfa alanları boş veya şablon durumda:
- `DANIŞMAN:` boş.
- İngilizce kapakta `THESIS TITLE`, `AD ve SOYAD`, `THESIS ADVISOR` placeholder olarak kalmış.
- Onay formu alanları (`Program Adı`, `Öğrenci No`, vb.) boş.

2. Özet/Abstract tamamen şablon metin:
- `TEZ BAŞLIĞI` ve tekrar eden şablon paragraflar var.
- Anahtar kelimeler yanlış konuya ait (çocuk davaları vb.).
- İngilizce abstract da şablon halinde.

3. Tablo/Şekil listeleri gerçek içerik yerine örnek şablon:
- `Tablo 2.1 ... Tek satırlı...`
- `Şekil 2.1 ... yazı bloğuna göre ortalı...`

4. Benzerlik Bildirimi alanları boş:
- `Rapor Tarihi`, `Benzerlik Oranı`, `Gönderim Numarası` gibi alanlar doldurulmamış.

5. Özgeçmiş bölümü boş şablon:
- Kişisel bilgiler, iş deneyimi, akademik bilgiler doldurulmamış.

### 1.2 Orta (Bilimsel tutarlılık için düzeltilmeli)

1. Metrik terminolojisi hatası:
- Birkaç yerde `özgüllük (recall)` yazıyor.
- Doğrusu:
  - `Recall = Duyarlılık` (TPR)
  - `Specificity = Özgüllük` (TNR)

2. Metin genel/iddia düzeyinde kalmış:
- 6. bölümde gerçek deney sonuçları sayısal olarak yeterince yer almıyor.
- 6.4 ve 6.5 başlıklarında tablo/grafik referansları eksik.

3. Ön söz tarihi/şablon kalıntıları:
- Ön sözde şablon cümleleri ve eski tarih formatı gözden geçirilmeli.

### 1.3 Biçimsel

1. Açık erişim URL yazım hatası:
- `openacess` yerine muhtemelen `openaccess` olmalı (kurum resmi URL’si ile teyit et).

2. İngilizce onay formunda 2023 tarihi kalmış:
- Tezin gerçek savunma/teslim tarihi ile güncellenmeli.

## 2. Proje Sonuçlarına Dayalı Bölüm Bazlı Ekleme Planı

Bu bölüm, tezin içerik omurgasına doğrudan uygulanacak ekleme/değiştirme planıdır.

## 2.1 Özet ve Abstract

Tamamen yeniden yazılmalı. İçermesi gereken zorunlu unsurlar:
1. Problem: web hosting ortamında e-posta trafiğinde spam ve anomali tespiti.
2. Yöntem: derin öğrenme tabanlı hibrit mimari (GRU + MLP + host embedding).
3. Veri: 5 sunucu logu, gerçek trafik, zaman pencereli özellik çıkarımı.
4. Sonuç: temel metrikler ve model karşılaştırması.
5. Katkı: recall-odaklı güvenlik yaklaşımı.

Kullanılacak sayısal değerler:
1. Toplam örnek: `1,769,332`
2. Train/Val/Test: `613,670 / 439,886 / 715,776`
3. Deep hybrid test:
- Accuracy: `0.986620`
- Precision macro: `0.742154`
- Recall macro: `0.970779`
- F1 macro: `0.785842`
- Recall anomaly: `0.925464`
- Recall spam: `1.000000`

## 2.2 Bölüm 4 (Veri Toplama ve Öznitelik)

Eklenecek net içerik:
1. Log kaynakları:
- MailEnable SMTP, MTA, MTAFILTER logları
- 5 farklı sunucu

2. Zaman penceresi ve sekans parametreleri:
- Pencere: `15 dakika`
- Sekans uzunluğu: `8`

3. Sınıf dengesizliği analizi:
- normal: `611,197`
- anomaly: `2,297`
- spam: `176`

Bu alt bölüme eklenecek grafik:
1. `fig_train_class_distribution.png`

## 2.3 Bölüm 5 (Model Tasarımı)

Metni, uygulanan gerçekle birebir hizala:
1. Zamansal kol: GRU
2. Statik kol: MLP
3. Host embedding
4. Füzyon katmanı ve 3-sınıf softmax çıktı
5. Eğitim hedefi: recall öncelikli güvenlik

Not: Eğer metinde LSTM kullanıldığı iddiası geçiyorsa, uygulanmayan kısım ya kaldırılmalı ya da "alternatif olarak değerlendirildi" diye notlanmalı. Nihai mimari GRU+MLP olarak sabitlenmeli.

## 2.4 Bölüm 6.3 (Eğitim ve Doğrulama)

Aşağıdaki tablo tezde mutlaka yer almalı (Tablo 6.x):
1. Epoch 1: loss `0.0002577`, val_f1_macro `0.8236`, val_recall_macro `0.9919`
2. Epoch 2: loss `0.0000270`, val_f1_macro `0.7483`, val_recall_macro `0.9824`
3. Epoch 3: loss `0.0000210`, val_f1_macro `0.8561`, val_recall_macro `0.9913`

Yorum cümlesi:
- En düşük loss tek başına nihai kaliteyi belirlemedi; sınıf dengesizliği nedeniyle makro F1 ve anomali yakalama performansı birlikte değerlendirildi.

## 2.5 Bölüm 6.4 (Performans Sonuçları)

Bu bölümde sadece anlatı değil, tablo + grafik + doğrudan yorum olmalı.

Eklenecek tablo (Tablo 6.y):
1. Deep Hybrid
2. RandomForest
3. XGBoost
4. Accuracy, Precision Macro, Recall Macro, F1 Macro, Recall Anomaly, Recall Spam sütunları

Eklenecek grafikler:
1. `fig_macro_metrics.png`
2. `fig_per_class_recall.png`
3. `fig_roc_auc_macro.png`
4. `fig_confusion_deep.png`

Zorunlu yorum:
1. Deep modelin anomaly recall değeri (`0.925464`) klasik modellere göre daha yüksek.
2. Güvenlik operasyonunda "tehdit kaçırmama" önceliği nedeniyle recall-odaklı değerlendirme tercih edildi.
3. Dengesiz veri nedeniyle macro precision/f1 düşüşü beklenen bir sonuçtur.

## 2.6 Bölüm 6.5 (Karşılaştırmalı Analiz)

Karşılaştırmayı nicel hale getir:
1. RandomForest anomaly recall: `0.700169`
2. XGBoost anomaly recall: `0.845194`
3. Deep Hybrid anomaly recall: `0.925464`

ROC-AUC:
1. Deep macro OVR AUC: `0.998680`
2. RandomForest: `0.992841`
3. XGBoost: `0.999161`

Yorum:
- XGBoost genel metrikte güçlü olsa da, derin hibrit model anomali yakalama hedefinde daha iyi performans vermiştir.

Eklenecek grafikler:
1. `fig_confusion_random_forest.png`
2. `fig_confusion_xgboost.png`

## 2.7 Bölüm 7 ve Sonuç

Bölüm 7’de öneri değil, proje çıktısıyla bağlanan uygulama dili kullanılmalı:
1. Modelin near real-time kullanım senaryosu (log akışı + risk skoru).
2. Yanlış pozitiflerin operasyonel etkisi ve insan doğrulama adımı.
3. Ölçekleme: çok sunuculu paralel işleme yaklaşımı.

Sonuç bölümüne eklenecek net kapanış noktaları:
1. Tezin "derin öğrenme tabanlı hibrit model" şartı teknik olarak sağlandı.
2. Gerçek log verisiyle doğrulama yapıldı.
3. En kritik çıktı: anomali sınıfında yüksek recall ile erken uyarı başarımı.

## 2.8 Tutarlılık Notu (İddia Dili)

Tezde aşağıdaki dil kullanılmalı:
1. "Model her metrikte en iyi" iddiası kullanılmamalı.
2. Doğru ifade: "Önerilen derin hibrit model, güvenlik operasyonu açısından kritik olan anomali yakalama (recall) hedefinde daha güçlü performans göstermiştir."
3. Accuracy ve macro F1 gibi metriklerde klasik yöntemlerin daha yüksek çıkabildiği açıkça belirtilmeli.

## 3. Teze Eklenecek Grafik ve Kaynak Dosya Eşlemesi

Grafikleri aşağıdaki mutlak dosyalardan içe aktar:
1. `/Users/huseyinkaranik/Tez Uygulaması/artifacts/full-20260225/figures/fig_train_class_distribution.png`
2. `/Users/huseyinkaranik/Tez Uygulaması/artifacts/full-20260225/figures/fig_macro_metrics.png`
3. `/Users/huseyinkaranik/Tez Uygulaması/artifacts/full-20260225/figures/fig_per_class_recall.png`
4. `/Users/huseyinkaranik/Tez Uygulaması/artifacts/full-20260225/figures/fig_roc_auc_macro.png`
5. `/Users/huseyinkaranik/Tez Uygulaması/artifacts/full-20260225/figures/fig_confusion_deep.png`
6. `/Users/huseyinkaranik/Tez Uygulaması/artifacts/full-20260225/figures/fig_confusion_random_forest.png`
7. `/Users/huseyinkaranik/Tez Uygulaması/artifacts/full-20260225/figures/fig_confusion_xgboost.png`

Sayısal referans dosyaları:
1. `/Users/huseyinkaranik/Tez Uygulaması/artifacts/full-20260225/performance_report.md`
2. `/Users/huseyinkaranik/Tez Uygulaması/artifacts/full-20260225/training_summary.json`
3. `/Users/huseyinkaranik/Tez Uygulaması/artifacts/full-20260225/eval-xgb/evaluation_summary.json`
4. `/Users/huseyinkaranik/Tez Uygulaması/artifacts/full-20260225/eval-xgb/baseline_comparison.md`

## 4. Hızlı Düzeltme Checklist (Savunma Öncesi)

1. Kapak ve onay sayfalarındaki tüm placeholder alanları doldur.
2. Özet/Abstract bölümlerini gerçek proje metniyle tamamen değiştir.
3. Tablo ve şekil listelerini gerçek numara/adlarla güncelle.
4. `özgüllük (recall)` ifadelerini düzelt (`duyarlılık/recall` ve `özgüllük/specificity` ayrımı).
5. Bölüm 6’ya nicel tabloları ve 7 grafiği ekle.
6. Sonuç bölümünü proje çıktılarıyla tekrar yaz.
7. Benzerlik bildirimi ve özgeçmişi kurum formatına göre doldur.
8. Kaynakça içi atıf-metni eşleşmesini son kez kontrol et.

## 5. Kullanıma Hazır Kısa Sonuç Metni (Teze Yapıştırılabilir)

Bu tez kapsamında, web hosting ortamlarında e-posta trafiği üzerinden spam ve anomali tespiti için derin öğrenme tabanlı hibrit bir güvenlik modeli geliştirilmiş ve gerçek log verileri üzerinde değerlendirilmiştir. Önerilen mimari, zamansal örüntüler için GRU tabanlı bir dalı ve yapısal metaveri için MLP tabanlı bir dalı birleştirmektedir. Toplam 1,769,332 örnek içeren veri setinde yapılan testlerde model, makro recall açısından 0.970779 değerine ulaşmış; anomali sınıfında 0.925464, spam sınıfında 1.000000 recall elde etmiştir. Elde edilen bulgular, güvenlik operasyonlarında tehdit kaçırmama hedefi açısından derin öğrenme tabanlı hibrit yaklaşımın uygulanabilir ve etkili olduğunu göstermektedir.
