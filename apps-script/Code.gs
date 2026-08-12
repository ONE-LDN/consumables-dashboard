/**
 * ONE LDN — Consumables Stock Take & Ordering connector (Google Apps Script)
 * ---------------------------------------------------------------------------
 * Bound to the master Consumables catalogue workbook. The workbook is the
 * single source of truth for the product list; the dashboard reads from
 * Supabase, which this script keeps in sync.
 *
 * TABS
 *   Products    — the master catalogue you maintain by hand (one row per item).
 *                 "Sync products to dashboard" pushes it into Supabase.
 *   Stock Count — weekly on-hand counts, in ITEMS (the Unit column says what an
 *                 item is for each product). "Submit stock count" writes them
 *                 to shop_stock_takes. Decimals are valid: half a 5L bottle is
 *                 0.5. Blank means "not counted"; 0 means "counted, none left".
 *   Order Log   — orders placed. "Submit order log" writes them to
 *                 shop_consumable_deliveries, then clears the entered rows.
 *
 * SETUP (one-time) — Extensions ▸ Apps Script ▸ Project Settings ▸ Script
 * properties, add:
 *   SUPABASE_URL          = https://ljjwssicvvyyueyznmou.supabase.co
 *   SUPABASE_SERVICE_KEY  = <service_role key>   (NEVER the anon key; never commit)
 * Then run "Sync products to dashboard" once to authorise.
 *
 * The service-role key stays server-side inside Apps Script and is never
 * exposed to the browser/dashboard.
 */

// ── Config ──────────────────────────────────────────────────────────────────
var PRODUCTS_SHEET = 'Products';
var COUNT_SHEET    = 'Stock Count';
var ORDER_SHEET    = 'Order Log';
var CATEGORY       = 'Consumables';

// Products-tab column headers (matched case-insensitively by name, so column
// order can change without breaking the sync).
var COL = {
  key:      'product_name_raw',   // the sync key — never edited by hand
  name:     'Product name',
  type:     'Category',           // what kind of thing it is
  location: 'Location',           // where you count it
  unit:     'Count unit',         // what a count of 1 means
  supplier: 'Supplier',
  link:     'Product description',
  units:    'Pack size',          // items per order unit
  price:    'Price per pack',     // NET of VAT
  min:      'Minimum',            // items — a formula on the tab
  minok:    'Min confirmed',      // yes | no
  klass:    'Order class',        // reorder | measure_only
};

// Stock Count / Order Log layout
// Stock Count columns are Product name | Category | Location | Count | Unit.
// Count is column 4 and there is no Notes column; see buildCountSheet().
var COUNT_DATE_CELL = 'B1';   // take date
var COUNT_HEADER_ROW = 3;
var COUNT_FIRST_ROW  = 4;

// The order you walk the building when counting. Rows are grouped by Location
// in this sequence, not alphabetically.
var COUNT_WALK_ORDER = [
  'FOH Desk', 'Cafe', 'Gym Floor', 'Toiletries', 'Staff Room', 'Plant room',
];
var ORDER_HEADER_ROW = 1;
var ORDER_FIRST_ROW  = 2;

// ── Menu ──────────────────────────────────────────────────────────────────
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Consumables')
    .addItem('① Sync products to dashboard', 'syncProducts')
    .addSeparator()
    .addItem('② Rebuild Stock Count sheet', 'buildCountSheet')
    .addItem('③ Submit stock count', 'submitCounts')
    .addItem('Clear count column', 'clearCounts')
    .addSeparator()
    .addItem('④ Rebuild Order Log sheet', 'buildOrderSheet')
    .addItem('⑤ Submit order log', 'submitOrders')
    .addToUi();
}

// ── Supabase helpers ────────────────────────────────────────────────────────
function _props() {
  var p = PropertiesService.getScriptProperties();
  var url = p.getProperty('SUPABASE_URL');
  var key = p.getProperty('SUPABASE_SERVICE_KEY');
  if (!url || !key) throw new Error('Missing SUPABASE_URL / SUPABASE_SERVICE_KEY in Script properties.');
  return { url: url.replace(/\/$/, ''), key: key };
}

