"""
Platform-specific SOP (Standard Operating Procedure) instructions.

Provides WHERE+HOW templates for each platform and content type.
Operators use these as step-by-step guides.
"""

from typing import Dict, Tuple


# ============================================================================
# LinkedIn SOPs
# ============================================================================

LINKEDIN_POST_SOP = """
WHERE TO POST:
1. Go to linkedin.com (logged into your business account)
2. Click "Start a post" in the top left of your feed
3. Select "Share a link" or paste into the text area

HOW TO POST:
1. Copy your pre-written text into the post box
2. Add any hashtags at the end (e.g., #industryname #hiring)
3. Add a link if provided, or upload an image
4. Click "Post" button

FORMATTING TIPS:
- Use line breaks to make content readable
- Put CTAs (Call-To-Action) at the bottom
- Optimal length: 150-250 characters
- Best time to post: 8-10am weekdays, 12-1pm lunch time

COMMON MISTAKES:
- ❌ Forgetting hashtags (reduces reach)
- ❌ Posting too many links (LinkedIn penalizes)
- ❌ Very long walls of text (break into paragraphs)
- ❌ Posting during night hours (low engagement)

COMPLETION:
- Screenshot the "Your post has been shared" notification
- Or paste the post URL in the completion proof field
"""

LINKEDIN_CAROUSEL_SOP = """
WHERE TO POST:
1. Go to linkedin.com (logged into your business account)
2. Click "Start a post" in the top left
3. Click "Add document" or image upload icon
4. Upload images for carousel (1-10 slides)

HOW TO POST:
1. Upload 2-10 images in order
2. Add captions to each slide if needed
3. Add main post caption with CTA
4. Review order of carousel slides
5. Click "Post" button

CAROUSEL TIPS:
- Use consistent branding/colors across slides
- Slide 1 is the "hook" - most important!
- Keep text minimal, images engaging
- Each slide should add value
- Call-to-action on last slide recommended

COMPLETION:
- Copy the post URL after posting
- Paste in completion proof field
"""

LINKEDIN_THREAD_SOP = """
WHERE TO POST:
1. Go to linkedin.com
2. Click "Start a post"
3. Type first message, then click "Add to your post"

HOW TO POST:
1. Write first tweet (120 chars)
2. Click "Add to your post" to add reply
3. Type second tweet
4. Repeat for 3-5 tweets total
5. Click "Post" to publish thread

THREAD TIPS:
- Structure: Hook → Point 1 → Point 2 → CTA
- Each tweet should be self-contained
- Use numbering: "1/" "2/" "3/" etc.
- Last tweet should have CTA or link

COMPLETION:
- Copy thread URL
- Paste in completion proof field
"""


# ============================================================================
# Instagram SOPs
# ============================================================================

INSTAGRAM_POST_SOP = """
WHERE TO POST:
1. Open Instagram app or go to instagram.com
2. Click "Create" (+ icon at bottom)
3. Select "Post"

HOW TO POST:
1. Upload image from gallery (or take photo)
2. Apply filters/edit if needed
3. Click "Next" → "Next"
4. Add caption (copy provided)
5. Add location if relevant
6. Add hashtags
7. Click "Share"

CAPTION TIPS:
- Start with emoji (catches attention)
- Hook in first 3 words
- Put CTA at the end
- 5-30 hashtags (mix popular + niche)
- Use line breaks for readability

CONTENT MISTAKES:
- ❌ No hashtags (kills reach)
- ❌ Poor image quality
- ❌ Generic captions
- ❌ Call-to-action buried in text

COMPLETION:
- Screenshot the post (showing likes/comments area)
- Or paste the post URL
"""

