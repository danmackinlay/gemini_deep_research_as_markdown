# GitHub Copilot Instructions for gemini_deep_research_as_markdown

## Project Overview

Python script that converts Google Deep Research documents into Markdown. Uses the Google Docs API to fetch content and processes it into Markdown with footnotes, links, and LaTeX equations.

## Technology Stack

- **Python**: 3.12+
- **Package Manager**: `uv`
- **Linting**: `ruff` (mandatory)
- **Dependencies**: google-api-python-client, google-auth-httplib2, google-auth-oauthlib

## Code Conventions

- Use `ruff` for linting and formatting
- Single-file script architecture (`gdr_md.py`)
- Include docstrings for functions
- Don't commit `credentials.json` or `token.json`

## Development

- Dependencies: `uv sync` / `uv add <package>`
- Linting: `ruff check` / `ruff format`
- Requires `credentials.json` from Google Cloud Console
- OAuth tokens stored in `token.json`

## Key Implementation

- **OAuth 2.0** for Google Docs API access
- **Footnote linking**: Links phrase after last comma in last sentence
- **LaTeX equations**: Double backslashes and escaped underscores
- **Paragraph styles**: Converts Google Docs headings to Markdown
- **Stops at**: "Works Cited" section
- **Horizontal rules**: After title and before "End of Report"

## Important Constraints

- **NO backward compatibility considerations** - this is an agile MVP
- **Testing is not a priority** - this is a disposable script
- Make changes directly; iterate quickly
