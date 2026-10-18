from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Task, User
from app.schemas import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])

TASK_NOT_FOUND = {404: {"description": "Задача не найдена"}}
OWNER_NOT_FOUND = {404: {"description": "Владелец не найден"}}
TASK_OR_OWNER_NOT_FOUND = {404: {"description": "Задача или новый владелец не найдены"}}


async def get_task_or_404(task_id: int, session: AsyncSession) -> Task:
    task = await session.get(Task, task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Задача не найдена")
    return task


async def ensure_owner_exists(owner_id: int, session: AsyncSession) -> None:
    if await session.get(User, owner_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Владелец не найден")


@router.post(
    "", response_model=TaskRead, status_code=status.HTTP_201_CREATED, responses=OWNER_NOT_FOUND
)
async def create_task(data: TaskCreate, session: AsyncSession = Depends(get_session)):
    await ensure_owner_exists(data.owner_id, session)
    task = Task(**data.model_dump())
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    done: bool | None = None,
    owner_id: int | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    query = select(Task).order_by(Task.id)
    if done is not None:
        query = query.where(Task.done == done)
    if owner_id is not None:
        query = query.where(Task.owner_id == owner_id)
    result = await session.scalars(query.limit(limit).offset(offset))
    return result.all()


@router.get("/{task_id}", response_model=TaskRead, responses=TASK_NOT_FOUND)
async def get_task(task_id: int, session: AsyncSession = Depends(get_session)):
    return await get_task_or_404(task_id, session)


@router.patch("/{task_id}", response_model=TaskRead, responses=TASK_OR_OWNER_NOT_FOUND)
async def update_task(
    task_id: int, data: TaskUpdate, session: AsyncSession = Depends(get_session)
):
    task = await get_task_or_404(task_id, session)
    changes = data.model_dump(exclude_unset=True)
    if "owner_id" in changes:
        await ensure_owner_exists(changes["owner_id"], session)
    for field, value in changes.items():
        setattr(task, field, value)
    await session.commit()
    await session.refresh(task)
    return task


@router.delete(
    "/{task_id}", status_code=status.HTTP_204_NO_CONTENT, responses=TASK_NOT_FOUND
)
async def delete_task(task_id: int, session: AsyncSession = Depends(get_session)):
    task = await get_task_or_404(task_id, session)
    await session.delete(task)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
