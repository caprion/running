#!/usr/bin/env python3
"""Wrapper to run sync-garmin with proper UTF-8 encoding"""
import sys
import io

# Force UTF-8 encoding for stdout/stderr
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Import and run the sync script
import sync_garmin
sync_garmin.main()
