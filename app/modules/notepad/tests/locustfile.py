from locust import HttpUser, TaskSet, task
from core.environment.host import get_host_for_locust_testing
from core.locust.common import fake, get_csrf_token
import re


class NotepadBehavior(TaskSet):
    def on_start(self):
        # Ensure we are logged in before exercising notepad endpoints
        self.login()

    def login(self):
        # GET login page to obtain CSRF token and cookies
        response = self.client.get("/login")
        csrf_token = get_csrf_token(response)

        # Use a fixed test user that exists in the test DB
        self.client.post(
            "/login",
            data={"email": "test@example.com", "password": "test1234", "csrf_token": csrf_token},
        )

    @task(4)
    def index(self):
        with self.client.get("/notepad", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Notepad index failed: {response.status_code}")

    @task(3)
    def create_notepad(self):
        # GET create page to fetch CSRF token
        response = self.client.get("/notepad/create")
        csrf_token = get_csrf_token(response)

        title = fake.sentence(nb_words=3)
        body = fake.paragraph()

        with self.client.post(
            "/notepad/create",
            data={"title": title, "body": body, "csrf_token": csrf_token},
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Create notepad failed: {resp.status_code}")

    @task(2)
    def show_and_edit_and_delete(self):
        # Try to fetch the list of notepads to find an id to operate on
        resp = self.client.get("/notepad")
        if resp.status_code != 200:
            return
        matches = re.findall(r"/notepad/(\d+)", resp.text)
        if not matches:
            return

        notepad_id = matches[0]

        # GET show
        with self.client.get(f"/notepad/{notepad_id}", catch_response=True) as r_show:
            if r_show.status_code != 200:
                r_show.failure(f"Show notepad {notepad_id} failed: {r_show.status_code}")

        # GET edit to obtain CSRF
        r_edit_get = self.client.get(f"/notepad/edit/{notepad_id}")
        csrf_token = get_csrf_token(r_edit_get)

        # POST edit
        new_title = fake.sentence(nb_words=2)
        new_body = fake.paragraph()
        with self.client.post(
            f"/notepad/edit/{notepad_id}",
            data={"title": new_title, "body": new_body, "csrf_token": csrf_token},
            catch_response=True,
        ) as r_edit_post:
            if r_edit_post.status_code != 200:
                r_edit_post.failure(f"Edit notepad {notepad_id} failed: {r_edit_post.status_code}")

        # POST delete
        # GET index again to obtain CSRF for delete if needed
        r_idx = self.client.get("/notepad")
        csrf_del = get_csrf_token(r_idx)
        with self.client.post(
            f"/notepad/delete/{notepad_id}", data={"csrf_token": csrf_del}, catch_response=True
        ) as r_del:
            # delete redirects to index (302) or returns 200 after redirect following
            if r_del.status_code not in (200, 302):
                r_del.failure(f"Delete notepad {notepad_id} failed: {r_del.status_code}")


class NotepadUser(HttpUser):
    tasks = [NotepadBehavior]
    # legacy wait style kept to match other locust files in repo
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()

