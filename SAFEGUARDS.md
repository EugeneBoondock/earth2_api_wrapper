# Earth2 API Wrapper - Bandwidth Protection Safeguards

This document outlines the comprehensive safeguards implemented to prevent abuse and protect Earth2's bandwidth.

## Rate Limiting System

### Multi-Tier Rate Limits

The wrapper implements multiple layers of rate limiting:

#### 1. Per-Endpoint Rate Limits (requests per minute)
- **Authentication**: 5 requests/min (prevents brute force attacks)
- **Market Search**: 30 requests/min (prevents excessive marketplace scraping)
- **Property Lookups**: 60 requests/min (reasonable for property research)
- **Leaderboards**: 20 requests/min (prevents excessive leaderboard polling)
- **User Info**: 40 requests/min (allows reasonable user data access)
- **Resources**: 30 requests/min (prevents resource data abuse)
- **Default**: 50 requests/min (for other endpoints)

#### 2. Global Rate Limit
- **200 requests per minute** across all endpoints combined
- Prevents any single client from overwhelming Earth2's servers

#### 3. Burst Protection
- **Maximum 10 requests in any 10-second window**
- Prevents rapid-fire request bursts that could impact server performance

## Error Handling & Backoff

### Exponential Backoff
- Automatic exponential backoff on API errors
- Backoff time: `2^error_count` seconds (max 5 minutes)
- Prevents hammering failing endpoints
- Resets on successful requests

### Error Tracking
- Per-endpoint error counting
- Automatic retry prevention during backoff periods
- Detailed error statistics for monitoring

## Response Caching

### Intelligent Caching
- **5-minute TTL** for GET requests by default
- Reduces redundant API calls for frequently accessed data
- Configurable cache duration
- Automatic cache size management (max 1000 entries)

### Cache Benefits
- Faster response times for repeated requests
- Significant reduction in API load
- Improved user experience

## Usage Monitoring

### Statistics Tracking
- Total requests made
- Requests blocked by rate limits
- Current requests per minute
- Cache hit rates
- Per-endpoint error counts
- Overall efficiency metrics

### Transparency
- `getRateLimitStats()` method provides real-time usage data
- Helps developers optimize their usage patterns
- Enables monitoring of wrapper efficiency

## Configuration Options

### Python Implementation
```python
from earth2_api_wrapper import Earth2Client

# Enable rate limiting (default)
client = Earth2Client(respect_rate_limits=True)

# Disable rate limiting (not recommended)
client = Earth2Client(respect_rate_limits=False)

# Get usage statistics
stats = client.get_rate_limit_stats()

# Clear cache
client.clear_cache()

# Set custom cache TTL (in seconds)
client.set_cache_ttl(600)  # 10 minutes
```

### Node.js Implementation
```typescript
import { Earth2Client } from 'earth2-api-wrapper';

// Enable rate limiting (default)
const client = new Earth2Client({ respectRateLimits: true });

// Disable rate limiting (not recommended)
const client = new Earth2Client({ respectRateLimits: false });

// Get usage statistics
const stats = client.getRateLimitStats();

// Clear cache
client.clearCache();

// Set custom cache TTL (in milliseconds)
client.setCacheTtl(600000); // 10 minutes
```

## Best Practices for Developers

### 1. Respect Rate Limits
- Always keep rate limiting enabled in production
- Monitor your usage with `getRateLimitStats()`
- Implement proper error handling for rate limit exceptions

### 2. Optimize Request Patterns
- Cache responses locally when possible
- Batch operations where feasible
- Avoid polling endpoints unnecessarily

### 3. Handle Errors Gracefully
- Implement retry logic with exponential backoff
- Don't ignore rate limit errors
- Log and monitor API usage patterns

### 4. Use Caching Effectively
- Leverage the built-in response cache
- Set appropriate cache TTL for your use case
- Clear cache when fresh data is required

## Monitoring & Alerts

### Usage Statistics
The wrapper provides detailed statistics to help monitor usage:

```json
{
  "totalRequests": 1250,
  "blockedRequests": 15,
  "currentRpm": 45,
  "cacheSize": 234,
  "errorCounts": {
    "search": 2,
    "property": 1
  },
  "efficiency": 98.8
}
```

### Key Metrics
- **Efficiency**: Percentage of requests that weren't blocked
- **Cache Hit Rate**: Implicit in reduced API calls
- **Error Patterns**: Helps identify problematic endpoints

## Security Considerations

### Authentication Rate Limiting
- Strict limits on login attempts (5/minute)
- Prevents credential stuffing attacks
- Protects both Earth2 and users

**Important**: Authentication only supports basic email/password. 2FA/TOTP is not supported.

### Request Validation
- URL validation and sanitization
- Method validation
- Header validation

## Compliance & Ethics

### Responsible Usage
- These safeguards ensure the wrapper can't be used to abuse Earth2's infrastructure
- Promotes fair usage among all Earth2 API consumers
- Maintains good standing with Earth2's services

### Terms of Service
- Wrapper usage must comply with Earth2's Terms of Service
- Rate limits help ensure compliance with usage policies
- Prevents actions that could result in API access revocation

## Emergency Controls

### Circuit Breaker Pattern
- Automatic request blocking during high error rates
- Prevents cascading failures
- Allows system recovery time

### Manual Override
- Cache clearing for fresh data requirements
- Rate limit statistics for usage monitoring
- Configurable cache TTL for different use cases

## Future Enhancements

### Planned Improvements
- Adaptive rate limiting based on server response times
- Distributed rate limiting for multi-instance deployments
- Enhanced caching with compression
- Request prioritization system
- Integration with Earth2's official rate limit headers (if available)

---

**Note**: These safeguards are designed to be transparent and configurable while providing strong default protection. They ensure the wrapper remains a responsible tool for Earth2 API access while providing excellent performance for legitimate use cases.