function _fetch(path, options) {
  var cfg = _props();
  var opts = options || {};
  opts.muteHttpExceptions = true;
  opts.headers = Object.assign({
    apikey: cfg.key,
    Authorization: 'Bearer ' + cfg.key,
  }, opts.headers || {});
  var res = UrlFetchApp.fetch(cfg.url + path, opts);
  if (res.getResponseCode() >= 300) {
    throw new Error('Supabase ' + res.getResponseCode() + ': ' + res.getContentText());
  }
  var body = res.getContentText();
  return body ? JSON.parse(body) : null;
}

function _sbSend(method, table, query, payload, prefer) {
  return _fetch('/rest/v1/' + table + (query ? '?' + query : ''), {
    method: method,
    contentType: 'application/json',
    headers: prefer ? { Prefer: prefer } : {},
    payload: JSON.stringify(payload),
  });
}

// ── ① Sync products (Sheet → Supabase, master = Sheet) ───────────────────────
function syncProducts() {
  var sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(PRODUCTS_SHEET);
  if (!sh) throw new Error('No "' + PRODUCTS_SHEET + '" tab found.');

  var values = sh.getDataRange().getValues();
  if (values.length < 2) throw new Error('Products tab is empty.');

  // Map headers → column indexes (case-insensitive, trimmed).
  var header = values[0].map(function (h) { return String(h).trim().toLowerCase(); });
  function idx(name) {
    var i = header.indexOf(name.toLowerCase());
    if (i < 0) throw new Error('Products tab is missing the "' + name + '" column.');
    return i;
  }
  var iKey = idx(COL.key), iName = idx(COL.name), iType = idx(COL.type),
      iLoc = idx(COL.location), iUnit = idx(COL.unit), iSup = idx(COL.supplier),
      iLink = idx(COL.link), iPrice = idx(COL.price), iUnits = idx(COL.units),
      iMin = idx(COL.min), iMinOk = idx(COL.minok), iKlass = idx(COL.klass);

  var rows = [], seen = {}, dupes = [];
  for (var r = 1; r < values.length; r++) {
    var row = values[r];
    var key = String(row[iKey] || '').trim();
    if (!key) continue;
    if (seen[key]) { dupes.push(key); continue; }
    seen[key] = true;
    rows.push({
      product_name_raw:  key,
      display_name:      String(row[iName] || key).trim(),
      brand:             '',
      category:          CATEGORY,
      product_type:      String(row[iType] || '').trim() || null,
      subcategory:       String(row[iLoc] || '').trim() || null,
      count_unit:        String(row[iUnit] || '').trim() || null,
      supplier:          String(row[iSup] || '').trim() || null,
      order_url:         String(row[iLink] || '').trim() || null,
      cost_price:        _num(row[iPrice]),
      pack_size:         _int(row[iUnits]),
      // Items, not packs. Blank stays null: "no minimum set" and "a minimum of
      // zero" are different claims and the dashboard treats them differently.
      min_stock_units:   _int(row[iMin]),
      min_confirmed:     String(row[iMinOk] || '').trim().toLowerCase() === 'yes',
      order_class:       String(row[iKlass] || '').trim() || null,
      active:            true,
      stock_tracked:     false,
    });
  }
  if (dupes.length) throw new Error('Duplicate product_name_raw on the Products tab: ' + dupes.join(', '));
  if (!rows.length) throw new Error('No product rows with a product_name_raw.');

  // display_name is the join key for the count and order sheets, so a
  // collision there breaks both. Catch it here rather than at submit time.
  var byName = {}, nameDupes = [];
  rows.forEach(function (p) {
    var n = p.display_name.toLowerCase();
    if (byName[n]) nameDupes.push(p.display_name);
    byName[n] = true;
  });
  if (nameDupes.length) throw new Error('Duplicate Product name on the Products tab: ' + nameDupes.join(', '));

  // Reconcile: deactivate any consumable in the DB that is no longer in the
  // sheet (soft delete), scoped strictly to category=Consumables so shop/merch
  // products are never touched. Then upsert the current set as active.
  _sbSend('PATCH', 'shop_product_lookup', 'category=eq.' + CATEGORY, { active: false }, 'return=minimal');
  _sbSend('POST', 'shop_product_lookup', 'on_conflict=product_name_raw',
          rows, 'resolution=merge-duplicates,return=minimal');

  SpreadsheetApp.getUi().alert('Synced ' + rows.length + ' consumable products to the dashboard.');
}

