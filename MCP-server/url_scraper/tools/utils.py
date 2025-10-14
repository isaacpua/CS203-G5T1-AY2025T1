# --- Imports ---
import os

from typing import Optional

# --- OpenAI Setup - for vision analysis ---
from openai import AsyncOpenAI, AsyncAzureOpenAI

# --- URL Parsing ---
from urllib.parse import urlparse

# --- Tempfile Setup - for session directory ---
import tempfile

# --- Image Processing Setup - for image processing ---
# --- Image Processing From BMP Screenshots to PNG for OpenAI ---
from PIL import Image
import io

# --- Environment Variable Loading ---
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- This is a utility file that contains common helper functions for the tools ---

# --- Client Initialization ---
# This block now supports both Azure OpenAI and standard OpenAI, prioritizing Azure.
client = None
model_to_use = None

# Try to initialize AzureOpenAI client first
azure_endpoint = os.getenv("GPT4O_API_BASE")
azure_api_key = os.getenv("GPT4O_API_KEY")
azure_api_version = os.getenv("GPT4O_API_VERSION")
azure_deployment = os.getenv("GPT4O_DEPLOYMENT_NAME")

# Try to initialize standard OpenAI client if Azure is not configured
standard_api_key = os.getenv("OPENAI_API_KEY")
openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")

if azure_endpoint and azure_api_key and azure_api_version and azure_deployment:
    print("Initializing with Azure OpenAI credentials.")
    try:
        client = AsyncAzureOpenAI(
            api_key=azure_api_key,
            api_version=azure_api_version,
            azure_endpoint=azure_endpoint
        )
        model_to_use = azure_deployment
    except Exception as e:
        print(f"Failed to initialize AzureOpenAI client: {e}")
        client = None
elif standard_api_key:
    # Fallback to standard OpenAI client
    print("Azure credentials not found or incomplete. Initializing with standard OpenAI credentials.")
    try:
        client = AsyncOpenAI(api_key=standard_api_key)
        model_to_use = openai_model
    except Exception as e:
        print(f"Failed to initialize standard OpenAI client: {e}")
        client = None

# --- URL Normalization ---
def normalize_url(url: str) -> str:
    """Ensure the URL has a scheme (e.g., http:// or https://)."""
    url = url.strip()
    if not url.startswith(('http://', 'https://', 'file://', 'raw:')):
        print(f"⚠️ URL '{url}' is missing a scheme. Prepending 'https://'.", flush=True)
        return f"https://{url}"
    return url

# --- Session Management Helper ---
def get_session_dir(url: str, custom_user_data_dir: Optional[str] = None) -> str:
    """
    Generate a session directory path based on domain or use custom path.
    
    Args:
        url: The URL to extract domain from
        custom_user_data_dir: Optional custom path to override domain-based generation
    
    Returns:
        Path to use for browser session data
    """
    if custom_user_data_dir:
        return custom_user_data_dir
    
    try:
        # Extract domain and create clean filesystem path
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www. prefix for consistency
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Clean domain for filesystem: medium.com -> medium_com
        clean_domain = domain.replace('.', '_').replace(':', '_').replace('-', '_')
        
        # Create session directory in temp folder
        base_dir = os.path.join(tempfile.gettempdir(), "mcp_browser_sessions")
        session_dir = os.path.join(base_dir, clean_domain)
        
        # Ensure directory exists
        os.makedirs(session_dir, exist_ok=True)
        
        return session_dir
        
    except Exception as e:
        # Fallback to temp directory if URL parsing fails
        fallback_dir = os.path.join(tempfile.gettempdir(), "mcp_browser_sessions", "fallback")
        os.makedirs(fallback_dir, exist_ok=True)
        return fallback_dir

# --- New Session Info Helper ---
def get_session_info(
    url: str,
    storage_state_path: Optional[str] = None,
    user_data_dir: Optional[str] = None
) -> tuple[str | None, str]:
    """
    Determines the correct session paths, automatically detecting existing sessions.

    This function is the single source of truth for session management. It checks for
    an existing 'storage_state.json' in the domain-specific session directory if one
    is not explicitly provided.

    Args:
        url: The URL to derive the session domain from.
        storage_state_path: An explicitly provided path to a session file.
        user_data_dir: An explicitly provided path to a user data directory.

    Returns:
        A tuple containing:
        - The path to the storage_state.json file (or None if not found/provided).
        - The path to the user data directory.
    """
    # First, determine the base session directory (domain-based or custom)
    session_dir = get_session_dir(url, user_data_dir)
    
    # Priority 1: Use explicitly provided storage_state_path if it exists
    if storage_state_path and os.path.exists(storage_state_path):
        print(f"✅ Using explicitly provided session file: {storage_state_path}", flush=True)
        return storage_state_path, session_dir

    # Priority 2: Auto-detect an existing session file in the session directory
    auto_detect_path = os.path.join(session_dir, "storage_state.json")
    if os.path.exists(auto_detect_path):
        print(f"🔄 Auto-detected and using existing session file: {auto_detect_path}", flush=True)
        return auto_detect_path, session_dir
        
    # Priority 3: No session file found, just return the directory path
    print("⚠️ No existing session file found. Proceeding with a fresh or directory-based session.", flush=True)
    return None, session_dir

