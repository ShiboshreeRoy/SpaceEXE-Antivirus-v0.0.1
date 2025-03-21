import os
import shutil
import logging
import threading
import time
import sys
import random
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from colorama import Fore, Style, init
import tkinter as tk
from tkinter import scrolledtext

# Initialize colorama
init()

# Set up logging
logging.basicConfig(filename='spaceexe_antivirus.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Cloud-based virus definition URL (replace with your server URL)
VIRUS_DB_URL = "https://example.com/virus_signatures.txt"

# Default virus signatures (updated dynamically)
VIRUS_SIGNATURES = [
    "os.system('rm -rf /')",
    "import subprocess; subprocess.call(['rm', '-rf', '/'])",
    "exec(",
    "eval(",
    "import base64; exec(base64.b64decode(",
    "subprocess.Popen(['rm', '-rf', '/'])",
]

# Create a quarantine directory if it doesn’t exist
QUARANTINE_DIR = 'quarantine'
if not os.path.exists(QUARANTINE_DIR):
    os.makedirs(QUARANTINE_DIR)

# ASCII Art for branding
BANNER = f"""{Fore.GREEN}
 ██████  ███████  █████  ███████ ███████ ███████ 
██       ██      ██   ██ ██      ██      ██      
██   ███ █████   ███████ █████   ███████ ███████ 
██    ██ ██      ██   ██ ██           ██      ██ 
 ██████  ███████ ██   ██ ██      ███████ ███████ 
                                               
          {Fore.RED}Version: 0.0.1 | Dev: Space EXE
{Style.RESET_ALL}"""

def update_virus_definitions():
    """Fetch the latest virus definitions from the cloud."""
    global VIRUS_SIGNATURES
    try:
        response = requests.get(VIRUS_DB_URL)
        if response.status_code == 200:
            VIRUS_SIGNATURES = response.text.splitlines()
            logging.info("[INFO] Virus definitions updated successfully.")
            print(f"{Fore.GREEN}[INFO] Virus definitions updated from the cloud.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}[ERROR] Failed to update virus definitions.{Style.RESET_ALL}")
    except Exception as e:
        logging.error(f"Error updating virus definitions: {e}")

def loading_animation():
    """Display a loading animation while scanning."""
    chars = ["|", "/", "-", "\\"]
    for _ in range(10):
        sys.stdout.write(f"\r{Fore.YELLOW}[INFO] Scanning {random.choice(chars)}{Style.RESET_ALL}")
        sys.stdout.flush()
        time.sleep(0.1)
    print("\r", end="")

def scan_file(file_path):
    """Scan a single file for virus signatures."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            for signature in VIRUS_SIGNATURES:
                if signature in content:
                    logging.warning(f"Virus detected in {file_path}: {signature}")
                    print(f"{Fore.RED}[WARNING] Virus detected in {file_path}{Style.RESET_ALL}")
                    delete_file(file_path)
                    return True
    except Exception as e:
        logging.error(f"Error scanning {file_path}: {e}")
    return False

def delete_file(file_path):
    """Delete the infected file permanently."""
    try:
        os.remove(file_path)
        logging.info(f"Deleted infected file: {file_path}")
        print(f"{Fore.GREEN}[INFO] Deleted infected file: {file_path}{Style.RESET_ALL}")
    except Exception as e:
        logging.error(f"Error deleting {file_path}: {e}")

def scan_directory(directory):
    """Scan all .py files in the directory and subdirectories."""
    scanned_files = []
    infected_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                scanned_files.append(file_path)
                loading_animation()
                print(f"{Fore.CYAN}[INFO] Scanning {file_path}...{Style.RESET_ALL}")
                if scan_file(file_path):
                    infected_files.append(file_path)
    return scanned_files, infected_files

class FileMonitorHandler(FileSystemEventHandler):
    """Monitor files in real time for new or modified files."""
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.py'):
            print(f"{Fore.YELLOW}[REAL-TIME SCAN] New file detected: {event.src_path}{Style.RESET_ALL}")
            scan_file(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.py'):
            print(f"{Fore.YELLOW}[REAL-TIME SCAN] Modified file detected: {event.src_path}{Style.RESET_ALL}")
            scan_file(event.src_path)

def start_real_time_monitor(directory):
    """Start real-time monitoring of a directory."""
    event_handler = FileMonitorHandler()
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=True)
    observer.start()
    print(f"{Fore.BLUE}[INFO] Real-time file monitoring started in: {directory}{Style.RESET_ALL}")
    return observer

def run_gui():
    """Run the GUI version of SpaceEXE Antivirus."""
    root = tk.Tk()
    root.title("SpaceEXE Antivirus")
    root.geometry("500x400")

    log_text = scrolledtext.ScrolledText(root, width=60, height=15)
    log_text.pack(pady=10)

    def update_log(msg):
        log_text.insert(tk.END, msg + "\n")
        log_text.see(tk.END)

    def start_scan():
        update_log("Starting scan...")
        scanned_files, infected_files = scan_directory(os.getcwd())
        update_log(f"Scan completed. Scanned {len(scanned_files)} files.")
        if infected_files:
            update_log(f"Found {len(infected_files)} infected files and deleted them.")
        else:
            update_log("No viruses found.")

    scan_button = tk.Button(root, text="Start Scan", command=start_scan)
    scan_button.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    print(BANNER)

    # Update virus signatures from cloud
    update_virus_definitions()

    # Start real-time monitoring in the background
    observer = start_real_time_monitor(os.getcwd())

    # Start GUI in a separate thread
    gui_thread = threading.Thread(target=run_gui, daemon=True)
    gui_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