// ── ② Build / rebuild the Stock Count sheet from the live product set ────────
//
// Layout: Product name | Category | Location | Count | Unit.
//
// There is deliberately NO product_name_raw column — the slug lives on the
// Products tab, not on the sheet people count into. submitCounts() joins on
// display_name instead, which is why display_name must stay unique and must be
// renamed in the catalogue rather than here.
//
// Category (what kind of thing) and Location (where you count it) are separate
// axes. `subcategory` holds the location; `product_type` holds the category.
function buildCountSheet() {
  // Built from the Products tab, not from Supabase. The workbook is the master,
  // so the count sheet should not need a round trip through the database to
  // rebuild — and this works before Supabase is set up at all.
  var products = _readProducts();

  // Count a room at a time. A list that jumps between rooms gets counted wrong,
  // so the walk beats alphabetical order. Unknown locations sort to the end
  // rather than vanishing.
  products.sort(function (a, b) {
    var ia = COUNT_WALK_ORDER.indexOf(a.location);
    var ib = COUNT_WALK_ORDER.indexOf(b.location);
    if (ia < 0) ia = COUNT_WALK_ORDER.length;
    if (ib < 0) ib = COUNT_WALK_ORDER.length;
    if (ia !== ib) return ia - ib;
    return a.name.localeCompare(b.name);
  });

  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(COUNT_SHEET) || ss.insertSheet(COUNT_SHEET);
  sh.clear();

  sh.getRange('A1').setValue('Take date:');
  sh.getRange(COUNT_DATE_CELL).setValue(new Date());
  sh.getRange(COUNT_DATE_CELL).setNumberFormat('yyyy-mm-dd');
  sh.getRange('A2').setValue('Counted by:');

  var headers = ['Product name', 'Category', 'Location', 'Count', 'Unit'];
  sh.getRange(COUNT_HEADER_ROW, 1, 1, headers.length).setValues([headers]).setFontWeight('bold');

  // Category, Location and Unit look themselves up from Products, per row, so
  // editing the catalogue flows through without rebuilding. Keyed on the name
  // in the same row on purpose: a whole-range formula would re-sort the names
  // without moving the counts beside them.
  var out = products.map(function (p, i) {
    var r = COUNT_FIRST_ROW + i;
    function look(col) {
      return '=IFERROR(VLOOKUP($A' + r + ',' + PRODUCTS_SHEET + '!$B:$E,' + col + ',FALSE),"")';
    }
    return [p.name, look(2), look(3), '', look(4)];
  });
  if (out.length) sh.getRange(COUNT_FIRST_ROW, 1, out.length, headers.length).setValues(out);

  // Count is the only column anyone types in; the rest is reference.
  sh.getRange(COUNT_HEADER_ROW, 1, out.length + 1, 3).setBackground('#f3f3f3');
  sh.getRange(COUNT_HEADER_ROW, 5, out.length + 1, 1).setBackground('#f3f3f3');
  sh.setFrozenRows(COUNT_HEADER_ROW);
  sh.autoResizeColumns(1, headers.length);
  SpreadsheetApp.getUi().alert('Stock Count sheet rebuilt with ' + out.length + ' products.');
}

