# Security Policy

## Supported versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

Only the latest release receives security fixes.

## Reporting a vulnerability

Please do **not** open a public issue for security problems.

Report vulnerabilities through [GitHub Security Advisories](https://github.com/MathiasPaulenko/behave-playwright/security/advisories/new)
— this creates a private, coordinated disclosure channel with the maintainer.

Include: the affected version, reproduction steps, and any relevant
feature/config that triggers the issue.

You can expect an acknowledgement within a few days. If the report is
confirmed we will work on a fix and credit you in the advisory unless you
prefer otherwise.

## Scope notes

This library drives a real browser on behalf of test authors. Feature
files and `behave -D` options are trusted input — treat them as code, not
as untrusted data. The library itself does not execute external payloads,
but intercepted network responses and mock bodies you write are passed to
the page under test by design.
