"""
Configuration management for SLD Processing API
"""

import os
from pathlib import Path
from typing import List, Optional
from functools import lru_cache

try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic.v1 import BaseSettings
    except ImportError:
        from pydantic import BaseSettings

try:
    from pydantic import field_validator
except ImportError:
    from pydantic import validator as field_validator

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application settings
    app_name: str = "SLD Processing Application"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    
    # Frontend settings
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    
    # File upload settings
    max_file_size: int = 10485760  # 10MB in bytes
    allowed_extensions: List[str] = ["jpg", "jpeg", "png", "pdf", "bmp", "tiff"]
    upload_folder: str = "uploads"
    
    # Azure Document Intelligence settings
    azure_document_intelligence_endpoint: Optional[str] = None
    azure_document_intelligence_key: Optional[str] = None
    
    # Azure AI Foundry settings (if needed)
    azure_ai_foundry_endpoint: Optional[str] = None
    azure_ai_foundry_key: Optional[str] = None
    
    # YOLO model settings - use absolute path to avoid path resolution issues
    yolo_model_path: str = str(Path(__file__).parent.parent / "component_detection" / "models" / "best.pt")
    yolo_confidence_threshold: float = 0.05  # Optimized balance between detection and false positives
    yolo_iou_threshold: float = 0.3  # Lower IoU for better small component detection
    
    # Database settings
    database_url: str = "sqlite:///./sld_app.db"
    
    # Security settings
    secret_key: str = "sld-processing-secret-key-2024"
    access_token_expire_minutes: int = 30
    
    # CORS settings
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Logging settings
    log_file: str = "logs/app.log"
    log_rotation: str = "1 week"
    log_retention: str = "4 weeks"
    
    # Performance settings
    worker_timeout: int = 300
    keep_alive: int = 2
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    @field_validator('allowed_extensions', mode='before')
    @classmethod
    def parse_allowed_extensions(cls, v):
        """Parse allowed extensions from string or list"""
        if isinstance(v, str):
            return [ext.strip().lower() for ext in v.split(',')]
        return [ext.lower() for ext in v]
    
    @field_validator('azure_document_intelligence_endpoint')
    @classmethod
    def validate_azure_endpoint(cls, v):
        """Validate Azure endpoint URL"""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('Azure endpoint must start with http:// or https://')
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "env_prefix": ""
    }

@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()

def validate_azure_credentials(settings: Settings) -> bool:
    """Validate Azure service credentials"""
    if not settings.azure_document_intelligence_endpoint:
        return False
    
    if not settings.azure_document_intelligence_key:
        return False
    
    return True

def get_azure_config(settings: Settings) -> dict:
    """Get Azure configuration dictionary"""
    return {
        "endpoint": settings.azure_document_intelligence_endpoint,
        "api_key": settings.azure_document_intelligence_key,
        "model_id": "prebuilt-read"
    }

def resolve_model_path(model_path: str) -> str:
    """Resolve model path relative to backend directory"""
    if Path(model_path).is_absolute():
        return str(Path(model_path).resolve())

    # Get the backend directory (where this config file is located)
    # This file is in utils/, so parent.parent gets us to backend/
    backend_dir = Path(__file__).parent.parent.resolve()
    resolved_path = backend_dir / model_path

    # Ensure the path is fully resolved and absolute
    final_path = resolved_path.resolve()

    # Additional validation
    if not final_path.exists():
        # Try alternative paths if the primary doesn't exist
        alternative_paths = [
            backend_dir / "component_detection" / "models" / "best.pt",
            Path(__file__).parent.parent.parent.parent / "component_detection" / "models" / "best.pt"
        ]

        for alt_path in alternative_paths:
            if alt_path.exists():
                return str(alt_path.resolve())

    return str(final_path)

def get_yolo_config(settings: Settings) -> dict:
    """Get YOLO configuration dictionary"""
    return {
        "model_path": resolve_model_path(settings.yolo_model_path),
        "confidence_threshold": settings.yolo_confidence_threshold,
        "iou_threshold": settings.yolo_iou_threshold
    }

def get_upload_config(settings: Settings) -> dict:
    """Get file upload configuration"""
    return {
        "max_file_size": settings.max_file_size,
        "allowed_extensions": settings.allowed_extensions,
        "upload_folder": settings.upload_folder
    }

def get_cors_config(settings: Settings) -> dict:
    """Get CORS configuration"""
    return {
        "allow_origins": settings.cors_origins,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["*"]
    }

# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings"""
    debug: bool = True
    log_level: str = "DEBUG"
    api_workers: int = 1

class ProductionSettings(Settings):
    """Production environment settings"""
    debug: bool = False
    log_level: str = "INFO"
    api_workers: int = 4

class TestingSettings(Settings):
    """Testing environment settings"""
    debug: bool = True
    log_level: str = "DEBUG"
    database_url: str = "sqlite:///./test_sld_app.db"
    upload_folder: str = "test_uploads"

def get_settings_for_environment(env: str = None) -> Settings:
    """Get settings for specific environment"""
    env = env or os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()

# Configuration validation
def validate_settings(settings: Settings) -> List[str]:
    """Validate settings and return list of issues"""
    issues = []
    
    # Check required Azure credentials
    if not validate_azure_credentials(settings):
        issues.append("Azure Document Intelligence credentials not configured")
    
    # Check YOLO model path
    if not os.path.exists(settings.yolo_model_path):
        issues.append(f"YOLO model not found: {settings.yolo_model_path}")
    
    # Check upload folder
    upload_path = settings.upload_folder
    if not os.path.exists(upload_path):
        try:
            os.makedirs(upload_path, exist_ok=True)
        except Exception as e:
            issues.append(f"Cannot create upload folder: {e}")
    
    # Check log folder
    log_path = os.path.dirname(settings.log_file)
    if log_path and not os.path.exists(log_path):
        try:
            os.makedirs(log_path, exist_ok=True)
        except Exception as e:
            issues.append(f"Cannot create log folder: {e}")
    
    # Validate thresholds
    if not (0.0 <= settings.yolo_confidence_threshold <= 1.0):
        issues.append("YOLO confidence threshold must be between 0.0 and 1.0")
    
    if not (0.0 <= settings.yolo_iou_threshold <= 1.0):
        issues.append("YOLO IoU threshold must be between 0.0 and 1.0")
    
    # Validate file size
    if settings.max_file_size <= 0:
        issues.append("Maximum file size must be positive")
    
    return issues

if __name__ == "__main__":
    # Test configuration
    settings = get_settings()
    
    print("Current Configuration:")
    print(f"  App Name: {settings.app_name}")
    print(f"  Version: {settings.app_version}")
    print(f"  Debug: {settings.debug}")
    print(f"  API Host: {settings.api_host}:{settings.api_port}")
    print(f"  Azure Endpoint: {settings.azure_document_intelligence_endpoint}")
    print(f"  YOLO Model: {settings.yolo_model_path}")
    print(f"  Upload Folder: {settings.upload_folder}")
    print(f"  Max File Size: {settings.max_file_size / 1024 / 1024:.1f}MB")
    print(f"  Allowed Extensions: {settings.allowed_extensions}")
    
    # Validate configuration
    issues = validate_settings(settings)
    if issues:
        print("\nConfiguration Issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✓ Configuration is valid")