INSTAGRAM_REEL_SOP = """
WHERE TO POST:
1. Open Instagram app
2. Click "Create" (+ icon)
3. Select "Reels"

HOW TO POST:
1. Record video (15-90 seconds) OR upload video file
2. Add music/audio from Instagram library
3. Add text overlays/stickers (optional)
4. Use effects if needed
5. Click "Next"
6. Add caption, hashtags, location
7. Click "Share"

REEL BEST PRACTICES:
- First 1 second = critical (hook viewer)
- Vertical video (9:16 aspect ratio)
- Use trending music/sounds
- Bold text overlays (+title, CTA)
- Include CTA at end of video

COMPLETION:
- Screenshot the reel
- Or paste reel URL from your profile
"""

INSTAGRAM_CAROUSEL_SOP = """
WHERE TO POST:
1. Open Instagram app
2. Click "Create"
3. Select "Post"
4. Choose "Multiple" after uploading first image

HOW TO POST:
1. Upload first image
2. Click "+" to add more images (up to 10)
3. Drag to reorder if needed
4. Click "Next"
5. Edit each slide (filter, brightness) OR use one filter for all
6. Click "Next" again
7. Add caption with CTA
8. Add hashtags
9. Click "Share"

CAROUSEL TIPS:
- Slide 1: Strong visual (grabs attention)
- Slide 2-8: Value/education
- Last slide: CTA + link in bio note
- Use text overlays for emphasis

COMPLETION:
- Screenshot carousel post
- Or paste post URL
"""

INSTAGRAM_STORY_SOP = """
WHERE TO POST:
1. Open Instagram app
2. Tap your Story profile pic (top left) OR swipe right
3. Click "Create" story icon

HOW TO POST:
1. Take photo or upload from gallery
2. Add text, stickers, filters
3. Add link/button if promotable (requires 10k followers)
4. Tap your username at bottom to add to story
5. Choose "Close Friends" or "Everyone"
6. Click "Share to Story"

STORY TIPS:
- Use polling stickers (interactive)
- Add CTAs with text or buttons
- Keep text readable (large font)
- Post 1-3 stories per session
- Stories disappear after 24 hours

COMPLETION:
- Screenshot your story before it expires
- Note: Stories don't stay, so screenshot immediately
"""


# ============================================================================
# Twitter/X SOPs
# ============================================================================

TWITTER_POST_SOP = """
WHERE TO POST:
1. Go to twitter.com or X.com (logged in)
2. Click "Post" (or "Compose") button (top left)

HOW TO POST:
1. Type your message (280 characters max)
2. Add link by pasting URL (auto-preview)
3. Add image by clicking image icon
4. Add hashtags (3-5 is ideal)
5. Mention users if relevant (@username)
6. Click "Post" button

TWITTER TIPS:
- First 140 chars are most visible (mobile preview)
- Use words like: guide, how to, best practices
- Ask questions (increases replies)
- Include link if promoting
- Retweet = endorsement, Like = agreement

COMMON MISTAKES:
- ❌ No hashtags (low reach)
- ❌ Too many mentions (@@ spam)
- ❌ Broken links
- ❌ Typos (hard to fix, delete and repost)

COMPLETION:
- Copy tweet URL (click ... menu → Copy link to Tweet)
- Paste in completion proof field
"""

TWITTER_THREAD_SOP = """
WHERE TO POST:
1. Go to X/Twitter.com
2. Click "Post" button
3. Type first tweet

HOW TO POST THREAD:
1. Write first tweet
2. Click "Add another Tweet" (appears below)
3. Add tweet 2, 3, 4, etc.
4. Preview the thread
5. Click "Post All" button

THREAD TIPS:
- Start with attention-grabbing statement
- Number each tweet: "1/" "2/" "3/"
- Escalate value as you go
- End with CTA or resource link
- 5-7 tweets is ideal length

COMPLETION:
- Copy URL of first tweet in thread
- Paste in completion proof
"""