# --- Session Data Management ---
import json
import tempfile
import asyncio

def create_playwright_storage_state(cookies=None, origins=None):
    """
    Create a proper Playwright storage state object structure.
    
    Args:
        cookies: List of cookies to include
        origins: List of origin objects with localStorage/sessionStorage
    
    Returns:
        Dict in proper Playwright storage state format
    """
    storage_state = {
        "cookies": cookies or [],
        "origins": origins or []
    }
    
    print(f"📦 Created storage state with {len(storage_state['cookies'])} cookies and {len(storage_state['origins'])} origins", flush=True)
    return storage_state

def clean_cookies_for_playwright(cookies, return_storage_state=True, target_url=None):
    """
    Clean cookies to ensure they meet Playwright's requirements and return in proper storage state format.
    
    Args:
        cookies: List of cookies to clean
        return_storage_state: If True, returns complete storage state object. If False, returns just cleaned cookies.
        target_url: Optional target URL for domain validation and secure flag enforcement
    
    Returns:
        Complete Playwright storage state object (default) or just cleaned cookies array
    """
    if not cookies:
        if return_storage_state:
            return create_playwright_storage_state([], [])
        return []
    
    print(f"🔍 DEBUGGING: Starting enhanced cookie cleaning with {len(cookies)} cookies", flush=True)
    if target_url:
        print(f"🎯 Target URL for validation: {target_url}", flush=True)
    
    # Parse target URL for domain and secure context validation
    target_domain = None
    is_secure_context = False
    if target_url:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(target_url)
            target_domain = parsed.netloc.lower()
            is_secure_context = parsed.scheme == 'https'
            print(f"🌐 Parsed target: domain={target_domain}, secure={is_secure_context}", flush=True)
        except Exception as e:
            print(f"⚠️ Failed to parse target URL: {e}", flush=True)
    
    cleaned_cookies = []
    validation_issues = []
    seen_cookies = set()  # For duplicate detection: (name, domain, path)
    total_cookies_size = 0
    
    for i, cookie in enumerate(cookies):
        print(f"\n--- Cookie #{i+1} ENHANCED VALIDATION ---", flush=True)
        print(f"Raw cookie: {cookie}", flush=True)
        
        # Log each field individually
        for key, value in cookie.items() if isinstance(cookie, dict) else []:
            print(f"  {key}: {repr(value)} (type: {type(value)})", flush=True)
        
        clean_cookie = {}
        cookie_issues = []
        
        # ===== REQUIRED FIELDS VALIDATION =====
        name = cookie.get('name')
        value = cookie.get('value', '')
        domain = cookie.get('domain')
        
        if not name or not isinstance(name, str):
            cookie_issues.append(f"Invalid name: {repr(name)} (type: {type(name)})")
        elif len(name) == 0:
            cookie_issues.append("Empty cookie name")
        elif len(name) > 4096:  # Chrome limit
            cookie_issues.append(f"Cookie name too long: {len(name)} chars (max 4096)")
        
        if not domain or not isinstance(domain, str):
            cookie_issues.append(f"Invalid domain: {repr(domain)} (type: {type(domain)})")
        
        # ===== DOMAIN VALIDATION =====
        if domain and isinstance(domain, str):
            # Basic domain format validation
            if not domain.replace('-', '').replace('_', '').replace('.', '').isalnum():
                cookie_issues.append(f"Invalid domain format: {repr(domain)}")
            
            # Domain length validation
            if len(domain) > 253:  # RFC limit
                cookie_issues.append(f"Domain too long: {len(domain)} chars (max 253)")
            
            # Target domain compatibility check
            if target_domain:
                cookie_domain_clean = domain.lstrip('.')
                target_domain_clean = target_domain.lstrip('.')
                
                # Check if cookie domain matches target domain or is a valid superdomain
                domain_compatible = (
                    cookie_domain_clean == target_domain_clean or  # Exact match
                    target_domain_clean.endswith('.' + cookie_domain_clean) or  # Superdomain
                    (domain.startswith('.') and target_domain_clean.endswith(cookie_domain_clean))  # Dot prefix superdomain
                )
                
                if not domain_compatible:
                    cookie_issues.append(f"Domain mismatch: cookie domain '{domain}' incompatible with target '{target_domain}'")
                    print(f"  🚫 DOMAIN MISMATCH: {domain} vs {target_domain}", flush=True)
        
        # ===== COOKIE VALUE VALIDATION =====
        if value is not None:
            value_str = str(value)
            
            # Size validation
            if len(value_str) > 4096:  # Chrome limit
                cookie_issues.append(f"Cookie value too long: {len(value_str)} chars (max 4096)")
            
            # Character validation - check for invalid control characters
            invalid_chars = []
            for char in value_str:
                if ord(char) < 32 and char not in ['\t']:  # Allow tab, disallow other control chars
                    invalid_chars.append(f"\\x{ord(char):02x}")
                elif char in ['\n', '\r', ';']:  # Explicitly forbidden
                    invalid_chars.append(repr(char))
            
            if invalid_chars:
                cookie_issues.append(f"Invalid characters in value: {invalid_chars[:5]}...")  # Show first 5
                print(f"  🚫 INVALID VALUE CHARS: {invalid_chars[:10]}", flush=True)
        
        # CRITICAL: Playwright requires either 'url' OR 'domain+path' - validate this
        url = cookie.get('url')
        path = cookie.get('path')
        
        if not url and not (domain and path):
            cookie_issues.append("Missing required: either 'url' OR both 'domain' and 'path' must be provided")
        
        # ===== EARLY REJECTION CHECK =====
        if cookie_issues:
            print(f"❌ Cookie {i+1} REJECTED: {'; '.join(cookie_issues)}", flush=True)
            validation_issues.extend(cookie_issues)
            continue
        
        # ===== BUILD CLEAN COOKIE =====
        clean_cookie['name'] = name
        clean_cookie['value'] = str(value) if value is not None else ''
        clean_cookie['domain'] = domain
        
        # Add URL if provided (Playwright prefers this method)
        if url and isinstance(url, str):
            clean_cookie['url'] = url
            print(f"  🌐 Using URL method: {url}", flush=True)
        
        # Path - default to '/' if missing or invalid (and no URL provided)
        if not url:  # Only set path if not using URL method
            path = cookie.get('path')
            if not path or not isinstance(path, str):
                path = '/'
                print(f"  📁 Fixed path: {repr(cookie.get('path'))} → '/'", flush=True)
            elif not path.startswith('/'):
                # Path must start with /
                path = '/' + path.lstrip('/')
                print(f"  📁 Fixed path format: {repr(cookie.get('path'))} → {repr(path)}", flush=True)
            clean_cookie['path'] = path
        
        # ===== DUPLICATE DETECTION =====
        cookie_key = (clean_cookie['name'], clean_cookie['domain'], clean_cookie.get('path', '/'))
        if cookie_key in seen_cookies:
            print(f"  🚫 DUPLICATE COOKIE: {cookie_key} already exists", flush=True)
            cookie_issues.append(f"Duplicate cookie: name='{name}', domain='{domain}', path='{clean_cookie.get('path', '/')}'")
            validation_issues.extend(cookie_issues)
            continue
        seen_cookies.add(cookie_key)
        
        # ===== SAMESITE VALIDATION (Enhanced) =====
        if 'sameSite' in cookie:
            same_site = cookie['sameSite']
            valid_same_site = ['Strict', 'Lax', 'None']
            if same_site not in valid_same_site:
                print(f"  🚫 CRITICAL: Invalid sameSite value: {repr(same_site)} (must be exactly: {valid_same_site})", flush=True)
                # Fix common case issues
                if isinstance(same_site, str):
                    same_site_fixed = same_site.capitalize()
                    if same_site_fixed in valid_same_site:
                        clean_cookie['sameSite'] = same_site_fixed
                        print(f"  🔧 Fixed sameSite case: {repr(same_site)} → {repr(same_site_fixed)}", flush=True)
                    else:
                        print(f"  🚫 Cannot fix sameSite: {repr(same_site)} - skipping field", flush=True)
                        # Don't add invalid sameSite - let Playwright use default
                else:
                    print(f"  🚫 sameSite is not a string: {repr(same_site)} (type: {type(same_site)}) - skipping field", flush=True)
            else:
                clean_cookie['sameSite'] = same_site
                print(f"  ✅ Valid sameSite: {repr(same_site)}", flush=True)
        
        # ===== BOOLEAN FIELDS VALIDATION =====
        for bool_field in ['httpOnly', 'secure']:
            if bool_field in cookie:
                original_value = cookie[bool_field]
                if not isinstance(original_value, bool):
                    # Try to convert to boolean
                    try:
                        clean_value = bool(original_value)
                        clean_cookie[bool_field] = clean_value
                        print(f"  🔧 Fixed {bool_field}: {repr(original_value)} ({type(original_value)}) → {clean_value}", flush=True)
                    except Exception as e:
                        print(f"  🚫 Cannot convert {bool_field}: {repr(original_value)} - skipping field", flush=True)
                else:
                    clean_cookie[bool_field] = original_value
        
        # ===== SECURE FLAG VALIDATION =====
        if clean_cookie.get('secure', False) and target_url and not is_secure_context:
            print(f"  🚫 SECURE FLAG VIOLATION: Cookie marked secure=True but target URL is HTTP", flush=True)
            print(f"     Target: {target_url} (secure={is_secure_context})", flush=True)
            cookie_issues.append(f"Secure cookie on HTTP context: secure=True but target is {target_url}")
            validation_issues.extend(cookie_issues)
            continue
        
        # ===== REMOVE CHROME-SPECIFIC FIELDS =====
        chrome_specific_fields = ['partitionKey', 'partitioned']
        for field in chrome_specific_fields:
            if field in cookie:
                print(f"  🚫 Removed Chrome-specific field: {field} = {repr(cookie[field])}", flush=True)
        
        # ===== EXPIRES VALIDATION (Enhanced) =====
        if 'expires' in cookie:
            expires = cookie['expires']
            print(f"  ⏰ Processing expires: {repr(expires)} (type: {type(expires)})", flush=True)
            
            try:
                # Convert string numbers to integers
                if isinstance(expires, str):
                    if expires.strip() == "" or expires.lower() in ['null', 'undefined', 'none']:
                        print(f"    🚫 Invalid string expires: {repr(expires)}", flush=True)
                        # Don't add expires field - let it be a session cookie
                    else:
                        expires = float(expires)
                        print(f"    🔄 Converted string to number: {repr(cookie['expires'])} → {expires}", flush=True)
                
                # Ensure we have a number
                if isinstance(expires, (int, float)):
                    # Handle special cases
                    if expires == -1:
                        # Session cookie - explicitly allowed by Playwright
                        clean_cookie['expires'] = -1
                        print(f"    ✅ Session cookie (expires: -1)", flush=True)
                    elif expires <= 0:
                        # Zero or negative (except -1) are invalid
                        print(f"    🚫 Invalid expires (≤0, not -1): {expires}", flush=True)
                        # Don't add expires field - let it be a session cookie
                    elif expires > 9999999999999:  # More than 13 digits - likely milliseconds
                        # Convert milliseconds to seconds
                        expires_seconds = int(expires / 1000)
                        clean_cookie['expires'] = expires_seconds
                        print(f"    🔄 Converted milliseconds to seconds: {expires} → {expires_seconds}", flush=True)
                    else:
                        # Valid positive timestamp in seconds
                        clean_cookie['expires'] = int(expires)
                        print(f"    ✅ Valid expires timestamp: {int(expires)}", flush=True)
                else:
                    print(f"    🚫 Non-numeric expires after conversion: {repr(expires)}", flush=True)
                    # Don't add expires field - let it be a session cookie
                    
            except (ValueError, TypeError, OverflowError) as e:
                print(f"    🚫 Failed to process expires: {e}", flush=True)
                # Don't add expires field - let it be a session cookie
        
        # ===== SIZE ACCOUNTING =====
        cookie_size = len(clean_cookie['name']) + len(clean_cookie['value']) + len(clean_cookie['domain'])
        if clean_cookie.get('path'):
            cookie_size += len(clean_cookie['path'])
        total_cookies_size += cookie_size
        
        # Individual cookie size check
        if cookie_size > 4096:
            print(f"  🚫 COOKIE TOO LARGE: {cookie_size} bytes (max 4096)", flush=True)
            cookie_issues.append(f"Cookie too large: {cookie_size} bytes")
            validation_issues.extend(cookie_issues)
            continue
        
        # Additional debug: Show all cookie fields
        extra_fields = {k: v for k, v in cookie.items() if k not in ['name', 'value', 'domain', 'path', 'url', 'httpOnly', 'secure', 'expires', 'sameSite', 'partitionKey', 'partitioned']}
        if extra_fields:
            print(f"  📋 Extra fields ignored: {extra_fields}", flush=True)
        
        cleaned_cookies.append(clean_cookie)
        print(f"✅ Cookie {i+1} PASSED ENHANCED VALIDATION: {clean_cookie}", flush=True)
    
    # ===== FINAL SUMMARY =====
    print(f"\n🧹 ENHANCED COOKIE CLEANING SUMMARY:", flush=True)
    print(f"  - Input: {len(cookies)} cookies", flush=True)
    print(f"  - Passed validation: {len(cleaned_cookies)} cookies", flush=True)
    print(f"  - Total cookies size: {total_cookies_size} bytes", flush=True)
    print(f"  - Validation issues: {len(validation_issues)}", flush=True)
    
    if validation_issues:
        print(f"❌ Issues found:", flush=True)
        for issue in validation_issues[:10]:  # Show first 10 issues
            print(f"  - {issue}", flush=True)
        if len(validation_issues) > 10:
            print(f"  - ... and {len(validation_issues) - 10} more issues", flush=True)
    
    # ===== GLOBAL SIZE CHECK =====
    if total_cookies_size > 4096:  # Chrome header size limit
        print(f"⚠️ WARNING: Total cookie size ({total_cookies_size} bytes) exceeds 4KB limit", flush=True)
    
    print(f"\n✅ ENHANCED VALIDATION COMPLETE: {len(cleaned_cookies)} cookies ready for Playwright", flush=True)
    
    # Return in requested format
    if return_storage_state:
        # Create complete storage state object with proper structure
        storage_state = create_playwright_storage_state(
            cookies=cleaned_cookies,
            origins=[]  # Empty origins array as placeholder
        )
        print(f"📦 Returning complete storage state object", flush=True)
        return storage_state
    else:
        print(f"🍪 Returning just cleaned cookies array for backward compatibility", flush=True)
        return cleaned_cookies

