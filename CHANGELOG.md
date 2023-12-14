# Changelog

## Unreleased

## [0.7.1] - 2023-12-14

### Changed

- Fix for Slack and Email message on NE online/offline metric.

## [0.7.0] - 2023-12-13

### Changed

- Improved Slack and Email templates.
- Fixed an issue with SMTP_HOST discovery.

### Changed

## [0.6.1] - 2023-01-06

### Changed

- Fix: bad import of datetime in notify-slack.

### Added

## [0.6.0] - 2022-02-18

### Changed

 - Fix: email notifier must split list of emails on spaces.
 - CI: added unit-test execution, build image for arm64 in CI.

## [0.5.0] - 2021-03-07

### Added

 - Alert and recovery notifications based on recovery flag in messages.
 - Set name for SMTP From.

## [0.4.3] - 2021-02-22

### Changed

 - Slack alert color and email image are green for NB online.

## [0.4.2] - 2021-02-19

### Changed

 - Go into retry loop in internal msg send on any smtp error.

## [0.4.1] - 2021-02-19

### Changed

 - Fix: catch any issue with smtp connection and reconnect.

## [0.4.0] - 2021-02-16

### Changed

  - First prod release.

## [0.3.0] - 2020-12-07

### Changed

  - Initial release.
  - Added CHANGELOG.md
