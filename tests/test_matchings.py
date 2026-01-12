# tests/test_matchings.py

import pytest
from httpx import AsyncClient


@pytest.fixture
async def uploaded_file_id_3participants(client: AsyncClient,
                                         raw_form_data_3participants_csv: str) -> str:
    """Upload a 3-participant file and return its ID"""
    with open(raw_form_data_3participants_csv, 'rb') as f:
        files = {'file': ('raw_form_data_3participants.csv', f, 'text/csv')}
        response = await client.post("/files/upload", files = files)

    return response.json()["file_id"]


@pytest.fixture
async def uploaded_file_id_30participants(client: AsyncClient,
                                          raw_form_data_30participants_csv: str) -> str:
    """Upload a 30-participant file and return its ID"""
    with open(raw_form_data_30participants_csv, 'rb') as f:
        files = {'file': ('raw_form_data_30participants.csv', f, 'text/csv')}
        response = await client.post("/files/upload", files = files)

    return response.json()["file_id"]


@pytest.mark.asyncio
async def test_create_matching_3participants(client: AsyncClient,
                                             uploaded_file_id_3participants: str):
    """Test creating a matching with 3 participants"""
    response = await client.post(
        "/matchings",
        params = {"file_id": uploaded_file_id_3participants}
    )

    assert response.status_code == 200
    data = response.json()
    assert "matching_id" in data
    assert data["file_id"] == uploaded_file_id_3participants
    assert data["total_count"] == 3
    assert data["success"] is True  # Should succeed with 3 people


@pytest.mark.asyncio
async def test_create_matching_30participants(client: AsyncClient,
                                              uploaded_file_id_30participants: str):
    """Test creating a matching with 30 participants"""
    response = await client.post(
        "/matchings",
        params = {"file_id": uploaded_file_id_30participants}
    )

    assert response.status_code == 200
    data = response.json()
    assert "matching_id" in data
    assert data["total_count"] == 30


@pytest.mark.asyncio
async def test_create_matching_invalid_file_id(client: AsyncClient):
    """Test creating matching with non-existent file_id"""
    response = await client.post(
        "/matchings",
        params = {"file_id": "fake-file-id"}
    )

    assert response.status_code == 404
    assert "No uploaded file found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_matching(client: AsyncClient, uploaded_file_id_3participants: str):
    """Test retrieving matching details with graph data"""
    # Create matching first
    create_response = await client.post(
        "/matchings",
        params = {"file_id": uploaded_file_id_3participants}
    )
    matching_id = create_response.json()["matching_id"]

    # Get matching details
    response = await client.get(f"/matchings/{matching_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["matching_id"] == matching_id
    assert "nodes" in data
    assert "links" in data
    assert "participants" in data
    assert "cycles" in data
    assert "unmatched" in data
    assert data["participants"] > 0


@pytest.mark.asyncio
async def test_matching_graph_structure(client: AsyncClient, uploaded_file_id_3participants: str):
    """Test that matching graph has correct structure"""
    # Create matching
    create_response = await client.post(
        "/matchings",
        params = {"file_id": uploaded_file_id_3participants}
    )
    matching_id = create_response.json()["matching_id"]

    # Get graph data
    response = await client.get(f"/matchings/{matching_id}")
    data = response.json()

    # Verify node structure
    assert len(data["nodes"]) > 0
    for node in data["nodes"]:
        assert "id" in node
        assert "name" in node
        assert "discord" in node
        assert "email" in node

    # Verify link structure
    assert len(data["links"]) > 0
    for link in data["links"]:
        assert "source" in link
        assert "target" in link


@pytest.mark.asyncio
async def test_download_matching(client: AsyncClient, uploaded_file_id_3participants: str):
    """Test downloading matching CSV output"""
    # Create matching
    create_response = await client.post(
        "/matchings",
        params = {"file_id": uploaded_file_id_3participants}
    )
    matching_id = create_response.json()["matching_id"]

    # Download
    response = await client.get(f"/matchings/{matching_id}/download")

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]

    # Verify CSV content exists
    content = response.text
    assert len(content) > 0
    assert "Requestor Name" in content or "Assignee Name" in content


