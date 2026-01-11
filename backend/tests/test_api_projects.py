"""
API tests for project endpoints
"""

import pytest
from fastapi import status


class TestProjectsAPI:
    """Test project API endpoints"""
    
    def test_list_projects_empty(self, client):
        """Test listing projects when none exist"""
        response = client.get("/api/projects/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
    
    def test_create_project(self, client):
        """Test creating a new project"""
        project_data = {
            "name": "Test Project",
            "description": "A test project",
            "root_path": "/tmp/test",
            "default_engine": "copilot_cli"
        }
        response = client.post("/api/projects/", json=project_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["description"] == "A test project"
        assert data["root_path"] == "/tmp/test"
        assert data["default_engine"] == "copilot_cli"
        assert "id" in data
        assert "db_path" in data
    
    def test_create_project_minimal(self, client):
        """Test creating a project with minimal data"""
        project_data = {
            "name": "Minimal Project"
        }
        response = client.post("/api/projects/", json=project_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == "Minimal Project"
        assert data["description"] is None
        assert data["default_engine"] == "copilot_cli"
    
    def test_create_duplicate_project(self, client):
        """Test creating a project with duplicate name fails"""
        project_data = {
            "name": "Duplicate Project",
            "description": "First project"
        }
        response1 = client.post("/api/projects/", json=project_data)
        assert response1.status_code == status.HTTP_200_OK
        
        # Try to create with same name
        response2 = client.post("/api/projects/", json=project_data)
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response2.json()["detail"]
    
    def test_list_projects(self, client):
        """Test listing multiple projects"""
        # Create multiple projects
        client.post("/api/projects/", json={"name": "Project 1"})
        client.post("/api/projects/", json={"name": "Project 2"})
        client.post("/api/projects/", json={"name": "Project 3"})
        
        response = client.get("/api/projects/")
        assert response.status_code == status.HTTP_200_OK
        
        projects = response.json()
        assert len(projects) == 3
        assert projects[0]["name"] == "Project 1"
        assert projects[1]["name"] == "Project 2"
        assert projects[2]["name"] == "Project 3"
    
    def test_list_projects_with_pagination(self, client):
        """Test listing projects with pagination"""
        # Create 5 projects
        for i in range(5):
            client.post("/api/projects/", json={"name": f"Project {i+1}"})
        
        # Get first 2
        response = client.get("/api/projects/?skip=0&limit=2")
        assert response.status_code == status.HTTP_200_OK
        projects = response.json()
        assert len(projects) == 2
        
        # Get next 2
        response = client.get("/api/projects/?skip=2&limit=2")
        assert response.status_code == status.HTTP_200_OK
        projects = response.json()
        assert len(projects) == 2
    
    def test_get_project(self, client):
        """Test getting a single project by ID"""
        # Create a project
        create_response = client.post("/api/projects/", json={
            "name": "Get Project Test",
            "description": "Test getting a project"
        })
        project_id = create_response.json()["id"]
        
        # Get the project
        response = client.get(f"/api/projects/{project_id}")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == "Get Project Test"
        assert data["description"] == "Test getting a project"
    
    def test_get_project_not_found(self, client):
        """Test getting a non-existent project returns 404"""
        response = client.get("/api/projects/9999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]
    
    def test_update_project(self, client):
        """Test updating a project"""
        # Create a project
        create_response = client.post("/api/projects/", json={
            "name": "Original Name",
            "description": "Original description"
        })
        project_id = create_response.json()["id"]
        
        # Update the project
        update_data = {
            "description": "Updated description",
            "root_path": "/new/path",
            "default_engine": "new_engine"
        }
        response = client.patch(f"/api/projects/{project_id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == "Original Name"  # Name should not change
        assert data["description"] == "Updated description"
        assert data["root_path"] == "/new/path"
        assert data["default_engine"] == "new_engine"
    
    def test_update_project_not_found(self, client):
        """Test updating a non-existent project returns 404"""
        response = client.patch("/api/projects/9999", json={"description": "New desc"})
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_project(self, client):
        """Test deleting a project"""
        # Create a project
        create_response = client.post("/api/projects/", json={"name": "To Delete"})
        project_id = create_response.json()["id"]
        
        # Delete the project
        response = client.delete(f"/api/projects/{project_id}")
        assert response.status_code == status.HTTP_200_OK
        
        # Verify it's deleted
        get_response = client.get(f"/api/projects/{project_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_project_not_found(self, client):
        """Test deleting a non-existent project returns 404"""
        response = client.delete("/api/projects/9999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
