"""
Test runner script for E-Council tests.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_tests():
    """Run all tests and report results."""
    import pytest
    
    # Run pytest with coverage
    exit_code = pytest.main([
        'tests/',
        '-v',  # Verbose output
        '--tb=short',  # Short traceback format
        '--cov=.',  # Coverage report
        '--cov-report=html',  # HTML coverage report
        '--cov-report=term-missing',  # Terminal coverage report
        '--no-cov-on-fail',  # Don't generate coverage on failure
    ])
    
    return exit_code

if __name__ == '__main__':
    print("Running E-Council test suite...")
    print("=" * 60)
    
    exit_code = run_tests()
    
    print("=" * 60)
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed.")
    
    sys.exit(exit_code)