# How to work out the minimum stock

Short version: **you have already written it — it's the `Par Qty` column.** The
job is to fill the gaps around it, not replace it.

## First, a correction about the invoice data

An earlier version of this document treated the invoice tab as a measurement of
consumption, and said the stored monthly pars were "verified" because they matched
it. That was wrong on both counts.

The previous operations manager ordered **reactively, after running out**. That
breaks the inference in two ways:

1. **Consumption was suppressed during the dry spells.** You cannot use toilet
   roll that isn't there. So purchases over the window are a **floor** on demand,
   not an estimate of it.
2. **The stored pars were derived from these same purchases**, so their matching
   the purchase rate to 2 d.p. showed a number agreeing with its own source. That
   was circularity, not validation.

Both the purchase rate and the stored pars are now treated as floors, and
labelled as such in `min_stock_model.csv`.

### How far off? Roughly 40–60% for the fast movers

There's one independent check available. The 29/07 count came a few days after a
delivery, and on the reactive-ordering premise on-hand was ~0 when each order went
in — so the difference is real burn:

| item | delivered | days to count | on hand | used | implied packs/mo | purchase floor | ratio |
|---|---|---|---|---|---|---|---|
| Jumbo T.Roll | 6 packs (23/07) | 6 | 27 rolls | 9 rolls | **7.61** | 5.59 | 1.38× |
| 2ply Blue roll | 5 packs (23/07) | 6 | 20 rolls | 10 rolls | **8.46** | 4.97 | 1.57× |
| Odyssey Shampoo | 6 packs (21/07) | 8 | 3 | 3 | **11.42** | 6.42 | 1.63× |
| Sea Kelp Hand Wash | 2 packs (19/05) | 71 | 0 | 2 | 0.86 | 0.83 | 1.07× |

All four point the same way. It doesn't work for the slow movers — moisturiser
counts 3 against 2 delivered, so the "zero at order" premise plainly fails there,
and those keep their floor figure.

Caveat: this is one count and one assumption. Treat it as a direction of travel,
not a measurement. It's used for order sizing where it's higher than the floor.

## The rule

With a count every Tuesday, the minimum stock is *whatever has to last until you
next get a chance to look, plus the wait for delivery, plus a bit of slack*:

```
minimum stock (units) = daily usage x (7 + lead time + safety days)
```

- **7 days** — if an item slips past this Tuesday's count you don't get another
  look for a week.
- **lead time** — days from placing the order to it arriving.
- **safety days** — 3 normally, 7 for anything a member would notice running out
  (toilet roll, blue roll, shampoo, hand wash, sanitiser, bin bags, tampons, pads).

For most items that lands around 12–17 days of cover, i.e. **roughly two weeks'
worth**. Everything below is guard rails on that.

## Four inputs, take the highest

A single formula gives silly answers at both ends — 0.3 of a 5L bottle for slow
movers, and nonsense wherever the usage figure is wrong. So the minimum is the
highest of four candidates:

| Candidate | Why it's there |
|---|---|
| **Your `Par Qty`** | Your judgement about the place. Never overridden downwards. |
| **usage × cover days** | The calculation above. Can only ever *raise* your figure. |
| **A minimum written in the notes** | D Batteries `Need to have 10 on hand`, Paper `2 on hand`, Notepads `need 1 on hand`. |
| **One pack** | You buy in packs, so a trigger below one pack is meaningless. |

This is why the reactive-ordering correction barely moved the minimums: taking the
highest meant your `Par Qty` was already carrying the fast movers. The correction
raised toilet roll from 24 to 25.5 rolls and shampoo from 6 to 6.4, and left the
rest alone. **The design was robust to the bad input** — which is the argument for
keeping it that way.

## Your `Par Qty` looks well-judged

At the burn-checked rates, your figures come out at almost exactly the cover the
formula is aiming for:

| item | your Par Qty | burn rate | that's cover of | target |
|---|---|---|---|---|
| Jumbo T.Roll | 24 rolls | 1.50 rolls/day | 16 days | 17 |
| 2ply Blue roll | 30 rolls | 1.67 rolls/day | 18 days | 17 |

You were already setting a fortnight of cover by eye.

## Where the correction *does* bite: order quantities

```
order up to = minimum stock + one month of usage,  rounded up to whole packs
```

