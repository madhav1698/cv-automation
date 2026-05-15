import os
import sys
import subprocess
import shutil

def build():
    print("=== ApplyCraft EXE Builder ===")
    
    # 1. Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 2. Find CustomTkinter path for assets
    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)
    print(f"CustomTkinter found at: {ctk_path}")

    # 3. Define build command
    # We use --noconsole for a clean GUI experience
    # We use --onefile for a single executable (easier to share)
    # Note: --onefile can be slow to start, but is most "intuitive"
    
    cmd = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        "--name=ApplyCraft",
        f"--add-data={ctk_path};customtkinter/",
        f"--add-data=templates;templates",
        f"--add-data=core;core",
        f"--add-data=helpers;helpers",
        "--hidden-import=babel.numbers", # Common hidden import for some UI libs
        "core/cv_generator_gui.py"
    ]

    print(f"Running command: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd)
        print("\nSUCCESS! Executable created in the 'dist' folder.")
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Build failed with exit code {e.returncode}")

if __name__ == "__main__":
    # Check if we are in the right directory
    if not os.path.exists("core/cv_generator_gui.py"):
        print("Error: Please run this script from the root of ApplyCraft_Next")
        sys.exit(1)
        
    build()
