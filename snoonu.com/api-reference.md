# Snoonu API Reference

## Base URLs

- **Admin API**: `https://admin.snoonu.com/api`
- **Market API**: `https://snoomarket-web.snoonu.com/api`

## Required Headers

```typescript
{
  "Content-Type": "application/json, application/json-patch+json",
  "token": string,                    // Auth token from session
  "snoonu-app-device-id": string,     // e.g., "web-ab8fd3325771b2fcbc36dfef2a05dba6"
  "snoonu-app-platform": "Web",
  "snoonu-app-version": "65535.65535.65535.65535",
  "latitude": string,                 // e.g., "25.30015325558983"
  "longitude": string,                // e.g., "51.49286493659019"
  "language": "en" | "ar",
  "appversion": "2",
  "referer": "https://snoonu.com/",
  "user-agent": string
}
```

## Endpoints

### Search Within Store

**POST** `/api/search/suggest_in_merchant_with_subcategory`

```typescript
// Request
{
  "term": "onion",
  "language": "en",
  "menu_id": 504231  // Store ID
}

// Response
{
  "status": "SUCCESS",
  "data": {
    "product_view_models": ProductViewModel[]
  }
}
```

### Global Search

**GET** `/api/v5/search/global?page=0&page_size=20&product_size=11&term=red%20onion`

### Cart Sync (REPLACES entire cart)

**POST** `https://snoomarket-web.snoonu.com/api/v1/multicart/sync`

**Warning**: This endpoint REPLACES the entire cart, not adds to it!

```typescript
// Request
{
  "items": [{
    "product_identity": {
      "product_id": "659e991a2330c87dbc3acb71",
      "choice_item_ids": [],
      "special_request": ""
    },
    "quantity": 1,
    "is_buy_later": false
  }]
}

// Response
{
  "status": "SUCCESS",
  "data": {
    "total_quantity": 19,
    "full_cart_price": 150.25,
    "items": [...],
    "cart_id": "uuid-string"
  }
}
```

### Other Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v5/orders/open` | GET | Open/active orders |
| `/api/v3/customer_data` | GET | Customer data |
| `/api/v6/address` | GET | Saved addresses |
| `/api/v3/banner` | GET | Promotional banners |
| `/api/v5/popular_terms` | GET | Popular search terms |
| `/api/v5/suggestions/search_with_highlight` | GET | Search suggestions |

## ProductViewModel Type

```typescript
interface ProductViewModel {
  id: number;                    // Internal numeric ID
  product_id: string;            // MongoDB ObjectId (for cart)
  object_id: string;             // Combined ID
  name: string;                  // Product name
  english_name: string;
  description: string;
  price: string;                 // Current price
  price_old: string | null;      // Original price (if discounted)
  min_price: number;
  base_price: number;
  discount_percentage: number | null;
  is_instock: boolean;
  is_available: boolean;
  stock_count: number;
  is_low_stock: boolean;
  product_order_limit: number;   // 0 = no limit
  image_url: string;
  images: string[];
  has_buy_one_get_one: boolean;
  merchant_id: number;
  merchant_name: string;
  merchant_status: "open" | "closed" | "busy";
  business_unit_id: string;
  is_food_merchant: boolean;
  brand_id: number;
  branch_id: string | null;
}
```

## Known Store IDs

| Store | menu_id |
|-------|---------|
| Monoprix | 504231 |
| Lulu Hypermarket | 509307 |

## CORS Notes

The Market API (`snoomarket-web.snoonu.com`) has CORS restrictions:
- Fetch from browser `page.evaluate()` will fail
- Node.js `https` module bypasses CORS but has session issues
- **Recommended**: Use UI automation instead of direct API calls

## API vs UI Trade-offs

| Approach | Pros | Cons |
|----------|------|------|
| API search | Fast, batch multiple | Read-only, can't add to cart |
| API cart sync | Atomic, full control | CORS, session binding issues |
| UI automation | Works reliably | Slower, sequential |

**Recommended workflow**: API for search, UI for adding to cart.
