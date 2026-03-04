"""Generate sample datasets for demo purposes."""
import json
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

OUT = Path(__file__).parent.parent / "sample_data"
OUT.mkdir(exist_ok=True)

rng = random.Random(42)

PRODUCTS = ["Widget Pro", "Gadget Lite", "Widget Max", "Gadget Pro", "Accessory A",
            "Accessory B", "Bundle S", "Bundle M", "Service Pack", "Extended Care"]
REGIONS = ["North", "South", "East", "West", "Central"]
SALESPEOPLE = [f"Rep_{i:02d}" for i in range(1, 21)]


def sales_data():
    rows = []
    start = date(2023, 1, 1)
    for i in range(500):
        d = start + timedelta(days=rng.randint(0, 364))
        product = rng.choice(PRODUCTS)
        region = rng.choice(REGIONS)
        person = rng.choice(SALESPEOPLE)
        # Seasonal boost in Q4
        seasonal = 1.3 if d.month >= 10 else 1.0
        qty = rng.randint(1, 20)
        price = rng.uniform(50, 500) * seasonal
        cost = price * rng.uniform(0.4, 0.7)
        rows.append({
            "date": d.isoformat(),
            "product": product,
            "region": region,
            "salesperson": person,
            "quantity": qty,
            "revenue": round(price * qty, 2),
            "cost": round(cost * qty, 2),
            "profit": round((price - cost) * qty, 2),
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "sales_data.csv", index=False)
    print(f"sales_data.csv: {len(df)} rows")


CATEGORIES = ["Software", "Hardware", "Services", "Consulting", "Training", "Support"]
DEPARTMENTS = ["Engineering", "Sales", "Marketing", "Operations", "Finance", "HR"]


def financial_data():
    rows = []
    start = date(2023, 1, 1)
    for i in range(200):
        d = start + timedelta(days=rng.randint(0, 364))
        cat = rng.choice(CATEGORIES)
        dept = rng.choice(DEPARTMENTS)
        tx_type = rng.choice(["income", "expense"])
        # Quarterly spikes
        spike = 1.5 if d.month % 3 == 0 else 1.0
        amount = rng.uniform(1000, 50000) * spike
        # One anomaly
        if i == 100:
            amount = 500000
        rows.append({
            "date": d.isoformat(),
            "category": cat,
            "department": dept,
            "type": tx_type,
            "amount": round(amount, 2),
        })
    df = pd.DataFrame(rows)
    df.to_excel(OUT / "financial_data.xlsx", index=False)
    print(f"financial_data.xlsx: {len(df)} rows")


CAMPAIGNS = [f"Campaign_{chr(65+i)}" for i in range(10)]
CHANNELS = ["Email", "Social", "Search", "Display", "Video"]


def marketing_data():
    records = []
    start = date(2023, 1, 1)
    for i in range(300):
        d = start + timedelta(days=rng.randint(0, 364))
        campaign = rng.choice(CAMPAIGNS)
        channel = rng.choice(CHANNELS)
        impressions = rng.randint(1000, 100000)
        ctr = rng.uniform(0.01, 0.15)
        clicks = int(impressions * ctr)
        cvr = rng.uniform(0.02, 0.12)
        conversions = int(clicks * cvr)
        spend = rng.uniform(100, 5000)
        records.append({
            "date": d.isoformat(),
            "campaign": campaign,
            "channel": channel,
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "spend": round(spend, 2),
            "ctr": round(ctr, 4),
            "cvr": round(cvr, 4),
        })
    path = OUT / "marketing_data.json"
    path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"marketing_data.json: {len(records)} records")


HR_DEPARTMENTS = ["Engineering", "Sales", "Marketing", "Operations", "Finance", "HR", "Legal", "Support"]
QUARTERS = [f"{y}-Q{q}" for y in [2022, 2023, 2024] for q in range(1, 5)]


def hr_data():
    rows = []
    for dept in HR_DEPARTMENTS:
        base_hc = rng.randint(20, 120)
        base_satisfaction = rng.uniform(3.0, 4.5)
        for q in QUARTERS:
            training_hours = rng.uniform(4, 40)
            # Training-satisfaction correlation
            satisfaction = min(5.0, base_satisfaction + training_hours * 0.02 + rng.uniform(-0.3, 0.3))
            rows.append({
                "quarter": q,
                "department": dept,
                "headcount": base_hc + rng.randint(-5, 5),
                "turnover_rate": round(rng.uniform(0.05, 0.25), 3),
                "satisfaction_score": round(satisfaction, 2),
                "training_hours": round(training_hours, 1),
                "avg_tenure_years": round(rng.uniform(1.5, 8.0), 1),
            })
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "hr_metrics.csv", index=False)
    print(f"hr_metrics.csv: {len(df)} rows")


if __name__ == "__main__":
    sales_data()
    financial_data()
    marketing_data()
    hr_data()
    print("Done. Sample data written to sample_data/")
