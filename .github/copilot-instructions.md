# GitHub Copilot Instructions for gemini_deep_research_as_markdown

## Project Overview

This is a Python tool that converts Google Deep Research documents into Markdown format. It uses the Google Docs API to fetch document content and processes it into clean, well-formatted Markdown with proper handling of footnotes, links, and LaTeX equations.

## Technology Stack

- **Python**: 3.12+
- **Package Manager**: uv (modern Python package manager)
- **Key Dependencies**: 
  - google-api-python-client
  - google-auth-httplib2
  - google-auth-oauthlib

## Code Style and Conventions

- Follow PEP 8 Python style guidelines
- Use descriptive variable and function names
- Include docstrings for all functions and classes
- Prefer explicit over implicit code
- Use type hints where appropriate
- Keep functions focused and single-purpose

## Project Structure

- `gdr_md.py`: Main script containing all conversion logic
- `pyproject.toml`: Project metadata and dependencies
- `uv.lock`: Locked dependency versions
- `.python-version`: Specifies Python version requirement

## Development Workflow

1. **Dependencies**: Use `uv` to manage dependencies
   - Install dependencies: `uv sync`
   - Add new dependencies: `uv add <package>`
   - Update dependencies: `uv lock --upgrade`

2. **Running the Script**: The script requires Google API credentials
   - Needs `credentials.json` from Google Cloud Console
   - Stores authentication tokens in `token.json`
   - Main function is commented out by default for safety

3. **Testing**: When making changes, ensure:
   - Footnote linking heuristics work correctly
   - LaTeX equation formatting is preserved
   - Google URL redirects are properly cleaned
   - Markdown output is well-formatted

## Key Implementation Details

### Authentication
- Uses OAuth 2.0 for Google Docs API access
- Implements token refresh mechanism
- Read-only access to Google Docs

### Content Processing
- Extracts footnote references and converts to inline Markdown links
- Applies intelligent linking heuristic (links phrase after last comma in last sentence)
- Handles paragraph styles (headings, title, normal text)
- Stops processing at "Works Cited" section
- Formats LaTeX equations with proper escaping

### Markdown Conversion
- Converts Google Docs heading styles to Markdown headers
- Adds horizontal rules after title and before "End of Report"
- Cleans up excessive newlines
- Preserves LaTeX notation in equations

## Common Tasks

### Adding New Features
- Consider backward compatibility with existing Google Docs
- Test with various document structures
- Update docstrings and comments

### Debugging
- Check API response structure when adding new element types
- Verify regex patterns with edge cases
- Test footnote linking logic with complex sentences

### Error Handling
- Handle Google API errors gracefully (401, 403, 404)
- Provide helpful error messages for missing credentials
- Validate document IDs before API calls

## Best Practices

- Keep the single-file structure for simplicity
- Maintain clear separation between authentication, processing, and conversion logic
- Use regex carefully and test edge cases
- Comment complex logic, especially the linking heuristic
- Don't commit sensitive files like `credentials.json` or `token.json` (already in .gitignore)

## Testing Considerations

- Test with various Google Docs structures
- Verify footnote reference processing
- Check LaTeX equation handling
- Ensure proper handling of edge cases (empty paragraphs, missing footnotes, etc.)
- Validate output Markdown syntax

## Future Enhancements to Consider

- Support for tables, images, and lists from Google Docs
- Command-line argument parsing for document IDs
- Batch processing of multiple documents
- Output to file instead of stdout
- Custom linking heuristic configurations
