import os.path
import re
import urllib.parse

# Required Google Libraries
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("Google API client libraries not found.")
    print("Please install them: pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    exit()

# Scope for read-only access to Google Docs
SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]

# --- Authentication ---

def authenticate():
    """Handles Google OAuth 2.0 authentication for a desktop application."""
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing token: {e}. Please delete token.json and re-authenticate.")
                return None
        else:
            # Assumes 'credentials.json' is in the working directory.
            if not os.path.exists("credentials.json"):
                print("Error: credentials.json not found.")
                print("Please download it from the Google Cloud Console and place it in the script directory.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            # This opens a browser window for the user to grant access
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds

# --- Helper Functions ---

def clean_google_url(url):
    """Cleans Google redirect URLs by extracting the 'q' parameter."""
    # Even in the API, Google often wraps URLs in redirects.
    if url and "google.com/url?q=" in url:
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        if 'q' in query_params:
            return query_params['q'][0]
    return url

def apply_linking_heuristic(text_before, url):
    """Applies the heuristic: Link the phrase after the last comma in the last sentence."""
    text = text_before.strip()
    if not text:
        return ""

    # Handle trailing punctuation (e.g., the period just before the footnote)
    trailing_punctuation = ""
    if text.endswith(('.', ',', ';', ':')):
        trailing_punctuation = text[-1]
        text = text[:-1].strip()

    # 1. Find the start of the last sentence (after ". ").
    last_period_index = text.rfind('. ')

    if last_period_index != -1:
        # Include the ". " in the preceding text
        text_before_sentence = text[:last_period_index+2]
        last_sentence = text[last_period_index+2:].strip()
    else:
        text_before_sentence = ""
        last_sentence = text.strip()

    # If the last sentence is empty, link the text before it as a fallback
    if not last_sentence:
         # Ensure we don't link empty text if the buffer was just punctuation
         if not text_before_sentence.strip() and not text.strip():
             return trailing_punctuation
         # Link the remaining text (which is 'text' variable after punctuation removal)
         return f"[{text.strip()}]({url}){trailing_punctuation}"

    # 2. Find the last comma in the last sentence (", ").
    last_comma_index = last_sentence.rfind(', ')

    if last_comma_index != -1:
        # Include the ", " in the preceding text
        text_before_phrase = last_sentence[:last_comma_index+2]
        linked_phrase = last_sentence[last_comma_index+2:].strip()
        # Format: Text before + [linked phrase](link) + punctuation
        return f"{text_before_sentence}{text_before_phrase}[{linked_phrase}]({url}){trailing_punctuation}"
    else:
        # If no comma, link the whole last sentence
        return f"{text_before_sentence}[{last_sentence}]({url}){trailing_punctuation}"

def format_latex_in_markdown(markdown_content):
    """Formats LaTeX equations with double backslashes and escaped underscores."""
    def format_latex_match(match):
        latex_content = match.group(0)
        # Double backslashes
        latex_content = latex_content.replace('\\', '\\\\')
        # Escape underscores (only if not already escaped)
        latex_content = re.sub(r'(?<!\\)_', r'\\_', latex_content)
        return latex_content

    # Apply format within display math blocks ($$...$$)
    markdown_content = re.sub(r'\$\$.*?\$\$', format_latex_match, markdown_content, flags=re.DOTALL)

    # Apply format to inline LaTeX patterns containing backslashes, e.g., |...|
    # This handles the specific notation seen in the example: $|\nabla \mathcal{L}|$
    markdown_content = re.sub(r'\|.*?\\.*?\|', format_latex_match, markdown_content, flags=re.DOTALL)

    return markdown_content

# --- Core Processing Logic ---

def extract_footnote_links(doc):
    """Maps footnote IDs to their URLs by parsing the 'footnotes' section of the API response."""
    footnote_links = {}
    if 'footnotes' not in doc:
        return footnote_links

    # Footnotes are structured similarly to the main body content
    for footnote_id, footnote in doc['footnotes'].items():
        for element in footnote.get('content', []):
            if 'paragraph' in element:
                for p_element in element['paragraph'].get('elements', []):
                    text_run = p_element.get('textRun')
                    # Check if the text run contains a link style
                    if text_run and 'textStyle' in text_run and 'link' in text_run['textStyle']:
                        url = text_run['textStyle']['link'].get('url')
                        if url:
                            footnote_links[footnote_id] = clean_google_url(url)
                            # Assume only one primary link per footnote, break after finding it
                            break
                if footnote_id in footnote_links:
                    break
    return footnote_links

def process_paragraph(paragraph, footnote_links):
    """Processes a paragraph element, handling text runs and footnote references."""
    content = ""
    # Buffer text runs to know what precedes a footnote reference
    text_buffer = ""

    for element in paragraph.get('elements', []):
        if 'textRun' in element:
            # Accumulate text content
            text = element['textRun'].get('content', '')
            # We accumulate all text, including spaces, but avoid the final newline character of the paragraph
            if text != '\n':
                 text_buffer += text

        elif 'footnoteReference' in element:
            footnote_id = element['footnoteReference'].get('footnoteId')
            if footnote_id in footnote_links:
                link = footnote_links[footnote_id]

                # Apply heuristic to the buffered text
                content += apply_linking_heuristic(text_buffer, link)
                text_buffer = "" # Clear buffer after linking
            else:
                # Fallback if link not found: append buffer and the superscript number
                content += text_buffer + f"^{element['footnoteReference'].get('footnoteNumber', '')}"
                text_buffer = ""

    # Append any remaining text in the buffer
    content += text_buffer

    # Determine paragraph style
    p_style = paragraph.get('paragraphStyle', {}).get('namedStyleType', 'NORMAL_TEXT')

    final_content = content.strip()

    # Stop processing if this paragraph is the "Works Cited" heading
    if re.match(r'^(Works cited|References|Bibliography)\s*$', final_content, re.IGNORECASE):
        return None, p_style, True # Signal to stop

    if not final_content:
        return "", p_style, False

    # Format as Markdown
    if p_style.startswith('HEADING_'):
        try:
            level = int(p_style.split('_')[1])
            # Google Docs often uses H1 for the main title
            if level == 1:
                 prefix = "#"
            else:
                 prefix = "#" * level
            return f"{prefix} {final_content}\n\n", p_style, False
        except (IndexError, ValueError):
            # Fallback if heading format is unexpected
            return f"{final_content}\n\n", p_style, False
    elif p_style == 'TITLE':
        return f"# {final_content}\n\n", p_style, False
    else:
        return f"{final_content}\n\n", p_style, False

def convert_doc_to_markdown(doc):
    """Converts the Google Doc API response to Markdown."""
    footnote_links = extract_footnote_links(doc)
    markdown_output = ""

    body_content = doc.get('body', {}).get('content', [])

    # Flag to track if the main title separator has been added
    title_separator_added = False

    for element in body_content:
        if 'paragraph' in element:
            md_text, style, stop_processing = process_paragraph(element['paragraph'], footnote_links)

            if md_text:
                markdown_output += md_text

                # Heuristic for Horizontal Rule (---):
                # The API does not reliably expose "Horizontal Line". We infer it based on structure.
                # Insert '---' after the main title (TITLE style or the first H1).
                if not title_separator_added:
                    if style == 'TITLE' or style == 'HEADING_1':
                        markdown_output += "---\n\n"
                        title_separator_added = True

            if stop_processing:
                break

        # (Add handling for Tables, Images, Lists etc., if necessary for future enhancements)

    # Final cleanup
    markdown_output = markdown_output.strip()

    # Post-processing: Handle "End of Report" separator
    # Insert '---' before "End of Report" if that specific phrase exists.
    # Use regex to ensure it's replaced correctly even if case differs slightly.
    markdown_output = re.sub(r'End of Report', r'---\n\nEnd of Report', markdown_output, flags=re.IGNORECASE)

    # Clean excessive newlines
    markdown_output = re.sub(r'\n{3,}', '\n\n', markdown_output)

    # Apply LaTeX formatting
    markdown_output = format_latex_in_markdown(markdown_output)

    return markdown_output


# --- Execution ---

def main(document_id):
    """Fetches the document via the API and converts it."""
    print("Starting authentication process...")
    creds = authenticate()
    if not creds:
        print("Authentication failed. Exiting.")
        return

    try:
        print(f"Connecting to Google Docs API...")
        service = build("docs", "v1", credentials=creds)

        print(f"Fetching document ID: {document_id}...")
        # Retrieve the documents contents from the Docs service.
        document = service.documents().get(documentId=document_id).execute()

        print("Document fetched. Processing content...")
        final_markdown = convert_doc_to_markdown(document)

        print("\n--- Conversion Successful ---")
        print(f"Document Title: {document.get('title')}\n")
        print(final_markdown)

    except HttpError as err:
        print(f"\nHTTP error occurred: {err}")
        if err.resp.status == 404:
            print("Error 404: Document not found. Check the ID and ensure you have access.")
        elif err.resp.status == 403:
            print("Error 403: Permission denied. Ensure the account used has access to this document.")
        elif err.resp.status == 401:
            print("Error 401: Unauthorized. Credentials may be invalid or expired.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    # The ID from the example URL provided:
    # https://docs.google.com/document/d/1fyO2F0M6fPPsKrEsI13paQOVWI655NEzsLTOhQd5kl4/edit?usp=sharing
    DOCUMENT_ID = "1fyO2F0M6fPPsKrEsI13paQOVWI655NEzsLTOhQd5kl4"

    # This script must be run locally with credentials.json configured.
    # To run the script, uncomment the following line:
    # main(DOCUMENT_ID)
    print("Script provided. To run, ensure you have 'credentials.json' configured,")
    print("uncomment the main(DOCUMENT_ID) call at the end of the script,")
    print("and execute it in your local Python environment.")