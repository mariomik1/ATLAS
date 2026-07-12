# Deployment

Sprint 1 can run locally or on a Streamlit-compatible host.

## Local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud / Render

Use `requirements.txt`. Start command:

```bash
streamlit run app.py
```

## Data provider note

`csv_sample` mode works without secrets and without internet. `yfinance` mode requires internet access. Later production versions should move to a more reliable market-data provider.
