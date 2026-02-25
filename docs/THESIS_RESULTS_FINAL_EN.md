# Experimental Results and Comparative Analysis (Final)

## Experimental Setup
The proposed model was implemented as a deep-learning hybrid architecture that jointly processes temporal behavior patterns and structural metadata from email traffic. The temporal branch uses a GRU layer, and the structural branch uses a fully connected neural network. The two branches are fused for 3-class prediction (`normal`, `anomaly`, `spam`).

Experiments were conducted on real MailEnable logs collected from 5 different servers (`SMTP`, `MTA`, `MTAFILTER`). Data was segmented into 15-minute windows, account+window level features were extracted, and a time-based split (train/validation/test) was applied. Training was configured with a recall-priority objective to reduce missed threats.

## Data Summary
- Total samples: 1,769,332
- Train: 613,670
- Validation: 439,886
- Test: 715,776
- Train class distribution: normal=611,197, anomaly=2,297, spam=176

This confirms a severe class imbalance in anomaly and spam classes.

## Proposed Deep Model Results (Test)
- Accuracy: 0.9866
- Precision (macro): 0.7422
- Recall (macro): 0.9708
- F1 (macro): 0.7858

Per-class recall:
- Normal recall: 0.9869
- Anomaly recall: 0.9255
- Spam recall: 1.0000

These results show strong performance of the hybrid model in threat-capture objectives, especially for anomaly and spam recall.

## Baseline Comparison
Two classical baselines were evaluated on the same test split:

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

Classical methods provide higher global precision/F1, while the proposed deep hybrid model yields higher anomaly recall. This aligns with recall-priority security operations.

## ROC-AUC Results (OvR)
- Deep Hybrid macro ROC-AUC: 0.9987
- RandomForest macro ROC-AUC: 0.9928
- XGBoost macro ROC-AUC: 0.9992

All models show strong discrimination capability. Since the thesis objective is threat miss reduction, anomaly/spam recall is treated as a primary model selection criterion.

## Conclusion
Findings indicate that the deep-learning hybrid approach is practically applicable for spam and anomaly detection in web hosting email environments. The proposed model improves early warning capacity through higher anomaly recall.