TWITTER_QUOTE_RETWEET_SOP = """
WHERE TO POST:
1. Find target tweet/post
2. Click the retweet icon (double arrow)
3. Select "Quote Tweet"

HOW TO POST:
1. Add your commentary (280 chars)
2. Mention what you agree/disagree with
3. Add link to resource if relevant
4. Click "Quote Tweet" button

TIPS:
- Add perspective: "I'd add..." "Great point, also..."
- Don't just +1 (be thoughtful)
- This is engagement, not original content

COMPLETION:
- Copy quote tweet URL
- Paste in completion proof
"""


# ============================================================================
# Email SOPs
# ============================================================================

EMAIL_NEWSLETTER_SOP = """
WHERE TO POST:
1. Log into your email service (Mailchimp, Substack, etc.)
2. Click "Create Campaign" or "New Email"

HOW TO POST:
1. Add subject line (provided)
2. Add "From" name
3. Paste email body content
4. Add images/links as provided
5. Set send time (usually 9am or 12pm)
6. Review preview on mobile
7. Click "Send" or "Schedule"

EMAIL TIPS:
- Subject line: 50 chars or less
- From name: Use personal name (higher open rate)
- First line visible in preview (make it compelling)
- Include unsubscribe link (required)
- Test link clicks before sending

COMMON MISTAKES:
- ❌ Typos in subject line
- ❌ No clear CTA
- ❌ Ugly on mobile
- ❌ Broken links

COMPLETION:
- Screenshot "Campaign Sent" confirmation
- Or share send report/metrics
"""


# ============================================================================
# Mapping & Lookup
# ============================================================================

PLATFORM_SOPs = {
    "linkedin": {
        "post": LINKEDIN_POST_SOP,
        "carousel": LINKEDIN_CAROUSEL_SOP,
        "thread": LINKEDIN_THREAD_SOP,
        "default": LINKEDIN_POST_SOP,
    },
    "instagram": {
        "post": INSTAGRAM_POST_SOP,
        "reel": INSTAGRAM_REEL_SOP,
        "carousel": INSTAGRAM_CAROUSEL_SOP,
        "story": INSTAGRAM_STORY_SOP,
        "default": INSTAGRAM_POST_SOP,
    },
    "twitter": {
        "post": TWITTER_POST_SOP,
        "thread": TWITTER_THREAD_SOP,
        "quote": TWITTER_QUOTE_RETWEET_SOP,
        "default": TWITTER_POST_SOP,
    },
    "x": {
        "post": TWITTER_POST_SOP,
        "thread": TWITTER_THREAD_SOP,
        "quote": TWITTER_QUOTE_RETWEET_SOP,
        "default": TWITTER_POST_SOP,
    },
    "email": {
        "newsletter": EMAIL_NEWSLETTER_SOP,
        "default": EMAIL_NEWSLETTER_SOP,
    },
}


def get_platform_sop(platform: str, content_type: str) -> str:
    """
    Get SOP instructions for a platform/content type combination.
    
    Args:
        platform: "linkedin", "instagram", "twitter", "email", etc.
        content_type: "post", "carousel", "reel", "thread", "email", etc.
    
    Returns:
        SOP instruction text
    """
    platform = platform.lower().strip()
    content_type = content_type.lower().strip()
    
    # Normalize platform names
    if platform in ("x", "twitter"):
        platform = "twitter"
    
    if platform not in PLATFORM_SOPs:
        return f"SOP not found for platform: {platform}"
    
    platform_dict = PLATFORM_SOPs[platform]
    
    # Try exact match
    if content_type in platform_dict:
        return platform_dict[content_type]
    
    # Fall back to default
    return platform_dict.get("default", "SOP not available")


def list_available_platforms() -> list:
    """List all supported platforms."""
    return list(PLATFORM_SOPs.keys())


def list_content_types(platform: str) -> list:
    """List content types for a platform."""
    platform = platform.lower().strip()
    if platform in ("x", "twitter"):
        platform = "twitter"
    
    if platform not in PLATFORM_SOPs:
        return []
    
    return list(PLATFORM_SOPs[platform].keys())
