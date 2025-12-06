"""Quick test to find Chrome installation"""
import os

print("🔍 Searching for Chrome installation...\n")

possible_paths = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
    os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"),
]

found = False
for i, path in enumerate(possible_paths, 1):
    expanded = os.path.expandvars(path)
    exists = os.path.exists(expanded)
    status = "✅ FOUND" if exists else "❌ Not found"
    print(f"{i}. {status}")
    print(f"   Path: {expanded}")
    if exists:
        found = True
        print(f"   👉 This is your Chrome path!")
    print()

if not found:
    print("⚠️ Chrome not found in any default location!")
    print("💡 Please install Chrome or the system will use your default browser.")
else:
    print("✅ Chrome installation detected! Voice commands will work.")
