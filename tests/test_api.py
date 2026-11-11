import pytest

pytestmark = pytest.mark.asyncio


async def create_user(client, email="marina@example.com", name="Марина"):
    return await client.post("/users", json={"email": email, "name": name})


async def create_task(client, owner_id, title="Сделать практическую работу №2"):
    return await client.post("/tasks", json={"title": title, "owner_id": owner_id})


# 1
async def test_create_user_201(client):
    r = await create_user(client)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "marina@example.com"
    assert body["name"] == "Марина"
    assert body["id"] == 1
    assert "created_at" in body


# 2
async def test_create_user_conflict_409(client):
    await create_user(client)
    r = await create_user(client, email="marina@example.com", name="Другой")
    assert r.status_code == 409
    assert r.json()["detail"] == "Email уже занят"


# 3
async def test_get_user_200(client):
    created = (await create_user(client)).json()
    r = await client.get(f"/users/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]
    assert r.json()["email"] == created["email"]


# 4
async def test_get_user_404(client):
    r = await client.get("/users/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Пользователь не найден"


# 5
async def test_create_task_201(client):
    user = (await create_user(client)).json()
    r = await create_task(client, user["id"])
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "Сделать практическую работу №2"
    assert body["done"] is False
    assert body["owner_id"] == user["id"]


# 6
async def test_create_task_owner_404(client):
    r = await create_task(client, owner_id=999)
    assert r.status_code == 404
    assert r.json()["detail"] == "Владелец не найден"


# 7
async def test_patch_task_done_200(client):
    user = (await create_user(client)).json()
    task = (await create_task(client, user["id"])).json()
    r = await client.patch(f"/tasks/{task['id']}", json={"done": True})
    assert r.status_code == 200
    assert r.json()["done"] is True
    # остальные поля не перезаписались
    assert r.json()["title"] == task["title"]


# 8
async def test_list_tasks_filter_200(client):
    user = (await create_user(client)).json()
    t1 = (await create_task(client, user["id"], "task-1")).json()
    await create_task(client, user["id"], "task-2")
    await client.patch(f"/tasks/{t1['id']}", json={"done": True})

    r = await client.get("/tasks", params={"done": True, "owner_id": user["id"]})
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["id"] == t1["id"]
    assert items[0]["done"] is True


# 9
async def test_delete_task_204_and_get_404(client):
    user = (await create_user(client)).json()
    task = (await create_task(client, user["id"])).json()

    r = await client.delete(f"/tasks/{task['id']}")
    assert r.status_code == 204
    assert r.content == b""

    r2 = await client.get(f"/tasks/{task['id']}")
    assert r2.status_code == 404
    assert r2.json()["detail"] == "Задача не найдена"


# 10 (дополнительно)
async def test_patch_task_404(client):
    r = await client.patch("/tasks/999", json={"done": True})
    assert r.status_code == 404
    assert r.json()["detail"] == "Задача не найдена"


# 11 (дополнительно)
async def test_update_task_null_title_422(client):
    user = (await create_user(client)).json()
    task = (await create_task(client, user["id"])).json()
    r = await client.patch(f"/tasks/{task['id']}", json={"title": None})
    assert r.status_code == 422


# 12 (дополнительно)
async def test_task_read_shape(client):
    user = (await create_user(client)).json()
    task = (await create_task(client, user["id"])).json()
    for key in ("id", "title", "description", "done", "created_at", "owner_id"):
        assert key in task
      