async def apply_session_data_to_context(context, session_data: dict, target_url: str = None):
    """
    Apply session data (cookies, localStorage, sessionStorage) to a browser context.
    
    Args:
        context: Playwright browser context
        session_data: Dictionary containing session data
        target_url: Optional target URL for enhanced cookie validation
    """
    try:
        # Add cookies if present
        if "cookies" in session_data and session_data["cookies"]:
            print(f"🍪 Starting cookie application: {len(session_data['cookies'])} cookies in session data", flush=True)
            
            # Get cleaned cookies in storage state format for validation, but extract just cookies for add_cookies()
            storage_state = clean_cookies_for_playwright(session_data["cookies"], return_storage_state=True, target_url=target_url)
            cleaned_cookies = storage_state.get("cookies", [])
            print(f"🧹 After cleaning: {len(cleaned_cookies)} valid cookies ready for Playwright", flush=True)
            
            if cleaned_cookies:
                try:
                    print(f"🎯 Attempting to add {len(cleaned_cookies)} cookies to Playwright context...", flush=True)
                    await context.add_cookies(cleaned_cookies)
                    print(f"✅ Successfully added {len(cleaned_cookies)} cookies to Playwright context", flush=True)
                except Exception as cookie_error:
                    print(f"❌ PLAYWRIGHT COOKIE ERROR: {cookie_error}", flush=True)
                    print(f"🔍 Cookies that failed to apply:", flush=True)
                    for i, cookie in enumerate(cleaned_cookies):
                        print(f"  Cookie {i}: {cookie}", flush=True)
                    raise  # Re-raise to maintain error flow
            else:
                print(f"⚠️ No valid cookies to apply after cleaning", flush=True)
        
        # Add localStorage and sessionStorage if present
        if "origins" in session_data:
            for origin_data in session_data["origins"]:
                origin_url = origin_data.get("origin")
                if not origin_url:
                    continue
                    
                # Create a temporary page to set storage
                page = await context.new_page()
                await page.goto(origin_url)
                
                # Set localStorage
                if "localStorage" in origin_data:
                    for item in origin_data["localStorage"]:
                        await page.evaluate(
                            f"localStorage.setItem('{item['name']}', '{item['value']}')"
                        )
                
                # Set sessionStorage
                if "sessionStorage" in origin_data:
                    for item in origin_data["sessionStorage"]:
                        await page.evaluate(
                            f"sessionStorage.setItem('{item['name']}', '{item['value']}')"
                        )
                
                await page.close()
                print(f"✅ Applied storage data for origin: {origin_url}", flush=True)
                
    except Exception as e:
        print(f"⚠️ Error applying session data: {str(e)}", flush=True)

