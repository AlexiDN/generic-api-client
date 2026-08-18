# Changelog

All notable changes to this project will be documented here.

## [1.1.0] - 2026-08-18
- Added `use_cache` option to `APISegment._execute_request`.
- Fixed auth injection order so `_inject_auth` runs after login/auth checks instead of unconditionally.
- Fixed request body serialization to use the `json` alias field.
- Fixed `to_json` to correctly recurse into nested lists/dicts and dump models in JSON mode.

## [1.0.0] - 2026-05-03
- Added usage examples, documentation, working cache (local+redis), API versioning, and overrideable methods for customization.
