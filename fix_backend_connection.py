"""
Backend Connection Fix Script
Diagnoses and fixes common backend connection issues.
"""

import os
import sys
import time
import requests
import subprocess
from pathlib import Path

class BackendConnectionFixer:
    """Fixes common backend connection issues."""
    
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.backend_dir = Path("web_app/core/backend")
        self.frontend_dir = Path("web_app/core/frontend")
    
    def diagnose_issues(self):
        """Diagnose common backend connection issues."""
        print("🔍 Diagnosing backend connection issues...")
        
        issues = []
        
        # Check if backend is running
        if not self._is_backend_running():
            issues.append("Backend server is not running")
        
        # Check if frontend is running
        if not self._is_frontend_running():
            issues.append("Frontend server is not running")
        
        # Check CORS configuration
        if not self._check_cors():
            issues.append("CORS configuration issue")
        
        # Check port conflicts
        port_conflicts = self._check_port_conflicts()
        if port_conflicts:
            issues.extend(port_conflicts)
        
        # Check Python dependencies
        missing_deps = self._check_python_dependencies()
        if missing_deps:
            issues.append(f"Missing Python dependencies: {', '.join(missing_deps)}")
        
        # Check Node.js dependencies
        if not self._check_node_dependencies():
            issues.append("Node.js dependencies not installed")
        
        return issues
    
    def fix_issues(self):
        """Attempt to fix identified issues."""
        print("🔧 Attempting to fix backend connection issues...")
        
        issues = self.diagnose_issues()
        
        if not issues:
            print("✅ No issues found!")
            return True
        
        print(f"Found {len(issues)} issues:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        
        # Fix issues
        fixed_count = 0
        
        # Install missing Python dependencies
        if any("Missing Python dependencies" in issue for issue in issues):
            if self._install_python_dependencies():
                fixed_count += 1
                print("✅ Fixed Python dependencies")
        
        # Install Node.js dependencies
        if any("Node.js dependencies" in issue for issue in issues):
            if self._install_node_dependencies():
                fixed_count += 1
                print("✅ Fixed Node.js dependencies")
        
        # Kill conflicting processes
        if any("port" in issue.lower() for issue in issues):
            if self._kill_conflicting_processes():
                fixed_count += 1
                print("✅ Killed conflicting processes")
        
        # Start servers if not running
        if any("not running" in issue for issue in issues):
            if self._start_servers():
                fixed_count += 1
                print("✅ Started servers")
        
        print(f"🎯 Fixed {fixed_count} out of {len(issues)} issues")
        
        # Re-check
        remaining_issues = self.diagnose_issues()
        if not remaining_issues:
            print("🎉 All issues resolved!")
            return True
        else:
            print(f"⚠️ {len(remaining_issues)} issues remain:")
            for issue in remaining_issues:
                print(f"  - {issue}")
            return False
    
    def _is_backend_running(self):
        """Check if backend server is running."""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _is_frontend_running(self):
        """Check if frontend server is running."""
        try:
            response = requests.get(self.frontend_url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _check_cors(self):
        """Check CORS configuration."""
        try:
            # Try to make a preflight request
            headers = {
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            response = requests.options(f"{self.backend_url}/api/component-detection/detect", 
                                      headers=headers, timeout=5)
            return 'access-control-allow-origin' in response.headers
        except:
            return False
    
    def _check_port_conflicts(self):
        """Check for port conflicts."""
        conflicts = []
        
        # Check port 8000 (backend)
        if self._is_port_in_use(8000) and not self._is_backend_running():
            conflicts.append("Port 8000 is in use by another process")
        
        # Check port 3000 (frontend)
        if self._is_port_in_use(3000) and not self._is_frontend_running():
            conflicts.append("Port 3000 is in use by another process")
        
        return conflicts
    
    def _is_port_in_use(self, port):
        """Check if a port is in use."""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('localhost', port)) == 0
        except:
            return False
    
    def _check_python_dependencies(self):
        """Check for missing Python dependencies."""
        required_deps = ['fastapi', 'uvicorn', 'python-multipart', 'pydantic']
        missing = []
        
        for dep in required_deps:
            try:
                __import__(dep.replace('-', '_'))
            except ImportError:
                missing.append(dep)
        
        return missing
    
    def _check_node_dependencies(self):
        """Check if Node.js dependencies are installed."""
        return (self.frontend_dir / "node_modules").exists()
    
    def _install_python_dependencies(self):
        """Install missing Python dependencies."""
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "fastapi", "uvicorn", "python-multipart", "pydantic-settings"
            ], check=True, capture_output=True)
            return True
        except:
            return False
    
    def _install_node_dependencies(self):
        """Install Node.js dependencies."""
        try:
            subprocess.run(["npm", "install"], 
                         cwd=self.frontend_dir, check=True, capture_output=True)
            return True
        except:
            return False
    
    def _kill_conflicting_processes(self):
        """Kill processes using ports 8000 and 3000."""
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(["taskkill", "/F", "/IM", "python.exe"], 
                             capture_output=True)
                subprocess.run(["taskkill", "/F", "/IM", "node.exe"], 
                             capture_output=True)
            else:  # Unix-like
                subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)
                subprocess.run(["pkill", "-f", "react-scripts"], capture_output=True)
            
            time.sleep(2)  # Wait for processes to terminate
            return True
        except:
            return False
    
    def _start_servers(self):
        """Start backend and frontend servers."""
        try:
            # Start backend
            if not self._is_backend_running():
                if os.name == 'nt':  # Windows
                    subprocess.Popen([
                        "cmd", "/c", "start", "cmd", "/k", 
                        f"cd {self.backend_dir} && python main.py"
                    ])
                else:  # Unix-like
                    subprocess.Popen([
                        "python", "main.py"
                    ], cwd=self.backend_dir)
                
                # Wait for backend to start
                for _ in range(10):
                    time.sleep(1)
                    if self._is_backend_running():
                        break
            
            # Start frontend
            if not self._is_frontend_running():
                if os.name == 'nt':  # Windows
                    subprocess.Popen([
                        "cmd", "/c", "start", "cmd", "/k", 
                        f"cd {self.frontend_dir} && npm start"
                    ])
                else:  # Unix-like
                    subprocess.Popen([
                        "npm", "start"
                    ], cwd=self.frontend_dir)
            
            return True
        except:
            return False
    
    def test_connection(self):
        """Test the connection between frontend and backend."""
        print("🧪 Testing backend connection...")
        
        # Test health endpoint
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ Backend health check passed")
            else:
                print(f"❌ Backend health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Backend health check failed: {e}")
            return False
        
        # Test API endpoint
        try:
            response = requests.get(f"{self.backend_url}/api/component-detection", timeout=10)
            if response.status_code in [200, 405]:  # 405 is OK for GET on POST endpoint
                print("✅ Component detection API accessible")
            else:
                print(f"❌ Component detection API failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Component detection API failed: {e}")
        
        # Test CORS
        try:
            headers = {'Origin': 'http://localhost:3000'}
            response = requests.get(f"{self.backend_url}/health", headers=headers, timeout=10)
            if 'access-control-allow-origin' in response.headers:
                print("✅ CORS configuration working")
            else:
                print("⚠️ CORS headers not found")
        except Exception as e:
            print(f"❌ CORS test failed: {e}")
        
        return True

def main():
    """Main function."""
    print("🔧 Backend Connection Fixer")
    print("=" * 40)
    
    fixer = BackendConnectionFixer()
    
    # Diagnose issues
    issues = fixer.diagnose_issues()
    
    if not issues:
        print("✅ No issues found!")
        fixer.test_connection()
    else:
        print(f"Found {len(issues)} issues. Attempting to fix...")
        if fixer.fix_issues():
            print("🎉 All issues resolved!")
            fixer.test_connection()
        else:
            print("❌ Some issues could not be resolved automatically.")
            print("Please check the remaining issues manually.")

if __name__ == "__main__":
    main()
