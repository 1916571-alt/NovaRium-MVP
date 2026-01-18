"""
Experiment Page - A/B Test Wizard (Steps 1-4)

This module has been refactored into a modular structure.
See src/ui/pages/experiment/ for the individual step implementations.

This file is kept for backwards compatibility.
"""
from src.ui.pages.experiment import render, PAGE_MAP, METRICS_DB

__all__ = ['render', 'PAGE_MAP', 'METRICS_DB']
