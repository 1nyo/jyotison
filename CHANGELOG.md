# Changelog

All notable changes to this project will be documented in this file.  
This project follows Semantic Versioning.

---

## [1.0.0] - 2026-03-17
### Added
- Initial public release of **JyotiSON v1.0**

### Added (JP)
- JyotiSON v1.0 を正式リリース

---

## [1.1.0] - 2026-03-21
### Added
- Automatic detection of UTC offset (timezone and daylight saving time)  
  based on birth datetime and birthplace (latitude / longitude)

### Changed
- Improved UI for better readability and usability

### Added (JP)
- 出生時刻・出生地の緯度経度から、UTCオフセット（タイムゾーン／夏時間）を自動取得する機能を追加

### Changed (JP)
- UI を見やすく改良

---

## [1.1.1] - 2026-3-26
### Added
- Extend automatic latitude / longitude retrieval  
  from Google Maps to also support Share link (Mobile firiendly)

### Added (JP)
- Google マップからの緯度経度自動取得を、共有リンクにも対応（モバイルからのUX向上）

---

## [1.1.2] - 2026-03-26

### Changed
- Reorganized internal file structure to clearly separate UI logic, input parsing, output filtering, and calculation layers.
- Improved maintainability and readability without changing calculation results or output schema.

### Fixed
- Fixed an issue where Google Maps share links generated from the Android app could not be parsed correctly when pasted into the birth location field.

---

## [1.2.0] - Planned
### Added

- Considering support for:
  - Ashtakavarga
  - Shadbala
  - Yoga detection

### Planned (JP)
- アシュタカヴァルガ、シャドバラ、ヨーガ判定の追加を検討中
