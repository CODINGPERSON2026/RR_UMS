from typing import Dict, Any, List
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)
from sklearn.model_selection import StratifiedKFold, cross_validate

from .config import RANDOM_STATE, CV_FOLDS
from .utils import get_logger

logger = get_logger("evaluate")

def top_k_accuracy(y_true: np.ndarray, y_proba: np.ndarray, k: int = 2) -> float:
    """Calculates top-k accuracy for multi-class predictions."""
    if k >= y_proba.shape[1]:
        return 1.0
    top_k_preds = np.argsort(y_proba, axis=1)[:, -k:]
    correct = [y_true[i] in top_k_preds[i] for i in range(len(y_true))]
    return float(np.mean(correct))

def evaluate_model(
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
    class_names: List[str],
    model_name: str = "Model"
) -> Dict[str, Any]:
    """
    Performs comprehensive, genuine evaluation of a model on unseen test data.
    """
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    prec_macro = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
    rec_macro = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
    f1_macro = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    f1_weighted = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
    
    top_1_acc = acc
    top_2_acc = top_k_accuracy(y_test, y_proba, k=2)

    # Multiclass ROC-AUC (OvR)
    try:
        roc_auc = float(roc_auc_score(y_test, y_proba, multi_class="ovr", average="macro"))
    except Exception as e:
        logger.warning(f"Could not compute ROC-AUC for {model_name}: {e}")
        roc_auc = 0.0

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    cm_list = cm.tolist()

    # Per-class classification metrics
    report = classification_report(y_test, y_pred, target_names=class_names, output_dict=True, zero_division=0)
    per_class_metrics = {}
    for c in class_names:
        if c in report:
            per_class_metrics[c] = {
                "precision": float(report[c]["precision"]),
                "recall": float(report[c]["recall"]),
                "f1": float(report[c]["f1-score"]),
                "support": int(report[c]["support"])
            }

    metrics = {
        "model_name": model_name,
        "accuracy": round(acc, 4),
        "precision": round(prec_macro, 4),
        "recall": round(rec_macro, 4),
        "f1": round(f1_macro, 4),
        "macro_f1": round(f1_macro, 4),
        "weighted_f1": round(f1_weighted, 4),
        "top_1_accuracy": round(top_1_acc, 4),
        "top_2_accuracy": round(top_2_acc, 4),
        "roc_auc": round(roc_auc, 4),
        "confusion_matrix": cm_list,
        "class_names": class_names,
        "per_class": per_class_metrics
    }
    
    logger.info(f"[{model_name}] Test Evaluation -> Accuracy: {acc:.4f}, Macro-F1: {f1_macro:.4f}, Top-2 Acc: {top_2_acc:.4f}, ROC-AUC: {roc_auc:.4f}")
    return metrics

def run_cross_validation(
    model: Any,
    X_train_resampled: np.ndarray,
    y_train_resampled: np.ndarray,
    folds: int = CV_FOLDS
) -> Dict[str, float]:
    """
    Runs Stratified K-Fold Cross-Validation on the training set to evaluate stability.
    """
    skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=RANDOM_STATE)
    
    scoring = {
        "accuracy": "accuracy",
        "f1_macro": "f1_macro",
        "precision_macro": "precision_macro",
        "recall_macro": "recall_macro"
    }
    
    cv_res = cross_validate(
        model,
        X_train_resampled,
        y_train_resampled,
        cv=skf,
        scoring=scoring,
        n_jobs=-1
    )
    
    mean_acc = float(np.mean(cv_res["test_accuracy"]))
    std_acc = float(np.std(cv_res["test_accuracy"]))
    mean_f1 = float(np.mean(cv_res["test_f1_macro"]))
    std_f1 = float(np.std(cv_res["test_f1_macro"]))

    return {
        "cv_mean_accuracy": round(mean_acc, 4),
        "cv_std_accuracy": round(std_acc, 4),
        "cv_mean_f1": round(mean_f1, 4),
        "cv_std_f1": round(std_f1, 4)
    }