async def extract_session_data_from_context(context, url: Optional[str] = None):
    """
    Extract session data from a browser context for in-memory storage.
    
    Args:
        context: Playwright browser context
        url: Optional URL to extract target domain for cookie filtering
        
    Returns:
        Dictionary containing filtered session data in proper Playwright storage state format
    """
    try:
        # PURE IN-MEMORY: Get storage_state as dictionary directly (no file operations)
        # CRITICAL FIX: Add timeout to prevent hanging on invalid browser context
        try:
            storage_data = await asyncio.wait_for(
                context.storage_state(),  # No path parameter = returns dict directly
                timeout=15.0
            )
            
            # Apply domain-based cookie filtering if URL is provided
            if url and storage_data.get('cookies'):
                storage_data = _filter_session_data_for_performance(storage_data, url)
            
            cookies_count = len(storage_data.get('cookies', []))
            origins_count = len(storage_data.get('origins', []))
            print(f"📦 Successfully extracted {cookies_count} cookies and {origins_count} origins in-memory", flush=True)
            return storage_data
            
        except asyncio.TimeoutError:
            print("⏰ Warning: storage_state() call timed out (15s) - browser context may be invalid", flush=True)
            return {}
            
    except Exception as e:
        print(f"⚠️ Error extracting session data: {e}", flush=True)
        return {}


