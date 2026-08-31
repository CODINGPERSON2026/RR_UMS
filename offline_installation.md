python -m pip download -r requirements.txt -d offline_packages


python -m pip install --no-index --find-links=offline_packages xgboost 
python -m pip install --no-index --find-links=offline_packages joblib
python -m pip install --no-index --find-links=offline_packages scikit-learn








python -m pip install --no-index --find-links=imblearn_installation imbalanced-learn
python -m pip install --no-index --find-links=shap_installation shap