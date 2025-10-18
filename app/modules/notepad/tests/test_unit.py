from app.modules.notepad import services


def test_sample_assertion(test_client):
    """
    Sample test to verify that the test framework and environment are working correctly.
    It does not communicate with the Flask application; it only performs a simple assertion to
    confirm that the tests in this module can be executed.
    """
    greeting = "Hello, World!"
    assert greeting == "Hello, World!", "The greeting does not coincide with 'Hello, World!'"


def test_get_all_notepads():
    service = services.NotepadService()
    result = service.get_all_by_user(user_id=1)
    assert isinstance(result, list)