def _filter_session_data_for_performance(storage_data: dict, url: str) -> dict:
    """
    Filter session data to reduce size for better o3 model performance.
    Keeps only essential cookies and storage items for authentication.
    """
    from urllib.parse import urlparse
    
    # Extract target domain from URL
    parsed_url = urlparse(url)
    target_domain = parsed_url.netloc.lower()
    
    # Remove 'www.' prefix for broader matching
    if target_domain.startswith('www.'):
        target_domain = target_domain[4:]
    
    # Essential auth domains to always keep
    essential_auth_domains = {
        'google.com', 'accounts.google.com', 'googleapis.com',
        'facebook.com', 'twitter.com', 'linkedin.com', 
        'github.com', 'microsoft.com', 'apple.com'
    }
    
    # Tracking cookie patterns to remove
    tracking_patterns = {
        '_ga', '_gid', '_gat', '_gtm', '_fbp', '_fbc', '__utma', '__utmb', '__utmc', 
        '__utmz', '_hjid', '_hjFirstSeen', '_vwo_uuid', '_mkto_trk', '_biz_uid'
    }
    
    original_cookie_count = len(storage_data.get('cookies', []))
    filtered_cookies = []
    
    for cookie in storage_data.get('cookies', []):
        cookie_domain = cookie.get('domain', '').lower()
        cookie_name = cookie.get('name', '')
        
        # Remove leading dot from domain for comparison
        if cookie_domain.startswith('.'):
            cookie_domain = cookie_domain[1:]
        
        # Keep cookie if it matches target domain
        if target_domain in cookie_domain or cookie_domain in target_domain:
            # Apply value size limiting before adding
            _apply_cookie_value_size_limit(cookie)
            filtered_cookies.append(cookie)
            continue
            
        # Keep cookie if it's from essential auth domain
        if any(auth_domain in cookie_domain for auth_domain in essential_auth_domains):
            # Apply value size limiting before adding
            _apply_cookie_value_size_limit(cookie)
            filtered_cookies.append(cookie)
            continue
            
        # Skip tracking cookies
        if any(pattern in cookie_name.lower() for pattern in tracking_patterns):
            continue
            
        # Keep other potentially important cookies (session, auth, login related)
        important_keywords = ['session', 'auth', 'login', 'token', 'csrf', 'xsrf']
        if any(keyword in cookie_name.lower() for keyword in important_keywords):
            # Apply value size limiting before adding
            _apply_cookie_value_size_limit(cookie)
            filtered_cookies.append(cookie)

    # Update storage data with filtered cookies
    storage_data['cookies'] = filtered_cookies
    
    # Filter storage data (localStorage/sessionStorage) for performance
    if storage_data.get('origins'):
        storage_data['origins'] = _filter_storage_origins(storage_data['origins'])
    
    # Log filtering results if significant reduction
    if original_cookie_count - len(filtered_cookies) > 5:
        print(f"🔽 Filtered session: {original_cookie_count}→{len(filtered_cookies)} cookies", flush=True)
    
    return storage_data


