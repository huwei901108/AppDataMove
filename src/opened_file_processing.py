import os
import subprocess
import zipfile
import win32api
import re

from utils import does_user_confirm

handle_url="https://download.sysinternals.com/files/Handle.zip"
list_dlls_url="https://download.sysinternals.com/files/ListDlls.zip"

def handle_opened_file(paths: list[str]) -> bool:
    print(f"Found file [{len(paths)}] blocking process.")
    print("Wana find the processes that opened the file?")
    print("Using handle in Sysinternals from Microsoft.")
    if not does_user_confirm():
        return False
    handle_path = get_handle_exe()
    if handle_path == "":
        return False
    pid_arr = find_related_pid(paths, handle_path)
    if len(pid_arr) <= 0:
        pid_arr = handle_opened_file_by_list_dlls(paths)
    print_pid_desc(pid_arr)
    if len(pid_arr) <= 0:
        print("No related process found. Try continue?")
    else:
        print("Try to close these process?")
    if not does_user_confirm():
        return False
    close_pids(pid_arr)
    return True

def handle_opened_file_by_list_dlls(paths: list[str]) -> list[int]:
    print("No related process found by handle.")
    print("Wana try with ListDlls?")
    print("Using ListDlls in Sysinternals from Microsoft.")
    if not does_user_confirm():
        return []
    list_dlls_path = get_list_dlls_exe()
    if list_dlls_path == "":
        return []
    return find_related_pid_by_list_dlls(paths, list_dlls_path)

def find_related_pid_by_list_dlls(paths: list[str], list_dlls_path: str) -> list[int]:
    pids = []
    for path in paths:
        print(f"ListDlls checking file: {path}")
        try:
            result = subprocess.run(
                [list_dlls_path, '-d', path],
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error running ListDlls for {path}: {e}")
            continue
        parse_pids_from_ld_stdout(result.stdout, pids)
    return list(set(pids))
def parse_pids_from_ld_stdout(stdout: str, pids: list[int]):
    lines = stdout.split('\n')
    for line in lines:
        # Use regex to find the pattern ".* pid: <number>"
        match = re.search(r'^.* pid: (\d+)$', line)
        if match:
            print(f"Found PID in ListDlls output: {match.group(1)}")
            pid = int(match.group(1))
            pids.append(pid)

def get_list_dlls_exe() -> str:
    current_dir = os.getcwd()
    tools_dir = os.path.join(current_dir, 'tools')
    if not os.path.isdir(tools_dir):
        try:
            os.makedirs(tools_dir)
        except OSError as e:
            print(f"failed to create tools dir: {e}")
            return ""
    list_dlls_path = os.path.join(tools_dir, 'ListDlls.exe')
    if not os.path.isfile(list_dlls_path):
        print("ListDlls.exe not found.")
        print("Downloading ListDlls from Sysinternals...")
        try:
            zip_path = os.path.join(tools_dir, 'ListDlls.zip')
            subprocess.run([
                'powershell', '-Command',
                f'Invoke-WebRequest -Uri "{list_dlls_url}" -OutFile "{zip_path}"'
            ], check=True)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tools_dir)

            os.remove(zip_path)
            print("Download and extraction completed successfully.")
        except (subprocess.CalledProcessError, zipfile.BadZipFile) as e:
            print(f"Download failed: {e}")
            return ""
    return list_dlls_path

def close_pids(pids: list[int]):
    for pid in pids:
        print(f"\nClosing process {pid}:")
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T"],
                timeout=5,
                check=True,
                capture_output=True,
                text=True
            )
            print("   Process terminated gracefully")
            continue
        except subprocess.TimeoutExpired:
            print("   Graceful termination timeout...")
        except Exception as e:
            print(f"   Error in graceful termination: {str(e)}")

        try:
            subprocess.run(
                ["taskkill", "/F", "/PID", str(pid), "/T"],
                check=True,
                capture_output=True,
                text=True
            )
            print("   Process force-closed")
        except Exception as e:
            print(f"   Failed to force close: {str(e)}")

def print_pid_desc(pids: list[int]):
    print("Found related process:")
    for pid in pids:
        process_path = get_path_from_pid(pid)
        if process_path == "":
            continue
        get_exe_desc(process_path)

def get_exe_desc(path: str):
    try:
        # Get file version info
        info = win32api.GetFileVersionInfo(path, '\\')

        # Get translations list
        translations = info.get('VarFileInfo', {}).get('Translation', [])
        string_info = info.get('StringFileInfo', {})

        # Try all available translations
        desc = ''
        for lang, codepage in translations:
            lang_codepage = f"{lang:04X}{codepage:04X}"
            if string_info.get(lang_codepage):
                desc = string_info[lang_codepage].get('FileDescription', '')
                if desc:
                    break

        # If not found, try first available item
        if not desc and string_info:
            lang_codepage = next(iter(string_info.keys()))
            desc = string_info[lang_codepage].get('FileDescription', '')

        if desc:
            print(f"   Description: {desc}")
        else:
            print("   No description available")
    except Exception as e:
        print(f"   Error getting description: {str(e)}")
    pass


def get_path_from_pid(pid: int) -> str:
    process_path = ""
    print(f" - PID: {pid}")
    try:
        result = subprocess.run(
            ['wmic', 'process', 'where', f'ProcessId={pid}', 'get', 'ExecutablePath,Name', '/FORMAT:CSV'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            check=True
        )
        lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        if len(lines) > 1:
            parts = lines[-1].split(',')
            if len(parts) >= 3:
                process_path = parts[1].strip()
                print(f"   Process: {parts[2].strip()}")
                print(f"   Path: {process_path}")
            else:
                print("   System process (no details)")
    except subprocess.CalledProcessError as e:
        print(f"   Error: {e}")
    return process_path

def find_related_pid(paths: list[str], handle_path: str):
    pids = []  # Store collected PIDs
    for path in paths:
        print(f"Handle checking file: {path}")
        try:
            result = subprocess.run([handle_path, "-v", path, "-nobanner"],
                capture_output=True, text=True, check=True)

            # Parse output lines
            for line in result.stdout.split('\n'):
                if line.strip() and not line.startswith('Process,PID,'):  # Skip header
                    parts = line.split(',')
                    if len(parts) >= 2:
                        pid = parts[1].strip()
                        pids.append(int(pid))
                        print(f"Found PID: {pid}")

        except subprocess.CalledProcessError as e:
            print(f"Error executing handle: {e}")
    return list(set(pids))  # Return unique PIDs

def get_handle_exe():
    current_dir = os.getcwd()
    tools_dir = os.path.join(current_dir, 'tools')
    if not os.path.isdir(tools_dir):
        try:
            os.makedirs(tools_dir)
        except OSError as e:
            print(f"failed to create tools dir: {e}")
            return ""
    handle_path = os.path.join(tools_dir, 'handle.exe')
    if not os.path.isfile(handle_path):
        print("handle.exe not found.")
        print("Downloading handle from Sysinternals...")
        try:
            zip_path = os.path.join(tools_dir, 'handle.zip')
            subprocess.run([
                'powershell', '-Command',
                f'Invoke-WebRequest -Uri "{handle_url}" -OutFile "{zip_path}"'
            ], check=True)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tools_dir)

            os.remove(zip_path)
            print("Download and extraction completed successfully.")
        except (subprocess.CalledProcessError, zipfile.BadZipFile) as e:
            print(f"Download failed: {e}")
            return ""
    return handle_path
