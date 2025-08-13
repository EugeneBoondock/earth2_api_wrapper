/**
 * Rate limiting and abuse prevention for Earth2 API wrapper.
 * Protects Earth2's bandwidth by implementing multiple safeguards.
 */

interface CacheEntry {
  timestamp: number;
  response: any;
}

export interface RateLimitStats {
  totalRequests: number;
  blockedRequests: number;
  currentRpm: number;
  cacheSize: number;
  errorCounts: Record<string, number>;
  efficiency: number;
}

export class RateLimiter {
  private endpointLimits: Record<string, number> = {
    auth: 5,           // Authentication attempts
    search: 30,        // Market searches
    property: 60,      // Property lookups
    leaderboard: 20,   // Leaderboard queries
    user: 40,          // User info requests
    resources: 30,     // Resource queries
    default: 50        // Default for other endpoints
  };

  private globalLimit = 200;  // Total requests per minute
  private burstLimit = 10;    // Max requests in 10 seconds

  // Tracking structures
  private endpointRequests: Map<string, number[]> = new Map();
  private globalRequests: number[] = [];
  private burstRequests: number[] = [];
  private errorCounts: Map<string, number> = new Map();
  private lastErrorTime: Map<string, number> = new Map();

  // Simple in-memory cache for GET requests
  private cache: Map<string, CacheEntry> = new Map();
  private cacheTtl = 300000; // 5 minutes in milliseconds

  // Usage tracking
  private totalRequests = 0;
  private blockedRequests = 0;

  private getEndpointCategory(url: string): string {
    const urlLower = url.toLowerCase();
    
    if (urlLower.includes('auth') || urlLower.includes('login')) {
      return 'auth';
    } else if (urlLower.includes('marketplace') || urlLower.includes('search')) {
      return 'search';
    } else if (urlLower.includes('landfields') && !urlLower.includes('/resources')) {
      return 'property';
    } else if (urlLower.includes('leaderboard')) {
      return 'leaderboard';
    } else if (urlLower.includes('user_info') || urlLower.includes('users')) {
      return 'user';
    } else if (urlLower.includes('resources')) {
      return 'resources';
    } else {
      return 'default';
    }
  }

  private cleanOldRequests(requestQueue: number[], windowMs: number): void {
    const currentTime = Date.now();
    const cutoff = currentTime - windowMs;
    
    // Remove old requests
    while (requestQueue.length > 0 && requestQueue[0] < cutoff) {
      requestQueue.shift();
    }
  }

  private getCacheKey(url: string, method: string = 'GET'): string {
    return `${method}:${url}`;
  }

  private getCachedResponse(cacheKey: string): any | null {
    const entry = this.cache.get(cacheKey);
    if (entry) {
      if (Date.now() - entry.timestamp < this.cacheTtl) {
        return entry.response;
      } else {
        this.cache.delete(cacheKey);
      }
    }
    return null;
  }

  private cacheResponse(cacheKey: string, response: any): void {
    // Limit cache size to prevent memory issues
    if (this.cache.size > 1000) {
      // Remove oldest 20% of entries
      const entries = Array.from(this.cache.entries());
      entries.sort((a, b) => a[1].timestamp - b[1].timestamp);
      
      for (let i = 0; i < 200 && i < entries.length; i++) {
        this.cache.delete(entries[i][0]);
      }
    }
    
    this.cache.set(cacheKey, {
      timestamp: Date.now(),
      response
    });
  }