@pytest.mark.asyncio
async def test_rematch_same_file(client: AsyncClient, uploaded_file_id_3participants: str):
    """Test creating multiple matchings from same file"""
    # Create first matching
    response1 = await client.post(
        "/matchings",
        params = {"file_id": uploaded_file_id_3participants}
    )
    matching_id_1 = response1.json()["matching_id"]

    # Create second matching (rematch)
    response2 = await client.post(
        "/matchings",
        params = {"file_id": uploaded_file_id_3participants}
    )
    matching_id_2 = response2.json()["matching_id"]

    # Should have different matching IDs
    assert matching_id_1 != matching_id_2

    # Both should reference same file
    assert response1.json()["file_id"] == response2.json()["file_id"]


@pytest.mark.asyncio
async def test_confirm_matching_requires_auth(client: AsyncClient,
                                              uploaded_file_id_3participants: str):
    """Test that confirming requires authentication"""
    # Create matching
    create_response = await client.post(
        "/matchings",
        params = {"file_id": uploaded_file_id_3participants}
    )
    matching_id = create_response.json()["matching_id"]

    # Try to confirm without auth
    response = await client.post(f"/matchings/{matching_id}/confirm")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_confirm_matching_authenticated(
        authenticated_client: AsyncClient,
        raw_form_data_3participants_csv: str
):
    """Test confirming matching while authenticated"""
    # Upload file
    with open(raw_form_data_3participants_csv, 'rb') as f:
        files = {'file': ('raw_form_data_3participants.csv', f, 'text/csv')}
        upload_response = await authenticated_client.post("/files/upload", files = files)

    file_id = upload_response.json()["file_id"]

    # Create matching
    create_response = await authenticated_client.post(
        "/matchings",
        params = {"file_id": file_id}
    )
    matching_id = create_response.json()["matching_id"]

    # Confirm matching
    response = await authenticated_client.post(f"/matchings/{matching_id}/confirm")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["matching_id"] == matching_id


@pytest.mark.asyncio
async def test_confirm_matching_twice_fails(
        authenticated_client: AsyncClient,
        raw_form_data_3participants_csv: str
):
    """Test that confirming the same matching twice fails"""
    # Upload and create matching
    with open(raw_form_data_3participants_csv, 'rb') as f:
        files = {'file': ('raw_form_data_3participants.csv', f, 'text/csv')}
        upload_response = await authenticated_client.post("/files/upload", files = files)

    file_id = upload_response.json()["file_id"]

    create_response = await authenticated_client.post(
        "/matchings",
        params = {"file_id": file_id}
    )
    matching_id = create_response.json()["matching_id"]

    # First confirmation should succeed
    response1 = await authenticated_client.post(f"/matchings/{matching_id}/confirm")
    assert response1.status_code == 200

    # Second confirmation should fail
    response2 = await authenticated_client.post(f"/matchings/{matching_id}/confirm")
    assert response2.status_code == 400
    assert "already confirmed" in response2.json()["detail"]


@pytest.mark.asyncio
async def test_get_my_matchings(authenticated_client: AsyncClient,
                                raw_form_data_3participants_csv: str):
    """Test retrieving user's matching history"""
    # Upload and create matching
    with open(raw_form_data_3participants_csv, 'rb') as f:
        files = {'file': ('raw_form_data_3participants.csv', f, 'text/csv')}
        upload_response = await authenticated_client.post("/files/upload", files = files)

    file_id = upload_response.json()["file_id"]

    create_response = await authenticated_client.post(
        "/matchings",
        params = {"file_id": file_id}
    )
    matching_id = create_response.json()["matching_id"]

    # Confirm it
    await authenticated_client.post(f"/matchings/{matching_id}/confirm")

    # Get history
    response = await authenticated_client.get("/my-matchings")

    assert response.status_code == 200
    data = response.json()
    assert "matchings" in data
    assert len(data["matchings"]) == 1
    assert data["matchings"][0]["matching_id"] == matching_id
    assert data["matchings"][0]["participant_count"] == 3


@pytest.mark.asyncio
async def test_get_nonexistent_matching(client: AsyncClient):
    """Test getting non-existent matching returns 404"""
    response = await client.get("/matchings/fake-matching-id")

    assert response.status_code == 404