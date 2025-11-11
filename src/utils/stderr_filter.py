"""
Stderr filter utility to suppress expected library warnings.

This module provides a stderr filter that suppresses common warnings from
Google ADK libraries that don't affect functionality.
"""

import sys


class StderrFilter:
    """Filter stderr to suppress expected library warnings."""

    def __init__(self, original_stderr):
        self.original_stderr = original_stderr

    def write(self, text):
        """Filter out expected warnings from stderr output."""
        # Suppress non-text parts warning (expected when tools are called)
        if "Warning: there are non-text parts in the response" in text:
            return

        # Suppress app name mismatch (Google ADK internal inference)
        if "App name mismatch detected" in text:
            return

        # Suppress experimental feature warnings
        if "[EXPERIMENTAL]" in text:
            return

        # Suppress async cleanup warnings (harmless library cleanup)
        if "RuntimeError: Attempted to exit cancel scope" in text:
            return
        if "an error occurred during closing of asynchronous generator" in text:
            return
        if "Exception Group Traceback" in text:
            return
        if "BaseExceptionGroup: unhandled errors in a TaskGroup" in text:
            return
        if "GeneratorExit" in text:
            return

        # Pass through all other messages
        self.original_stderr.write(text)

    def flush(self):
        """Flush the underlying stderr stream."""
        self.original_stderr.flush()


def apply_stderr_filter():
    """Apply the stderr filter to sys.stderr."""
    sys.stderr = StderrFilter(sys.stderr)
