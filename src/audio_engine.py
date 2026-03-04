# -*- coding: utf-8 -*-
"""Audio engine for sound generation in Acoustica."""

from __future__ import annotations

import datetime
import wave
from pathlib import Path

import numpy as np

# Default sample rate
SAMPLE_RATE = 44100

# Assets directory for audio files
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

# Reports audio directory
REPORTS_AUDIO_DIR = Path(__file__).resolve().parent.parent / "reports" / "audio"

# Frequency bands for RT60 values (Hz)
FREQ_BANDS = [125, 250, 500, 1000, 2000, 4000]


def generate_sine_wave(
    frequency: float = 440.0,
    duration: float = 1.0,
    volume: float = 0.5,
    sample_rate: int = SAMPLE_RATE
) -> np.ndarray:
    """
    Generate a sine wave with fade in/out.
    
    Args:
        frequency: Frequency in Hz (default: 440 Hz - A4 note)
        duration: Duration in seconds (default: 1.0)
        volume: Volume level from 0.0 to 1.0 (default: 0.5)
        sample_rate: Sample rate in Hz (default: 44100)
    
    Returns:
        numpy array containing the sine wave
    """
    # Generate time array
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # Generate sine wave
    wave = volume * np.sin(2 * np.pi * frequency * t)
    
    # Apply fade in/out to avoid clicks
    fade_samples = int(sample_rate * 0.01)  # 10ms fade
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)
    wave[:fade_samples] *= fade_in
    wave[-fade_samples:] *= fade_out
    
    return wave


def generate_impulse_response(
    rt60_values: list[float],
    duration: float = 2.0,
    sample_rate: int = SAMPLE_RATE
) -> np.ndarray:
    """
    Generate a synthetic impulse response based on RT60 values for each frequency band.
    
    The impulse response simulates room reverb by creating a decay envelope
    that varies by frequency band, reflecting how different frequencies
    decay at different rates in a room.
    
    Args:
        rt60_values: List of 6 RT60 values (in seconds) for bands [125, 250, 500, 1000, 2000, 4000] Hz
        duration: Maximum duration of the impulse response in seconds (default: 2.0)
        sample_rate: Sample rate in Hz (default: 44100)
    
    Returns:
        numpy array containing the impulse response
    """
    num_samples = int(sample_rate * duration)
    
    # Create time array
    t = np.linspace(0, duration, num_samples, endpoint=False)
    
    # Initialize IR with zeros
    ir = np.zeros(num_samples)
    
    # Generate IR for each frequency band
    for i, rt60 in enumerate(rt60_values):
        if rt60 <= 0:
            continue
        
        freq = FREQ_BANDS[i]
        
        # Decay time constant (RT60 is time for 60dB decay)
        # Convert to exponential decay constant
        decay_rate = 6.91 / max(rt60, 0.01)  # ln(1000) ≈ 6.91 for 60dB
        
        # Generate band-limited noise decay envelope
        # Use the actual RT60 for this band
        decay_envelope = np.exp(-decay_rate * t)
        
        # Generate random noise for this band
        noise = np.random.randn(num_samples)
        
        # Apply bandpass filter around this frequency
        # Simple approximation using FFT
        fft_noise = np.fft.rfft(noise)
        freqs = np.fft.rfftfreq(num_samples, 1.0 / sample_rate)
        
        # Bandwidth proportional to frequency (1 octave)
        bandwidth = freq * 0.5
        low = max(freq - bandwidth, 20)
        high = min(freq + bandwidth, sample_rate / 2 - 100)
        
        # Create bandpass mask
        mask = ((freqs >= low) & (freqs <= high)).astype(float)
        fft_noise = fft_noise * mask
        
        # Convert back to time domain
        band_noise = np.fft.irfft(fft_noise, n=num_samples)
        
        # Normalize
        band_noise = band_noise / (np.max(np.abs(band_noise)) + 1e-10)
        
        # Apply decay envelope
        ir += band_noise * decay_envelope
    
    # Add initial impulse (direct sound)
    ir[0] = 1.0
    
    # Normalize the IR
    max_val = np.max(np.abs(ir))
    if max_val > 0:
        ir = ir / max_val
    
    return ir


