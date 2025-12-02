@echo off
echo 🔧 Fixing Frontend Issues
echo ========================

echo Clearing npm cache...
npm cache clean --force

echo Removing node_modules...
if exist node_modules rmdir /s /q node_modules

echo Removing package-lock.json...
if exist package-lock.json del package-lock.json

echo Reinstalling dependencies...
npm install

echo Starting development server...
npm start

pause
