# Product Selection Guide

When searching returns multiple results, use agent judgment to select the best match.

## Selection Priority

| Priority | Criterion | Weight | Rationale |
|----------|-----------|--------|-----------|
| 1 | Exact product type | Critical | "Fancy Tuna" (chunks) ≠ "Tuna Slices" |
| 2 | Whole over processed | High | Better value, fresher |
| 3 | Local origin | Medium | Fresher, cheaper, supports local |
| 4 | Price per unit | Medium | 1kg bags often better value |
| 5 | In stock status | High | Skip unavailable items |

## Product Type Matching

### Good vs Bad Matches

| Search | Good Match | Bad Match |
|--------|------------|-----------|
| fancy tuna | Al Alali Fancy Meat Tuna | Al Alali Tuna Slices |
| rock melon | Melon Rock 1Kg | Fresh Rock Melon Cut bowl |
| greek yoghurt | Baladna Greek Yoghurt | Flavored Yoghurt |
| red onion | Onion Red 1Kg | Onion Spring |
| potato | Potato Regular 1Kg | Potato Baby/Chips |

### Indicators of Wrong Product

- **Cut/Sliced/Chopped/Diced** - Usually processed, more expensive per unit
- **Bowl/Tray/Pack** - Pre-packaged portions, markup
- **Flavored/Seasoned** - Not the base product
- **Baby/Mini** - Different variety

## Whole vs Processed

Prefer whole items over cut/processed versions:

| Processed Pattern | Prefer Instead |
|-------------------|----------------|
| "Fresh Rock Melon Cut bowl" | "Melon Rock 1Kg" |
| "Pineapple Sliced Tray" | "Pineapple Whole" |
| "Onion Diced Pack" | "Onion Red 1Kg" |
| "Mango Ready to Eat" | "Mango 1Kg" |

**Exception**: If user specifically requests cut/sliced, respect that.

## Local Origin Preference

Regional products are often fresher and cheaper:

| Origin | Priority |
|--------|----------|
| Qatar | Highest |
| Local | Highest |
| Jordan | High |
| Oman | High |
| Saudi | Medium |
| UAE | Medium |
| Kuwait | Medium |
| Bahrain | Medium |
| Imported | Lowest |

**Look for keywords**: "Qatar", "Local", "Jordan", "Oman" in product name.

## Price Efficiency

### Per-Unit Value

| Pattern | Value |
|---------|-------|
| "Per Kg" / "1Kg" | Usually best value |
| "500g" | Good value |
| "250g" or less | Often markup |
| Small packs/trays | Convenience premium |

### Price Flags

- **price_old not null**: Item is discounted
- **discount_percentage**: Check if significant (>10%)
- **has_buy_one_get_one**: BOGO offer available

## Stock Status

Always check before selecting:

```typescript
if (!product.is_instock || !product.is_available) {
  // Skip this product, find alternative
}

if (product.is_low_stock) {
  // May run out, consider backup option
}

if (product.stock_count < quantity_needed) {
  // Insufficient stock
}
```

## Search Term Tips

Be specific to get better results:

| Item | Better Search | Avoid |
|------|---------------|-------|
| Red onion | "onion red 1kg" | "onion" |
| Greek yoghurt | "baladna greek yoghurt" | "yoghurt" |
| Tuna chunks | "alali fancy tuna" | "tuna" |
| Regular potato | "potato regular 1kg" | "potato" |
| Rock melon | "melon rock 1kg" | "melon" |

### Include When Relevant

- **Brand**: "baladna", "alali", "monoprix"
- **Size**: "1kg", "500g", "170g"
- **Type**: "regular", "whole", "fresh"
- **Color/Variety**: "red", "green", "baby"

## Decision Checklist

Before selecting a product:

1. [ ] Name matches what user asked for?
2. [ ] Correct type (not sliced when whole wanted)?
3. [ ] In stock and available?
4. [ ] Reasonable price?
5. [ ] Local option available?

## When Multiple Good Options Exist

If several products match equally well:

1. Pick the one with better stock count
2. Pick the one with a discount
3. Pick the local option
4. Pick the larger quantity (better per-unit value)
5. If still tied, pick the first one
