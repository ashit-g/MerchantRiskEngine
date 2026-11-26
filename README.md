# MerchantRiskEngine

MerchantRiskEngine is an ML lab project for marketplace fulfilment monitoring. At each month-end it forecasts which sellers are likely to have **at least 20% of eligible deliveries arrive late in the next promised-delivery month**. An operations team can use the merchant score to prioritise reviews and drill down into the products or categories contributing to recent delays.

The project uses observed delivery outcomes from [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

## Run locally

Use Python 3.11 or 3.12. Download and extract the Olist archive into `data/olist/`. See the [data guide](docs/data.md) for the required files.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m merchant_risk train
python -m unittest discover -s tests -v
```

Training writes the model, evaluation report and held-out seller scores to `artifacts/`. To inspect a seller, use a seller ID and its scoring date from the held-out table. Category is the default drill-down. Use `--group-by product_id` for individual products.

```sh
head -5 artifacts/test_scores.csv
python -m merchant_risk score --seller-id SELLER_ID --as-of YYYY-MM-DD
```

The score includes the forecast, an example operations review tier, up to three feature comparisons and a 30-day drill-down. For input and output options, use `python -m merchant_risk --help`.

## Run the Streamlit dashboard

From the repository root with the virtual environment active:

```sh
python -m pip install -r requirements-dashboard.txt
python -m merchant_risk train
python -m streamlit run dashboard.py --server.address 127.0.0.1
```

Open [the local dashboard](http://localhost:8501). If you already have a model and score export from the same training run, you can reuse them.

Choose a forecast month and review tier, then inspect a seller from the ranked queue. The **Delivery trend** and **Product breakdown** tabs cover deliveries observed by the scoring date. **Score drivers** shows how the forecast changes when individual inputs are replaced with their training medians.

The review queue uses the held-out evaluation export. It includes sellers with both sufficient historical activity and a mature outcome label. Forecasts use the saved model and information available at the scoring date. The dashboard reports a warning if the model and queue need to be regenerated together.

## Project notes

- [Data and target](docs/data.md) covers source files, the outcome rule and known exclusions.
- [Modelling and evaluation](docs/methodology.md) explains the split, baseline, features and review thresholds.
- [Initial results](docs/results.md) records the first validation and held-out evaluation.
- [Two-person task plan](TASKS.md) assigns the remaining evaluation and dashboard work.
- Code lives in `merchant_risk/`. Raw data and locally generated artifacts are ignored by Git.
