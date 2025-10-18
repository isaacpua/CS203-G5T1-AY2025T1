import os
import re
from openai import AzureOpenAI
from dotenv import load_dotenv
import urllib.parse

# Load environment variables
load_dotenv()

# =============================================================================
# ENVIRONMENT CONFIGURATION - GPT-4 FOR FORMATTING ONLY
# =============================================================================
# This service uses SEPARATE credentials from the main Jarvis agent:
# - Main Jarvis Agent: Uses GPTO3_MINI_* (O3-mini reasoning model)
# - Content Formatter: Uses GPT4O_* (GPT-4 for reliable long content formatting)
# =============================================================================

def validate_formatting_environment() -> tuple[bool, str]:
    """
    Validate that all required GPT-4 environment variables are present.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    required_vars = {
        "GPT4O_API_BASE": "Azure OpenAI endpoint",
        "GPT4O_API_KEY": "Azure OpenAI API key", 
        "GPT4O_API_VERSION": "Azure OpenAI API version",
        "GPT4O_DEPLOYMENT_NAME": "GPT-4 deployment name"
    }
    
    missing_vars = []
    for var_name, description in required_vars.items():
        if not os.getenv(var_name):
            missing_vars.append(f"{var_name} ({description})")
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        return False, error_msg
    
    return True, "All formatting environment variables present"

def initialize_formatting_client():
    """
    Initialize the dedicated GPT-4 client for content formatting.
    Separate from main Jarvis agent configuration.
    
    Returns:
        tuple: (client, model_name) or (None, None) if initialization fails
    """
    # Validate environment first
    is_valid, validation_message = validate_formatting_environment()
    if not is_valid:
        print(f"❌ Environment validation failed: {validation_message}")
        print("🔧 Required environment variables for formatting:")
        print("   - GPT4O_API_BASE (Azure endpoint)")
        print("   - GPT4O_API_KEY (API key)")
        print("   - GPT4O_API_VERSION (API version)")
        print("   - GPT4O_DEPLOYMENT_NAME (GPT-4 deployment)")
        return None, None
    
    # Extract environment variables
    azure_endpoint = os.getenv("GPT4O_API_BASE")
    azure_api_key = os.getenv("GPT4O_API_KEY")
    azure_api_version = os.getenv("GPT4O_API_VERSION")
    azure_deployment = os.getenv("GPT4O_DEPLOYMENT_NAME")
    
    try:
        # Initialize Azure OpenAI client
        
        # Initialize Azure OpenAI client  
        client = AzureOpenAI(
            api_key=azure_api_key,
            api_version=azure_api_version,
            azure_endpoint=azure_endpoint
        )
        
        return client, azure_deployment
        
    except Exception as e:
        print(f"❌ Failed to initialize Azure OpenAI client: {e}")
        print("🔧 Check your GPT4O_* environment variables")
        return None, None

# Initialize the formatting client
client, model_to_use = initialize_formatting_client()

# Initialize content formatter

def get_configuration_status() -> dict:
    """
    Get the current configuration status for monitoring and debugging.
    
    Returns:
        dict: Configuration status information
    """
    main_agent_vars = {
        "GPTO3_MINI_API_BASE": os.getenv("GPTO3_MINI_API_BASE"),
        "GPTO3_MINI_DEPLOYMENT_NAME": os.getenv("GPTO3_MINI_DEPLOYMENT_NAME")
    }
    
    formatter_vars = {
        "GPT4O_API_BASE": os.getenv("GPT4O_API_BASE"), 
        "GPT4O_DEPLOYMENT_NAME": os.getenv("GPT4O_DEPLOYMENT_NAME")
    }
    
    return {
        "formatting_service": {
            "client_initialized": client is not None,
            "model": model_to_use,
            "purpose": "Long content formatting (GPT-4)",
            "environment_vars": {k: "✅ Set" if v else "❌ Missing" for k, v in formatter_vars.items()}
        },
        "main_agent": {
            "model_type": "O3-mini (reasoning model)",
            "purpose": "Main conversational agent",
            "environment_vars": {k: "✅ Set" if v else "❌ Missing" for k, v in main_agent_vars.items()}
        },
        "separation_status": "✅ Proper separation maintained" if client and main_agent_vars["GPTO3_MINI_DEPLOYMENT_NAME"] else "⚠️ Check configuration"
    }

def print_configuration_summary():
    """Print a summary of the current configuration for debugging."""
    status = get_configuration_status()
    
    print("\n" + "="*60)
    print("SERVICE CONFIGURATION SUMMARY")
    print("="*60)
    
    print(f"🤖 MAIN JARVIS AGENT:")
    print(f"   Model: {status['main_agent']['model_type']}")
    print(f"   Purpose: {status['main_agent']['purpose']}")
    for var, status_text in status['main_agent']['environment_vars'].items():
        print(f"   {var}: {status_text}")
    
    print(f"\n📝 CONTENT FORMATTER:")
    print(f"   Model: {status['formatting_service']['model']}")
    print(f"   Purpose: {status['formatting_service']['purpose']}")
    print(f"   Client Ready: {'✅ Yes' if status['formatting_service']['client_initialized'] else '❌ No'}")
    for var, status_text in status['formatting_service']['environment_vars'].items():
        print(f"   {var}: {status_text}")
    
    print(f"\n🔀 SEPARATION STATUS: {status['separation_status']}")
    print("="*60 + "\n")

def validate_image_url(url: str) -> tuple[bool, str]:
    """
    Validate if an image URL is accessible and well-formed.
    
    Args:
        url: The image URL to validate
        
    Returns:
        tuple: (is_valid, reason)
    """
    if not url or url.strip() == "":
        return False, "Empty URL"
    
    # Check if it's a relative URL
    if url.startswith('/'):
        return False, "Relative URL (needs domain)"
    
    # Check if it's a data URL
    if url.startswith('data:'):
        return True, "Data URL (embedded)"
    
    # Check if it has a valid scheme
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme or parsed.scheme not in ['http', 'https']:
        return False, f"Invalid scheme: {parsed.scheme}"
    
    # Check if it has a domain
    if not parsed.netloc:
        return False, "No domain"
    
    return True, "Valid URL format"

def estimate_token_count(text: str) -> int:
    """
    Rough estimation of token count for input text.
    Using conservative estimate: 1 token ≈ 4 characters
    """
    return len(text) // 4

def validate_html_completeness(html_content: str, original_length: int) -> bool:
    """
    Check if the formatted HTML appears to be complete and not truncated.
    
    Args:
        html_content: The formatted HTML content
        original_length: Length of original markdown content
        
    Returns:
        bool: True if content appears complete, False if likely truncated
    """
    if not html_content or html_content.strip() == "":
        return False
    
    # Check for abrupt endings (common truncation patterns)
    content_lower = html_content.lower().strip()
    
    # Truncation indicators
    truncation_indicators = [
        "the content was cut off",
        "content truncated",
        "due to length limits",
        "...and more",
        # Check if ends mid-sentence (no proper punctuation)
    ]
    
    for indicator in truncation_indicators:
        if indicator in content_lower:
            return False
    
    # Check if content is suspiciously short compared to original
    if len(html_content) < (original_length * 0.3):  # Less than 30% of original length
        return False
    
    # Check for proper HTML structure (should have opening and closing tags)
    if html_content.count('<') != html_content.count('>'):
        return False
    
    # Check if ends abruptly without punctuation
    last_text = re.sub(r'<[^>]+>', '', html_content.strip())
    if last_text and not last_text[-1] in '.!?。！？':
        # Could be truncated mid-sentence
        return False
    
    return True

def verify_formatting_configuration() -> bool:
    """
    Verify that the formatting service is properly configured and ready to use.
    
    Returns:
        bool: True if ready, False if configuration issues exist
    """
    status = get_configuration_status()
    
    if not status['formatting_service']['client_initialized']:
        print("❌ Content formatter client not initialized")
        print_configuration_summary()
        return False
    
    if status['separation_status'].startswith("⚠️"):
        print("⚠️ Configuration separation issues detected")
        print_configuration_summary()
        return False
    
    print("✅ Content formatting service ready")
    return True

async def format_scraped_content_for_display(scraped_content: dict) -> str:
    """
    Formats scraped content using Azure OpenAI GPT-4 to create clean HTML.
    
    Args:
        scraped_content: Dictionary containing scraped content from MCP tools
                        Expected structure: {
                            "content": {
                                "main_text_markdown": str,
                                "metadata": dict
                            }
                        }
    
    Returns:
        str: Formatted HTML content ready for popup and PDF display
    """
    if not client or not model_to_use:
        print("❌ Content Formatter: Azure OpenAI client not initialized")
        print_configuration_summary()
        raise RuntimeError("Content formatting service not properly configured. Check GPT4O_* environment variables.")
    
    # Extract content from MCP tool response
    if not scraped_content or "content" not in scraped_content:
        raise ValueError("Invalid scraped content structure - missing 'content' field")
    
    content_data = scraped_content["content"]
    markdown_text = content_data.get("main_text_markdown", "")
    metadata = content_data.get("metadata", {})
    
    if not markdown_text or markdown_text.strip() == "":
        raise ValueError("No markdown content found to format")
    
    # Extract author from metadata and source URL from main response
    author = metadata.get("author") if metadata else None
    source_url = scraped_content.get("url", "")
    
    # Quick debug: Check for images in input
    image_matches_input = re.findall(r'!\[(.*?)\]\((.*?)\)', markdown_text)
    image_count_input = len(image_matches_input)
    print(f"Content Formatter: Found {image_count_input} images in input markdown")
    if image_matches_input:
        print("Content Formatter: Input image URLs:")
        for i, (alt, url) in enumerate(image_matches_input[:3]):  # Show first 3
            print(f"  {i+1}. ALT: '{alt}' URL: '{url}'")
    
    # Estimate token count for input
    estimated_tokens = estimate_token_count(markdown_text)
    print(f"Content Formatter: Processing content (~{estimated_tokens} tokens)")
    
    # For now, process as single chunk (Task 4 will add chunking for very long content)
    if estimated_tokens > 12000:  # Conservative limit for 16K context
        print(f"Content Formatter: Warning - Content may be too long ({estimated_tokens} tokens), but proceeding...")
    
    try:
        # Simplified system prompt based on working reference
        system_prompt = """You are an expert content extractor and HTML formatter. Your task is to take the raw markdown from a webpage and isolate ONLY the main article content, then convert it to clean HTML.

