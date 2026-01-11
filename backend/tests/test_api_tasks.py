"""
API tests for task endpoints
"""

import pytest
from fastapi import status


class TestTasksAPI:
    """Test task API endpoints"""
    
    def test_list_tasks_empty(self, client):
        """Test listing tasks when none exist"""
        response = client.get("/api/tasks/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
    
    def test_create_task(self, client):
        """Test creating a new task"""
        # First create a project
        project_response = client.post("/api/projects/", json={"name": "Test Project"})
        project_id = project_response.json()["id"]
        
        task_data = {
            "project_id": project_id,
            "title": "Test Task",
            "description": "A test task",
            "priority": 5
        }
        response = client.post("/api/tasks/", json=task_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["description"] == "A test task"
        assert data["priority"] == 5
        assert data["project_id"] == project_id
        assert data["status"] == "pending"
        assert "id" in data
    
    def test_create_task_minimal(self, client):
        """Test creating a task with minimal data"""
        project_response = client.post("/api/projects/", json={"name": "Test Project"})
        project_id = project_response.json()["id"]
        
        task_data = {
            "project_id": project_id,
            "title": "Minimal Task"
        }
        response = client.post("/api/tasks/", json=task_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["title"] == "Minimal Task"
        assert data["description"] is None
        assert data["priority"] == 0
    
    def test_list_tasks(self, client):
        """Test listing multiple tasks"""
        project_response = client.post("/api/projects/", json={"name": "Test Project"})
        project_id = project_response.json()["id"]
        
        # Create multiple tasks
        client.post("/api/tasks/", json={"project_id": project_id, "title": "Task 1"})
        client.post("/api/tasks/", json={"project_id": project_id, "title": "Task 2"})
        client.post("/api/tasks/", json={"project_id": project_id, "title": "Task 3"})
        
        response = client.get("/api/tasks/")
        assert response.status_code == status.HTTP_200_OK
        
        tasks = response.json()
        assert len(tasks) == 3
    
    def test_list_tasks_filter_by_project(self, client):
        """Test listing tasks filtered by project"""
        # Create two projects
        project1 = client.post("/api/projects/", json={"name": "Project 1"}).json()
        project2 = client.post("/api/projects/", json={"name": "Project 2"}).json()
        
        # Create tasks for each project
        client.post("/api/tasks/", json={"project_id": project1["id"], "title": "P1 Task 1"})
        client.post("/api/tasks/", json={"project_id": project1["id"], "title": "P1 Task 2"})
        client.post("/api/tasks/", json={"project_id": project2["id"], "title": "P2 Task 1"})
        
        # Filter by project 1
        response = client.get(f"/api/tasks/?project_id={project1['id']}")
        assert response.status_code == status.HTTP_200_OK
        tasks = response.json()
        assert len(tasks) == 2
        assert all(t["project_id"] == project1["id"] for t in tasks)
    
    def test_list_tasks_filter_by_status(self, client):
        """Test listing tasks filtered by status"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        
        # Create tasks and update their status
        task1 = client.post("/api/tasks/", json={"project_id": project["id"], "title": "Task 1"}).json()
        task2 = client.post("/api/tasks/", json={"project_id": project["id"], "title": "Task 2"}).json()
        
        # Update task1 to approved
        client.patch(f"/api/tasks/{task1['id']}?project_id={project['id']}", 
                    json={"status": "approved"})
        
        # Filter by approved status
        response = client.get("/api/tasks/?status=approved")
        assert response.status_code == status.HTTP_200_OK
        tasks = response.json()
        assert len(tasks) == 1
        assert tasks[0]["status"] == "approved"
    
    def test_get_task(self, client):
        """Test getting a single task by ID"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        create_response = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Get Task Test",
            "description": "Test getting a task"
        })
        task_id = create_response.json()["id"]
        
        response = client.get(f"/api/tasks/{task_id}?project_id={project['id']}")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == "Get Task Test"
    
    def test_get_task_not_found(self, client):
        """Test getting a non-existent task returns 404"""
        response = client.get("/api/tasks/9999?project_id=1")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_task(self, client):
        """Test updating a task"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        create_response = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Original Title",
            "description": "Original description"
        })
        task_id = create_response.json()["id"]
        
        # Update the task
        update_data = {
            "title": "Updated Title",
            "description": "Updated description",
            "priority": 10
        }
        response = client.patch(f"/api/tasks/{task_id}?project_id={project['id']}", 
                               json=update_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Updated description"
        assert data["priority"] == 10
        assert data["version"] == 2  # Version should increment
    
    def test_update_task_status(self, client):
        """Test updating task status"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Status Test"
        }).json()
        
        response = client.patch(f"/api/tasks/{task['id']}?project_id={project['id']}", 
                               json={"status": "in_progress"})
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "in_progress"
    
    def test_delete_task(self, client):
        """Test deleting a task"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "To Delete"
        }).json()
        
        response = client.delete(f"/api/tasks/{task['id']}?project_id={project['id']}")
        assert response.status_code == status.HTTP_200_OK
        
        # Verify it's deleted
        get_response = client.get(f"/api/tasks/{task['id']}?project_id={project['id']}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_approve_task(self, client):
        """Test approving a task"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Approve Test"
        }).json()
        
        response = client.post(
            f"/api/tasks/{task['id']}/approve?project_id={project['id']}&approver=test_user"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True
        
        # Verify status changed
        task_response = client.get(f"/api/tasks/{task['id']}?project_id={project['id']}")
        assert task_response.json()["status"] == "approved"
    
    def test_advance_task(self, client):
        """Test advancing a task to next phase"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Advance Test"
        }).json()
        
        # Set to planner phase
        client.patch(f"/api/tasks/{task['id']}?project_id={project['id']}", 
                    json={"current_phase": "planner"})
        
        # Advance to next phase
        response = client.post(f"/api/tasks/{task['id']}/advance?project_id={project['id']}")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "advanced"
        assert data["next_phase"] == "architect"
    
    def test_get_task_versions(self, client):
        """Test getting task version history"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Version Test"
        }).json()
        
        # Update task to create versions
        client.patch(f"/api/tasks/{task['id']}?project_id={project['id']}", 
                    json={"title": "Updated Version 1"})
        client.patch(f"/api/tasks/{task['id']}?project_id={project['id']}", 
                    json={"title": "Updated Version 2"})
        
        response = client.get(f"/api/tasks/{task['id']}/versions")
        assert response.status_code == status.HTTP_200_OK
        
        versions = response.json()
        assert len(versions) >= 2
        assert all("version_num" in v for v in versions)
    
    def test_split_task(self, client):
        """Test splitting a task into two"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Task to Split",
            "description": "This task will be split"
        }).json()
        
        split_data = {
            "task1_title": "First Part",
            "task1_description": "First part of split",
            "task2_title": "Second Part",
            "task2_description": "Second part of split"
        }
        
        response = client.post(
            f"/api/tasks/{task['id']}/split?project_id={project['id']}", 
            json=split_data
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["success"] is True
        assert len(data["new_tasks"]) == 2
        assert data["new_tasks"][0]["title"] == "First Part"
        assert data["new_tasks"][1]["title"] == "Second Part"
        
        # Verify original task is cancelled
        original = client.get(f"/api/tasks/{task['id']}?project_id={project['id']}")
        assert original.json()["status"] == "cancelled"
    
    def test_merge_tasks(self, client):
        """Test merging multiple tasks into one"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        
        # Create multiple tasks
        task1 = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Task 1"
        }).json()
        task2 = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Task 2"
        }).json()
        task3 = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Task 3"
        }).json()
        
        merge_data = {
            "task_ids": [task1["id"], task2["id"], task3["id"]],
            "merged_title": "Merged Task",
            "merged_description": "All tasks merged"
        }
        
        response = client.post(
            f"/api/tasks/merge?project_id={project['id']}", 
            json=merge_data
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["success"] is True
        assert data["merged_task_title"] == "Merged Task"
        assert len(data["source_task_ids"]) == 3
        
        # Verify source tasks are cancelled
        for task_id in [task1["id"], task2["id"], task3["id"]]:
            task = client.get(f"/api/tasks/{task_id}?project_id={project['id']}")
            assert task.json()["status"] == "cancelled"
    
    def test_merge_tasks_insufficient(self, client):
        """Test merging with less than 2 tasks fails"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Single Task"
        }).json()
        
        merge_data = {
            "task_ids": [task["id"]],
            "merged_title": "Invalid Merge"
        }
        
        response = client.post(
            f"/api/tasks/merge?project_id={project['id']}", 
            json=merge_data
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "at least 2 tasks" in response.json()["detail"]
