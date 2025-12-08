# Virtual Environment Path Issue - Quick Fix Guide

## Problem Identified

Health check fails because dependencies are installed to the wrong virtual environment.

**Current Situation:**
- You're working in: `C:\Users\admin\Downloads\Single-Line-Diagram\SLD`  
- But pip installs packages to: `C:\Users\admin\Downloads\SLD\SLD\.venv`

This causes `ModuleNotFoundError: No module named 'fastapi'` when starting the app.

---

## Solution: Recreate Virtual Environment

Run these commands in PowerShell from the project root:

```powershell
# 1. Navigate to project directory
cd C:\Users\admin\Downloads\Single-Line-Diagram\SLD

# 2. Delete the misconfigured venv
Remove-Item -Recurse -Force .\.venv

# 3. Create a fresh virtual environment  
python -m venv .venv

# 4. Install all dependencies
.\.venv\Scripts\pip install -r requirements.txt

# 5. Start the application
.\.venv\Scripts\python app.py
```

Then test health check:
```powershell
curl http://localhost:8000/health
```

**Expected Result:** HTTP 200, status "healthy"

---

## Why This Happened

The `.venv` directory was likely created or configured with an incorrect base path, causing pip to install packages to a different location than where Python looks for them.

---

## If Issue Persists

Check if there's a duplicate project at `C:\Users\admin\Downloads\SLD\SLD\` and delete it to avoid confusion.
