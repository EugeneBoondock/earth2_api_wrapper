# earth2-api-wrapper (Python)

Unofficial Earth2 API wrapper with CLI. Read-only operations. Excludes raiding/dispensing/charging/jewel/civilian automation.

Dev install:

```bash
pip install -e .
python -m earth2_api_wrapper.cli trending
```

Environment variables when needed:
- E2_COOKIE
- E2_CSRF

Examples:
```bash
# Trending
python -m earth2_api_wrapper.cli trending

# Property
python -m earth2_api_wrapper.cli property <uuid>

# Market search
python -m earth2_api_wrapper.cli market --country AU --tier 1 --tile-count 5-50 --items 100

# Leaderboard
python -m earth2_api_wrapper.cli leaderboard --type players --sort-by tiles_count --country AU

# Resources
python -m earth2_api_wrapper.cli resources <uuid>
```