// Read the Products tab into plain objects. One reader for every function that
// needs the catalogue, so the header names are resolved in exactly one place.
function _readProducts() {
  var sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(PRODUCTS_SHEET);
  if (!sh) throw new Error('No "' + PRODUCTS_SHEET + '" tab found.');
  var values = sh.getDataRange().getValues();
  if (values.length < 2) throw new Error('Products tab is empty.');

  var header = values[0].map(function (h) { return String(h).trim().toLowerCase(); });
  function idx(name) {
    var i = header.indexOf(name.toLowerCase());
    if (i < 0) throw new Error('Products tab is missing the "' + name + '" column.');
    return i;
  }
  var iKey = idx(COL.key), iName = idx(COL.name), iType = idx(COL.type),
      iLoc = idx(COL.location), iUnit = idx(COL.unit), iSup = idx(COL.supplier),
      iPrice = idx(COL.price), iUnits = idx(COL.units), iKlass = idx(COL.klass);

  var out = [];
  for (var r = 1; r < values.length; r++) {
    var row = values[r];
    var key = String(row[iKey] || '').trim();
    if (!key) continue;
    out.push({
      key:        key,
      name:       String(row[iName] || key).trim(),
      type:       String(row[iType] || '').trim(),
      location:   String(row[iLoc] || '').trim(),
      unit:       String(row[iUnit] || '').trim(),
      supplier:   String(row[iSup] || '').trim(),
      price:      _num(row[iPrice]),
      pack_size:  _int(row[iUnits]),
      order_class: String(row[iKlass] || '').trim(),
    });
  }
  return out;
}

// ── ③ Submit stock counts → shop_stock_takes (upsert by product + date) ──────
function submitCounts() {
  var sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(COUNT_SHEET);
  if (!sh) throw new Error('No "' + COUNT_SHEET + '" sheet — run "Rebuild Stock Count sheet" first.');

  var dateVal = sh.getRange(COUNT_DATE_CELL).getValue();
  if (!(dateVal instanceof Date)) throw new Error('Set a valid Take date in ' + COUNT_DATE_CELL + '.');
  var takeDate = Utilities.formatDate(dateVal, Session.getScriptTimeZone(), 'yyyy-MM-dd');

  var last = sh.getLastRow();
  if (last < COUNT_FIRST_ROW) throw new Error('No product rows.');
  var data = sh.getRange(COUNT_FIRST_ROW, 1, last - COUNT_FIRST_ROW + 1, 5).getValues();

  // The count sheet carries no slug column, so the product name is the join
  // key. Resolved against the Products tab — the workbook's own catalogue —
  // rather than against Supabase, so the two can never disagree.
  var keyByName = {};
  _readProducts().forEach(function (p) {
    keyByName[p.name.toLowerCase()] = p.key;
  });

  var payload = [];
  var unmatched = [];
  data.forEach(function (row) {
    var name = String(row[0] || '').trim();
    var count = row[3];
    if (!name || count === '' || count === null || isNaN(count)) return;
    var key = keyByName[name.toLowerCase()];
    if (!key) { unmatched.push(name); return; }
    payload.push({
      product_name_raw: key,
      take_date:        takeDate,
      actual_count:     Number(count),
      source:           'sheet',
    });
  });

  // Refuse the whole submission rather than silently dropping the rows that did
  // not match. A partial count reads as a real count and corrupts the usage
  // arithmetic for every product that went missing.
  if (unmatched.length) {
    throw new Error(
      'These product names are not in the catalogue, so nothing was submitted:\n  ' +
      unmatched.join('\n  ') +
      '\n\nRename products on the Products tab and rebuild the Stock Count sheet — ' +
      'not here.');
  }
  if (!payload.length) { SpreadsheetApp.getUi().alert('No counts entered.'); return; }

  _sbSend('POST', 'shop_stock_takes', 'on_conflict=product_name_raw,take_date',
          payload, 'resolution=merge-duplicates,return=minimal');
  SpreadsheetApp.getUi().alert('Submitted ' + payload.length + ' counts for ' + takeDate + '.');
}

function clearCounts() {
  var sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(COUNT_SHEET);
  if (!sh) return;
  var last = sh.getLastRow();
  if (last >= COUNT_FIRST_ROW) sh.getRange(COUNT_FIRST_ROW, 4, last - COUNT_FIRST_ROW + 1, 1).clearContent();
}

