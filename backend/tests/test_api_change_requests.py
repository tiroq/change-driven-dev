"""
API tests for change request endpoints
"""

import pytest
from fastapi import status


class TestChangeRequestsAPI:
    """Test change request API endpoints"""
    
    def test_list_change_requests_empty(self, client):
        """Test listing change requests when none exist"""
        response = client.get("/api/change-requests/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
    
    def test_create_change_request(self, client):
        """Test creating a new change request"""
        # Create project and task
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Test Task"
        }).json()
        
        cr_data = {
            "task_id": task["id"],
            "phase": "planner",
            "content": "This is a test change request"
        }
        response = client.post("/api/change-requests/", json=cr_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["task_id"] == task["id"]
        assert data["phase"] == "planner"
        assert data["content"] == "This is a test change request"
        assert data["status"] == "draft"
        assert data["version"] == 1
        assert "id" in data
    
    def test_create_change_request_invalid_task(self, client):
        """Test creating a change request with invalid task fails"""
        cr_data = {
            "task_id": 9999,
            "phase": "planner",
            "content": "Invalid task"
        }
        response = client.post("/api/change-requests/", json=cr_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]
    
    def test_list_change_requests(self, client):
        """Test listing multiple change requests"""
        # Create project and task
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Test Task"
        }).json()
        
        # Create multiple change requests
        for i in range(3):
            client.post("/api/change-requests/", json={
                "task_id": task["id"],
                "phase": "planner",
                "content": f"Change request {i+1}"
            })
        
        response = client.get("/api/change-requests/")
        assert response.status_code == status.HTTP_200_OK
        
        crs = response.json()
        assert len(crs) == 3
    
    def test_list_change_requests_filter_by_task(self, client):
        """Test listing change requests filtered by task"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        
        # Create two tasks
        task1 = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Task 1"
        }).json()
        task2 = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Task 2"
        }).json()
        
        # Create change requests for each task
        client.post("/api/change-requests/", json={
            "task_id": task1["id"],
            "phase": "planner",
            "content": "CR for task 1"
        })
        client.post("/api/change-requests/", json={
            "task_id": task1["id"],
            "phase": "architect",
            "content": "Another CR for task 1"
        })
        client.post("/api/change-requests/", json={
            "task_id": task2["id"],
            "phase": "planner",
            "content": "CR for task 2"
        })
        
        # Filter by task 1
        response = client.get(f"/api/change-requests/?task_id={task1['id']}")
        assert response.status_code == status.HTTP_200_OK
        
        crs = response.json()
        assert len(crs) == 2
        assert all(cr["task_id"] == task1["id"] for cr in crs)
    
    def test_list_change_requests_filter_by_status(self, client):
        """Test listing change requests filtered by status"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Test Task"
        }).json()
        
        # Create change requests and update their statuses
        cr1 = client.post("/api/change-requests/", json={
            "task_id": task["id"],
            "phase": "planner",
            "content": "CR 1"
        }).json()
        cr2 = client.post("/api/change-requests/", json={
            "task_id": task["id"],
            "phase": "planner",
            "content": "CR 2"
        }).json()
        
        # Submit cr1
        client.post(f"/api/change-requests/{cr1['id']}/submit")
        
        # Filter by submitted status
        response = client.get("/api/change-requests/?status=submitted")
        assert response.status_code == status.HTTP_200_OK
        
        crs = response.json()
        assert len(crs) == 1
        assert crs[0]["status"] == "submitted"
    
    def test_get_change_request(self, client):
        """Test getting a single change request by ID"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Test Task"
        }).json()
        
        create_response = client.post("/api/change-requests/", json={
            "task_id": task["id"],
            "phase": "planner",
            "content": "Get CR Test"
        })
        cr_id = create_response.json()["id"]
        
        response = client.get(f"/api/change-requests/{cr_id}")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == cr_id
        assert data["content"] == "Get CR Test"
    
    def test_get_change_request_not_found(self, client):
        """Test getting a non-existent change request returns 404"""
        response = client.get("/api/change-requests/9999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_submit_change_request(self, client):
        """Test submitting a change request for approval"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Test Task"
        }).json()
        
        cr = client.post("/api/change-requests/", json={
            "task_id": task["id"],
            "phase": "planner",
            "content": "Submit Test"
        }).json()
        
        response = client.post(f"/api/change-requests/{cr['id']}/submit")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == cr["id"]
        assert data["status"] == "submitted"
        assert "message" in data
        
        # Verify status changed
        get_response = client.get(f"/api/change-requests/{cr['id']}")
        assert get_response.json()["status"] == "submitted"
    
    def test_submit_change_request_not_found(self, client):
        """Test submitting a non-existent change request returns 404"""
        response = client.post("/api/change-requests/9999/submit")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_approve_change_request(self, client):
        """Test approving a change request"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Test Task"
        }).json()
        
        cr = client.post("/api/change-requests/", json={
            "task_id": task["id"],
            "phase": "planner",
            "content": "Approve Test"
        }).json()
        
        response = client.post(
            f"/api/change-requests/{cr['id']}/approve?approver=test_user"
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == cr["id"]
        assert data["status"] == "approved"
        assert "message" in data
        
        # Verify status changed
        get_response = client.get(f"/api/change-requests/{cr['id']}")
        assert get_response.json()["status"] == "approved"
    
    def test_approve_change_request_default_approver(self, client):
        """Test approving with default approver"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Test Task"
        }).json()
        
        cr = client.post("/api/change-requests/", json={
            "task_id": task["id"],
            "phase": "planner",
            "content": "Approve Test"
        }).json()
        
        response = client.post(f"/api/change-requests/{cr['id']}/approve")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "approved"
    
    def test_approve_change_request_not_found(self, client):
        """Test approving a non-existent change request returns 404"""
        response = client.post("/api/change-requests/9999/approve")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_reject_change_request(self, client):
        """Test rejecting a change request"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Test Task"
        }).json()
        
        cr = client.post("/api/change-requests/", json={
            "task_id": task["id"],
            "phase": "planner",
            "content": "Reject Test"
        }).json()
        
        response = client.post(
            f"/api/change-requests/{cr['id']}/reject?approver=test_user&reason=Not%20good%20enough"
        )
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == cr["id"]
        assert data["status"] == "rejected"
        assert "message" in data
        
        # Verify status changed
        get_response = client.get(f"/api/change-requests/{cr['id']}")
        assert get_response.json()["status"] == "rejected"
    
    def test_reject_change_request_no_reason(self, client):
        """Test rejecting a change request without a reason"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Test Task"
        }).json()
        
        cr = client.post("/api/change-requests/", json={
            "task_id": task["id"],
            "phase": "planner",
            "content": "Reject Test"
        }).json()
        
        response = client.post(f"/api/change-requests/{cr['id']}/reject")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "rejected"
    
    def test_reject_change_request_not_found(self, client):
        """Test rejecting a non-existent change request returns 404"""
        response = client.post("/api/change-requests/9999/reject")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_change_request_workflow(self, client):
        """Test the complete workflow: create -> submit -> approve"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Workflow Task"
        }).json()
        
        # Create change request
        cr = client.post("/api/change-requests/", json={
            "task_id": task["id"],
            "phase": "planner",
            "content": "Workflow test"
        }).json()
        assert cr["status"] == "draft"
        
        # Submit for approval
        submit_response = client.post(f"/api/change-requests/{cr['id']}/submit")
        assert submit_response.json()["status"] == "submitted"
        
        # Approve
        approve_response = client.post(
            f"/api/change-requests/{cr['id']}/approve?approver=reviewer"
        )
        assert approve_response.json()["status"] == "approved"
        
        # Verify final state
        final = client.get(f"/api/change-requests/{cr['id']}")
        assert final.json()["status"] == "approved"
    
    def test_change_request_workflow_reject(self, client):
        """Test the workflow: create -> submit -> reject"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Workflow Task"
        }).json()
        
        # Create and submit
        cr = client.post("/api/change-requests/", json={
            "task_id": task["id"],
            "phase": "planner",
            "content": "Reject workflow test"
        }).json()
        client.post(f"/api/change-requests/{cr['id']}/submit")
        
        # Reject
        reject_response = client.post(
            f"/api/change-requests/{cr['id']}/reject?approver=reviewer&reason=Needs%20improvement"
        )
        assert reject_response.json()["status"] == "rejected"
        
        # Verify final state
        final = client.get(f"/api/change-requests/{cr['id']}")
        assert final.json()["status"] == "rejected"
    
    def test_create_change_requests_different_phases(self, client):
        """Test creating change requests for different phases"""
        project = client.post("/api/projects/", json={"name": "Test Project"}).json()
        task = client.post("/api/tasks/", json={
            "project_id": project["id"],
            "title": "Multi-phase Task"
        }).json()
        
        phases = ["planner", "architect", "coder", "review_approval"]
        
        for phase in phases:
            response = client.post("/api/change-requests/", json={
                "task_id": task["id"],
                "phase": phase,
                "content": f"CR for {phase}"
            })
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["phase"] == phase
