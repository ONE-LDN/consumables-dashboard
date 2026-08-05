# Reset shopping list

**The `order` column is in PACKS. `have` and `min` are individual items.** The
`arriving` column spells out how many individual items each order brings in.

Sizing rule: restock to **minimum + one month of usage** only where that usage
figure is trustworthy, and to **minimum + one pack** everywhere else. Order sizing
never uses the post-delivery burn rate — that includes dispenser refills, so it
overstates.

**Prices below are net ex-VAT.** The sheet mixed two bases; that's now resolved
line by line — see *VAT* at the bottom, and the `VAT basis` column in
`shopping_list.csv`. Two lines are still unverified.

## 1. Order now

### Futures Supplies — £283.26

| item | have | min | **order** | arriving | net each | line | basis |
|---|---|---|---|---|---|---|---|
| 2ply Blue Embossed C/feed Roll 150m 96711 | 20 rolls | 30 | **7 packs** | 42 rolls | £11.31 | £79.17 | verified |
| Sea Kelp Liquid Hand Wash Refill 5L | 0 × 5L | 2 | **3 packs** | 3 × 5L | £29.12 | £87.36 | verified |
| Sea Kelp Luxury Conditioner Refill 5L | 1 × 5L | 2 | **2 packs** | 2 × 5L | £29.12 | £58.24 | verified |
| Sea Kelp Luxury Hand & Body Lotion 5L Refill (Moisturiser) | 3 × 5L | 3 | **1 pack** | 1 × 5L | £29.12 | £29.12 | verified |
| Hand sanitiser | 1 × 5L | 1.1 | **2 packs** | 2 × 5L | £14.68 | £29.37 | from old record |

### Out of Eden — £188.90

| item | have | min | **order** | arriving | net each | line | basis |
|---|---|---|---|---|---|---|---|
| Odyssey Black Pepper & Sandalwood Shampoo & Body Wash 5L | 3 × 5L | 6 | **10 packs** | 10 × 5L | £18.89 | £188.90 | verified |

### Amazon — £149.65

| item | have | min | **order** | arriving | net each | line |
|---|---|---|---|---|---|---|
| Puly Caffe Cleaner | 0.5 bottles | 2 | **2 packs** | 4 bottles | £17.89 | £35.78 |
| Bin bags | 100 bags | 210.2 | **2 packs** | 400 bags | £13.85 | £27.70 |
| Urinal case | 0 shields | 10 | **2 packs** | 20 shields | £12.46 | £24.92 |
| Blue cloth | 0 rolls | 6 | **2 packs** | 12 rolls | £9.98 | £19.97 |
| Washing up liquid | 0.5 × 5L | 1 | **2 packs** | 2 × 5L | £9.89 | £19.78 |
| Microfibre Cloths | 0 cloths | 12 | **2 packs** | 24 cloths | £7.91 | £15.82 |
| Blue Gloves Large | 0 gloves | 100 | **2 packs** | 200 gloves | £2.84 | £5.68 |

All seven were listed VAT-inclusive and have been converted.

### Newline — £97.92 *(basis unverified)*

| item | have | min | **order** | arriving | listed each | line |
|---|---|---|---|---|---|---|
| Wet kit bag | 3 bags | 20 | **2 packs** | 40 bags | £48.96 | £97.92 |

### Concept Spa — £45.00 *(basis unverified)*

| item | have | min | **order** | arriving | listed each | line |
|---|---|---|---|---|---|---|
| Chill Tubs Sanitiser | 3 tubs | 23.7 | **3 packs** | 60 tubs | £15.00 | £45.00 |

### No price anywhere

| item | have | min | **order** | arriving |
|---|---|---|---|---|
| Deodorant - Men | 0 cans | 24 | **5 packs** | 30 cans |
| Deodorant - Women | 0 cans | 24 | **5 packs** | 30 cans |

**15 priced lines, £764.73 net / £917.67 gross.** Plus 10 packs of deodorant at an
unknown price.

## VAT — settled for 13 of 15 lines

The sheet's `Cost` column mixed two bases. Resolved as follows:

| basis | lines | value as listed | how it was established |
|---|---|---|---|
| **net ex-VAT** | 4 Futures + 1 Out of Eden | £442.79 | **Verified.** Each price matches an invoice line to the penny, and the invoice tab states all its figures are net of VAT. |
| **gross** | 7 Amazon + 2 taken from the old DB record | £214.82 | Amazon lists VAT-inclusive; the DB stores gross throughout (exactly ×1.20 on every trade item that appears in both). |
| **unverified** | Newline, Concept Spa | £142.92 | No invoice line and no DB price, so there is nothing to check them against. Read as net above — **not** because that's likely, but so the figure is stated rather than assumed. |