**Primary Goal:** Extract the core article—the main text, its headings, and any embedded media.

**Exclusion Criteria (What to REMOVE):**
- Site headers, top navigation bars, and menus (e.g., 'Home', 'Log In', 'Subscribe').
- Sidebars with related links or ads.
- Footers, copyright notices, legal disclaimers, and app download links.
- "Related Articles", "Read More", or "Recommended for You" sections.
- Social media sharing buttons and comment sections.
- "Loading" indicators or video player controls that are rendered as text.

**Formatting Instructions:**
1. **Author and Date**: At the very top of the article, add a small, grayed-out `div` for the author and publication date.
   - If an author is provided in the input, use it.
   - Search the text for the author and publication date. These might be in English, Chinese, Malay, or Tamil.
   - **Localize the output format.** You MUST determine the language of the article and use the appropriate labels. For example:
       - English: `<div>Author: [Author Name] | Date: [Date]</div>`
       - Chinese: `<div>作者: [Author Name] | 日期: [Date]</div>`
       - Malay: `<div>Pengarang: [Author Name] | Tarikh: [Date]</div>`
       - Tamil: `<div>ஆசிரியர்: [Author Name] | தேதி: [Date]</div>`
   - If no author or date can be found, omit that part of the `div`.
2. **Convert Markdown**: Convert markdown elements (headings, lists, bold, italics, links, images) to their proper HTML tags.
   - **For images specifically**: Wrap each image in a centering container like this: `<div style="text-align: center; margin: 20px 0;"><img src="..." alt="..." style="max-width: 100%; height: auto;"></div>`
