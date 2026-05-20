"""
One-time migration script to restore the sp_zp project from local backup
into Azure Blob Storage.

Reads images and COCO annotations from D:\SLD\sp_zp and uploads them to
the configured Azure Blob Storage container under the sp_zp/ prefix.

Usage:
    python scripts/restore_sp_zp.py
"""

import json
import mimetypes
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path so we can import our modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

# Load .env from project root
load_dotenv(PROJECT_ROOT / ".env")

from azure.storage.blob import BlobServiceClient, ContentSettings


def main():
    # ── Configuration ──────────────────────────────────────────
    LOCAL_SP_ZP = PROJECT_ROOT / "sp_zp"
    IMAGES_DIR = LOCAL_SP_ZP / "images"
    COCO_FILE = LOCAL_SP_ZP / "_annotations.coco.json"
    PROJECT_NAME = "sp_zp"

    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "annotation-data")

    if not connection_string:
        print("ERROR: AZURE_STORAGE_CONNECTION_STRING is not set in .env")
        sys.exit(1)

    if not LOCAL_SP_ZP.exists():
        print(f"ERROR: Local backup directory not found: {LOCAL_SP_ZP}")
        sys.exit(1)

    if not COCO_FILE.exists():
        print(f"ERROR: COCO annotation file not found: {COCO_FILE}")
        sys.exit(1)

    # ── Connect to Azure ───────────────────────────────────────
    print(f"Connecting to Azure Blob Storage (container: {container_name})...")
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)

    # Ensure the container exists
    try:
        if not container_client.exists():
            container_client.create_container()
            print(f"  Created container: {container_name}")
    except Exception as e:
        print(f"  Warning: Could not check/create container: {e}")

    # ── Check if project already exists ────────────────────────
    project_json_blob = f"{PROJECT_NAME}/project.json"
    blob_client = container_client.get_blob_client(project_json_blob)
    if blob_client.exists():
        print(f"\nProject '{PROJECT_NAME}' already exists in Blob Storage.")
        response = input("Overwrite? (y/N): ").strip().lower()
        if response != "y":
            print("Aborted.")
            sys.exit(0)
        # Delete existing blobs under the project prefix
        print("  Deleting existing blobs...")
        blobs = list(container_client.list_blobs(name_starts_with=f"{PROJECT_NAME}/"))
        for b in blobs:
            container_client.delete_blob(b.name)
        print(f"  Deleted {len(blobs)} existing blobs.")

    # ── Read COCO annotations ─────────────────────────────────
    print(f"\nReading COCO annotations from {COCO_FILE}...")
    with open(COCO_FILE, "r", encoding="utf-8") as f:
        coco_data = json.load(f)

    image_count = len(coco_data.get("images", []))
    annotation_count = len(coco_data.get("annotations", []))
    category_count = len(coco_data.get("categories", []))
    print(f"  Found {image_count} images, {annotation_count} annotations, {category_count} categories")

    # ── Upload images ──────────────────────────────────────────
    print(f"\nUploading images from {IMAGES_DIR}...")
    image_files = sorted(IMAGES_DIR.glob("*"))
    uploaded = 0
    skipped = 0

    for img_path in image_files:
        if not img_path.is_file():
            continue

        blob_name = f"{PROJECT_NAME}/images/{img_path.name}"
        content_type = mimetypes.guess_type(str(img_path))[0] or "image/png"

        try:
            blob_client = container_client.get_blob_client(blob_name)
            with open(img_path, "rb") as img_file:
                blob_client.upload_blob(
                    img_file,
                    overwrite=True,
                    content_settings=ContentSettings(content_type=content_type),
                )
            uploaded += 1
            if uploaded % 10 == 0:
                print(f"  Uploaded {uploaded}/{len(image_files)} images...")
        except Exception as e:
            print(f"  ERROR uploading {img_path.name}: {e}")
            skipped += 1

    print(f"  Done: {uploaded} uploaded, {skipped} skipped")

    # ── Upload COCO JSON ───────────────────────────────────────
    print("\nUploading _annotations.coco.json...")
    coco_blob_name = f"{PROJECT_NAME}/_annotations.coco.json"
    blob_client = container_client.get_blob_client(coco_blob_name)
    coco_bytes = json.dumps(coco_data, indent=2, ensure_ascii=False).encode("utf-8")
    blob_client.upload_blob(
        coco_bytes,
        overwrite=True,
        content_settings=ContentSettings(content_type="application/json"),
    )
    print(f"  Uploaded ({len(coco_bytes):,} bytes)")

    # ── Create project.json metadata ───────────────────────────
    print("\nCreating project.json metadata...")
    now = datetime.now(timezone.utc).isoformat()
    project_meta = {
        "name": PROJECT_NAME,
        "display_name": PROJECT_NAME,
        "created_by": "migration_script",
        "created_at": now,
        "last_modified": now,
        "next_sequence": image_count + 1,
    }
    meta_blob_name = f"{PROJECT_NAME}/project.json"
    blob_client = container_client.get_blob_client(meta_blob_name)
    meta_bytes = json.dumps(project_meta, indent=2, ensure_ascii=False).encode("utf-8")
    blob_client.upload_blob(
        meta_bytes,
        overwrite=True,
        content_settings=ContentSettings(content_type="application/json"),
    )
    print(f"  Uploaded ({len(meta_bytes):,} bytes)")

    # ── Verification ───────────────────────────────────────────
    print("\n── Verification ──")
    blobs = list(container_client.list_blobs(name_starts_with=f"{PROJECT_NAME}/"))
    image_blobs = [b for b in blobs if "/images/" in b.name]
    json_blobs = [b for b in blobs if b.name.endswith(".json")]
    print(f"  Total blobs under '{PROJECT_NAME}/': {len(blobs)}")
    print(f"  Image blobs: {len(image_blobs)}")
    print(f"  JSON blobs:  {len(json_blobs)}")

    if len(image_blobs) == image_count:
        print(f"\n✅ Migration complete! '{PROJECT_NAME}' project restored with {image_count} images.")
    else:
        print(f"\n⚠️  Expected {image_count} images but found {len(image_blobs)} in blob storage.")

    print("\nThe project should now appear in the annotation portal.")


if __name__ == "__main__":
    main()
