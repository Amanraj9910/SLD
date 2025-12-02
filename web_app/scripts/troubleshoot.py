#!/usr/bin/env python3
"""
Troubleshooting script to identify issues with the SLD backend
"""

import sys
import importlib
import traceback

def test_import(module_name, description=""):
    """Test if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {description or module_name}: OK")
        return True
    except ImportError as e:
        print(f"❌ {description or module_name}: FAILED - {e}")
        return False
    except Exception as e:
        print(f"⚠️ {description or module_name}: ERROR - {e}")
        return False

def main():
    print("🔍 SLD Backend Troubleshooting")
    print("=" * 40)
    
    # Test basic Python modules
    print("\n📦 Testing Basic Dependencies:")
    basic_modules = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("pydantic_settings", "Pydantic Settings"),
    ]
    
    basic_ok = True
    for module, desc in basic_modules:
        if not test_import(module, desc):
            basic_ok = False
    
    if not basic_ok:
        print("\n❌ Basic dependencies are missing. Install them with:")
        print("pip install fastapi uvicorn pydantic pydantic-settings")
        return
    
    # Test optional modules
    print("\n🔧 Testing Optional Dependencies:")
    optional_modules = [
        ("ultralytics", "YOLO"),
        ("cv2", "OpenCV"),
        ("PIL", "Pillow"),
        ("numpy", "NumPy"),
        ("azure.ai.documentintelligence", "Azure Document Intelligence"),
    ]
    
    for module, desc in optional_modules:
        test_import(module, desc)
    
    # Test our modules
    print("\n📁 Testing Application Modules:")
    try:
        sys.path.append('.')
        
        app_modules = [
            ("utils.config", "Configuration"),
            ("utils.logging_config", "Logging"),
        ]
        
        for module, desc in app_modules:
            test_import(module, desc)
            
    except Exception as e:
        print(f"❌ Application modules test failed: {e}")
    
    # Test FastAPI app creation
    print("\n🚀 Testing FastAPI App Creation:")
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        
        app = FastAPI(title="Test App")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @app.get("/test")
        async def test():
            return {"status": "ok"}
        
        print("✅ FastAPI app creation: OK")
        
    except Exception as e:
        print(f"❌ FastAPI app creation: FAILED - {e}")
        traceback.print_exc()
    
    print("\n" + "=" * 40)
    print("🎯 Troubleshooting Complete")
    print("\nIf basic dependencies are OK, try running:")
    print("python minimal_server.py")

if __name__ == "__main__":
    main()
