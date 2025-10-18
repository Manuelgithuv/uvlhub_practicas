import pytest
from app import db
from app.modules.notepad.models import Notepad
from app.modules.auth.models import User
from app.modules.conftest import login, logout


@pytest.fixture
def logged_in_user(test_client):
    login(test_client, "test@example.com", "test1234")
    user = User.query.filter_by(email="test@example.com").first()
    yield user
    logout(test_client)


@pytest.fixture
def other_user():
    """Crea un usuario distinto para pruebas de acceso no autorizado."""
    user = User(email="other@example.com", password="other1234")
    db.session.add(user)
    db.session.commit()
    yield user
    db.session.delete(user)
    db.session.commit()


def test_index_view_empty(test_client, logged_in_user):
    """GET /notepad: vista de notas vacía."""
    response = test_client.get("/notepad")
    assert response.status_code == 200
    assert b"/notepad/scripts.js" in response.data


def test_create_notepad(test_client, logged_in_user):
    """POST /notepad/create: crea una nueva nota."""
    data = {"title": "Mi primera nota", "body": "Contenido inicial"}
    response = test_client.post("/notepad/create", data=data, follow_redirects=True)

    assert response.status_code == 200
    nota = Notepad.query.filter_by(title="Mi primera nota", user_id=logged_in_user.id).first()
    assert nota is not None
    assert nota.body == "Contenido inicial"


def test_get_notepad_detail(test_client, logged_in_user):
    """GET /notepad/<id>: muestra detalle de la nota."""
    nota = Notepad.query.first()
    response = test_client.get(f"/notepad/{nota.id}")
    assert response.status_code == 200
    assert nota.title.encode() in response.data
    assert nota.body.encode() in response.data


def test_edit_notepad(test_client, logged_in_user):
    """POST /notepad/edit/<id>: actualiza nota existente."""
    nota = Notepad.query.first()
    data = {"title": "Nota editada", "body": "Contenido actualizado"}
    response = test_client.post(f"/notepad/edit/{nota.id}", data=data, follow_redirects=True)

    assert response.status_code == 200
    updated = db.session.get(Notepad, nota.id)
    assert updated.title == "Nota editada"
    assert updated.body == "Contenido actualizado"


def test_delete_notepad(test_client, logged_in_user):
    """POST /notepad/delete/<id>: elimina nota existente."""
    nota = Notepad.query.first()
    response = test_client.post(f"/notepad/delete/{nota.id}", follow_redirects=True)

    assert response.status_code == 200
    deleted = db.session.get(Notepad, nota.id)
    assert deleted is None


def test_unauthorized_access(test_client, other_user):
    """GET /notepad/<id> de otro usuario: debe impedir acceso."""
    
    user1 = User.query.filter_by(email="test@example.com").first()
    nota = Notepad(title="Secreta", body="No ver", user_id=user1.id)
    db.session.add(nota)
    db.session.commit()
    login(test_client, other_user.email, "other1234")
    response = test_client.get(f"/notepad/{nota.id}", follow_redirects=True)
    assert response.status_code == 200
    
    assert nota.user_id != other_user.id

    data = {"title": "Hack", "body": "Intento"}
    response = test_client.post(f"/notepad/edit/{nota.id}", data=data, follow_redirects=True)
    assert response.status_code == 200
    
    nota_actual = db.session.get(Notepad, nota.id)
    assert nota_actual.title == "Secreta"
    assert nota_actual.body == "No ver"
    response = test_client.post(f"/notepad/delete/{nota.id}", follow_redirects=True)
    assert response.status_code == 200
    
    nota_actual = db.session.get(Notepad, nota.id)
    assert nota_actual is not None

    logout(test_client)