def _filter_storage_origins(origins: list) -> list:
    """
    Filter localStorage and sessionStorage items to keep only auth-related data.
    """
    # Auth-related storage key patterns to keep
    auth_storage_keywords = {
        'token', 'auth', 'session', 'login', 'user', 'csrf', 'xsrf', 
        'oauth', 'jwt', 'access', 'refresh', 'credential', 'identity'
    }
    
    # Analytics/tracking patterns to remove
    tracking_storage_patterns = {
        '_ga', '_gid', '_gat', '_gtm', '_fb', '_hjid', '_vwo', '_mkto',
        'analytics', 'tracking', 'amplitude', 'mixpanel', 'segment'
    }
    
    filtered_origins = []
    
    for origin in origins:
        if not isinstance(origin, dict):
            continue
            
        # Filter localStorage items
        if 'localStorage' in origin:
            filtered_local_storage = []
            for item in origin['localStorage']:
                if not isinstance(item, dict) or 'name' not in item:
                    continue
                    
                key_name = item['name'].lower()
                
                # Keep auth-related items
                if any(keyword in key_name for keyword in auth_storage_keywords):
                    filtered_local_storage.append(item)
                    continue
                    
                # Skip tracking items
                if any(pattern in key_name for pattern in tracking_storage_patterns):
                    continue
                    
                # Keep if unclear but potentially important (short keys often are)
                if len(key_name) <= 10:
                    filtered_local_storage.append(item)
            
            origin['localStorage'] = filtered_local_storage
        
        # Filter sessionStorage items with same logic
        if 'sessionStorage' in origin:
            filtered_session_storage = []
            for item in origin['sessionStorage']:
                if not isinstance(item, dict) or 'name' not in item:
                    continue
                    
                key_name = item['name'].lower()
                
                # Keep auth-related items
                if any(keyword in key_name for keyword in auth_storage_keywords):
                    filtered_session_storage.append(item)
                    continue
                    
                # Skip tracking items
                if any(pattern in key_name for pattern in tracking_storage_patterns):
                    continue
                    
                # Keep if unclear but potentially important (short keys often are)
                if len(key_name) <= 10:
                    filtered_session_storage.append(item)
            
            origin['sessionStorage'] = filtered_session_storage
        
        # Only include origin if it has some storage data left
        if (origin.get('localStorage') or origin.get('sessionStorage') or 
            origin.get('indexedDB') or origin.get('webSQL')):
            filtered_origins.append(origin)
    
    return filtered_origins


def _apply_cookie_value_size_limit(cookie: dict, max_length: int = 200):
    """
    Truncate cookie value if it exceeds max_length to prevent response bloating.
    Auth cookies are typically short; massive values are usually tracking data.
    """
    value = cookie.get('value', '')
    if len(value) > max_length:
        cookie['value'] = value[:max_length] + '...[truncated]'

