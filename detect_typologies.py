"""
Detect two AML typologies in a transaction file:

1. STRUCTURING - three or more cash deposits in the $9,000-$9,999.99 band
   (just under the $10,000 CTR threshold) by one account within 7 days.
2. MULE FAN-IN / FAN-OUT - an account receives funds from 5 or more unique
   senders within 7 days totalling at least $15,000, then sends out 80% or
   more of the received total within the following 5 days.

Input:  transactions.csv (see generate_data.py for how the synthetic file
        is built - all data is fictional)
Output: alerts printed to the console, one block per alert, in the style of
        a transaction-monitoring alert summary.

Usage:  python detect_typologies.py [path-to-csv]
"""

import csv
import sys
from collections import defaultdict
from datetime import date, timedelta

CTR_THRESHOLD = 10000.00
STRUCTURING_BAND_LOW = 9000.00
STRUCTURING_MIN_COUNT = 3
STRUCTURING_WINDOW_DAYS = 7

FANIN_MIN_SENDERS = 5
FANIN_MIN_TOTAL = 15000.00
FANIN_WINDOW_DAYS = 7
FANOUT_MIN_RATIO = 0.80
FANOUT_WINDOW_DAYS = 5


def load_transactions(path):
    with open(path, newline="") as f:
        txns = []
        for row in csv.DictReader(f):
            row["date"] = date.fromisoformat(row["date"])
            row["amount"] = float(row["amount"])
            txns.append(row)
    return sorted(txns, key=lambda r: r["date"])


def detect_structuring(txns):
    """Cash deposits clustered just under the CTR threshold."""
    alerts = []
    by_account = defaultdict(list)
    for t in txns:
        if (t["direction"] == "in" and t["channel"] == "cash"
                and STRUCTURING_BAND_LOW <= t["amount"] < CTR_THRESHOLD):
            by_account[t["account_id"]].append(t)

    for account, deposits in by_account.items():
        deposits.sort(key=lambda r: r["date"])
        for i, first in enumerate(deposits):
            window = [d for d in deposits[i:]
                      if d["date"] <= first["date"]
                      + timedelta(days=STRUCTURING_WINDOW_DAYS - 1)]
            if len(window) >= STRUCTURING_MIN_COUNT:
                alerts.append({
                    "typology": "STRUCTURING",
                    "account": account,
                    "start": window[0]["date"],
                    "end": window[-1]["date"],
                    "count": len(window),
                    "total": sum(d["amount"] for d in window),
                    "detail": ", ".join(
                        f"${d['amount']:,.2f} on {d['date']}"
                        for d in window),
                })
                break  # one alert per account is enough for a demo
    return alerts


def detect_mule_fan_in_out(txns):
    """Many senders in, one large transfer out shortly after."""
    alerts = []
    by_account = defaultdict(list)
    for t in txns:
        by_account[t["account_id"]].append(t)

    for account, activity in by_account.items():
        inbound = sorted([t for t in activity if t["direction"] == "in"],
                         key=lambda r: r["date"])
        outbound = [t for t in activity if t["direction"] == "out"]
        for i, first in enumerate(inbound):
            window = [t for t in inbound[i:]
                      if t["date"] <= first["date"]
                      + timedelta(days=FANIN_WINDOW_DAYS - 1)]
            senders = {t["counterparty_id"] for t in window}
            total_in = sum(t["amount"] for t in window)
            if len(senders) < FANIN_MIN_SENDERS or total_in < FANIN_MIN_TOTAL:
                continue
            follow_out = [t for t in outbound
                          if window[-1]["date"] <= t["date"]
                          <= window[-1]["date"]
                          + timedelta(days=FANOUT_WINDOW_DAYS)]
            total_out = sum(t["amount"] for t in follow_out)
            if total_out >= FANOUT_MIN_RATIO * total_in:
                alerts.append({
                    "typology": "MULE FAN-IN / FAN-OUT",
                    "account": account,
                    "start": window[0]["date"],
                    "end": follow_out[-1]["date"],
                    "count": len(senders),
                    "total": total_in,
                    "detail": (f"{len(senders)} unique senders, "
                               f"${total_in:,.2f} in, then "
                               f"${total_out:,.2f} out "
                               f"({total_out / total_in:.0%} of funds)"),
                })
                break
    return alerts


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "transactions.csv"
    txns = load_transactions(path)
    alerts = detect_structuring(txns) + detect_mule_fan_in_out(txns)

    print(f"Scanned {len(txns)} transactions from {path}")
    print(f"{len(alerts)} alert(s) generated\n")
    for a in alerts:
        print(f"[{a['typology']}] account {a['account']}")
        print(f"  Window : {a['start']} to {a['end']}")
        print(f"  Total  : ${a['total']:,.2f}")
        print(f"  Detail : {a['detail']}\n")


if __name__ == "__main__":
    main()
