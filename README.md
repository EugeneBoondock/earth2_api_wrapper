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
- 🛡️ **Built-in Safeguards**: Comprehensive rate limiting and abuse prevention to protect Earth2's bandwidth
- 📈 **Usage Monitoring**: Real-time statistics and efficiency tracking
- 💾 **Smart Caching**: Intelligent response caching to reduce API load

## API Endpoints Covered

### Public Data Endpoints
- Landing metrics and trending places
- Property details by ID
- Public user information

### Authenticated Endpoints
- Market (requires authentication)
- Leaderboard (requires authentication)
- Resource data for properties (requires authentication)
- Territory release winners (requires authentication)
- Leaderboards (players, countries, player countries) (requires authentication)
- Marketplace search with advanced filtering (requires authentication)
- Market floor price discovery (requires authentication)
- Avatar sales data (requires authentication)

## Installation

### Node.js/TypeScript

**Direct from GitHub (Recommended):**
```bash
# Install directly from GitHub
npm install https://github.com/EugeneBoondock/earth2_api_wrapper.git#main:node

# Or with Bun
bun install https://github.com/EugeneBoondock/earth2_api_wrapper.git#main:node

# For global CLI access
npm install -g https://github.com/EugeneBoondock/earth2_api_wrapper.git#main:node
```

**From npm (Now Available!):**
```bash
# Install from npm
npm install earth2-api-wrapper

# Or with Bun
bun install earth2-api-wrapper

# Or install globally for CLI access
npm install -g earth2-api-wrapper
```

### Python

**Direct from GitHub (Recommended):**
```bash
# Install directly from GitHub
pip install git+https://github.com/EugeneBoondock/earth2_api_wrapper.git#subdirectory=python
```

**From PyPI (Now Available!):**
```bash
# Install from PyPI
pip install earth2-api-wrapper
```

**For development:**
```bash
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

Both Node.js and Python versions include CLI tools with built-in safeguards.

### Node.js CLI

```bash
# Authentication (OAuth flow)
e2 login --email your@email.com --password yourpassword
e2 check-session         # Verify session is still valid

# Data commands with beautiful formatted output
e2 trending              # 🌍 Trending places in a nice table
e2 market --country AU   # 🏪 Marketplace search with formatting
e2 leaderboard --type players  # 🏆 Leaderboards with colors

# Raw JSON output (for scripts/automation)
e2 trending --json
e2 market --country AU --json

# Rate limiting and monitoring commands
e2 stats                 # 📊 Show usage statistics and efficiency
e2 clear-cache          # 🗑️ Clear response cache
e2 set-cache-ttl 600000 # ⏱️ Set cache TTL (milliseconds)

# Other commands
e2 property <uuid>
e2 resources <uuid>
e2 avatar-sales
e2 user <user-id>
e2 my-favorites  # Requires auth
```

### Python CLI

```bash
# Authentication (OAuth flow)
e2 login --email your@email.com --password yourpassword
e2 check-session         # Verify session is still valid

# Data commands with beautiful formatted output
e2 trending              # 🌍 Trending places in a nice table
e2 market --country AU   # 🏪 Marketplace search with formatting
e2 leaderboard --type players  # 🏆 Leaderboards with colors

# Raw JSON output (for scripts/automation)
e2 trending --json
e2 market --country AU --json

# Rate limiting and monitoring commands
e2 stats                 # 📊 Show usage statistics and efficiency
e2 clear-cache          # 🗑️ Clear response cache
e2 set-cache-ttl 600    # ⏱️ Set cache TTL (seconds)

# Other commands
e2 property <uuid>
e2 resources <uuid>
e2 avatar-sales
e2 user <user-id>
e2 my-favorites  # Requires auth
```

> **Note**: The CLI now features beautiful formatted tables, colors, and emojis for better readability. Use the `--json` flag on any command to get raw JSON output for scripting purposes.

## Authentication

The wrapper provides multiple ways to authenticate with Earth2 for accessing private endpoints like favorites.

### Method 1: CLI Login (Recommended)

The wrapper handles Earth2's complex Kinde OAuth authentication flow automatically:

```bash
# Interactive login with OAuth flow
e2 login --email your@email.com --password yourpassword

