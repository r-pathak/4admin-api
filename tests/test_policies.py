"""
Unit tests for the policies router.
"""
import base64
import datetime
from fastapi import status


class TestPolicyUpload:
    """Tests for policy upload endpoint."""
    
    def test_upload_policy_success(self, client):
        """Test successful policy upload."""
        # Create a sample base64 file
        sample_file = base64.b64encode(b"Sample policy document").decode()
        
        payload = {
            "file_b64": sample_file,
            "filename": "test_policy.pdf",
            "tenant_id": "tenant-123",
            "retain": True
        }
        
        response = client.post("/policies/", json=payload)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        # Check response structure
        assert "analysis" in data
        assert "file_url" in data
        
        # Check analysis fields
        analysis = data["analysis"]
        assert "id" in analysis
        assert analysis["tenant_id"] == "tenant-123"
        assert "extracted_fields" in analysis
        assert isinstance(analysis["extracted_fields"], list)
        assert "created_at" in analysis
        
        # Check file URL is present when retain=True
        assert data["file_url"] is not None
        assert f"/policies/{analysis['id']}/file" in data["file_url"]
    
    def test_upload_policy_without_retention(self, client):
        """Test policy upload without file retention."""
        sample_file = base64.b64encode(b"Sample policy document").decode()
        
        payload = {
            "file_b64": sample_file,
            "filename": "test_policy.pdf",
            "retain": False
        }
        
        response = client.post("/policies/", json=payload)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        # File URL should be None when retain=False
        assert data["file_url"] is None
    
    def test_upload_policy_minimal_data(self, client):
        """Test policy upload with only required fields."""
        sample_file = base64.b64encode(b"Minimal policy").decode()
        
        payload = {
            "file_b64": sample_file
        }
        
        response = client.post("/policies/", json=payload)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "analysis" in data
    
    def test_upload_policy_missing_required_field(self, client):
        """Test policy upload with missing required field."""
        payload = {
            "filename": "test.pdf"
            # Missing file_b64
        }
        
        response = client.post("/policies/", json=payload)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestPolicyGet:
    """Tests for getting policy endpoint."""
    
    def test_get_policy_success(self, client):
        """Test successful retrieval of a policy."""
        # First, upload a policy
        sample_file = base64.b64encode(b"Sample policy").decode()
        upload_payload = {
            "file_b64": sample_file,
            "tenant_id": "tenant-456",
            "retain": True
        }
        
        upload_response = client.post("/policies/", json=upload_payload)
        policy_id = upload_response.json()["analysis"]["id"]
        
        # Now get the policy
        response = client.get(f"/policies/{policy_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["analysis"]["id"] == policy_id
        assert data["analysis"]["tenant_id"] == "tenant-456"
        assert data["file_url"] is not None
    
    def test_get_policy_not_found(self, client):
        """Test getting a non-existent policy."""
        response = client.get("/policies/non-existent-id")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_policy_without_file(self, client):
        """Test getting a policy that doesn't have a retained file."""
        # Upload without retention
        sample_file = base64.b64encode(b"Sample policy").decode()
        upload_payload = {
            "file_b64": sample_file,
            "retain": False
        }
        
        upload_response = client.post("/policies/", json=upload_payload)
        policy_id = upload_response.json()["analysis"]["id"]
        
        # Get the policy
        response = client.get(f"/policies/{policy_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["file_url"] is None


class TestPolicyUpdate:
    """Tests for updating policy endpoint."""
    
    def test_update_policy_success(self, client):
        """Test successful policy update."""
        # First, upload a policy
        sample_file = base64.b64encode(b"Sample policy").decode()
        upload_payload = {
            "file_b64": sample_file,
            "tenant_id": "tenant-789"
        }
        
        upload_response = client.post("/policies/", json=upload_payload)
        policy_id = upload_response.json()["analysis"]["id"]
        
        # Update the policy
        update_payload = {
            "updated_fields": [
                {
                    "name": "coverage_amount",
                    "value": "500000",
                    "confidence": 0.98,
                    "source_pages": [2, 3],
                    "citation_text": "Coverage amount listed on page 2",
                    "model_version": "v1.2.3"
                },
                {
                    "name": "premium",
                    "value": "1500",
                    "confidence": 0.95,
                    "source_pages": [1]
                }
            ]
        }
        
        response = client.put(f"/policies/{policy_id}", json=update_payload)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["id"] == policy_id
        assert "updated_at" in data
        assert data["message"] == "Policy analysis updated successfully"
        
        # Verify the update by getting the policy
        get_response = client.get(f"/policies/{policy_id}")
        updated_fields = get_response.json()["analysis"]["extracted_fields"]
        
        assert len(updated_fields) == 2
        assert updated_fields[0]["name"] == "coverage_amount"
        assert updated_fields[0]["value"] == "500000"
        assert updated_fields[1]["name"] == "premium"
    
    def test_update_policy_not_found(self, client):
        """Test updating a non-existent policy."""
        update_payload = {
            "updated_fields": [
                {
                    "name": "test_field",
                    "value": "test_value"
                }
            ]
        }
        
        response = client.put("/policies/non-existent-id", json=update_payload)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_policy_empty_fields(self, client):
        """Test updating policy with empty fields list."""
        # Upload a policy first
        sample_file = base64.b64encode(b"Sample policy").decode()
        upload_response = client.post("/policies/", json={"file_b64": sample_file})
        policy_id = upload_response.json()["analysis"]["id"]
        
        # Update with empty fields
        update_payload = {
            "updated_fields": []
        }
        
        response = client.put(f"/policies/{policy_id}", json=update_payload)
        
        assert response.status_code == status.HTTP_200_OK


class TestPolicyList:
    """Tests for listing policies endpoint."""
    
    def test_list_all_policies(self, client):
        """Test listing all policies."""
        # Upload multiple policies
        sample_file = base64.b64encode(b"Sample policy").decode()
        
        for i in range(3):
            client.post("/policies/", json={
                "file_b64": sample_file,
                "tenant_id": f"tenant-{i}"
            })
        
        # List all policies
        response = client.get("/policies/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 3
    
    def test_list_policies_by_tenant(self, client):
        """Test listing policies filtered by tenant."""
        sample_file = base64.b64encode(b"Sample policy").decode()
        
        # Upload policies for different tenants
        client.post("/policies/", json={
            "file_b64": sample_file,
            "tenant_id": "tenant-A"
        })
        client.post("/policies/", json={
            "file_b64": sample_file,
            "tenant_id": "tenant-A"
        })
        client.post("/policies/", json={
            "file_b64": sample_file,
            "tenant_id": "tenant-B"
        })
        
        # List policies for tenant-A
        response = client.get("/policies/?tenant_id=tenant-A")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data) == 2
        for policy in data:
            assert policy["analysis"]["tenant_id"] == "tenant-A"
    
    def test_list_policies_empty(self, client):
        """Test listing policies when none exist."""
        response = client.get("/policies/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_list_policies_no_match_tenant(self, client):
        """Test listing policies with tenant filter that matches nothing."""
        # Upload a policy
        sample_file = base64.b64encode(b"Sample policy").decode()
        client.post("/policies/", json={
            "file_b64": sample_file,
            "tenant_id": "tenant-X"
        })
        
        # Query for different tenant
        response = client.get("/policies/?tenant_id=tenant-Y")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data) == 0


class TestPolicyDelete:
    """Tests for deleting policy endpoint."""
    
    def test_delete_policy_success(self, client):
        """Test successful policy deletion."""
        # Upload a policy
        sample_file = base64.b64encode(b"Sample policy").decode()
        upload_response = client.post("/policies/", json={"file_b64": sample_file})
        policy_id = upload_response.json()["analysis"]["id"]
        
        # Delete the policy
        response = client.delete(f"/policies/{policy_id}")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify it's deleted
        get_response = client.get(f"/policies/{policy_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_policy_not_found(self, client):
        """Test deleting a non-existent policy."""
        response = client.delete("/policies/non-existent-id")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_policy_multiple_times(self, client):
        """Test deleting the same policy twice."""
        # Upload a policy
        sample_file = base64.b64encode(b"Sample policy").decode()
        upload_response = client.post("/policies/", json={"file_b64": sample_file})
        policy_id = upload_response.json()["analysis"]["id"]
        
        # First deletion should succeed
        response1 = client.delete(f"/policies/{policy_id}")
        assert response1.status_code == status.HTTP_204_NO_CONTENT
        
        # Second deletion should fail
        response2 = client.delete(f"/policies/{policy_id}")
        assert response2.status_code == status.HTTP_404_NOT_FOUND


class TestPolicyIntegration:
    """Integration tests for policy workflows."""
    
    def test_full_policy_lifecycle(self, client):
        """Test complete policy lifecycle: upload, get, update, list, delete."""
        # 1. Upload
        sample_file = base64.b64encode(b"Complete lifecycle test").decode()
        upload_response = client.post("/policies/", json={
            "file_b64": sample_file,
            "filename": "lifecycle_test.pdf",
            "tenant_id": "lifecycle-tenant",
            "retain": True
        })
        
        assert upload_response.status_code == status.HTTP_201_CREATED
        policy_id = upload_response.json()["analysis"]["id"]
        
        # 2. Get
        get_response = client.get(f"/policies/{policy_id}")
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json()["analysis"]["tenant_id"] == "lifecycle-tenant"
        
        # 3. Update
        update_response = client.put(f"/policies/{policy_id}", json={
            "updated_fields": [
                {
                    "name": "policy_number",
                    "value": "POL-12345"
                }
            ]
        })
        assert update_response.status_code == status.HTTP_200_OK
        
        # 4. List
        list_response = client.get("/policies/?tenant_id=lifecycle-tenant")
        assert list_response.status_code == status.HTTP_200_OK
        assert len(list_response.json()) == 1
        
        # 5. Delete
        delete_response = client.delete(f"/policies/{policy_id}")
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify deletion
        final_get = client.get(f"/policies/{policy_id}")
        assert final_get.status_code == status.HTTP_404_NOT_FOUND
    
    def test_multiple_tenants_isolation(self, client):
        """Test that policies from different tenants are properly isolated."""
        sample_file = base64.b64encode(b"Tenant isolation test").decode()
        
        # Create policies for different tenants
        tenant_a_response = client.post("/policies/", json={
            "file_b64": sample_file,
            "tenant_id": "tenant-alpha"
        })
        tenant_b_response = client.post("/policies/", json={
            "file_b64": sample_file,
            "tenant_id": "tenant-beta"
        })
        
        tenant_a_id = tenant_a_response.json()["analysis"]["id"]
        tenant_b_id = tenant_b_response.json()["analysis"]["id"]
        
        # Verify tenant A can only see their policy
        tenant_a_list = client.get("/policies/?tenant_id=tenant-alpha")
        assert len(tenant_a_list.json()) == 1
        assert tenant_a_list.json()[0]["analysis"]["id"] == tenant_a_id
        
        # Verify tenant B can only see their policy
        tenant_b_list = client.get("/policies/?tenant_id=tenant-beta")
        assert len(tenant_b_list.json()) == 1
        assert tenant_b_list.json()[0]["analysis"]["id"] == tenant_b_id

