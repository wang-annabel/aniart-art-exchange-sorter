# tests/test_files.py

import pytest
from httpx import AsyncClient



@pytest.mark.asyncio
async def test_upload_raw_form_data(client: AsyncClient, raw_form_data_csv: str):
    """Test uploading raw Google Form response CSV"""
    with open(raw_form_data_csv, 'rb') as f:
        files = {'file': ('raw_form_data.csv', f, 'text/csv')}
        response = await client.post("/files/upload", files = files)

    assert response.status_code == 200
    data = response.json()
    assert "file_id" in data
    assert data["participant_count"] > 0


@pytest.mark.asyncio
async def test_upload_1_participant(client: AsyncClient, raw_form_data_1participant_csv: str):
    """Test upload with 1 participant"""
    with open(raw_form_data_1participant_csv, 'rb') as f:
        files = {'file': ('raw_form_data_1participant.csv', f, 'text/csv')}
        response = await client.post("/files/upload", files = files)

    assert response.status_code == 200
    data = response.json()
    assert data["participant_count"] == 1


@pytest.mark.asyncio
async def test_upload_3_participants(client: AsyncClient, raw_form_data_3participants_csv: str):
    """Test upload with 3 participants"""
    with open(raw_form_data_3participants_csv, 'rb') as f:
        files = {'file': ('raw_form_data_3participants.csv', f, 'text/csv')}
        response = await client.post("/files/upload", files = files)

    assert response.status_code == 200
    data = response.json()
    assert data["participant_count"] == 3


@pytest.mark.asyncio
async def test_upload_30_participants(client: AsyncClient, raw_form_data_30participants_csv: str):
    """Test upload with 30 participants"""
    with open(raw_form_data_30participants_csv, 'rb') as f:
        files = {'file': ('raw_form_data_30participants.csv', f, 'text/csv')}
        response = await client.post("/files/upload", files = files)

    assert response.status_code == 200
    data = response.json()
    assert data["participant_count"] == 30


@pytest.mark.asyncio
async def test_upload_invalid_file(client: AsyncClient):
    """Test uploading non-CSV file fails"""
    files = {'file': ('test.txt', b'not a csv', 'text/plain')}
    response = await client.post("/files/upload", files = files)

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_file_info(client: AsyncClient, raw_form_data_3participants_csv: str):
    """Test retrieving file info"""
    # Upload file first
    with open(raw_form_data_3participants_csv, 'rb') as f:
        files = {'file': ('raw_form_data_3participants.csv', f, 'text/csv')}
        upload_response = await client.post("/files/upload", files = files)

    file_id = upload_response.json()["file_id"]

    # Get file info
    response = await client.get(f"/files/{file_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["file_id"] == file_id
    assert data["participant_count"] == 3


@pytest.mark.asyncio
async def test_get_nonexistent_file(client: AsyncClient):
    """Test getting info for non-existent file"""
    response = await client.get("/files/fake-id-123")

    assert response.status_code == 404
    assert "No file found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_authenticated(authenticated_client: AsyncClient, raw_form_data_csv: str):
    """Test that authenticated users can upload files"""
    with open(raw_form_data_csv, 'rb') as f:
        files = {'file': ('raw_form_data.csv', f, 'text/csv')}
        response = await authenticated_client.post("/files/upload", files = files)

    assert response.status_code == 200
    data = response.json()
    assert "file_id" in data