def get_session_info_enhanced(
    url: str,
    storage_state_path: Optional[str] = None,
    user_data_dir: Optional[str] = None,
    session_data: Optional[dict] = None
) -> tuple[str | None, dict | None]:
    """
    Enhanced session info helper that handles both file-based and in-memory session data.
    NOW FOCUSES ON PURE IN-MEMORY SESSION MANAGEMENT - no persistent directories created.
    
    Args:
        url: The URL to derive the session domain from (used for logging only).
        storage_state_path: An explicitly provided path to a session file (legacy support).
        user_data_dir: DEPRECATED - no longer used, kept for API compatibility.
        session_data: In-memory session data dictionary (PREFERRED METHOD).
    
    Returns:
        A tuple containing:
        - The path to the storage_state.json file (or None if using session_data).
        - The session data dictionary (or None if using file path).
    """
    
    # Priority 1: Use in-memory session_data if provided (PREFERRED)
    if session_data:
        print("✅ Using in-memory session data", flush=True)
        return None, session_data
    
    # Priority 2: Use explicitly provided storage_state_path if it exists (legacy support)
    if storage_state_path and os.path.exists(storage_state_path):
        print(f"✅ Using explicitly provided session file: {storage_state_path}", flush=True)
        return storage_state_path, None
        
    # Priority 3: No session found
    print("⚠️ No existing session found. Proceeding with a fresh session.", flush=True)
    return None, None
    

# --- Vision-Based Paywall Detection ---
async def analyze_screenshot_for_paywall(screenshot_base64: str, url: str) -> dict:
    """
    Analyze a screenshot using GPT-4o to detect paywall indicators.
    
    Args:
        screenshot_base64: Base64 encoded screenshot from Crawl4AI
        url: The URL being analyzed (for context)
    
    Returns:
        Dict with paywall detection results
    """
    # Check if any client was successfully initialized
    if not client or not model_to_use:
        return {
            "paywall_detected": False,
            "confidence": 0,
            "method": "vision_analysis",
            "error": "OpenAI client not configured. Check environment variables for Azure or OpenAI."
        }
    
    try:
        # Debug: Check screenshot format
        print(f"📸 Screenshot debug info:", flush=True)
        print(f"   - Base64 length: {len(screenshot_base64)}", flush=True)
        print(f"   - First 50 chars: {screenshot_base64[:50]}", flush=True)
        
        # Validate base64 and try to detect format
        import base64
        try:
            decoded_data = base64.b64decode(screenshot_base64)
            print(f"   - Decoded size: {len(decoded_data)} bytes", flush=True)
            
            # Check PNG magic bytes
            if decoded_data.startswith(b'\x89\x50\x4E\x47'):
                image_format = "png"
                print(f"   - Detected format: PNG ✓", flush=True)
                final_base64 = screenshot_base64  # Use as-is
            elif decoded_data.startswith(b'\xFF\xD8\xFF'):
                image_format = "jpeg"
                print(f"   - Detected format: JPEG ✓", flush=True)
                final_base64 = screenshot_base64  # Use as-is
            elif decoded_data.startswith(b'GIF8'):
                image_format = "gif"
                print(f"   - Detected format: GIF ✓", flush=True)
                final_base64 = screenshot_base64  # Use as-is
            elif decoded_data.startswith(b'RIFF') and b'WEBP' in decoded_data[:12]:
                image_format = "webp"
                print(f"   - Detected format: WEBP ✓", flush=True)
                final_base64 = screenshot_base64  # Use as-is
            elif decoded_data.startswith(b'BM'):
                print(f"   - Detected format: BMP (converting to PNG for OpenAI)", flush=True)
                # Convert BMP to PNG
                try:
                    
                    # Load BMP from bytes
                    bmp_image = Image.open(io.BytesIO(decoded_data))
                    
                    # Convert to PNG
                    png_buffer = io.BytesIO()
                    bmp_image.save(png_buffer, format='PNG')
                    png_data = png_buffer.getvalue()
                    
                    # Encode back to base64
                    final_base64 = base64.b64encode(png_data).decode('utf-8')
                    image_format = "png"
                    
                    print(f"   - BMP converted to PNG: {len(png_data)} bytes", flush=True)
                    
                except ImportError:
                    return {
                        "paywall_detected": False,
                        "confidence": 0,
                        "method": "vision_analysis",
                        "error": "BMP format detected but PIL/Pillow not available for conversion. Install with: pip install Pillow"
                    }
                except Exception as conversion_error:
                    return {
                        "paywall_detected": False,
                        "confidence": 0,
                        "method": "vision_analysis",
                        "error": f"BMP to PNG conversion failed: {str(conversion_error)}"
                    }
            else:
                print(f"   - Unknown format, first 20 bytes: {decoded_data[:20]}", flush=True)
                return {
                    "paywall_detected": False,
                    "confidence": 0,
                    "method": "vision_analysis",
                    "error": f"Unsupported image format. OpenAI requires PNG, JPEG, GIF, or WEBP."
                }
                
        except Exception as decode_error:
            print(f"   - Base64 decode error: {decode_error}", flush=True)
            return {
                "paywall_detected": False,
                "confidence": 0,
                "method": "vision_analysis",
                "error": f"Invalid base64 screenshot data: {str(decode_error)}"
            }
        
        # The client is now initialized at the module level
        
        # Create the vision analysis prompt
        vision_prompt = f"""
Analyze this webpage screenshot for paywall indicators. The URL is: {url}

Look for these paywall signs, note that the webpages can be in languages other than English:
1. **Modal overlays** - Popup windows blocking content with subscription prompts
2. **Blurred/faded content** - Text or articles that are intentionally obscured
3. **Member-only indicators** - Text like "Member-only story", "Premium content", "Subscribers only"
4. **Login gates** - Forms or buttons forcing user authentication to continue reading
5. **Content truncation** - Articles cut off with "Continue reading" or "Read more" prompts
6. **Upgrade prompts** - Messages about reaching article limits or needing premium access

The most probable indicator of a paywall is if the full content is not visible.

Return your analysis as JSON in this exact format:
{{
    "paywall_detected": true/false,
    "confidence": 0-100,
    "indicators": ["list", "of", "detected", "elements"],
    "description": "Brief explanation of what you see"
}}

Be very specific about what paywall elements you detect, if any.
"""

        response = await client.chat.completions.create(
            model=model_to_use,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": vision_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{image_format};base64,{final_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.1  # Low temperature for consistent analysis
        )
        
        # Parse the JSON response
        import json
        analysis_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON from the response
        try:
            # Look for JSON in the response
            start_idx = analysis_text.find('{')
            end_idx = analysis_text.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = analysis_text[start_idx:end_idx]
                analysis = json.loads(json_str)
            else:
                # Fallback if no JSON found
                analysis = {
                    "paywall_detected": "paywall" in analysis_text.lower() or "subscription" in analysis_text.lower(),
                    "confidence": 50,
                    "indicators": ["text_analysis"],
                    "description": analysis_text[:200]
                }
        except json.JSONDecodeError:
            # Fallback parsing
            paywall_keywords = ["paywall", "subscribe", "member-only", "premium", "sign up", "upgrade"]
            detected = any(keyword in analysis_text.lower() for keyword in paywall_keywords)
            analysis = {
                "paywall_detected": detected,
                "confidence": 70 if detected else 30,
                "indicators": ["keyword_fallback"],
                "description": analysis_text[:200]
            }
        
        analysis["method"] = "vision_analysis"
        analysis["model"] = "gpt-4o"
        return analysis
        
    except Exception as e:
        return {
            "paywall_detected": False,
            "confidence": 0,
            "method": "vision_analysis",
            "error": f"Vision analysis failed: {str(e)}",
            "model": "gpt-4o"
        }

