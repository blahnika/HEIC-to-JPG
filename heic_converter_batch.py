"""
Multi-select wrapper for HEIC converter
Batches multiple quick calls into a single conversion session
"""
import sys
import os
import time
from pathlib import Path
import tempfile
import json
from heic_converter import convert_heic_to_jpg

BATCH_FILE = Path(tempfile.gettempdir()) / "heic_converter_batch.json"
LOCK_FILE = Path(tempfile.gettempdir()) / "heic_converter_lock.tmp"
BATCH_WAIT_INITIAL = 0.3  # Initial wait time
BATCH_WAIT_STABLE = 0.5   # Time to wait for batch to be stable (no new files added)

def add_to_batch(file_path):
    """Add a file to the batch queue"""
    files = []
    if BATCH_FILE.exists():
        try:
            with open(BATCH_FILE, 'r') as f:
                files = json.load(f)
        except:
            files = []
    
    if str(file_path) not in files:  # Avoid duplicates
        files.append(str(file_path))
    
    with open(BATCH_FILE, 'w') as f:
        json.dump(files, f)
    
    return len(files)

def get_batch():
    """Get all files in the batch"""
    if BATCH_FILE.exists():
        try:
            with open(BATCH_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def clear_batch():
    """Clear the batch file"""
    if BATCH_FILE.exists():
        try:
            BATCH_FILE.unlink()
        except:
            pass

def is_locked():
    """Check if another instance is processing"""
    if LOCK_FILE.exists():
        # Check if lock is stale (older than 10 seconds)
        age = time.time() - LOCK_FILE.stat().st_mtime
        if age < 10:
            return True
        else:
            # Stale lock, remove it
            try:
                LOCK_FILE.unlink()
            except:
                pass
    return False

def acquire_lock():
    """Acquire processing lock"""
    try:
        LOCK_FILE.touch()
        return True
    except:
        return False

def release_lock():
    """Release processing lock"""
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except:
        pass

def wait_for_stable_batch():
    """Wait until no new files are being added to the batch"""
    last_count = 0
    stable_time = 0
    
    while stable_time < BATCH_WAIT_STABLE:
        time.sleep(0.1)  # Check every 100ms
        current_count = len(get_batch())
        
        if current_count == last_count:
            stable_time += 0.1
        else:
            # New files added, reset stability timer
            stable_time = 0
            last_count = current_count

def main():
    if len(sys.argv) < 2:
        print("This script is called by the context menu")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    
    # Add this file to the batch
    count = add_to_batch(file_path)
    
    # If another instance is already processing, just exit
    if is_locked():
        sys.exit(0)
    
    # We're the first/only instance, acquire lock
    if not acquire_lock():
        sys.exit(0)
    
    try:
        # Wait a bit for other files to be added to batch initially
        time.sleep(BATCH_WAIT_INITIAL)
        
        # Now wait until the batch is stable (no new files being added)
        wait_for_stable_batch()
        
        # Get all files in the batch
        files = get_batch()
        clear_batch()
        
        if not files:
            return
        
        # Convert all files
        print(f"HEIC to JPG Converter")
        print(f"{'='*50}")
        print(f"Found {len(files)} file(s) to convert\n")
        
        success_count = 0
        for file_str in files:
            file_path = Path(file_str)
            if file_path.exists():
                if convert_heic_to_jpg(file_path):
                    success_count += 1
            else:
                print(f"Skipping: {file_path.name} (not found)")
        
        print(f"\n{'='*50}")
        print(f"Conversion complete: {success_count}/{len(files)} successful")
        print(f"{'='*50}")
        
        # Pause so user can see results
        input("\nPress Enter to exit...")
        
    finally:
        release_lock()

if __name__ == "__main__":
    main()
