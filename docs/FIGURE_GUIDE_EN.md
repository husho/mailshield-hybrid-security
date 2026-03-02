# Figure and Table Guide

This document contains reusable figure/table caption templates and short interpretation texts for report or presentation use.

Public assets:
- Figures: `docs/figures/`
- Tables: `docs/tables/`

## Table 1 - Training Epoch Summary
File: `tables/table_training_epoch_summary.png`

Suggested caption:
"Table 1 presents loss, validation macro F1, and validation macro recall values for each training epoch."

![Table 1](tables/table_training_epoch_summary.png)

## Table 2 - Model Comparison Metrics
File: `tables/table_model_comparison_metrics.png`

Suggested caption:
"Table 2 jointly reports accuracy, macro precision, macro recall, macro F1, anomaly recall, spam recall, and ROC-AUC values for the proposed deep-learning hybrid model and the classical baseline models."

![Table 2](tables/table_model_comparison_metrics.png)

## Figure 1 - Macro Metric Comparison Across Models
File: `figures/fig_macro_metrics.png`

Suggested caption:
"Figure 1 compares macro precision, macro recall, and macro F1 scores of Deep Hybrid, RandomForest, and XGBoost on the test split. The proposed deep-learning hybrid model achieves higher macro recall, which is advantageous for threat miss reduction objectives."

![Figure 1](figures/fig_macro_metrics.png)

## Figure 2 - Per-Class Recall Comparison
File: `figures/fig_per_class_recall.png`

Suggested caption:
"Figure 2 shows recall values for normal, anomaly, and spam classes. The proposed hybrid model reaches a higher anomaly recall."

![Figure 2](figures/fig_per_class_recall.png)

## Figure 3 - Macro ROC-AUC Comparison
File: `figures/fig_roc_auc_macro.png`

Suggested caption:
"Figure 3 presents macro OvR ROC-AUC values of the evaluated models. All models demonstrate high discrimination power; model choice is interpreted with operational recall priorities."

![Figure 3](figures/fig_roc_auc_macro.png)

## Figure 4 - Training Class Distribution
File: `figures/fig_train_class_distribution.png`

Suggested caption:
"Figure 4 illustrates class imbalance in the training split. The minority nature of anomaly and spam classes increases the importance of macro metrics and class-level recall analysis."

![Figure 4](figures/fig_train_class_distribution.png)

## Figure 5 - Deep Hybrid Confusion Matrix
File: `figures/fig_confusion_deep.png`

Suggested caption:
"Figure 5 presents the confusion matrix of the proposed model. Spam detection is strong, while high anomaly recall is preserved."

![Figure 5](figures/fig_confusion_deep.png)

## Figure 6 - RandomForest Confusion Matrix
File: `figures/fig_confusion_random_forest.png`

![Figure 6](figures/fig_confusion_random_forest.png)

## Figure 7 - XGBoost Confusion Matrix
File: `figures/fig_confusion_xgboost.png`

Suggested caption:
"Figures 6 and 7 show the error distributions of classical baseline models. This comparison is used to discuss the operational alignment of the proposed deep-learning hybrid model, especially for anomaly capture objectives."

![Figure 7](figures/fig_confusion_xgboost.png)
