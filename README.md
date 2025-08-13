# Earth2 API Wrapper

[![npm version](https://img.shields.io/npm/v/earth2-api-wrapper)](https://www.npmjs.com/package/earth2-api-wrapper)
[![PyPI version](https://img.shields.io/pypi/v/earth2-api-wrapper)](https://pypi.org/project/earth2-api-wrapper/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Unofficial Earth2 API wrapper library and CLI tools for Node.js/TypeScript and Python. This library provides read-only access to Earth2's public APIs for market data, leaderboards, property information, and more.

> **Note**: This is an unofficial wrapper and is not affiliated with Earth2. It only includes read-only operations and excludes any automation for raiding, dispensing, charging, jewel management, or civilian operations.

## Features

- 🌍 **Comprehensive API Coverage**: Access to all major Earth2 public endpoints
- 🔧 **Dual Language Support**: Both Node.js/TypeScript and Python implementations
- 🖥️ **CLI Tools**: Command-line interfaces for both platforms
- 📊 **Market Data**: Search marketplace, get trending places, calculate floor prices
- 🏆 **Leaderboards**: Access player, country, and player-country leaderboards
- 🏠 **Property Information**: Get detailed property and resource data
- 👤 **User Data**: Fetch public user information and profiles
- 🎮 **Avatar Sales**: Track recent avatar skin sales
- 🔐 **Authentication Support**: Optional cookie/CSRF token authentication for private data

## API Endpoints Covered

### Public Data Endpoints
- Landing metrics and trending places
- Territory release winners
- Property details by ID
- Marketplace search with advanced filtering
- Market floor price discovery
- Leaderboards (players, countries, player countries)
- Avatar sales data
- Public user information
- Resource data for properties

### Authenticated Endpoints
- User favorites (requires authentication)

## Installation

### Node.js/TypeScript

```bash
# Install from npm
npm install earth2-api-wrapper

# Or install globally for CLI access
npm install -g earth2-api-wrapper
```

### Python

```bash
# Install from PyPI
pip install earth2-api-wrapper

# Or for development
git clone https://github.com/EugeneBoondock/earth2_api_wrapper.git
cd earth2_api_wrapper/python
pip install -e .
```

## Quick Start

### Node.js/TypeScript

```typescript
import { Earth2Client } from 'earth2-api-wrapper';

const client = new Earth2Client();

// Get trending places
const trending = await client.getTrendingPlaces();
console.log(trending.data);

// Search marketplace
const market = await client.searchMarket({
  country: 'AU',
  landfieldTier: 1,
  tileCount: '5-50',
  page: 1,
  items: 100
});
console.log(market.items);

// Get property details
const property = await client.getProperty('property-uuid-here');
console.log(property);
```

### Python

```python
from earth2_api_wrapper import Earth2Client

client = Earth2Client()

# Get trending places
trending = client.get_trending_places()
print(trending['data'])

# Search marketplace
market = client.search_market(
    country='AU',
    landfieldTier='1',
    tileCount='5-50',
    page=1,
    items=100
)
print(market['items'])

# Get property details
property_data = client.get_property('property-uuid-here')
print(property_data)
```

## CLI Usage

Both Node.js and Python versions include CLI tools.

### Node.js CLI

```bash
# After global install
e2 trending
e2 property <uuid>
e2 market --country AU --tier 1 --tile-count "5-50"
e2 leaderboard --type players --sort_by tiles_count
e2 resources <uuid>
e2 avatar-sales
e2 user <user-id>
e2 my-favorites  # Requires auth
```

### Python CLI

```bash
# Using the e2 command (after pip install)
e2 trending
e2 property <uuid>
e2 market --country AU --tier 1 --tile-count "5-50"
e2 leaderboard --type players --sort-by tiles_count
e2 resources <uuid>
e2 avatar-sales
e2 user <user-id>
e2 my-favorites  # Requires auth
```

## Authentication

For endpoints that require authentication (like favorites), you can provide authentication details:

### Environment Variables

```bash
export E2_COOKIE="your-cookie-string"
export E2_CSRF="your-csrf-token"
```

### Programmatic Authentication

#### Node.js
```typescript
const client = new Earth2Client({
  cookieJar: 'your-cookie-string',
  csrfToken: 'your-csrf-token'
});
```

#### Python
```python
client = Earth2Client(
    cookie_jar='your-cookie-string',
    csrf_token='your-csrf-token'
)
```

## Advanced Usage

### Market Floor Price Discovery

```typescript
// Node.js
const floor = await client.getMarketFloor({
  country: 'AU',
  landfieldTier: '1',
  tileClass: '1'
});
console.log(`Floor price: ${floor?.ppt} (source: ${floor?.source})`);
```

```python
# Python - Note: Python version uses general market search for floor discovery
market = client.search_market(country='AU', landfieldTier='1', items=1)
if market['items']:
    print(f"Floor price: {market['items'][0]['ppt']}")
```

### Leaderboard Queries

```typescript
// Node.js
const players = await client.getLeaderboardPlayers({
  sort_by: 'tiles_count',
  country: 'AU'
});

const countries = await client.getLeaderboardCountries({
  sort_by: 'tiles_count'
});
```

```python
# Python
players = client.get_leaderboard('players', sort_by='tiles_count', country='AU')
countries = client.get_leaderboard('countries', sort_by='tiles_count')
```

### Bulk User Information

```typescript
// Node.js
const users = await client.getUsers(['user-id-1', 'user-id-2']);
```

```python
# Python
users = client.get_users(['user-id-1', 'user-id-2'])
```

## Development

### Node.js Development

```bash
cd node
npm install
npm run build
npm test  # If tests are available
```

### Python Development

```bash
cd python
pip install -e .
# Run CLI commands for testing
python -m earth2_api_wrapper.cli trending
```

## API Reference

### Available Methods

| Method | Node.js | Python | Description |
|--------|---------|--------|-------------|
| Landing Metrics | `getLandingMetrics()` | `get_landing_metrics()` | Get landing page metrics |
| Trending Places | `getTrendingPlaces()` | `get_trending_places()` | Get trending locations |
| Territory Winners | `getTerritoryReleaseWinners()` | `get_territory_release_winners()` | Get territory release winners |
| Property Details | `getProperty(id)` | `get_property(id)` | Get property information |
| Market Search | `searchMarket(query)` | `search_market(**params)` | Search marketplace |
| Market Floor | `getMarketFloor(params)` | N/A (use search_market) | Get minimum price per tile |
| Player Leaderboard | `getLeaderboardPlayers(params)` | `get_leaderboard('players', **params)` | Get player rankings |
| Country Leaderboard | `getLeaderboardCountries(params)` | `get_leaderboard('countries', **params)` | Get country rankings |
| Player Country LB | `getLeaderboardPlayerCountries(params)` | `get_leaderboard('player_countries', **params)` | Get player-country rankings |
| Resources | `getResources(propertyId)` | `get_resources(property_id)` | Get property resources |
| Avatar Sales | `getAvatarSales()` | `get_avatar_sales()` | Get avatar sales data |
| User Info | `getUserInfo(userId)` | `get_user_info(user_id)` | Get user information |
| Bulk Users | `getUsers(userIds)` | `get_users(user_ids)` | Get multiple users |
| My Favorites | `getMyFavorites()` | `get_my_favorites()` | Get user favorites (auth required) |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This is an unofficial API wrapper and is not affiliated with Earth2. Use at your own risk. The wrapper only provides read-only access to public APIs and does not include any automation features for game mechanics.

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/EugeneBoondock/earth2_api_wrapper/issues) page
2. Create a new issue with detailed information about your problem
3. Include code examples and error messages when applicable

---

Made with ❤️ for the Earth2 community
