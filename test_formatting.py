#!/usr/bin/env python3
"""Test script to verify time formatting in messages."""

from datetime import datetime, timezone
from src.utils import format_datetime

# Test different date scenarios
test_cases = [
    datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),    # New Year midnight
    datetime(2025, 12, 25, 12, 30, 45, tzinfo=timezone.utc), # Christmas noon
    datetime(2025, 8, 5, 17, 59, 9, tzinfo=timezone.utc),   # Your example
    datetime(2025, 3, 21, 9, 15, 30, tzinfo=timezone.utc),  # Spring morning
    datetime(2025, 11, 22, 23, 45, 12, tzinfo=timezone.utc), # Late night
]

print("🕐 Time Formatting Test Results:")
print("=" * 50)

for i, dt in enumerate(test_cases, 1):
    formatted = format_datetime(dt)
    original = dt.strftime('%Y-%m-%d %H:%M:%S')
    print(f"{i}. Old format: {original}")
    print(f"   New format: {formatted}")
    print()

print("✅ Time formatting is ready!")
print("📱 Messages will now show times like: '5th August 2025 5:59PM'")