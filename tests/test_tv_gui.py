import pytest

tk = pytest.importorskip("tkinter")

from app import tv_gui


def test_preferred_icon_file_does_not_raise():
    # Regression test: _preferred_icon_file() used to call an undefined
    # _project_root() (the imported name is project_root, no underscore),
    # raising NameError and crashing GUI startup before the window ever
    # appeared - "failed to execute script 'tv_main' due to unhandled
    # exception: name '_project_root' is not defined".
    tv_gui._preferred_icon_file()
