import pytest

pytest.importorskip("tkinter")

from app import tv_gui_classic


def test_preferred_icon_file_does_not_raise():
    # Regression test: the Classic app was restored from the pre-pywebview
    # implementation where _preferred_icon_file() once called an undefined
    # _project_root() (the imported name is project_root, no underscore).
    # Guard against that bug reappearing.
    tv_gui_classic._preferred_icon_file()


def test_launch_tv_gui_is_defined():
    assert callable(tv_gui_classic.launch_tv_gui)
