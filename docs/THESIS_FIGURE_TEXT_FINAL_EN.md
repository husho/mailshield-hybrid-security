# Figure Captions and Explanations for Thesis (Final)

This document contains final figure caption templates and short interpretation texts for thesis integration.

## Figure 1 - Macro Metric Comparison Across Models
File: `artifacts/full-20260225/figures/fig_macro_metrics.png`

Suggested caption:
"Figure 1 compares macro precision, macro recall, and macro F1 scores of Deep Hybrid, RandomForest, and XGBoost on the test split. The proposed deep-learning hybrid model achieves higher macro recall, which is advantageous for threat miss reduction objectives."

## Figure 2 - Per-Class Recall Comparison
File: `artifacts/full-20260225/figures/fig_per_class_recall.png`

Suggested caption:
"Figure 2 shows recall values for normal, anomaly, and spam classes. The proposed hybrid model reaches a higher anomaly recall."

## Figure 3 - Macro ROC-AUC Comparison
File: `artifacts/full-20260225/figures/fig_roc_auc_macro.png`

Suggested caption:
"Figure 3 presents macro OvR ROC-AUC values of the evaluated models. All models demonstrate high discrimination power; model choice is interpreted with operational recall priorities."

## Figure 4 - Training Class Distribution
File: `artifacts/full-20260225/figures/fig_train_class_distribution.png`

Suggested caption:
"Figure 4 illustrates class imbalance in the training split. The minority nature of anomaly and spam classes increases the importance of macro metrics and class-level recall analysis."

## Figure 5 - Deep Hybrid Confusion Matrix
File: `artifacts/full-20260225/figures/fig_confusion_deep.png`

Suggested caption:
"Figure 5 presents the confusion matrix of the proposed model. Spam detection is strong, while high anomaly recall is preserved."

## Figure 6 - RandomForest Confusion Matrix
File: `artifacts/full-20260225/figures/fig_confusion_random_forest.png`

## Figure 7 - XGBoost Confusion Matrix
File: `artifacts/full-20260225/figures/fig_confusion_xgboost.png`

Suggested caption:
"Figures 6 and 7 show the error distributions of classical baseline models. This comparison is used to discuss the operational alignment of the proposed deep-learning hybrid model, especially for anomaly capture objectives."
