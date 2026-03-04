# -*- coding: utf-8 -*-
"""
Acoustica TUI  --  Acoustic Reverb & Room Mode Analyzer
========================================================
Pure terminal application built with Textual.
No display server required -- runs in any terminal, VS Code, Codespace.

Install : pip install textual
Run     : python -m src.app
"""
from __future__ import annotations

if __name__ == "__main__":
    from src.app import run

    run()
