# Implementer Agent — Example Implementation

## Scenario

Implementing the task creation endpoint for the task management API, following the validated design from the Maker and Reviewer Agents.

---

## Phase 1: Design Comprehension

### Requirements
- FR-03: Task creation with title (required), description, due date, priority, assignee
- Must validate inputs (Reviewer Finding #2)
- Must use standard error format (Reviewer Finding #3)
- Must include logging for production debugging

### Acceptance Criteria
- POST /api/v1/tasks creates a task and returns 201
- Missing title returns 422 with validation error
- Invalid priority returns 422 with validation error
- Unauthenticated request returns 401
- Unauthorized request (not a team member) returns 403

---

## Phase 2: Implementation Plan

1. Define the Task model (database)
2. Define the request/response schemas
3. Implement the create task endpoint
4. Add input validation
5. Add error handling
6. Add logging
7. Write tests

---

## Phase 3: Implementation

### Task Model

```python
# models/task.py
from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
import enum

from app.database import Base


class TaskPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.OPEN, nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    is_deleted = Column(Boolean, default=False, nullable=False)
```

### Create Task Endpoint

```python
# routes/tasks.py
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.task import Task, TaskPriority
from app.schemas.task import TaskCreate, TaskResponse
from app.services.team_service import verify_team_membership

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new task within a team.
    
    Requires authentication and team membership.
    """
    request_id = current_user.request_id  # For distributed tracing
    
    # Authorization: verify user is a member of the team
    if not verify_team_membership(db, current_user.id, task_data.team_id):
        logger.warning(
            "Unauthorized task creation attempt",
            extra={
                "request_id": request_id,
                "user_id": str(current_user.id),
                "team_id": str(task_data.team_id),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team",
        )
    
    # Validate assignee is a team member (if provided)
    if task_data.assignee_id is not None:
        if not verify_team_membership(db, task_data.assignee_id, task_data.team_id):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Assignee is not a member of this team",
            )
    
    # Create the task
    task = Task(
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        due_date=task_data.due_date,
        assignee_id=task_data.assignee_id,
        team_id=task_data.team_id,
        created_by=current_user.id,
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    logger.info(
        "Task created successfully",
        extra={
            "request_id": request_id,
            "task_id": str(task.id),
            "team_id": str(task.team_id),
            "created_by": str(current_user.id),
        },
    )
    
    return task
```

---

## Phase 4: Tests

```python
# tests/test_create_task.py

def test_create_task_with_valid_input_returns_201(client, auth_headers, test_team):
    """Creating a task with all valid fields should return 201 and the task."""
    response = client.post(
        "/api/v1/tasks/",
        headers=auth_headers,
        json={
            "title": "Implement user authentication",
            "description": "Add JWT-based authentication to the API",
            "priority": "high",
            "team_id": str(test_team.id),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Implement user authentication"
    assert data["priority"] == "high"
    assert data["status"] == "open"


def test_create_task_without_title_returns_422(client, auth_headers, test_team):
    """Missing required title field should return 422 validation error."""
    response = client.post(
        "/api/v1/tasks/",
        headers=auth_headers,
        json={"team_id": str(test_team.id)},
    )
    assert response.status_code == 422


def test_create_task_unauthenticated_returns_401(client, test_team):
    """Request without auth token should return 401."""
    response = client.post(
        "/api/v1/tasks/",
        json={"title": "Test task", "team_id": str(test_team.id)},
    )
    assert response.status_code == 401


def test_create_task_non_team_member_returns_403(client, other_user_headers, test_team):
    """User not in the team should get 403."""
    response = client.post(
        "/api/v1/tasks/",
        headers=other_user_headers,
        json={"title": "Test task", "team_id": str(test_team.id)},
    )
    assert response.status_code == 403
```

---

## Phase 5: Self-Review Results

- ✅ Design conformance: Matches FR-03 requirements
- ✅ Code quality: Small functions, clear naming, injected dependencies
- ✅ Error handling: Auth, authorization, validation all return proper HTTP codes
- ✅ Security: Auth check, team membership validation, parameterized queries (via ORM)
- ✅ Logging: Structured logging with request_id, user_id, task_id
- ✅ Testing: Happy path, validation error, auth error, authorization error all tested