3. **DO NOT alter or summarize the main article text.**
4. Return ONLY the clean HTML for the main article, starting with your author/date div. Do not include `<html>` or `<body>` tags.
5. **Crucially, your response must be only the raw HTML content. Do not wrap it in markdown code fences (like ```html) or add any explanatory text before or after the HTML.**

**CRITICAL: Preserve ALL images and media. Never remove or skip image references.**"""

        # Make the API call with explicit token limits and temperature
        response = client.chat.completions.create(
            model=model_to_use,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": f"""Please extract the main article from the following markdown and convert it to clean HTML.
                    
                    Source URL: {source_url if source_url else 'Not provided'}
                    Author from metadata: {author if author else 'Not provided'}

                    ---

                    Markdown Content:
                    {markdown_text}
                    """
                }
            ],
            max_tokens=4000,  # Explicit output limit to prevent truncation
            temperature=0.0   # Deterministic formatting
        )
        
        formatted_content = response.choices[0].message.content

        # Validate the response
        if not formatted_content or formatted_content.strip() == "" or formatted_content.strip() == "None":
            raise ValueError("LLM returned empty or None content")
        
        # Quick debug: Check if LLM preserved images
        image_matches_output = re.findall(r'!\[(.*?)\]\((.*?)\)', formatted_content)
        html_img_matches_llm = re.findall(r'<img[^>]+src="([^"]+)"[^>]*>', formatted_content)
        image_count_output = len(image_matches_output)
        html_img_count_llm = len(html_img_matches_llm)
        
        print(f"Content Formatter: LLM output has {image_count_output} markdown images + {html_img_count_llm} HTML img tags")
        
        if image_matches_output:
            print("Content Formatter: LLM output markdown image URLs:")
            for i, (alt, url) in enumerate(image_matches_output[:3]):  # Show first 3
                print(f"  {i+1}. ALT: '{alt}' URL: '{url}'")
        
        if html_img_matches_llm:
            print("Content Formatter: ✅ LLM correctly converted images to HTML format")
        elif image_count_input > 0:
            print("Content Formatter: ⚠️ WARNING: LLM removed all images during processing!")
        
        # Validate completeness
        if not validate_html_completeness(formatted_content, len(markdown_text)):
            print("Content Formatter: Warning - Content may be truncated or incomplete")
            # For now, continue with the content; Task 4 will add chunking fallback
        
        # Simple, proven post-processing approach (based on working reference)
        
        # Fix images FIRST - with proper sizing for popup display
        formatted_content = re.sub(
            r'!\[(.*?)\]\((.*?)\)', 
            r'<div style="text-align: center; margin: 20px 0;"><img src="\2" alt="\1" style="max-width: 100%; max-height: 400px; height: auto; width: auto; object-fit: contain; border-radius: 4px;" /></div>', 
            formatted_content
        )
        
        # Debug: Check final HTML img tags
        html_img_matches = re.findall(r'<img src="([^"]+)"[^>]*>', formatted_content)
        print(f"Content Formatter: Final HTML has {len(html_img_matches)} img tags")
        if html_img_matches:
            print("Content Formatter: Final image src URLs:")
            for i, src in enumerate(html_img_matches[:3]):  # Show first 3
                is_valid, reason = validate_image_url(src)
                status = "✅ VALID" if is_valid else f"❌ INVALID ({reason})"
                print(f"  {i+1}. SRC: '{src}' - {status}")
        elif image_count_input > 0:
            print("Content Formatter: ⚠️ WARNING: All images were lost during processing!")
        
        # Fix relative image URLs using source URL
        if source_url:
            formatted_content = fix_relative_image_urls(formatted_content, source_url)
            print("Content Formatter: Fixed relative image URLs using source URL")
            
            # Re-check final URLs after fixing
            fixed_img_matches = re.findall(r'<img src="([^"]+)"[^>]*>', formatted_content)
            if len(fixed_img_matches) != len(html_img_matches):
                print(f"Content Formatter: Image count changed after URL fixing: {len(html_img_matches)} → {len(fixed_img_matches)}")
        
        # Fix headers
        formatted_content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', formatted_content, flags=re.MULTILINE)
        formatted_content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', formatted_content, flags=re.MULTILINE)
        formatted_content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', formatted_content, flags=re.MULTILINE)
        
        # Fix bold text
        formatted_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted_content)
        
        # Fix links
        formatted_content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', formatted_content)
        
        # Wrap content in clean structure (like working reference)
        formatted_content = f"""
        <div class="content-container">
            <div class="article-content">
                {formatted_content}
            </div>
        </div>
        """
        
        # Add source URL at the very top
        if source_url:
            source_div = f'<div style="font-size: 12px; color: #666; margin-bottom: 16px; border-bottom: 1px solid #eee; padding-bottom: 8px;"><strong>Source:</strong> <a href="{source_url}" target="_blank" style="color: #0066cc; text-decoration: none;">{source_url}</a></div>'
            formatted_content = source_div + '\n' + formatted_content

        print(f"Content Formatter: Successfully formatted content ({len(formatted_content)} characters)")
        
        # DEBUG: Print full HTML content for debugging popup display issues
        print("="*80)
        print("FULL HTML CONTENT BEING SENT TO POPUP:")
        print("="*80)
        print(formatted_content)
        print("="*80)
        print("END OF HTML CONTENT")
        print("="*80)
        
        return formatted_content
        
    except Exception as e:
        print(f"Content Formatter: Error during formatting: {e}")
        raise RuntimeError(f"Failed to format content: {str(e)}") 

def fix_relative_image_urls(content: str, base_url: str) -> str:
    """
    Convert relative image URLs to absolute URLs.
    
    Args:
        content: HTML content with img tags
        base_url: Base URL of the source page
        
    Returns:
        str: Content with fixed absolute URLs
    """
    if not base_url:
        return content
    
    def fix_src(match):
        full_tag = match.group(0)
        src = match.group(1)
        
        # Skip if already absolute URL or data URL
        if src.startswith(('http://', 'https://', 'data:')):
            return full_tag
        
        # Convert relative URL to absolute
        try:
            absolute_url = urllib.parse.urljoin(base_url, src)
            return full_tag.replace(f'src="{src}"', f'src="{absolute_url}"')
        except Exception:
            return full_tag
    
    # Fix all img src attributes
    content = re.sub(r'<img src="([^"]+)"([^>]*>)', fix_src, content)
    return content 