#!/usr/bin/env python3
"""Test script for audio generation - run this to test WAV output."""

import sys
sys.path.insert(0, 'src')

from audio_engine import generate_test_tone, generate_sine_wave, save_wav, ASSETS_DIR

# Test 1: Generate a simple 440 Hz test tone
print("Generating 440 Hz test tone...")
result = generate_test_tone(frequency=440, duration=1.0, volume=0.5)
if result:
    print(f"SUCCESS: Created {result}")
else:
    print("FAILED: Could not create test tone")

# Test 2: Generate a 1 kHz tone
print("\nGenerating 1000 Hz test tone...")
result = generate_test_tone(frequency=1000, duration=1.0, volume=0.5, filename="test_1000hz.wav")
if result:
    print(f"SUCCESS: Created {result}")
else:
    print("FAILED: Could not create test tone")

print(f"\nWAV files saved to: {ASSETS_DIR}")
