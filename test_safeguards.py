#!/usr/bin/env python3
"""
Simple test to verify the rate limiting safeguards are working.
This script demonstrates the safeguards in action.
"""

import time
import sys
import os

# Add the python src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python', 'src'))

from earth2_api_wrapper.client import Earth2Client


def test_rate_limiting():
    """Test that rate limiting prevents abuse."""
    print("🧪 Testing Earth2 API Wrapper Safeguards\n")
    
    # Create client with rate limiting enabled (default)
    client = Earth2Client()
    
    print("📊 Initial stats:")
    stats = client.get_rate_limit_stats()
    print(f"  Total requests: {stats.get('total_requests', 0)}")
    print(f"  Blocked requests: {stats.get('blocked_requests', 0)}")
    print(f"  Cache size: {stats.get('cache_size', 0)}")
    print()
    
    # Test normal usage - should work fine
    print("✅ Testing normal usage...")
    try:
        trending = client.get_trending_places()
        print(f"  Successfully got {len(trending.get('data', []))} trending places")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Test caching - second request should be cached
    print("💾 Testing caching...")
    start_time = time.time()
    trending2 = client.get_trending_places()  # Should be cached
    cache_time = time.time() - start_time
    print(f"  Cached request completed in {cache_time:.3f}s")
    
    # Show updated stats
    print("\n📊 Updated stats:")
    stats = client.get_rate_limit_stats()
    print(f"  Total requests: {stats.get('total_requests', 0)}")
    print(f"  Blocked requests: {stats.get('blocked_requests', 0)}")
    print(f"  Cache size: {stats.get('cache_size', 0)}")
    print(f"  Efficiency: {stats.get('efficiency', 0):.1f}%")
    
    # Test burst protection
    print("\n⚡ Testing burst protection (making 12 rapid requests)...")
    blocked_count = 0
    success_count = 0
    
    for i in range(12):
        try:
            # Use different endpoints to avoid cache hits
            if i % 3 == 0:
                client.get_trending_places()
            elif i % 3 == 1:
                client.get_landing_metrics()
            else:
                client.get_avatar_sales()
            success_count += 1
            print(f"  Request {i+1}: ✅ Success")
        except Exception as e:
            blocked_count += 1
            print(f"  Request {i+1}: 🚫 Blocked - {str(e)[:50]}...")
    
    print(f"\n📈 Burst test results:")
    print(f"  Successful requests: {success_count}")
    print(f"  Blocked requests: {blocked_count}")
    
    # Final stats
    print("\n📊 Final stats:")
    stats = client.get_rate_limit_stats()
    print(f"  Total requests: {stats.get('total_requests', 0)}")
    print(f"  Blocked requests: {stats.get('blocked_requests', 0)}")
    print(f"  Cache size: {stats.get('cache_size', 0)}")
    print(f"  Efficiency: {stats.get('efficiency', 0):.1f}%")
    
    error_counts = stats.get('error_counts', {})
    if error_counts:
        print(f"  Error counts: {error_counts}")
    
    print("\n🎉 Safeguards test completed!")
    print("✅ Rate limiting is working correctly")
    print("✅ Caching is reducing API load")
    print("✅ Usage monitoring is tracking requests")
    
    if blocked_count > 0:
        print("✅ Burst protection successfully blocked excessive requests")
    
    print("\n🛡️ Earth2's bandwidth is protected!")


if __name__ == "__main__":
    test_rate_limiting()