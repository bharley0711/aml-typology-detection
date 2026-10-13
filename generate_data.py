"""
Generate a synthetic transaction dataset with known AML typologies embedded.

The dataset is 100% fictional - generated locally with a fixed seed so the
results are reproducible. It contains ordinary background activity plus two
deliberately planted patterns:

1. STRUCTURING  - one subject makes repeated cash deposits just under the
   $10,000 currency transaction reporting threshold.
2. MULE FAN-IN / FAN-OUT - multiple senders funnel money into one account,
   which then sends most of it out in a single transfer.

Output: transactions.csv with columns
    date, account_id, counterparty_id, direction, amount, channel

Usage:  python generate_data.py
"""

import csv
import random
from datetime import date, timedelta

random.seed(42)

START = date(2026, 1, 5)
DAYS = 60

rows = []

# ---------------------------------------------------------------- background
# Ordinary customers: salaries in, bills and card spend out, occasional P2P.
background_accounts = [f"ACCT-{1000 + i}" for i in range(40)]
for acct in background_accounts:
    day = START
    while day < START + timedelta(days=DAYS):
        # salary roughly every two weeks
        if day.weekday() == 4 and (day.day % 14) < 7:
            rows.append([day, acct, "EMPLOYER-PAYROLL", "in",
                         round(random.uniform(1800, 4200), 2), "ACH"])
        # everyday spending
        for _ in range(random.randint(0, 2)):
            rows.append([day, acct, random.choice(
                ["GROCERY-STORE", "UTILITY-CO", "CARD-PAYMENT", "LANDLORD-LLC"]),
                "out", round(random.uniform(25, 600), 2), "card"])
        # occasional person-to-person transfer
        if random.random() < 0.15:
            rows.append([day, acct, random.choice(background_accounts),
                         random.choice(["in", "out"]),
                         round(random.uniform(20, 450), 2), "P2P"])
        day += timedelta(days=1)

# ------------------------------------------------------- planted: structuring
# Subject spreads $47,600 in cash deposits across 5 days, every deposit just
# under $10,000 - the classic structuring signature (31 USC 5324).
structurer = "ACCT-9001"
structuring_amounts = [9800, 9500, 9900, 9200, 9200]
for i, amt in enumerate(structuring_amounts):
    rows.append([START + timedelta(days=10 + i), structurer,
                 f"BRANCH-{random.choice(['A', 'B', 'C'])}", "in",
                 float(amt), "cash"])

# ------------------------------------------------- planted: mule fan-in / out
# Six senders each move money into one account inside a 4-day window; the
# account then wires 92% of the total out to a single external beneficiary.
mule = "ACCT-9002"
senders = [f"ACCT-{2000 + i}" for i in range(6)]
fan_in_total = 0.0
for i, sender in enumerate(senders):
    amt = round(random.uniform(2800, 4600), 2)
    fan_in_total += amt
    rows.append([START + timedelta(days=30 + i % 4), mule, sender, "in",
                 amt, "P2P"])
rows.append([START + timedelta(days=35), mule, "EXT-BENEFICIARY-77", "out",
             round(fan_in_total * 0.92, 2), "wire"])

rows.sort(key=lambda r: r[0])

with open("transactions.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["date", "account_id", "counterparty_id", "direction",
                     "amount", "channel"])
    writer.writerows(rows)

print(f"Wrote {len(rows)} transactions to transactions.csv")
print(f"Planted structuring total: ${sum(structuring_amounts):,.2f} "
      f"across {len(structuring_amounts)} cash deposits")
print(f"Planted mule fan-in total: ${fan_in_total:,.2f} from "
      f"{len(senders)} senders, followed by one outbound wire")
