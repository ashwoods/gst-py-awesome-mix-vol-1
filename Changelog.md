# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.5.0 (Unreleaed)

This pre-release introduces several breaking changes.

- Removed all non async helpers
- Renamed AsyncPlayer to Player
- Added plugin infrastructure based on `pluggy`
- Removed Bus wrapper and implemented as a plugin
- Removed logging and implemented as a plugin
- Changed stop signature: removed send_eos and teardown
- Added exceptions and common error handling

## 0.4.0 (2020-02-24)

- Refactored asyncplayer to use co-routines by default
- Using async bus-based events for asyncio state change 