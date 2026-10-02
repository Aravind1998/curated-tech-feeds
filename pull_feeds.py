#!/usr/bin/env python3
"""
pull_feeds.py - Quick CLI to refresh tech & systems engineering feeds and dashboard
"""
import os
import subprocess
import sys

if __name__ == "__main__":
    script = os.path.join(os.path.dirname(__file__), "pipeline", "feed_reader.py")
    subprocess.run([sys.executable, script])
