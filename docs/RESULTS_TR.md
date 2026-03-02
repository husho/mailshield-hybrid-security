# Deneysel Sonuclar ve Karsilastirmali Analiz

## Deneysel Kurulum
Bu calismada onerilen model, e-posta trafiginin zamansal davranis oruntulerini ve yapisal metaveri ozelliklerini birlikte isleyen derin ogrenme tabanli hibrit bir mimari olarak gelistirilmistir. Modelin zamansal kolunda GRU katmani, yapisal kolunda tam baglantili sinir agi kullanilmis ve bu iki kol birlestirilerek uc sinifli (normal, anomaly, spam) karar uretimi yapilmistir.

Deneylerde 5 farkli sunucudan toplanan MailEnable loglari (SMTP, MTA, MTAFILTER) kullanilmistir. Veri, 15 dakikalik pencerelere bolunmus, hesap+pencere bazli ozellikler cikartilmis ve zaman bazli ayrim (train/validation/test) uygulanmistir. Egitim tarafinda recall oncelikli ayar tercih edilmis, sistemin tehdit kacirmama kabiliyeti onceliklendirilmistir.

## Veri Ozeti
- Toplam ornek sayisi: 1,769,332
- Train: 613,670
- Validation: 439,886
- Test: 715,776
- Train sinif dagilimi: normal=611,197, anomaly=2,297, spam=176

Bu dagilim, anomaly ve spam siniflarinin ciddi derecede dengesiz oldugunu gostermektedir.

## Onerilen Derin Ogrenme Modeli Sonuclari (Test)
- Accuracy: 0.9866
- Precision (macro): 0.7422
- Recall (macro): 0.9708
- F1 (macro): 0.7858

Sinif bazli recall degerleri:
- Normal recall: 0.9869
- Anomaly recall: 0.9255
- Spam recall: 1.0000

Bu sonuclar, onerilen hibrit modelin ozellikle anomaly ve spam kacirmama (high recall) hedefinde guclu performans sergiledigini gostermektedir.

## Baseline Yontemlerle Karsilastirma
Ayni test bolumunde iki klasik baseline ile karsilastirma yapilmistir:

1. RandomForest
- Accuracy: 0.9978
- Precision (macro): 0.9176
- Recall (macro): 0.8839
- F1 (macro): 0.9002
- Anomaly recall: 0.7002

2. XGBoost
- Accuracy: 0.9978
- Precision (macro): 0.8992
- Recall (macro): 0.9479
- F1 (macro): 0.9212
- Anomaly recall: 0.8452

Karsilastirma sonucunda klasik yontemlerin genel precision/F1 performansi yuksek gorulmekle birlikte, onerilen derin ogrenme hibrit modelin anomaly recall degeri daha yuksek bulunmustur. Bu durum, operasyonel guvenlik acisindan kritik olan tehdit kacirmama hedefi ile uyumludur.

## ROC-AUC Sonuclari (OvR)
- Deep Hybrid macro ROC-AUC: 0.9987
- RandomForest macro ROC-AUC: 0.9928
- XGBoost macro ROC-AUC: 0.9992

ROC-AUC degerleri tum modellerin ayristirma gucunun yuksek oldugunu gostermektedir. Ancak uygulama kapsaminda oncelik recall odakli oldugundan, model seciminde sadece AUC/F1 degil, anomaly/spam recall metrikleri de belirleyici kabul edilmistir.

## Sonuc
Elde edilen bulgular, web hosting e-posta ortamlarinda spam ve anomali tespiti icin derin ogrenme tabanli hibrit model yaklasiminin pratikte uygulanabilir oldugunu gostermektedir. Onerilen model, ozellikle anomaly sinifinda daha yuksek yakalama oranina ulasarak guvenlik operasyonlarinda erken uyari kapasitesini artirmaktadir.
