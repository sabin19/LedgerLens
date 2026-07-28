import pytest
from frontend.components import dialogs

def test_json_dialogs_exist():
    assert hasattr(dialogs, 'view_extracted_json_dialog')
    assert hasattr(dialogs, 'view_reviewed_json_dialog')
    assert hasattr(dialogs, 'view_json_dialog')

def test_json_dialogs_callable():
    assert callable(dialogs.view_extracted_json_dialog)
    assert callable(dialogs.view_reviewed_json_dialog)
    assert callable(dialogs.view_json_dialog)
