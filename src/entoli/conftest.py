from rich.traceback import install
import pytest

# Automatically install the rich traceback handler
install(show_locals=True)

# Optional: Configure pytest to use rich's console for output
@pytest.hookimpl(tryfirst=True)
def pytest_exception_interact(node, call, report):
    if report.failed:
        # Re-install rich traceback in case pytest modifies the environment
        install(show_locals=True)