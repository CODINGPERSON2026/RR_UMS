"""
Evaluation metrics computation for AI/ML Fitness models.
"""

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score
)


def evaluate_classifier(model, X_test, y_test, class_labels=None):
    """
    Computes comprehensive classification metrics on validation/test set.
    """
    y_pred = model.predict(X_test)
    
    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, average='weighted', zero_division=0))
    rec = float(recall_score(y_test, y_pred, average='weighted', zero_division=0))
    f1_w = float(f1_score(y_test, y_pred, average='weighted', zero_division=0))
    f1_m = float(f1_score(y_test, y_pred, average='macro', zero_division=0))
    
    labels = class_labels if class_labels is not None else sorted(list(set(y_test) | set(y_pred)))
    cm = confusion_matrix(y_test, y_pred, labels=labels).tolist()
    
    return {
        'accuracy': round(acc, 4),
        'precision_weighted': round(prec, 4),
        'recall_weighted': round(rec, 4),
        'f1_weighted': round(f1_w, 4),
        'f1_macro': round(f1_m, 4),
        'confusion_matrix': cm,
        'classes': [str(c) for c in labels]
    }


def evaluate_regressor(model, X_test, y_test):
    """
    Computes regression metrics on validation/test set.
    """
    y_pred = model.predict(X_test)
    
    mae = float(mean_absolute_error(y_test, y_pred))
    mse = float(mean_squared_error(y_test, y_pred))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_test, y_pred))
    
    return {
        'mae': round(mae, 4),
        'mse': round(mse, 4),
        'rmse': round(rmse, 4),
        'r2_score': round(r2, 4)
    }