  canMakeRequest(url: string, method: string = 'GET'): {
    canProceed: boolean;
    reason?: string;
    cachedResponse?: any;
  } {
    const currentTime = Date.now();
    const endpointCategory = this.getEndpointCategory(url);
    
    // Check cache first for GET requests
    if (method.toUpperCase() === 'GET') {
      const cacheKey = this.getCacheKey(url, method);
      const cachedResponse = this.getCachedResponse(cacheKey);
      if (cachedResponse !== null) {
        return { canProceed: true, cachedResponse };
      }
    }
    
    // Clean old requests
    this.cleanOldRequests(this.globalRequests, 60000); // 1 minute
    this.cleanOldRequests(this.burstRequests, 10000);  // 10 seconds
    
    if (!this.endpointRequests.has(endpointCategory)) {
      this.endpointRequests.set(endpointCategory, []);
    }
    const endpointQueue = this.endpointRequests.get(endpointCategory)!;
    this.cleanOldRequests(endpointQueue, 60000);
    
    // Check for exponential backoff on errors
    const errorCount = this.errorCounts.get(endpointCategory) || 0;
    const lastError = this.lastErrorTime.get(endpointCategory) || 0;
    
    if (errorCount > 0) {
      const backoffTime = Math.min(Math.pow(2, errorCount) * 1000, 300000); // Max 5 minutes
      if (currentTime - lastError < backoffTime) {
        this.blockedRequests++;
        return {
          canProceed: false,
          reason: `Backing off due to errors (wait ${Math.ceil(backoffTime / 1000)}s)`
        };
      }
    }
    
    // Check burst limit
    if (this.burstRequests.length >= this.burstLimit) {
      this.blockedRequests++;
      return {
        canProceed: false,
        reason: 'Burst limit exceeded (max 10 requests per 10 seconds)'
      };
    }
    
    // Check global rate limit
    if (this.globalRequests.length >= this.globalLimit) {
      this.blockedRequests++;
      return {
        canProceed: false,
        reason: `Global rate limit exceeded (max ${this.globalLimit} requests per minute)`
      };
    }
    
    // Check endpoint-specific rate limit
    const endpointLimit = this.endpointLimits[endpointCategory] || this.endpointLimits.default;
    if (endpointQueue.length >= endpointLimit) {
      this.blockedRequests++;
      return {
        canProceed: false,
        reason: `Endpoint rate limit exceeded (max ${endpointLimit} requests per minute for ${endpointCategory})`
      };
    }
    
    return { canProceed: true };
  }

  recordRequest(url: string, method: string = 'GET'): void {
    const currentTime = Date.now();
    const endpointCategory = this.getEndpointCategory(url);
    
    this.globalRequests.push(currentTime);
    this.burstRequests.push(currentTime);
    
    if (!this.endpointRequests.has(endpointCategory)) {
      this.endpointRequests.set(endpointCategory, []);
    }
    this.endpointRequests.get(endpointCategory)!.push(currentTime);
    
    this.totalRequests++;
    
    // Reset error count on successful request
    this.errorCounts.set(endpointCategory, 0);
  }

  recordError(url: string, statusCode?: number): void {
    const endpointCategory = this.getEndpointCategory(url);
    const currentCount = this.errorCounts.get(endpointCategory) || 0;
    
    this.errorCounts.set(endpointCategory, currentCount + 1);
    this.lastErrorTime.set(endpointCategory, Date.now());
  }

  cacheResponseData(url: string, method: string, response: any): void {
    if (method.toUpperCase() === 'GET') {
      const cacheKey = this.getCacheKey(url, method);
      this.cacheResponse(cacheKey, response);
    }
  }

  getStats(): RateLimitStats {
    const currentTime = Date.now();
    
    // Clean old requests for accurate counts
    this.cleanOldRequests(this.globalRequests, 60000);
    
    const errorCounts: Record<string, number> = {};
    this.errorCounts.forEach((count, category) => {
      errorCounts[category] = count;
    });
    
    return {
      totalRequests: this.totalRequests,
      blockedRequests: this.blockedRequests,
      currentRpm: this.globalRequests.length,
      cacheSize: this.cache.size,
      errorCounts,
      efficiency: (1 - this.blockedRequests / Math.max(1, this.totalRequests + this.blockedRequests)) * 100
    };
  }

  clearCache(): void {
    this.cache.clear();
  }

  setCacheTtl(ms: number): void {
    this.cacheTtl = ms;
  }
}

// Global rate limiter instance
const rateLimiter = new RateLimiter();

export function getRateLimiter(): RateLimiter {
  return rateLimiter;
}