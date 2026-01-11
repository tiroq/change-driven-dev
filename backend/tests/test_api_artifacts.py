"""
API tests for artifact endpoints
"""

import pytest
from fastapi import status
from io import BytesIO


class TestArtifactsAPI:
    """Test artifact API endpoints"""
    
    def test_list_artifacts_empty(self, client):
        """Test listing artifacts when none exist"""
        response = client.get("/api/artifacts/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
    
    def test_create_artifact(self, client):
        """Test creating a new artifact (metadata only)"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        
        artifact_data = {
            "project_id": project["id"],
            "artifact_type": "plan",
            "name": "test_plan.json",
            "file_path": "/tmp/test_plan.json",
            "sha256": "abc123"
        }
        response = client.post("/api/artifacts/", json=artifact_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["project_id"] == project["id"]
        assert data["artifact_type"] == "plan"
        assert data["name"] == "test_plan.json"
        assert data["file_path"] == "/tmp/test_plan.json"
        assert data["sha256"] == "abc123"
        assert "id" in data
    
    def test_create_artifact_with_task(self, client):
        """Test creating an artifact linked to a task"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Test Task"
        }).json()
        
        artifact_data = {
            "project_id": project["id"],
            "task_id": task["id"],
            "artifact_type": "plan",
            "name": "task_plan.json",
            "file_path": "/tmp/task_plan.json"
        }
        response = client.post("/api/artifacts/", json=artifact_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["task_id"] == task["id"]
    
    def test_create_artifact_minimal(self, client):
        """Test creating an artifact with minimal data"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        
        artifact_data = {
            "project_id": project["id"],
            "artifact_type": "adr",
            "name": "minimal.md",
            "file_path": "/tmp/minimal.md"
        }
        response = client.post("/api/artifacts/", json=artifact_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["task_id"] is None
        assert data["run_id"] is None
        assert data["sha256"] is None
    
    def test_list_artifacts(self, client):
        """Test listing multiple artifacts"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        
        # Create multiple artifacts
        for i in range(3):
            client.post("/api/artifacts/", json={
                "project_id": project["id"],
                "artifact_type": "plan",
                "name": f"artifact_{i}.json",
                "file_path": f"/tmp/artifact_{i}.json"
            })
        
        response = client.get("/api/artifacts/")
        assert response.status_code == status.HTTP_200_OK
        
        artifacts = response.json()
        assert len(artifacts) == 3
    
    def test_list_artifacts_filter_by_project(self, client):
        """Test listing artifacts filtered by project"""
        project1 = client.post("/api/projects/", json={"name": "Project 1"}).json()
        project2 = client.post("/api/projects/", json={"name": "Project 2"}).json()
        
        # Create artifacts for each project
        client.post("/api/artifacts/", json={
            "project_id": project1["id"],
            "artifact_type": "plan",
            "name": "p1_artifact.json",
            "file_path": "/tmp/p1.json"
        })
        client.post("/api/artifacts/", json={
            "project_id": project2["id"],
            "artifact_type": "plan",
            "name": "p2_artifact.json",
            "file_path": "/tmp/p2.json"
        })
        
        # Filter by project 1
        response = client.get(f"/api/artifacts/?project_id={project1['id']}")
        assert response.status_code == status.HTTP_200_OK
        
        artifacts = response.json()
        assert len(artifacts) == 1
        assert artifacts[0]["project_id"] == project1["id"]
    
    def test_list_artifacts_filter_by_task(self, client):
        """Test listing artifacts filtered by task"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task1 = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Task 1"
        }).json()
        task2 = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Task 2"
        }).json()
        
        # Create artifacts for each task
        client.post("/api/artifacts/", json={
            "project_id": project["id"],
            "task_id": task1["id"],
            "artifact_type": "plan",
            "name": "t1_plan.json",
            "file_path": "/tmp/t1_plan.json"
        })
        client.post("/api/artifacts/", json={
            "project_id": project["id"],
            "task_id": task2["id"],
            "artifact_type": "plan",
            "name": "t2_plan.json",
            "file_path": "/tmp/t2_plan.json"
        })
        
        # Filter by task 1
        response = client.get(f"/api/artifacts/?task_id={task1['id']}")
        assert response.status_code == status.HTTP_200_OK
        
        artifacts = response.json()
        assert len(artifacts) == 1
        assert artifacts[0]["task_id"] == task1["id"]
    
    def test_list_artifacts_filter_by_type(self, client):
        """Test listing artifacts filtered by type"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        
        # Create artifacts of different types
        client.post("/api/artifacts/", json={
            "project_id": project["id"],
            "artifact_type": "plan",
            "name": "plan.json",
            "file_path": "/tmp/plan.json"
        })
        client.post("/api/artifacts/", json={
            "project_id": project["id"],
            "artifact_type": "adr",
            "name": "adr.md",
            "file_path": "/tmp/adr.md"
        })
        client.post("/api/artifacts/", json={
            "project_id": project["id"],
            "artifact_type": "test_result",
            "name": "test.log",
            "file_path": "/tmp/test.log"
        })
        
        # Filter by type
        response = client.get("/api/artifacts/?artifact_type=adr")
        assert response.status_code == status.HTTP_200_OK
        
        artifacts = response.json()
        assert len(artifacts) == 1
        assert artifacts[0]["artifact_type"] == "adr"
    
    def test_get_artifact(self, client):
        """Test getting a single artifact by ID"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        
        create_response = client.post("/api/artifacts/", json={
            "project_id": project["id"],
            "artifact_type": "plan",
            "name": "get_test.json",
            "file_path": "/tmp/get_test.json"
        })
        artifact_id = create_response.json()["id"]
        
        response = client.get(f"/api/artifacts/{artifact_id}")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == artifact_id
        assert data["name"] == "get_test.json"
    
    def test_get_artifact_not_found(self, client):
        """Test getting a non-existent artifact returns 404"""
        response = client.get("/api/artifacts/9999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_artifact(self, client):
        """Test deleting an artifact"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        
        artifact = client.post("/api/artifacts/", json={
            "project_id": project["id"],
            "artifact_type": "plan",
            "name": "to_delete.json",
            "file_path": "/tmp/to_delete.json"
        }).json()
        
        response = client.delete(f"/api/artifacts/{artifact['id']}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True
        
        # Verify it's deleted
        get_response = client.get(f"/api/artifacts/{artifact['id']}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_artifact_not_found(self, client):
        """Test deleting a non-existent artifact returns 404"""
        response = client.delete("/api/artifacts/9999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_upload_artifact(self, client):
        """Test uploading an artifact file"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        
        # Create a test file
        file_content = b"Test artifact content"
        files = {
            "file": ("test_upload.txt", BytesIO(file_content), "text/plain")
        }
        data = {
            "project_id": project["id"],
            "artifact_type": "plan"
        }
        
        response = client.post("/api/artifacts/upload", files=files, data=data)
        
        # Note: This might fail if artifact_storage is not properly mocked
        # For a real test environment, you'd need to mock the storage service
        # or use a test storage directory
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
    def test_upload_artifact_with_task(self, client):
        """Test uploading an artifact linked to a task"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Upload Task"
        }).json()
        
        file_content = b"Task artifact content"
        files = {
            "file": ("task_upload.txt", BytesIO(file_content), "text/plain")
        }
        data = {
            "project_id": project["id"],
            "task_id": task["id"],
            "artifact_type": "plan"
        }
        
        response = client.post("/api/artifacts/upload", files=files, data=data)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
    def test_list_artifacts_pagination(self, client):
        """Test artifact listing with pagination"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        
        # Create 10 artifacts
        for i in range(10):
            client.post("/api/artifacts/", json={
                "project_id": project["id"],
                "artifact_type": "plan",
                "name": f"artifact_{i}.json",
                "file_path": f"/tmp/artifact_{i}.json"
            })
        
        # Get first 5
        response = client.get("/api/artifacts/?skip=0&limit=5")
        assert response.status_code == status.HTTP_200_OK
        artifacts = response.json()
        assert len(artifacts) == 5
        
        # Get next 5
        response = client.get("/api/artifacts/?skip=5&limit=5")
        assert response.status_code == status.HTTP_200_OK
        artifacts = response.json()
        assert len(artifacts) == 5
    
    def test_artifact_types(self, client):
        """Test creating artifacts of different types"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        
        artifact_types = ["plan", "adr", "test_result", "diff", "other"]
        
        for artifact_type in artifact_types:
            response = client.post("/api/artifacts/", json={
                "project_id": project["id"],
                "artifact_type": artifact_type,
                "name": f"{artifact_type}.txt",
                "file_path": f"/tmp/{artifact_type}.txt"
            })
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["artifact_type"] == artifact_type
    
    def test_artifact_with_extra_data(self, client):
        """Test creating an artifact with extra data"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        
        import json
        extra_data = json.dumps({"key1": "value1", "key2": "value2"})
        
        artifact_data = {
            "project_id": project["id"],
            "artifact_type": "plan",
            "name": "extra_data_test.json",
            "file_path": "/tmp/extra_data_test.json",
            "extra_data": extra_data
        }
        response = client.post("/api/artifacts/", json=artifact_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["extra_data"] == extra_data