So the headline moved from a mixed-basis **£800.53**, which was not a real number in
either currency, to:

| | net ex-VAT | gross |
|---|---|---|
| taking the 2 unverified lines as net | **£764.73** | **£917.67** |
| if they turn out to be gross | £740.91 | £889.09 |

**The whole ambiguity is worth £23.82.** Not worth holding the order for — place it,
and correct the two lines when the invoices arrive. If the gym reclaims VAT, the net
column is the one that hits the P&L and there's roughly **£153** of recoverable VAT
in the gross figure.

Sanitary products are zero-rated in the UK, so tampons and pads would need their own
treatment — neither is being ordered, so it doesn't touch this total.

## 2. New stock just arrived — measure, don't reorder

The four printer inks, 1 each on hand. Count them every Tuesday and let them tell us
how long a set lasts. Key fobs likewise — counted, never ordered here.

## 3. Do not order — overstocked

| item | on hand | minimum | |
|---|---|---|---|
| Sanitary Pads | 484 pads | 44 | **11.0× minimum** — confirmed by you |
| Chill Tub Filters | 10 filters | 1.6 | **6.2× minimum** |
| Tampons | 256 tampons | 64 | **4.0× minimum** — confirmed by you |
| Water Softener Salt | 36 bags | 10 | **3.6× minimum** — confirmed by you |
| Greenspeed Techno Multi - Single 5L | 2.5 × 5L | 2 | **1.2× minimum** |
| Jumbo T.Roll 2ply 2.25" Core J26300 300m | 27 rolls | 24 | **1.1× minimum** |

## 4. Hold until Tuesday's count

**Pack size unknown (14 first-aid lines + 4 stationery):** Blue Gloves, Burn
Dressing 10x10cm, Clothing Cutters, Conforming Bandages, Eye Pad Bandages, Face
Shield, Finger Dressing, First Aid Dressing 12x12cm, First Aid Dressing 18x18cm,
Foil Blankets, Safety Pins, Sterile Wipes, Triangular Bandages, Washproof Plasters,
Waterproof Tape; Notepads, Paper - printer, Pens, Sea Kelp Luxury Shampoo 5L Refill.

**Usage figure known wrong — set it from the count:** Chalk Block, D Batteries,
Hair Bands.

**Count basis still unknown:** Glade airfreshner sparys.

**Ice packs** — requirement now set to **16**, 11 on hand, so short 5. The only pack
size on record is 24, from the old DB row, which would overshoot to 35. Confirm the
pack size before ordering.

## 5. Four worth a second look

**Odyssey shampoo — 10 × 5L bottles = 50 litres, £188.90.**
The unit is a 5L refill bottle, not a litre, so 10 packs is 10 bottles. Down from
15 in an earlier version: that 15 came from a burn rate of 11.42 bottles/month
measured over 8 days straight after a delivery, which counts refilling the wall
dispensers as consumption. Sized on the purchase floor instead (6.42/month), it's
10 bottles — about 1.5 months' cover. Still the biggest line here.

**Deodorants — 5 packs of 6 = 30 cans each, not 5 × 12.**
Sure 150ml sprays, 6-pack. But 30 cans against an estimated 6 a month is five
months of cover, driven by a `Par Qty` of 24. Either that par is high or the usage
estimate is low. Worth halving to 3 packs until a count settles it.

**Chill Tubs Sanitiser — 60 tubs, £45.**
The minimum of 23.7 rests on an unverified 3 packs/month, i.e. 2 tubs a day. If
that's right, 60 is fine. Also confirm a pack really is 20 tubs for £15 — that's
75p a tub, which looks low. This is also one of the two unverified VAT lines, so
the supplier is worth a call either way.

**Bin bags — 400 bags, £27.70.**
Minimum of 210 rests on an unverified par of ~13 bags a day. Cheap enough to be
low-risk, and a fortnight of counts will show it either way.

## What this list does not cover

Chalk block needs nothing — your 1 pack of 8 already meets the minimum of 8. The
first-aid lines, pens, notepads, paper and Sea Kelp shampoo are all held for want of
a pack size.

Everything ordered must go through the **Order Log**. Usage is
`opening + orders − closing`, so an unlogged delivery costs you the baseline.
