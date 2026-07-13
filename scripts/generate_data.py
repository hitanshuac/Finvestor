import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def generate_domain_accurate_data():
    np.random.seed(42)
    random.seed(42)
    dates = [datetime.today() - timedelta(days=x) for x in range(90)]
    data = []

    # =======================================================
    # PERSONA 1: Rahul, Age 28 (The Target for SIPs & Budgeting)
    # Profile: High salary, but high lifestyle inflation. Drowning in Swiggy/Uber.
    # AI Expected Insight: "Cut back on Dining, start an Equity SIP."
    # =======================================================
    balance_1 = 35000  # Low starting idle cash
    for d in dates:
        # Salary Credit (1st of month)
        if d.day == 1:
            data.append(["101", 28, d.strftime("%Y-%m-%d"), 85000, "CR", "Salary", balance_1 + 85000])
            balance_1 += 85000
        # Fixed Outflows (Rent & EMI)
        elif d.day == 5:
            data.append(["101", 28, d.strftime("%Y-%m-%d"), 25000, "DR", "Housing_Rent", balance_1 - 25000])
            balance_1 -= 25000
        elif d.day == 10:
            data.append(["101", 28, d.strftime("%Y-%m-%d"), 12000, "DR", "Auto_Loan_EMI", balance_1 - 12000])
            balance_1 -= 12000
        # Daily Discretionary Spends (High frequency)
        else:
            if random.random() > 0.4:  # Spends almost every day
                spend = np.random.randint(400, 1500)
                cat = np.random.choice(["Food_Delivery", "Cab_Aggregator", "Entertainment", "Shopping"])
                data.append(["101", 28, d.strftime("%Y-%m-%d"), spend, "DR", cat, balance_1 - spend])
                balance_1 -= spend

    # =======================================================
    # PERSONA 2: Anil, Age 55 (The Target for FDs & Bonds)
    # Profile: High earner, low expenses, huge amount of idle cash doing nothing.
    # AI Expected Insight: "You have ₹15L idle. Let's lock this in a low-risk FD/Liquid Fund."
    # =======================================================
    balance_2 = 1450000  # Massive starting idle cash
    for d in dates:
        # Salary Credit (1st of month)
        if d.day == 1:
            data.append(["102", 55, d.strftime("%Y-%m-%d"), 220000, "CR", "Salary", balance_2 + 220000])
            balance_2 += 220000
        # Heavy Investments & Medical
        elif d.day == 7:
            data.append(["102", 55, d.strftime("%Y-%m-%d"), 40000, "DR", "Existing_Mutual_Funds", balance_2 - 40000])
            balance_2 -= 40000
        # Daily Spends (Low frequency, essential categories)
        else:
            if random.random() > 0.7:  # Spends less frequently
                spend = np.random.randint(1000, 4000)
                cat = np.random.choice(["Groceries", "Pharmacy/Medical", "Utilities", "Fuel"])
                data.append(["102", 55, d.strftime("%Y-%m-%d"), spend, "DR", cat, balance_2 - spend])
                balance_2 -= spend

    # Save to CSV
    df = pd.DataFrame(
        data, columns=["customer_id", "age", "date", "amount", "transaction_type", "category", "running_balance"]
    )

    # Sort by date
    df = df.sort_values(by=["customer_id", "date"], ascending=[True, False])
    df.to_csv("data/bank_transactions.csv", index=False)
    print("✅ Domain-Accurate Dataset Generated: data/bank_transactions.csv")


if __name__ == "__main__":
    generate_domain_accurate_data()
