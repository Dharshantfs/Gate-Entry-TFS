# Changelog

All notable changes to the Gate Entry module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial stable release for ERPNext v15

### Changed

### Deprecated

### Removed

### Fixed

### Security

---

## [1.0.0] - 2025-11-28

### Added
- Gate Pass module for recording material and people movement
- Stock Entry integration with automatic gate pass creation
- Support for external material transfers
- Return material transfer handling
- Multi-pass allocations for partial dispatches
- Discrepancy logging for material movements
- Gate Pass Type doctype for categorizing gate operations
- Gate Register report for tracking all gate movements
- Material Reconciliation report
- Pending Gate Passes report
- Custom fields on Stock Entry for external transfer tracking
- Integration with Purchase Receipt and Subcontracting Receipt
- Security Guard role with appropriate permissions

### Technical Details
- Background job processing for gate pass creation
- Database-level locking for allocation validation
- Automatic reference cleanup on document cancellation
- ERPNext v15 compatibility

---

## [0.0.1] - Development Version

Initial development version (pre-release)

[Unreleased]: https://github.com/Guru107/gate-entry/compare/v1.0.0...develop
[1.0.0]: https://github.com/Guru107/gate-entry/releases/tag/v1.0.0

