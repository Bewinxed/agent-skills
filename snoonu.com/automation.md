# UI Automation Patterns

Complete code patterns for Snoonu browser automation using Playwriter MCP.

## Why UI Automation?

Direct API cart operations have issues:
- **CORS blocks** fetch from browser context
- **Session binding** - API calls may not affect user's actual cart
- **Cart sync replaces** - Must include ALL items, risk of data loss

UI automation **reliably works** with the user's actual session.

## Setup

Ensure browser is on Snoonu store page:

```javascript
// Check current page
console.log('url:', page.url());

// Navigate if needed
if (!page.url().includes('snoonu.com')) {
  await page.goto('https://snoonu.com/groceries/monoprix', { waitUntil: 'domcontentloaded' });
  await waitForPageLoad({ page, timeout: 10000 });
}
```

## Pattern 1: Search via API, Review, Then Add via UI

Best approach - fast search, reliable add.

### Step 1: Batch Search via API

```javascript
// Search multiple items at once
const searchTerms = ['red onion 1kg', 'potato regular', 'baladna yoghurt'];

const searchResults = await page.evaluate(async (terms) => {
  const results = {};
  for (const term of terms) {
    try {
      const res = await fetch('https://admin.snoonu.com/api/search/suggest_in_merchant_with_subcategory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ term, language: 'en', menu_id: 504231 })
      });
      const data = await res.json();
      results[term] = data.data?.product_view_models?.slice(0, 5).map(p => ({
        id: p.product_id,
        name: p.name,
        price: p.price,
        inStock: p.is_instock
      })) || [];
    } catch (e) {
      results[term] = [];
    }
  }
  return results;
}, searchTerms);

console.log(JSON.stringify(searchResults, null, 2));
```

### Step 2: Agent Reviews and Selects

After seeing results, pick exact product names to add.

### Step 3: Add Items via UI

```javascript
async function addItem(searchTerm, exactProductName) {
  // Search in store UI
  const searchInput = page.locator('input[placeholder*="Search"]');
  await searchInput.fill(searchTerm);
  await searchInput.press('Enter');
  await page.waitForTimeout(2000);

  // Click exact product
  const productCard = page.locator(`text="${exactProductName}"`).first();
  await productCard.click();
  await page.waitForTimeout(1000);

  // Add via JS click (avoids timeout)
  const clicked = await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button'))
      .find(b => b.textContent?.trim() === 'Add');
    if (btn) { btn.click(); return true; }
    return false;
  });

  if (clicked) {
    await page.waitForTimeout(500);
    console.log(`Added: ${exactProductName}`);
  } else {
    console.log(`Failed: ${exactProductName} - no Add button`);
  }

  // Go back to search
  await page.goBack();
  await page.waitForTimeout(500);
}
```

## Pattern 2: Full Shopping List Automation

```javascript
// Shopping list with specific search terms
const shoppingList = [
  { search: 'onion red 1kg', select: 'Onion Red 1Kg' },
  { search: 'potato regular 1kg', select: 'Potato Regular 1Kg' },
  { search: 'tomato bunch', select: 'Tomato Bunch' },
  { search: 'alali fancy tuna', select: 'Al Alali Fancy Meat Tuna In S/Oil 170g' },
  { search: 'baladna greek yoghurt', select: 'Baladna Greek Yoghurt 400g' },
  { search: 'melon rock 1kg', select: 'Melon Rock 1Kg' },
];

const results = [];

for (const item of shoppingList) {
  try {
    // Search
    const searchInput = page.locator('input[placeholder*="Search"]');
    await searchInput.fill(item.search);
    await searchInput.press('Enter');
    await page.waitForTimeout(2000);

    // Click product
    const found = await page.locator(`text="${item.select}"`).first().isVisible()
      .catch(() => false);

    if (!found) {
      results.push({ item: item.search, status: 'not found' });
      continue;
    }

    await page.locator(`text="${item.select}"`).first().click();
    await page.waitForTimeout(1000);

    // Add to cart
    const clicked = await page.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button'))
        .find(b => b.textContent?.trim() === 'Add');
      if (btn) { btn.click(); return true; }
      return false;
    });

    results.push({
      item: item.search,
      status: clicked ? 'added' : 'no Add button'
    });

    await page.waitForTimeout(500);
    await page.goBack();
    await page.waitForTimeout(500);

  } catch (e) {
    results.push({ item: item.search, status: `error: ${e.message}` });
  }
}

console.log('Results:', JSON.stringify(results, null, 2));
```

## Pattern 3: Increment Existing Item

If item already in cart, increment quantity:

```javascript
// After clicking product, check for +/- buttons
const hasQuantityControl = await page.evaluate(() => {
  return document.querySelector('button[aria-label*="increase"]') !== null ||
         Array.from(document.querySelectorAll('button')).some(b => b.textContent === '+');
});

if (hasQuantityControl) {
  // Item already in cart, increment
  await page.evaluate(() => {
    const plusBtn = document.querySelector('button[aria-label*="increase"]') ||
                    Array.from(document.querySelectorAll('button')).find(b => b.textContent === '+');
    if (plusBtn) plusBtn.click();
  });
} else {
  // New item, click Add
  await page.evaluate(() => {
    const addBtn = Array.from(document.querySelectorAll('button'))
      .find(b => b.textContent?.trim() === 'Add');
    if (addBtn) addBtn.click();
  });
}
```

## Pattern 4: Handle Out of Stock

```javascript
// Check if item is available before clicking
const isAvailable = await page.evaluate(() => {
  const outOfStock = document.querySelector('[class*="out-of-stock"]') ||
                     document.body.innerText.includes('Out of Stock') ||
                     document.body.innerText.includes('Unavailable');
  return !outOfStock;
});

if (!isAvailable) {
  console.log('Item out of stock, skipping');
  return;
}
```

## Troubleshooting

### Playwright Click Timeout

Use JS click instead:

```javascript
// Bad - may timeout
await page.locator('button:has-text("Add")').click();

// Good - direct JS click
await page.evaluate(() => {
  document.querySelector('button:has-text("Add")')?.click();
});
```

### Element Not Found

Use accessibility snapshot to find elements:

```javascript
const snapshot = await accessibilitySnapshot({ page, search: /add|cart/i });
console.log(snapshot);
```

### Page Not Loading

Reset and retry:

```javascript
await page.reload();
await waitForPageLoad({ page, timeout: 10000 });
```

### Cart Not Updating

UI automation should work. If cart shows wrong value:
1. Refresh the page
2. Check cart icon directly
3. Navigate to cart page to verify

## Performance Tips

1. **Batch searches** - Search multiple items in one API call
2. **Skip product pages** - If you can add from search results, do that
3. **Parallel where possible** - Multiple tabs for different stores
4. **Cache search results** - Store in `state` for re-use

```javascript
// Store results for session
state.searchCache = state.searchCache || {};
if (!state.searchCache[term]) {
  state.searchCache[term] = await searchAPI(term);
}
```