// ── ④ Build / rebuild the Order Log entry sheet ──────────────────────────────
function buildOrderSheet() {
  // From the Products tab, so the dropdown matches the catalogue exactly and
  // no order can name a product that submitOrders will then reject.
  var names = _readProducts().map(function (p) { return p.name; }).sort();

  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(ORDER_SHEET) || ss.insertSheet(ORDER_SHEET);
  // Only the header and the dropdown are rewritten — no sh.clear(). Rebuilding
  // the dropdown after a catalogue edit must not discard rows that have been
  // entered but not yet submitted; usage is opening + orders_between − closing,
  // so a delivery lost before it reaches Supabase makes the arithmetic lie.
  var headers = ['Date', 'Product', 'Packs ordered', 'Unit cost £ (optional)', 'Supplier (optional)', 'Notes'];
  sh.getRange(ORDER_HEADER_ROW, 1, 1, headers.length).setValues([headers]).setFontWeight('bold');
  sh.setFrozenRows(ORDER_HEADER_ROW);

  // Product dropdown on the entry column for the next 200 rows.
  var rule = SpreadsheetApp.newDataValidation().requireValueInList(names, true).build();
  sh.getRange(ORDER_FIRST_ROW, 2, 200, 1).setDataValidation(rule);
  sh.getRange(ORDER_FIRST_ROW, 1, 200, 1).setNumberFormat('yyyy-mm-dd');
  SpreadsheetApp.getUi().alert('Order Log sheet ready. Enter one order per row, then run "Submit order log".');
}

// ── ⑤ Submit order log → shop_consumable_deliveries, then clear entered rows ──
function submitOrders() {
  var sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(ORDER_SHEET);
  if (!sh) throw new Error('No "' + ORDER_SHEET + '" sheet — run "Rebuild Order Log sheet" first.');

  var last = sh.getLastRow();
  if (last < ORDER_FIRST_ROW) { SpreadsheetApp.getUi().alert('No orders entered.'); return; }

  // Resolve product name → key / location / pack size / cost, from the
  // Products tab rather than Supabase, for the same reason as submitCounts.
  var byName = {};
  _readProducts().forEach(function (p) { byName[p.name.toLowerCase()] = p; });

  var data = sh.getRange(ORDER_FIRST_ROW, 1, last - ORDER_FIRST_ROW + 1, 6).getValues();
  var payload = [], errors = [];
  data.forEach(function (row, i) {
    var dateVal = row[0], name = String(row[1] || '').trim(), packs = row[2];
    if (!name && (packs === '' || packs === null)) return; // blank row
    var p = byName[name.toLowerCase()];
    if (!p) { errors.push('Row ' + (ORDER_FIRST_ROW + i) + ': unknown product "' + name + '"'); return; }
    if (packs === '' || packs === null || isNaN(packs)) {
      errors.push('Row ' + (ORDER_FIRST_ROW + i) + ': missing packs'); return;
    }
    var date = (dateVal instanceof Date)
      ? Utilities.formatDate(dateVal, Session.getScriptTimeZone(), 'yyyy-MM-dd')
      : Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd');
    var unitCost = (row[3] === '' || row[3] === null || isNaN(row[3])) ? p.price : Number(row[3]);
    payload.push({
      delivery_date:    date,
      product_name_raw: p.key,
      subcategory:      p.location || null,
      qty_cases:        Number(packs),
      pack_size:        p.pack_size || null,
      unit_cost:        unitCost != null ? Number(unitCost) : null,
      total:            unitCost != null ? Number(unitCost) * Number(packs) : null,
      supplier:         String(row[4] || '').trim() || p.supplier || null,
      notes:            String(row[5] || '').trim() || null,
    });
  });

  if (errors.length) throw new Error('Fix these first:\n' + errors.join('\n'));
  if (!payload.length) { SpreadsheetApp.getUi().alert('No orders entered.'); return; }

  _sbSend('POST', 'shop_consumable_deliveries', '', payload, 'return=minimal');
  sh.getRange(ORDER_FIRST_ROW, 1, last - ORDER_FIRST_ROW + 1, 6).clearContent();
  SpreadsheetApp.getUi().alert('Logged ' + payload.length + ' orders.');
}

// ── Small helpers ────────────────────────────────────────────────────────────
function _num(v) { return (v === '' || v === null || isNaN(v)) ? null : Number(v); }
function _int(v) { var n = _num(v); return n === null ? null : Math.round(n); }
