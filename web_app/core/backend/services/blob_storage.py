"""
Azure Blob Storage Service Wrapper
Provides helper methods for uploading, downloading, listing, and deleting blobs in Azure Storage.
"""

import logging
from typing import Any, Dict, List, Optional
from azure.storage.blob import BlobServiceClient, ContainerClient, ContentSettings
from azure.core.exceptions import ResourceNotFoundError, AzureError

from web_app.core.backend.utils.config import get_settings

logger = logging.getLogger(__name__)


class BlobStorageBackend:
    """Wrapper class for Azure Blob Storage operations."""

    def __init__(self):
        settings = get_settings()
        self.connection_string = settings.azure_storage_connection_string
        self.container_name = settings.azure_storage_container_name
        self._blob_service_client: Optional[BlobServiceClient] = None
        self._container_client: Optional[ContainerClient] = None

        if self.connection_string:
            try:
                self._blob_service_client = BlobServiceClient.from_connection_string(
                    self.connection_string
                )
                self._container_client = self._blob_service_client.get_container_client(
                    self.container_name
                )
                # Create the container if it doesn't exist
                try:
                    if not self._container_client.exists():
                        self._container_client.create_container()
                        logger.info(f"Created Azure Blob container: {self.container_name}")
                except AzureError as ae:
                    # Catch cases where container creation might fail due to race conditions or permissions
                    logger.warning(f"Error checking/creating container '{self.container_name}': {ae}")
                
                logger.info(f"Azure Blob Storage client initialized for container: {self.container_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Azure Blob Storage client: {e}", exc_info=True)
        else:
            logger.warning("AZURE_STORAGE_CONNECTION_STRING is not set. Falling back to local storage.")

    def is_active(self) -> bool:
        """Return True if Azure Blob Storage is active and configured."""
        return self._container_client is not None

    def upload_file(self, blob_name: str, data: bytes, content_type: Optional[str] = None) -> bool:
        """Upload bytes data to a blob."""
        if not self.is_active():
            logger.error("Blob storage is not active.")
            return False

        try:
            blob_client = self._container_client.get_blob_client(blob_name)
            
            content_settings = None
            if content_type:
                content_settings = ContentSettings(content_type=content_type)

            blob_client.upload_blob(data, overwrite=True, content_settings=content_settings)
            logger.debug(f"Successfully uploaded blob: {blob_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload blob {blob_name}: {e}", exc_info=True)
            return False

    def download_file(self, blob_name: str) -> Optional[bytes]:
        """Download bytes from a blob."""
        if not self.is_active():
            logger.error("Blob storage is not active.")
            return None

        try:
            blob_client = self._container_client.get_blob_client(blob_name)
            download_stream = blob_client.download_blob()
            return download_stream.readall()
        except ResourceNotFoundError:
            logger.warning(f"Blob not found: {blob_name}")
            return None
        except Exception as e:
            logger.error(f"Failed to download blob {blob_name}: {e}", exc_info=True)
            return None

    def file_exists(self, blob_name: str) -> bool:
        """Check if a blob exists."""
        if not self.is_active():
            return False

        try:
            blob_client = self._container_client.get_blob_client(blob_name)
            return blob_client.exists()
        except Exception as e:
            logger.error(f"Failed to check existence of blob {blob_name}: {e}", exc_info=True)
            return False

    def delete_file(self, blob_name: str) -> bool:
        """Delete a single blob."""
        if not self.is_active():
            return False

        try:
            blob_client = self._container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            logger.debug(f"Deleted blob: {blob_name}")
            return True
        except ResourceNotFoundError:
            logger.warning(f"Blob to delete not found: {blob_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete blob {blob_name}: {e}", exc_info=True)
            return False

    def list_files(self, prefix: str) -> List[str]:
        """List all blobs matching a specific prefix/path."""
        if not self.is_active():
            return []

        try:
            blobs = self._container_client.list_blobs(name_starts_with=prefix)
            return [b.name for b in blobs]
        except Exception as e:
            logger.error(f"Failed to list blobs under prefix {prefix}: {e}", exc_info=True)
            return []

    def delete_files_with_prefix(self, prefix: str) -> None:
        """Delete all blobs under a specific prefix/path."""
        if not self.is_active():
            return

        try:
            blobs = self._container_client.list_blobs(name_starts_with=prefix)
            blobs_to_delete = [b.name for b in blobs]
            if blobs_to_delete:
                for b_name in blobs_to_delete:
                    self.delete_file(b_name)
                logger.info(f"Deleted {len(blobs_to_delete)} blobs under prefix: {prefix}")
        except Exception as e:
            logger.error(f"Failed to bulk delete blobs under prefix {prefix}: {e}", exc_info=True)


# Singleton
_storage_backend_instance: Optional[BlobStorageBackend] = None


def get_blob_storage_backend() -> BlobStorageBackend:
    """Get singleton BlobStorageBackend instance."""
    global _storage_backend_instance
    if _storage_backend_instance is None:
        _storage_backend_instance = BlobStorageBackend()
    return _storage_backend_instance
