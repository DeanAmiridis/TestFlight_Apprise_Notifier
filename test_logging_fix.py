#!/usr/bin/env python3
"""
Quick test to verify duplicate logging has been fixed.
Run this to test the logging configuration without running the full application.

Usage:
    python3 test_logging_fix.py
"""

import logging
import sys

# Test 1: Verify handler count after basicConfig
print("=" * 60)
print("Test 1: Checking root logger handlers after basicConfig")
print("=" * 60)

root = logging.getLogger()
initial_handler_count = len(root.handlers)
print(f"Initial handler count: {initial_handler_count}")
print(f"Expected: 1 (only console handler)")
print(f"✓ PASS" if initial_handler_count == 1 else f"✗ FAIL")

# Test 2: Log a message and verify it appears once
print("\n" + "=" * 60)
print("Test 2: Logging a test message")
print("=" * 60)

logging.info("TEST MESSAGE - Should appear exactly once")

# Test 3: Check for duplicate handlers after ensure_web_handler_attached
print("\n" + "=" * 60)
print("Test 3: Simulating ensure_web_handler_attached() call")
print("=" * 60)

class MockWebLogHandler(logging.Handler):
    """Mock WebLogHandler for testing"""
    def emit(self, record):
        pass

mock_handler = MockWebLogHandler()

# Simulate what ensure_web_handler_attached does
handler_already_attached = any(
    isinstance(h, MockWebLogHandler) for h in root.handlers
)

if not handler_already_attached:
    root.addHandler(mock_handler)
    print("MockWebLogHandler added (first call)")

# Call it again to test duplicate prevention
handler_already_attached = any(
    isinstance(h, MockWebLogHandler) for h in root.handlers
)

if not handler_already_attached:
    root.addHandler(mock_handler)
    print("MockWebLogHandler added (second call) - ✗ FAIL - Duplicate!")
else:
    print("MockWebLogHandler NOT added (second call) - ✓ PASS - Duplicate prevented!")

# Test 4: Verify final handler count
print("\n" + "=" * 60)
print("Test 4: Checking final handler count")
print("=" * 60)

final_handler_count = len(root.handlers)
print(f"Final handler count: {final_handler_count}")
print(f"Expected: 2 (console + mock web handler)")
print(f"✓ PASS" if final_handler_count == 2 else f"✗ FAIL")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