Understated usage means undersized orders — and undersized orders are the
mechanism that keeps you reordering reactively. This is where the numbers moved:

| item | order-up-to before | after |
|---|---|---|
| Jumbo T.Roll | 60 rolls | **72** |
| 2ply Blue roll | 60 rolls | **84** |
| Odyssey Shampoo | 13 | **18** |

The cadence then falls out of the numbers rather than being set by hand — fast
movers land on ~30 days, slow movers on 60–150. See `implied_order_every_days` in
`min_stock_model.csv`. **You don't need the `Cadence` column; it can go.**

## Why the weekly count is the real fix

The invoice tab records four `Ran out before next order` lines — toilet roll and
blue roll, twice each — with order gaps of 13, 30, 39, 16 and 49 days.

Read correctly, those gaps aren't the *cause* of the stockouts; the order dates
*mark* them. Each order was placed because the cupboard was already empty. The
gap tells you how long a batch lasted plus how long the dry spell ran.

Which is the point: counting every Tuesday replaces the whole mechanism. The worst
case stops being "however long until someone notices" and becomes 7 days. You set
two numbers per product — usage and minimum — and stop reacting.

## The usage figures still aren't good

After the correction, of 52 products:

- **4** have a burn-checked usage figure (one count, one assumption).
- **3** have a purchase floor and nothing better.
- **27** have an unverified hand-typed estimate.
- **18** have no usage figure at all.

Seven of the estimates look like **units-per-month entered as packs-per-month** —
multiplying by pack size gives an implausible result:

| product | stored par | implies | your Par Qty |
|---|---|---|---|
| Ice packs | 24 packs/mo | 576 ice packs/mo | (blank) |
| Tampons | 6 packs/mo | 384 tampons/mo | 64 |
| Sanitary Pads | 6 packs/mo | 264 pads/mo | 44 |
| D Batteries | 8 packs/mo | 64 batteries/mo | 8 (note says 10 on hand) |
| Water Softener Salt | 10 packs/mo | 100 bags/mo | 10 |
| Hair Bands | 1 pack/mo | 100 bands/mo | 1 |
| Chalk Block | 2 packs/mo | 16 blocks/mo | 2 |

Where that happens the model ignores the par, falls back to your `Par Qty` or one
pack, and flags the row. Nothing silently inherits a bad number.

Bin bags is the remaining judgement call: 2 packs/month is 400 bags, ~13 a day.
Plausible for a busy gym, but it drives a minimum of 210 bags, so worth confirming.

**The honest conclusion: your first few Tuesday counts will be the first
trustworthy usage data this system has ever had.** The hybrid model already
measures usage from consecutive counts (`opening + orders − closing`), so after
two or three weeks it supersedes everything above. Don't over-invest in
reconstructing the past — set the minimums from `Par Qty`, let the counts take
over, and expect to revise the fast movers upward.

The delivery backfill is still worth loading, incidentally. Those orders genuinely
happened and the `orders_between` term needs them; it's only the *inference* about
demand that was unsafe.

## Counting in individual units

- `shop_stock_takes.actual_count` becomes **units**, and every product needs
  `units_per_pack` to convert for ordering. Known for 45 of 52; unknown for Pens,
  Notepads, Paper, and the 14 first-aid lines.
- **Decimals are fine and expected** — half a 5L bottle is a real count of 0.5.
- **The existing count needs a fresh start, not a conversion.** Several figures in
  the current `Stock` column are part-*packs*: bin bags `0.5`, washing up liquid
  `0.5`, Puly `0.5`, paper `0.5`, Greenspeed `2.5`. Read as units, 0.5 bin bags
  instead of 100 is badly wrong.

## What this produces right now

Against the counts currently in the sheet, **29 of 52 products are at or below
their minimum**. Expected on a first proper count rather than a sign the
thresholds are wrong — plenty of rows genuinely read `0`, and reactive ordering is
exactly what leaves a cupboard looking like that. It'll settle after a cycle or
two.

## Still needs a number from you

- **Pens** — no `Par Qty`, no pack size, no usage. The only product with nothing
  to work from.
- **Microfibre Cloths** — no category on the Stock tab.
- **The 14 first-aid lines** — `Par Qty` gives them a minimum, but with no pack
  size and no prices they can't produce an order. They're components of restock
  boxes rather than order units; consider tracking the 4 boxes as one item and
  keeping the component list as a checklist.
