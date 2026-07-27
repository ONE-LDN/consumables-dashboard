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
 *   Stock Count — weekly on-hand counts, in PACKS. "Submit stock count" writes
 *                 them to shop_stock_takes.
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
  key:      'product_name_raw',
  name:     'display_name',
  location: 'location',
  supplier: 'supplier',
  link:     'order_link_or_desc',
  price:    'price_per_pack_gbp',
  units:    'units_per_pack',
  par:      'packs_per_month_par',
};

// Stock Count / Order Log layout
var COUNT_DATE_CELL = 'B1';   // take date
var COUNT_HEADER_ROW = 3;
var COUNT_FIRST_ROW  = 4;
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

function _sbGet(table, query) {
  return _fetch('/rest/v1/' + table + '?' + query, { method: 'get' }) || [];
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
  var iKey = idx(COL.key), iName = idx(COL.name), iLoc = idx(COL.location),
      iSup = idx(COL.supplier), iLink = idx(COL.link), iPrice = idx(COL.price),
      iUnits = idx(COL.units), iPar = idx(COL.par);

  var rows = [], seen = {};
  for (var r = 1; r < values.length; r++) {
    var row = values[r];
    var key = String(row[iKey] || '').trim();
    if (!key) continue;
    seen[key] = true;
    rows.push({
      product_name_raw:  key,
      display_name:      String(row[iName] || key).trim(),
      brand:             '',
      category:          CATEGORY,
      subcategory:       String(row[iLoc] || '').trim() || null,
      supplier:          String(row[iSup] || '').trim() || null,
      order_url:         String(row[iLink] || '').trim() || null,
      cost_price:        _num(row[iPrice]),
      pack_size:         _int(row[iUnits]),
      monthly_par_packs: _num(row[iPar]),
      active:            true,
      stock_tracked:     false,
    });
  }
  if (!rows.length) throw new Error('No product rows with a product_name_raw.');

  // Reconcile: deactivate any consumable in the DB that is no longer in the
  // sheet (soft delete), scoped strictly to category=Consumables so shop/merch
  // products are never touched. Then upsert the current set as active.
  _sbSend('PATCH', 'shop_product_lookup', 'category=eq.' + CATEGORY, { active: false }, 'return=minimal');
  _sbSend('POST', 'shop_product_lookup', 'on_conflict=product_name_raw',
          rows, 'resolution=merge-duplicates,return=minimal');

  SpreadsheetApp.getUi().alert('Synced ' + rows.length + ' consumable products to the dashboard.');
}

// ── ② Build / rebuild the Stock Count sheet from the live product set ────────
function buildCountSheet() {
  var products = _sbGet('shop_product_lookup',
    'select=product_name_raw,display_name,subcategory&category=eq.' + CATEGORY +
    '&active=eq.true&order=subcategory,display_name');

  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(COUNT_SHEET) || ss.insertSheet(COUNT_SHEET);
  sh.clear();

  sh.getRange('A1').setValue('Take date:');
  sh.getRange(COUNT_DATE_CELL).setValue(new Date());
  sh.getRange(COUNT_DATE_CELL).setNumberFormat('yyyy-mm-dd');

  var headers = ['product_name_raw', 'Product', 'Location', 'Count (packs)', 'Notes'];
  sh.getRange(COUNT_HEADER_ROW, 1, 1, headers.length).setValues([headers]).setFontWeight('bold');

  var out = products.map(function (p) {
    return [p.product_name_raw, p.display_name || p.product_name_raw, p.subcategory || '', '', ''];
  });
  if (out.length) sh.getRange(COUNT_FIRST_ROW, 1, out.length, headers.length).setValues(out);

  sh.hideColumns(1);
  sh.setFrozenRows(COUNT_HEADER_ROW);
  SpreadsheetApp.getUi().alert('Stock Count sheet rebuilt with ' + out.length + ' products.');
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

  var payload = [];
  data.forEach(function (row) {
    var key = String(row[0] || '').trim();
    var count = row[3];
    if (key && count !== '' && count !== null && !isNaN(count)) {
      payload.push({
        product_name_raw: key,
        take_date:        takeDate,
        actual_count:     Number(count),
        notes:            String(row[4] || '').trim() || null,
        source:           'sheet',
      });
    }
  });
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
  var products = _sbGet('shop_product_lookup',
    'select=display_name&category=eq.' + CATEGORY + '&active=eq.true&order=display_name');
  var names = products.map(function (p) { return p.display_name; });

  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(ORDER_SHEET) || ss.insertSheet(ORDER_SHEET);
  sh.clear();

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

  // Resolve display_name → product_name_raw / subcategory / pack_size / cost.
  var lookup = _sbGet('shop_product_lookup',
    'select=product_name_raw,display_name,subcategory,pack_size,cost_price,supplier&category=eq.' +
    CATEGORY + '&active=eq.true');
  var byName = {};
  lookup.forEach(function (p) { byName[String(p.display_name).trim().toLowerCase()] = p; });

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
    var unitCost = (row[3] === '' || row[3] === null || isNaN(row[3])) ? p.cost_price : Number(row[3]);
    payload.push({
      delivery_date:    date,
      product_name_raw: p.product_name_raw,
      subcategory:      p.subcategory || null,
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
