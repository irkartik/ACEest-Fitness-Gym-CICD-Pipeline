import tkinter as tk
import pytest
from app.main import ACEestApp


@pytest.fixture
def app():
    root = tk.Tk()
    root.withdraw()  # hide the window during tests
    application = ACEestApp(root)
    yield application
    root.destroy()


def test_programs_loaded(app):
    """Verify that all three fitness programs are loaded on startup."""
    expected_programs = {"Fat Loss (FL)", "Muscle Gain (MG)", "Beginner (BG)"}
    assert set(app.programs.keys()) == expected_programs
