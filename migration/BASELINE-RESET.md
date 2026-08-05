# Baseline reset

Saffron's proposal: treat the next count as clearing the slate, restock to a known
level, then measure real consumption from the weekly counts and adjust.

**Do it.** It's exactly the input the prediction model is built for — usage is
computed as `opening + orders_between − closing`, which needs two consecutive
counts and the orders between them, and no history at all. Three months of
guesswork gets replaced by three weeks of measurement.

Four things make the difference between a clean baseline and another year of
guessing.

## 1. Count first, then order

Not the other way round. The current `Stock` column mixes packs and items and 9
products can't be told apart, so ordering off it is how you end up buying 444
tampons against a surplus of 256. The fresh count resolves the ambiguity for free.

**Tuesday: count everything in individual items, with the unit written into the
column header. Then place the reset order from that count.**

## 2. Restock *above* the minimum, not *to* it

The minimum is the floor you never want to cross. Land exactly on it and every
product flags "order now" at the very next count, and you've learned nothing.

## 3. Don't multiply a guess

The obvious rule — restock to `minimum + one month of usage` — is wrong here,
because for 45 of 52 products that usage figure is the very thing you don't know.
It inflates the order without making the measurement better.

Better:

| situation | restock to |
|---|---|
| usage is burn-checked or a purchase floor (7 products) | minimum + one month of usage |
| usage is an unverified estimate or absent (45) | **minimum + one pack** |

You'll know the real number in 2–4 weeks and can top up then. The difference is
material:

| rule | reset order |
|---|---|
| minimum + one month of usage, everywhere | ~£2,830 |
| the rule above, sized on the burn rate | ~£750 |
| **the rule above, sized on the purchase floor** | **£764.73 net / £917.67 gross** |

The first two are the mixed-basis figures they were originally quoted at, kept only
to show the shape of the difference — they haven't been restated on a single VAT
basis, because only the chosen rule became a real order. See `SHOPPING-LIST.md` for
the line-by-line VAT resolution.

The naive rule wanted 11 packs of water softener salt at £149.99 (£1,650), driven by
a par of 10 packs/month that is one of the seven known to be wrong. Saffron has since
confirmed the salt is heavily overstocked, so it sits in the do-not-order list — 36
bags on hand against a note saying 6 packs fill the tub.

### The reset order as it stands

Indicative — real quantities come from Tuesday's count. Full detail in
`SHOPPING-LIST.md` and `shopping_list.csv`.

| supplier | lines | cost (net ex-VAT) |
|---|---|---|
| Futures Supplies | blue roll ×7, hand wash ×3, conditioner ×2, moisturiser ×1, hand sanitiser ×2 | £283.26 |
| Out of Eden | Odyssey shampoo ×10 | £188.90 |
| Amazon | bin bags ×2, blue gloves ×2, blue cloth ×2, microfibre ×2, Puly ×2, urinal shields ×2, washing up liquid ×2 | £149.65 |
| Newline | wet kit bag ×2 | £97.92 *(basis unverified)* |
| Concept Spa | chill tubs sanitiser ×3 | £45.00 *(basis unverified)* |
| *(price TBC)* | deodorants ×5 each | — |
| **17 lines, total where priced** | | **£764.73 net / £917.67 gross** |

**VAT is now settled for 13 of the 15 priced lines**, so this is a budget figure
rather than the mixed-basis £800.53 it was quoted at before. Verified net for
Futures and Out of Eden (matched to invoice lines to the penny); converted from
gross for Amazon and the two prices taken from the old DB record. Newline and
Concept Spa can't be checked against anything and are read as net — if they turn out
to be gross the total drops to £740.91 net. **The ambiguity is worth £23.82**, so
it isn't a reason to hold the order. Full working in `SHOPPING-LIST.md`.

**Don't restock these 6** — already above minimum: pads (11×), water softener salt
(3.6×, confirmed), tampons (4×), chill tub filters (6.3×), toilet roll (1.1×),
Greenspeed (1.2×). Tampons, pads and salt are confirmed overstocked rather than
inferred, and are hard-excluded.

**Count but never order (5):** the four printer inks (new stock just arrived — count
them to learn how long a set lasts) and key fobs (handled separately).

**Hold back 24** until a real count exists: the 14 first-aid lines; ice packs, hair
bands, chalk block and D batteries (usage figures known wrong); Sea Kelp shampoo,
paper, pens and notepads (no pack size); and Glade, whose old count could still be
cans or packs. Tuesday's count supplies what each is missing.

## 4. Nothing may hit zero during the measurement window

This is the one hard constraint, and it's the same trap the invoice data fell into.
A product that runs dry mid-week reads as low consumption, because nobody could use
what wasn't there. One stockout corrupts that product's baseline and you start
again.

Since the minimum is already ~2 weeks of cover, minimum + one pack should hold for
a week comfortably. But it means: **during the reset period, err generous.** One
slightly oversized order is much cheaper than another quarter of guessing.

It also means every order must go through the Order Log. Usage is
`opening + orders − closing`; an off-book delivery makes the arithmetic lie.

## What you'll know, and when

A weekly count can only resolve about one unit, so a product using less than one
unit a week shows nothing on Tuesday.

| horizon | products | examples |
|---|---|---|
| **after 1 week** | 18 | toilet roll (10.5/wk), blue roll (11.7/wk), shampoo (2.6/wk), bin bags, deodorants |
| **2–4 weeks** | 5 | Puly, chill tub filters, Glade, hand sanitiser, urinal case |
| **1–3 months** | 11 | the 5L refills (0.1–0.2/wk), printer ink, key fobs, washing up liquid |
| **no estimate yet** | 18 | the 14 first-aid lines, pens, notepads, paper, Sea Kelp shampoo |

So: the fast movers — which are also the ones that actually run out and the ones
carrying the spend — are readable after **one Tuesday**, and solid after three or
four. The 5L refills will take a quarter, and that's fine; they're slow, cheap to
overstock, and your `Par Qty` already handles them.

Realistic expectation: **by early September the fast movers run on measured usage
rather than anyone's estimate.** The slow movers keep running on your `Par Qty`
until Christmas, which is the right answer for a product that moves one bottle a
month.

## Sequence

1. **Tuesday** — fresh count, individual items, unit in the header. This is
   count 1 and the baseline.
2. Place the reset order from that count, using the rule in §3. Log it.
3. **Following Tuesdays** — count again. From count 2 the model starts producing
   measured usage; treat the first reading as noisy.
4. **After 3–4 counts** — replace the estimated pars for the fast movers with
   measured usage. Revisit the 7 known-bad pars first; they'll have real numbers by
   then.
5. Leave the slow movers on `Par Qty` and revisit at the end of the quarter.

The resulting order is in `SHOPPING-LIST.md`.

One thing worth deciding up front: whether the reset order goes in as a single
purchase or is split across two weeks. £918 gross in one go is a cash-flow question,
not a data question — splitting it costs you nothing analytically as long as every
delivery is logged.
