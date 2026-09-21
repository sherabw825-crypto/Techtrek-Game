#!/usr/bin/env python3
"""Entry point. Run this: python run.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import pygame  # noqa: F401
except ImportError:
    sys.exit("pygame is not installed. Run:  pip install pygame")

from game.app import main

if __name__ == "__main__":
    main()
