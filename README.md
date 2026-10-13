# AML Typology Detection — Synthetic Data

A small transaction-monitoring exercise: generate a fully fictional
transaction dataset with known money-laundering patterns planted in it, then
write detection logic that finds them — the same shape as a real monitoring
rule, at portfolio scale.

> ⚠️ **All data in this repository is synthetic.** It is generated locally by
> `generate_data.py` from a fixed random seed. No real customer, account,
> employer, or case data is used anywhere in this project.

## Typologies covered

**1. Structuring** — A subject makes repeated cash deposits just under the
$10,000 currency transaction reporting (CTR) threshold, apparently to evade
the reporting requirement (31 USC 5324).

*Detection rule:* 3+ cash deposits in the $9,000–$9,999.99 band by one account
within a rolling 7-day window.

**2. Mule fan-in / fan-out** — Multiple senders funnel funds into a single
account in a short window; the account then forwards most of the money in one
outbound transfer, keeping little behind. A common money-mule / layering
signature.

*Detection rule:* an account receives funds from 5+ unique senders within
7 days totalling $15,000+, then sends out 80%+ of the received total within
the following 5 days.

## How to run

```bash
python generate_data.py      # writes transactions.csv (3,054 records)
python detect_typologies.py  # scans the file and prints alerts
```

Pure Python standard library — no dependencies.

## Results on the synthetic dataset

The generator plants exactly two patterns in 60 days of background activity
across 40 ordinary accounts. The detector finds both, with no false alerts
on the background population:

```
Scanned 3054 transactions from transactions.csv
2 alert(s) generated

[STRUCTURING] account ACCT-9001
  Window : 2026-01-15 to 2026-01-19
  Total  : $47,600.00
  Detail : $9,800.00 on 2026-01-15, $9,500.00 on 2026-01-16, $9,900.00 on
           2026-01-17, $9,200.00 on 2026-01-18, $9,200.00 on 2026-01-19

[MULE FAN-IN / FAN-OUT] account ACCT-9002
  Window : 2026-02-04 to 2026-02-09
  Total  : $23,324.79
  Detail : 6 unique senders, $23,324.79 in, then $21,458.81 out
           (92% of funds)
```

## Design notes

- **Thresholds are parameters, not magic numbers.** Every rule constant
  (band, window, count, ratio) is named at the top of `detect_typologies.py`,
  mirroring how production rules are tuned and documented.
- **Rolling windows, not calendar buckets.** Patterns that straddle a month
  boundary still alert.
- **One alert per account per typology** in this demo, to keep output
  readable; a production rule would emit every qualifying window and rely on
  downstream alert consolidation.

## What I would add next

- A third typology: rapid movement of funds (pass-through) across chained
  accounts.
- Precision/recall scoring against the planted ground truth as thresholds
  vary — a small tuning study.
- The same rules expressed in SQL, the way they often run in production
  monitoring systems.
