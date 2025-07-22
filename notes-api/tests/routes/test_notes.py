from fastapi import status


class TestNotesRoutes:
    """Test suite for notes routes using database-level mocking"""

    def test_get_note_by_id_success(self, test_client_with_db_mock, sample_document):
        """Test successful retrieval of a note by ID"""
        # Arrange
        client, mock_db = test_client_with_db_mock
        note_id = 1
        mock_db.get.return_value = sample_document

        # Act
        response = client.get(f"/notes/{note_id}")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == sample_document.title
        assert data["content"] == sample_document.content
        assert data["file_path"] == sample_document.file_path
        mock_db.get.assert_called_once()

    def test_get_note_by_id_not_found(self, test_client_with_db_mock):
        """Test retrieval of a non-existent note"""
        # Arrange
        client, mock_db = test_client_with_db_mock
        note_id = 999
        mock_db.get.return_value = None

        # Act
        response = client.get(f"/notes/{note_id}")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Note with id 999 not found" in response.json()["detail"]
        mock_db.get.assert_called_once()

    def test_create_new_note_success(self, test_client_with_db_mock):
        """Test successful creation of a new note"""
        # Arrange
        client, mock_db = test_client_with_db_mock
        note_data = {
            "file_path": "/test/note.md",
            "title": "Test Note",
            "content": "This is a test note content",
            "document_type": "note",
            "metadata": {"tags": ["test", "sample"]},
        }

        # Mock the refresh to populate the document with an ID after save
        def mock_refresh(document):
            document.id = 1
            return document

        mock_db.refresh.side_effect = mock_refresh

        # Act
        response = client.post("/notes/", json=note_data)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == note_data["title"]
        assert data["content"] == note_data["content"]
        assert data["file_path"] == note_data["file_path"]
        mock_db.add.assert_called_once()
        mock_db.refresh.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_new_note_invalid_data(self, test_client_with_db_mock):
        """Test note creation with invalid data"""
        # Arrange
        client, mock_db = test_client_with_db_mock
        invalid_data = {
            "title": "Test Note"
            # Missing required fields
        }

        # Act
        response = client.post("/notes/", json=invalid_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_update_note(self, test_client_with_db_mock, sample_document):
        """Test note update"""
        # Arrange
        client, mock_db = test_client_with_db_mock
        note_id = 1
        update_data = {
            "title": "Updated Test Note",
            "content": "This is updated test note content",
        }

        # Mock get to return existing document
        mock_db.get.return_value = sample_document

        # Act
        response = client.put(f"/notes/{note_id}", json=update_data)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        mock_db.get.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_delete_note(self, test_client_with_db_mock, sample_document):
        """Test note deletion"""
        # Arrange
        client, mock_db = test_client_with_db_mock
        note_id = 1

        # Mock get to return existing document
        mock_db.get.return_value = sample_document

        # Act
        response = client.delete(f"/notes/{note_id}")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        mock_db.get.assert_called_once()
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_update_note_not_found(self, test_client_with_db_mock):
        """Test updating a non-existent note"""
        # Arrange
        client, mock_db = test_client_with_db_mock
        note_id = 999
        update_data = {
            "title": "Updated Test Note",
            "content": "This is updated test note content",
        }

        # Mock get to return None (document not found)
        mock_db.get.return_value = None

        # Act
        response = client.put(f"/notes/{note_id}", json=update_data)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Note with id 999 not found" in response.json()["detail"]
        mock_db.get.assert_called_once()
        mock_db.commit.assert_not_called()

    def test_delete_note_not_found(self, test_client_with_db_mock):
        """Test deleting a non-existent note"""
        # Arrange
        client, mock_db = test_client_with_db_mock
        note_id = 999

        # Mock get to return None (document not found)
        mock_db.get.return_value = None

        # Act
        response = client.delete(f"/notes/{note_id}")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is False
        mock_db.get.assert_called_once()
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_invalid_note_id_type(self, test_client_with_db_mock):
        """Test request with invalid note ID type"""
        # Arrange
        client, mock_db = test_client_with_db_mock

        # Act
        response = client.get("/notes/invalid_id")

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
