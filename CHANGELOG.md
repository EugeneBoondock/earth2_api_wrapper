# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2025-01-13

### Fixed
- **Type Annotations**: Fixed Python type annotations using `Any` instead of `any`
- **Code Quality**: All flake8 linting issues resolved
- **Import Optimization**: Removed unused imports for cleaner code

### Documentation
- **Authentication Limitations**: Clearly documented that 2FA/TOTP is NOT supported
- **Troubleshooting Guide**: Added comprehensive authentication troubleshooting
- **Manual Cookie Extraction**: Detailed guide for 2FA account users
- **CLI Help Updates**: Updated command descriptions to mention 2FA limitation

## [0.2.0] - 2025-01-13

### Added
- **🛡️ Comprehensive Bandwidth Protection Safeguards**
  - Multi-tier rate limiting system with per-endpoint limits
  - Global rate limiting (200 requests/minute maximum)
  - Burst protection (max 10 requests per 10 seconds)
  - Exponential backoff on API errors (2^error_count seconds, max 5 minutes)
  
- **💾 Intelligent Response Caching**
  - 5-minute TTL for GET requests by default
  - Automatic cache size management (max 1000 entries)
  - Configurable cache duration
  - Significant bandwidth reduction through cache hits
  
- **📊 Usage Monitoring & Statistics**
  - Real-time metrics tracking (total requests, blocked requests, efficiency)
  - Per-endpoint error counting and analysis
  - Cache hit rate monitoring
  - New CLI commands: `e2 stats`, `e2 clear-cache`, `e2 set-cache-ttl`
  
- **🔧 Configuration Options**
  - Optional rate limiting (enabled by default)
  - Configurable cache TTL
  - Runtime cache management
  - Transparent operation with detailed statistics

### Enhanced
- **CLI Tools**
  - Added usage statistics command (`e2 stats`)
  - Added cache management commands
  - Improved error messages with rate limiting information
  - Enhanced user experience with monitoring capabilities

- **API Client**
  - All HTTP requests now go through rate limiting
  - Automatic caching for GET requests
  - Improved error handling with exponential backoff
  - Better session management with rate limiting

### Technical
- **Rate Limiting Implementation**
  - Thread-safe rate limiting (Python: threading.Lock)
  - Memory-efficient request tracking
  - Automatic cleanup of old request records
  - Per-endpoint categorization and limits

- **Caching System**
  - In-memory caching with TTL support
  - Automatic cache size management
  - Cache key generation and validation
  - Transparent cache hits

### Documentation
- Added comprehensive `SAFEGUARDS.md` documentation
- Added `IMPLEMENTATION_SUMMARY.md` with technical details
- Updated README with safeguards information
- Added test script demonstrating safeguards effectiveness

### Security
- **Authentication Rate Limiting**
  - Strict limits on login attempts (5/minute)
  - Prevents credential stuffing attacks
  - OAuth flow protection

- **Abuse Prevention**
  - Prevents excessive marketplace scraping
  - Protects against bulk data extraction
  - Reasonable limits for legitimate usage

### Performance
- **Improved Response Times**
  - Cached responses return instantly
  - Reduced API load through intelligent caching
  - Better user experience for repeated requests

- **Bandwidth Optimization**
  - Significant reduction in redundant API calls
  - Smart caching reduces Earth2 server load
  - Efficient request patterns

### Breaking Changes
- None - All existing code continues to work unchanged

### Migration Guide
- No migration required
- Rate limiting is enabled by default
- Existing applications will automatically benefit from caching and protection
- Optional: Use new monitoring commands to optimize usage patterns

## [0.1.0] - 2024-12-XX

### Added
- Initial release of Earth2 API wrapper
- Support for Node.js/TypeScript and Python
- CLI tools for both platforms
- Comprehensive API coverage for Earth2 endpoints
- Authentication support with OAuth flow
- Market data access and property information
- Leaderboard queries and user data
- Avatar sales tracking
- Resource data access

### Features
- Dual language support (Node.js/TypeScript and Python)
- Command-line interfaces
- OAuth authentication handling
- Public and authenticated endpoint access
- Market search and floor price discovery
- Property and resource information
- User and leaderboard data
- Beautiful CLI output with tables and colors