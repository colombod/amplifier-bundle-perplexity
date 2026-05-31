# Security Policy

## Supported Versions

This project is currently maintained on the `main` branch.
We address security issues in the latest release only.

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public GitHub issue.

Instead, please report it via one of the following channels:

- **GitHub Security Advisories**: Use the
  [Security Advisory](https://github.com/colombod/amplifier-bundle-perplexity/security/advisories/new)
  feature on this repository (preferred).
- **GitHub Issues**: If the vulnerability is low-severity and has no exploitable impact,
  you may open a regular issue with the `security` label.

We will acknowledge your report within 5 business days and aim to provide a fix or
mitigation within 30 days for confirmed vulnerabilities.

## Scope

This bundle handles:

- A Perplexity API key (`PERPLEXITY_API_KEY`) passed via environment variable or config.
- Outbound HTTP requests to the Perplexity API.

Security-relevant areas to consider:

- Do not commit API keys to version control (see README for guidance).
- The bundle does not store or log API keys beyond the current process.

## Out of Scope

- Vulnerabilities in third-party dependencies (report upstream).
- Issues in the Perplexity API itself (report to Perplexity directly).
