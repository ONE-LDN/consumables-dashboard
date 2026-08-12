# Deliveries since the baseline count

Every delivery landing **after** the 2026-08-04 baseline count. `deliveries_backfill.csv`
covers Feb–Jul 2026 and is closed; new deliveries append to
`deliveries_since_baseline.csv`, same schema, so the two concatenate for the
Supabase load.

This exists because usage is `opening + orders_between − closing`. An unlogged
delivery does not just go missing — it makes the arithmetic lie, and it lies in
the direction of *understating* consumption.

---

## 2026-08-07 — two deliveries, £283.64 net

**Futures Supplies** — £49.60 net

| product | qty | unit | net |
|---|---|---|---|
| Blue Roll (centrefeed) `002.025B` | 2 cases × 6 | £11.31/case | £22.62 |
| Hand Sanitiser 5L `007.302S` | 1 each | £26.98 | £26.98 |

**Out of Eden** — £234.04 net, £46.81 VAT, **£280.85 gross**

| product | qty | list | discount | net |
|---|---|---|---|---|
| Hand Wash 5L | 3 | £20.99 | 5% | £59.82 |
| Hand & Body Lotion 5L | 1 | £20.99 | — | £20.99 |
| Conditioner 5L | 2 | £20.99 | 5% | £39.88 |
| Shampoo & Body Wash 5L | 6 | £20.99 | 10% | £113.35 |

### Position after these deliveries

Baseline (04/08) plus the delivery, **before any usage is deducted**:

| product | 04/08 | +07/08 | = | minimum | was | now |
|---|---|---|---|---|---|---|
| Blue Roll | 20 rolls | +12 | **32** | 30 | BELOW | ok, **+2** |
| Shampoo & Body Wash | 3 bottles | +6 | **9** | 6 | BELOW | ok, +3 |
| Hand Wash | 0 bottles | +3 | **3** | 2 | BELOW | ok, +1 |
| Conditioner | 1 bottle | +2 | **3** | 2 | BELOW | ok, +1 |
| Hand & Body Lotion | 3 bottles | +1 | **4** | 3 | ok | ok, +1 |
| Hand Sanitiser 5L | 1 bottle | +1 | **2** | 1 | ok | ok, +1 |

**Four of the fourteen below-minimum lines are cleared. Ten remain**: Hair Bands,
Bin Bags, Deodorant (Men), Deodorant (Women), D Batteries, Coffee Machine
Cleaner, Printer Paper, Chalk Block, Washing Up Liquid, Wet Kit Bags.

⚠ **Blue Roll's +2 is not a real margin.** The purchase floor runs at roughly
4.8 cases a month — about 0.95 rolls a day — so eight days between the delivery
and today is worth around 7–8 rolls. On that arithmetic Blue Roll is already
back below 30. Treat the `ok` above as a ceiling, not a reading. Every figure in
that table is a ceiling: none of them has usage deducted, because there has been
no count since 04/08.

---

## Two findings from these invoices

### 1. The v4 price column mixes net and gross

`products_v4.csv` carries **£25.19** for all four Out of Eden toiletries. The
invoice says **£20.99** net — and `20.99 × 1.20 = 25.19`. So the v4 sheet's Out
of Eden prices are **VAT-inclusive**, while the Futures prices are net:
`blue_rolls` at £11.31 and `sanitiser_gel` at £26.98 both match this invoice to
the penny, ex VAT.

This is the same failure as the £800.53 total in the first session — a price
column with two bases and no column saying which. It is worth fixing at source
before any of these prices enters a costed order, and worth stating in the sheet
header that prices are net.

Correction to apply: `hand_wash`, `conditioner`, `moisturiser`, `shampoo`
→ **£20.99 net** list.

Separately, **Out of Eden discounts by line** (5% and 10% here), so the price
paid is not the list price. The catalogue should hold list net; the discount
belongs on the delivery record, which is where it now is.

### 2. Possible duplicate — the shampoo line

`deliveries_backfill.csv` already holds `2026-07-21, shampoo, 6, £113.35 net`,
which matches this invoice's shampoo line exactly.

**Logged as distinct**, on this reasoning: 6 bottles at the standing 10%
discount always totals £113.35, so an identical figure is what a repeat order
looks like rather than evidence of one. The shampoo cadence — 09/03, 28/04,
13/05, 04/06, 25/06, 21/07 — is roughly three-weekly, and 07/08 is 17 days after
21/07, which fits. And every prior Out of Eden order in the backfill is
**shampoo alone**; the hand wash, conditioner and lotion lines came from Futures
as Sea Kelp until May. A four-line Out of Eden order is the new supplier
arrangement, not a re-transcription of an old one.

**If the 21/07 entry turns out to be this same invoice**, drop the shampoo row
from `deliveries_since_baseline.csv` — nothing else on it is affected.

---

## To do with this

1. Paste both deliveries into the sheet's **`Order Log`** tab, in packs:

   | Date | Product | Packs ordered | Unit cost £ | Supplier |
   |---|---|---|---|---|
   | 2026-08-07 | Blue Roll (centrefeed) | 2 | 11.31 | Futures Supplies |
   | 2026-08-07 | Hand Sanitiser 5L | 1 | 26.98 | Futures Supplies |
   | 2026-08-07 | Hand Wash 5L | 3 | 19.94 | Out of Eden |
   | 2026-08-07 | Hand & Body Lotion 5L | 1 | 20.99 | Out of Eden |
   | 2026-08-07 | Conditioner 5L | 2 | 19.94 | Out of Eden |
   | 2026-08-07 | Shampoo & Body Wash 5L | 6 | 18.89 | Out of Eden |

2. **Take count 2.** It was due Tue 11/08. These six lines are the only ones
   with a known delivery between counts, which makes them the first products
   able to produce a real usage figure — and Blue Roll, moving nearly a roll a
   day, is the one that will read cleanest after a single week.
3. Fix the four Out of Eden prices to £20.99 net at source.