def convolve_audio(
    dry_signal: np.ndarray,
    impulse_response: np.ndarray
) -> np.ndarray:
    """
    Convolve a dry signal with an impulse response to apply reverb.
    
    Args:
        dry_signal: numpy array containing the dry audio signal
        impulse_response: numpy array containing the impulse response
    
    Returns:
        numpy array containing the wet (reverberated) signal
    """
    # Perform convolution using FFT for efficiency
    wet_signal = np.convolve(dry_signal, impulse_response, mode='full')
    
    # Normalize to prevent clipping
    max_val = np.max(np.abs(wet_signal))
    if max_val > 0:
        wet_signal = wet_signal / max_val * 0.9  # Leave headroom
    
    # Trim to reasonable length (dry signal length + 2 seconds of reverb tail)
    max_length = len(dry_signal) + int(SAMPLE_RATE * 2)
    if len(wet_signal) > max_length:
        wet_signal = wet_signal[:max_length]
    
    return wet_signal


def save_wav(
    wave_data: np.ndarray,
    filepath: Path,
    sample_rate: int = SAMPLE_RATE
) -> bool:
    """
    Save wave data to a WAV file.
    
    Args:
        wave_data: numpy array containing audio data (values should be -1.0 to 1.0)
        filepath: Path to save the WAV file
        sample_rate: Sample rate in Hz (default: 44100)
    
    Returns:
        True if save succeeded, False otherwise
    """
    try:
        # Convert to 16-bit PCM
        pcm_data = (wave_data * 32767).astype(np.int16)
        
        # Write WAV file
        with wave.open(str(filepath), 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data.tobytes())
        
        return True
    except Exception:
        return False


def generate_test_tone(
    frequency: float = 440.0,
    duration: float = 1.0,
    volume: float = 0.5,
    filename: str = "test_tone.wav"
) -> Path | None:
    """
    Generate a test tone and save it to the assets folder.
    
    Args:
        frequency: Frequency in Hz (default: 440 Hz - A4 note)
        duration: Duration in seconds (default: 1.0)
        volume: Volume level from 0.0 to 1.0 (default: 0.5)
        filename: Output filename (default: "test_tone.wav")
    
    Returns:
        Path to the generated file, or None if generation failed
    """
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = ASSETS_DIR / filename
    
    wave_data = generate_sine_wave(frequency, duration, volume)
    
    if save_wav(wave_data, filepath):
        return filepath
    return None


def generate_room_audio(
    rt60_values: list[float],
    frequency: float = 440.0,
    duration: float = 1.0,
    volume: float = 0.5
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate dry and wet audio signals based on room RT60 values.
    
    Args:
        rt60_values: List of 6 RT60 values for frequency bands
        frequency: Frequency of the test tone in Hz (default: 440 Hz)
        duration: Duration of the test tone in seconds (default: 1.0)
        volume: Volume level from 0.0 to 1.0 (default: 0.5)
    
    Returns:
        Tuple of (dry_signal, wet_signal, impulse_response)
    """
    # Generate dry sine wave
    dry_signal = generate_sine_wave(frequency, duration, volume)
    
    # Generate impulse response from RT60 values
    impulse_response = generate_impulse_response(rt60_values)
    
    # Apply reverb
    wet_signal = convolve_audio(dry_signal, impulse_response)
    
    return dry_signal, wet_signal, impulse_response


def save_audio_pair(
    dry_signal: np.ndarray,
    wet_signal: np.ndarray,
    output_dir: Path
) -> tuple[Path | None, Path | None]:
    """
    Save both dry and wet audio files to a directory.
    
    Args:
        dry_signal: numpy array containing the dry signal
        wet_signal: numpy array containing the wet (reverberated) signal
        output_dir: Directory to save the files (will be created if needed)
    
    Returns:
        Tuple of (dry_path, wet_path) or (None, None) on failure
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    dry_path = output_dir / "dry.wav"
    wet_path = output_dir / "reverb.wav"
    
    dry_success = save_wav(dry_signal, dry_path)
    wet_success = save_wav(wet_signal, wet_path)
    
    if dry_success and wet_success:
        return dry_path, wet_path
    return None, None