def _is_paywall_present(
    keyword_detected: bool,
    vision_analysis: Optional[dict],
    raw_content: str,
    content_length_threshold: int = 2000
) -> tuple[bool, str, dict]:
    """
    Determines if a paywall is present using a combination of keyword, vision, and content length analysis.
    
    Args:
        keyword_detected: Whether keywords like "subscribe" were found.
        vision_analysis: The result from the GPT-4o vision analysis.
        raw_content: The scraped markdown content.
        content_length_threshold: The character count above which content is considered "substantial".
        
    Returns:
        A tuple of (is_paywall, reason_string, updated_vision_analysis).
    """
    vision_detected = vision_analysis.get("paywall_detected", False) if vision_analysis else False
    content_length = len(raw_content)
    
    final_decision = False
    reason = ""

    # Case 1: Vision model is confident there's a paywall. Trust it.
    if vision_detected and vision_analysis.get("confidence", 0) > 60:
        final_decision = True
        reason = "Vision analysis detected a high-confidence paywall."

    # Case 2: Keywords are detected, but vision is not (or has low confidence).
    # This is the ambiguous case (e.g., footer banners). Use content length as a tie-breaker.
    elif keyword_detected and not vision_detected:
        if content_length > content_length_threshold:
            reason = (
                f"False positive: Keywords detected, but vision analysis did not find a paywall "
                f"and content length ({content_length}) exceeds threshold ({content_length_threshold})."
            )
            final_decision = False
        else:
            reason = (
                f"Paywall confirmed: Keywords detected and content length ({content_length}) "
                f"is below threshold ({content_length_threshold})."
            )
            final_decision = True

    # Case 3: Only vision detected a paywall, but with low confidence.
    elif vision_detected and not keyword_detected:
        if content_length > content_length_threshold:
             reason = (
                f"False positive: Low-confidence vision detection, but content length ({content_length}) "
                f"exceeds threshold ({content_length_threshold})."
            )
             final_decision = False
        else:
            reason = (
                f"Paywall confirmed: Low-confidence vision detection is supported by "
                f"low content length ({content_length})."
            )
            final_decision = True

    # Case 4: Both methods agree there is no paywall.
    elif not keyword_detected and not vision_detected:
        final_decision = False
        reason = "Neither keyword nor vision analysis detected a paywall."
        
    # Default fallback
    else:
        final_decision = keyword_detected or vision_detected
        reason = "Default determination based on keyword or vision detection."

    print(f"🕵️  Paywall decision: {final_decision}. Reason: {reason}", flush=True)
    
    # Update vision analysis to reflect the final decision
    if vision_analysis:
        vision_analysis["final_decision"] = final_decision
        vision_analysis["decision_reason"] = reason
    
    return final_decision, reason, vision_analysis