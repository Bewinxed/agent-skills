---
name: snoonu
description: Add grocery items to cart via Snoonu delivery platform in Qatar.
  Use when user wants to order groceries from Monoprix, Lulu, or other Snoonu stores.
  Searches products, selects best matches, and adds to cart via browser automation.
allowed-tools: Read, Bash, mcp__playwriter__execute, mcp__playwriter__reset
---

# Snoonu Grocery Shopping

Add items to cart from Snoonu (Qatar's delivery platform) using browser automation.

## Quick Start

1. **Open Snoonu store** in browser (e.g., `https://snoonu.com/groceries/monoprix`)
2. **Search via API** to get product candidates with IDs/names/prices
3. **Agent reviews results** - pick exact match, not first result
4. **Add via UI click** - navigate to product, click Add button

## Store IDs

| Store | menu_id |
|-------|---------|
| Monoprix | 504231 |
| Lulu Hypermarket | 509307 |

## Workflow

### Step 1: Search for Products

Use the search API to get candidates:

```javascript
// In Playwriter - search via page context
const results = await page.evaluate(async (term) => {
  const res = await fetch('https://admin.snoonu.com/api/search/suggest_in_merchant_with_subcategory', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ term, language: 'en', menu_id: 504231 })
  });
  const data = await res.json();
  return data.data?.product_view_models?.slice(0, 5).map(p => ({
    id: p.product_id,
    name: p.name,
    price: p.price,
    inStock: p.is_instock
  }));
}, 'red onion');
```

### Step 2: Select Best Product

Review results and pick the **exact match**:

| Priority | Criterion | Example |
|----------|-----------|---------|
| 1 | Exact type match | "Fancy Meat Tuna" vs "Tuna Slices" |
| 2 | Whole over processed | "Melon Rock 1Kg" vs "Cut bowl" |
| 3 | Local origin | Qatar/Jordan/Oman items |
| 4 | Price per unit | 1kg bags > small packs |

**See [selection-guide.md](selection-guide.md) for detailed criteria.**

### Step 3: Add to Cart

Navigate and click Add button via JS (avoids timeouts):

```javascript
// Search in store UI
await page.locator('input[placeholder*="Search"]').fill('melon rock 1kg');
await page.locator('input[placeholder*="Search"]').press('Enter');
await page.waitForTimeout(2000);

// Click exact product
await page.locator('text="Melon Rock 1Kg"').first().click();
await page.waitForTimeout(1000);

// Add via JS click
await page.evaluate(() => {
  const btn = Array.from(document.querySelectorAll('button'))
    .find(b => b.textContent?.trim() === 'Add');
  if (btn) btn.click();
});
```

## Key Principles

- **Agent selects items** - Don't use algorithms, review results yourself
- **Be specific** - Search "baladna greek yoghurt" not "yoghurt"
- **UI automation works** - API cart sync has session issues
- **JS clicks** - Use `page.evaluate()` to avoid Playwright timeouts

## Reference Files

- [api-reference.md](api-reference.md) - Full API endpoints and headers
- [selection-guide.md](selection-guide.md) - Product selection criteria
- [automation.md](automation.md) - Complete UI automation patterns

## Common Items

| Item | Search Term |
|------|-------------|
| Red onion | "onion red 1kg" |
| Potatoes | "potato regular 1kg" |
| Tuna (chunks) | "alali fancy tuna" |
| Greek yoghurt | "baladna greek yoghurt" |
| Rock melon | "melon rock 1kg" |