# Or using environment variables
export E2_EMAIL="your@email.com"
export E2_PASSWORD="yourpassword"
e2 login
```

The login process will:
1. Navigate through Earth2's OAuth redirects
2. Handle the Kinde authentication flow
3. Extract and store session cookies
4. Validate the session

After successful login, you can use authenticated endpoints:
```bash
e2 my-favorites
e2 check-session  # Verify your session is still valid
```

### Method 2: Programmatic Authentication

The wrapper automatically handles the complex OAuth flow programmatically:

#### Node.js
```typescript
import { Earth2Client } from 'earth2-api-wrapper';

const client = new Earth2Client();

// Perform OAuth authentication
const result = await client.authenticate('your@email.com', 'yourpassword');

if (result.success) {
  console.log('✓ OAuth authentication successful!');
  
  // Check session validity
  const sessionCheck = await client.checkSessionValidity();
  if (sessionCheck.isValid) {
    // Now you can use authenticated endpoints
    const favorites = await client.getMyFavorites();
  }
} else {
  console.error('✗ OAuth authentication failed:', result.message);
}
```

#### Python
```python
from earth2_api_wrapper import Earth2Client

client = Earth2Client()

# Perform OAuth authentication
result = client.authenticate('your@email.com', 'yourpassword')

if result['success']:
    print('✓ OAuth authentication successful!')
    
    # Check session validity
    session_check = client.check_session_validity()
    if session_check['isValid']:
        # Now you can use authenticated endpoints
        favorites = client.get_my_favorites()
else:
    print('✗ OAuth authentication failed:', result['message'])
```

### Method 3: Manual Cookie/Token Setup

If you already have session cookies and CSRF tokens:

#### Environment Variables
```bash
export E2_COOKIE="your-cookie-string"
export E2_CSRF="your-csrf-token"
```

#### Programmatic Setup
```typescript
// Node.js
const client = new Earth2Client({
  cookieJar: 'your-cookie-string',
  csrfToken: 'your-csrf-token'
});
```

```python
# Python
client = Earth2Client(
    cookie_jar='your-cookie-string',
    csrf_token='your-csrf-token'
)
```

## Bandwidth Protection Safeguards

This wrapper includes comprehensive safeguards to prevent abuse and protect Earth2's bandwidth:

### 🛡️ Multi-Tier Rate Limiting
- **Per-endpoint limits**: Different limits for different API categories
- **Global rate limiting**: 200 requests per minute maximum
- **Burst protection**: Max 10 requests per 10 seconds
- **Exponential backoff**: Automatic retry delays on errors

### 📊 Usage Monitoring
```bash
# Check your usage statistics
e2 stats
```

Example output:
```
📊 API Usage Statistics

┌─────────────────┬─────────┐
│ Metric          │ Value   │
├─────────────────┼─────────┤
│ Total Requests  │ 1,250   │
│ Blocked Requests│ 15      │
│ Current RPM     │ 45      │
│ Cache Size      │ 234     │
│ Efficiency      │ 98.8%   │
└─────────────────┴─────────┘
```

### 💾 Smart Caching
- **5-minute default TTL** for GET requests
- **Automatic cache management** (max 1000 entries)
- **Configurable cache duration**
- **Significant bandwidth reduction**

### ⚙️ Configuration Options

#### Disable Rate Limiting (Not Recommended)
```typescript
// Node.js - Only for testing/development
const client = new Earth2Client({ respectRateLimits: false });
```

```python
# Python - Only for testing/development
client = Earth2Client(respect_rate_limits=False)
```

#### Monitor and Configure
```typescript
// Node.js
const stats = client.getRateLimitStats();
client.clearCache();
client.setCacheTtl(600000); // 10 minutes
```

```python
# Python
stats = client.get_rate_limit_stats()
client.clear_cache()
client.set_cache_ttl(600)  # 10 minutes
```

For detailed information about the safeguards, see [SAFEGUARDS.md](SAFEGUARDS.md).

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

**With npm:**
```bash
cd node
npm install
npm run build
npm test  # If tests are available
```

**With Bun:**
```bash
cd node
bun install
bun run build
bun test  # If tests are available
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
