# TestFlight Status Detection - Debugging Fixes

## Problem
The TestFlight status checker was reporting "Unknown Status" for TestFlight betas that were actually open/available for joining. This prevented notifications from being sent when betas became available.

## Root Cause
Apple has likely updated the HTML structure of their TestFlight pages, causing the status detection patterns to no longer match the actual page content. The `STATUS_PATTERNS` dictionary in `utils/testflight.py` contained only basic patterns that were insufficient to detect all variations of beta availability.

## Changes Made

### 1. Enhanced Status Pattern Matching (`utils/testflight.py`)
**File**: `utils/testflight.py` - Lines 28-51

Updated the `STATUS_PATTERNS` dictionary with additional pattern variations:

#### OPEN Status Patterns (added):
- `"open to testers"` - Indicates beta is open
- `"get this app from the app store"` - CTA for available betas
- `"get it from the app store"` - Alternative CTA
- `"join the test"` - Alternative phrasing
- `"become a tester"` - Alternative phrasing
- `"join as a tester"` - Alternative phrasing
- `"test this app"` - Alternative phrasing

#### FULL Status Patterns (added):
- `"full - there aren't any more spots"` - More specific phrasing
- `"there are no more spots available"` - Alternative phrasing

#### CLOSED Status Patterns (added):
- `"isn't accepting any new testers"` - Alternative phrasing
- `"beta isn't open to new testers"` - Alternative phrasing

### 2. Improved HTML Parsing (`utils/testflight.py`)
**File**: `utils/testflight.py` - Lines 298-320

Enhanced the HTML parsing to handle different Apple page structures:

- **Multiple CSS selector fallbacks**: If the primary `.beta-status span` selector doesn't find content, tries alternative selectors:
  - `main p` - Main content area paragraphs
  - `[data-testid='beta-status']` - Data attribute selector
  - `.status-text` - Alternative class name
  - `div[role='main'] p` - Semantic HTML structure

- **Full page text fallback**: Captures the entire page text as a fallback for pattern matching when specific status elements aren't found

- **Enhanced debug information**: Stores up to 300 characters of raw text for debugging when UNKNOWN status is encountered

### 3. Improved Debugging Logging (`main.py`)
**File**: `main.py` - Lines 2617-2626

Enhanced logging for UNKNOWN status detection to help identify missing patterns:

```python
logging.warning(
    f"200 - {app_name} - UNKNOWN status detected. "
    f"Full raw text (first 200 chars): '{raw_text[:200]}' - "
    f"Please check the TestFlight page and report this pattern "
    f"so we can add it to STATUS_PATTERNS for proper detection."
)
```

This provides actionable information about what text patterns are missing from the detection logic.

## How This Fixes the Issue

1. **More comprehensive pattern matching**: The additional patterns cover more variations of how Apple displays beta status, reducing the chance of an UNKNOWN result.

2. **Fallback HTML parsing**: By trying multiple CSS selectors and falling back to full page text, the code is more resilient to HTML structure changes.

3. **Better debugging**: When an UNKNOWN status is still encountered, the enhanced logging provides the exact text from the page, making it easy to add new patterns without manual investigation.

## Testing Recommendations

To verify the fix works:

1. **Check open TestFlights**: Run the checker on a known open TestFlight and verify it detects status as OPEN
2. **Check full TestFlights**: Run on a known full beta and verify it shows FULL status
3. **Check closed TestFlights**: Run on a closed beta and verify it shows CLOSED status
4. **Monitor logs**: Watch the console logs for UNKNOWN status messages with the raw text - if any appear, add those patterns to `STATUS_PATTERNS`

## Future Improvements

1. Implement a web scraper to periodically check real TestFlight pages and automatically detect new patterns
2. Use machine learning or fuzzy matching for more intelligent status detection
3. Add a configuration option to update patterns without code changes
4. Create a community-contributed pattern library for sharing discovered patterns
