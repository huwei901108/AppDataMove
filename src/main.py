import re
import os
import ctypes
import sys
import shutil
import stat

import opened_file_processing as ofp
import utils

path_pattern = r"""
    ^c:\\users\\([\w\.-]+)          # Match_username_part
    \\appdata\\(local|locallow|roaming)  # Match_one_of_the_three_required_subdirectories
    \\([\w\.-]+)$                    # Match_any_valid_subdirectory_name
""".replace(' ', '')

def validate_appdata_path_pattern(path: str) -> bool:
    normalized_path = path.lower().replace('/', '\\')
    return re.match(path_pattern, normalized_path, re.IGNORECASE | re.VERBOSE) is not None

def get_target_path() -> str:
    while True:
        # Get user input and store in target_path variable
        target_path = input("Please enter the target path: ")

        if not validate_appdata_path_pattern(target_path):
            print(f"Invalid path: {target_path}")
            print("Path must follow pattern: " + path_pattern)
            print("Please try again.\n")
            continue
        if not os.path.isdir(target_path):
            print(f"Invalid path: {target_path}")
            print("Path must be a directory.")
            print("Please try again.\n")
            continue
        if os.path.islink(target_path):
            print(f"Invalid path: {target_path}")
            print("Path must not be a symbolic link.")
            print("Please try again.\n")
            continue
        print(f"Target path is valid: {target_path}")
        return target_path

def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def restart_as_admin():
    """Restart the program with admin rights"""
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit(0)

def get_dest_path(target_path: str) -> str:
    # Replace C: with D: in the path
    dest_path = 'd:' + target_path[2:]
    if os.path.exists(dest_path):
        if not rmtree_if_in_use(dest_path):
            print("Failed to delete existing path.")
            return ""
    return dest_path


def is_file_in_use(filepath):
    try:
        # Try to open file in exclusive mode
        handle = ctypes.windll.kernel32.CreateFileW(
            filepath,
            0x80000000,  # GENERIC_READ
            0,           # Exclusive mode
            None,
            3,           # OPEN_EXISTING
            0x80,        # FILE_ATTRIBUTE_NORMAL
            None
        )
        if handle == -1:
            return True
        ctypes.windll.kernel32.CloseHandle(handle)
        return False
    except Exception:
        return True

def precheck_files_in_use(folder_path: str) -> list[str]:
    in_use_files = []
    for root, _, files in os.walk(folder_path):
        for filename in files:
            filepath = os.path.join(root, filename)
            if is_file_in_use(filepath):
                in_use_files.append(filepath)
    return in_use_files

def rmtree_if_in_use(folder_path: str):
    while True:
        try:
            shutil.rmtree(folder_path)
        except OSError as e:
            if e.errno != 13:  # not Access denied
                print(f"Failed to delete {folder_path}: {e}")
                return False
            print(f"WARN: Access denied when deleting {folder_path}.")
            block_file_path = get_blocking_file_from_error(e)
            if block_file_path == "":
                print(f"Failed to get blocking file path")
                return False
            print(f"Blocking file: {block_file_path}")
            done_rm = try_rm_file(block_file_path)
            if done_rm:
                print(f"Deleted {block_file_path}. Continue...")
                continue
            done_close = ofp.handle_opened_file([block_file_path])
            if not done_close:
                return False
            # done closing, return to rmtree
        else:
            print(f"Deleted {folder_path}")
            return True
def try_rm_file(file_path: str) -> bool:
    try:
        print(f"Trying remove readonly: {file_path}")
        os.chmod(file_path, stat.S_IWRITE)
        os.unlink(file_path)
        return True
    except Exception as e:
        print(f"Failed to delete {file_path}: {e}")
        return False

def mksure_no_inuse_files(folder_path: str):
    while True:
        print("Checking if there are any opened files in the folder...")
        in_use_files = precheck_files_in_use(folder_path)
        if len(in_use_files) <= 0:
            return True
        print("found opened files:")
        for f in in_use_files:
            print(f" - {f}")
        done_close = ofp.handle_opened_file(in_use_files)
        if not done_close:
            return False
        print("done closing, continue to check again")

def move_path(target_path: str, dest_path: str) -> bool:
    try:
        print("start copying files...")
        shutil.copytree(target_path, dest_path)
    except Exception as e:
        print(f"Failed copy [{target_path}] -> [{dest_path}]: {e}")
        if os.path.exists(dest_path):
            print(f"Deleting {dest_path}")
            rmtree_if_in_use(dest_path)
    print(f"Path copied successfully: {target_path} -> {dest_path}")
    print(f"Deleting {target_path}")
    ret_rm = rmtree_if_in_use(target_path)
    if not ret_rm:
        print(f"Failed to delete org path {target_path}")
        print(f"Try to recover target path by dest path")
        try:
            shutil.copytree(dest_path, target_path, dirs_exist_ok=True)
        except Exception as e:
            print(f"Failed to recover {target_path} from {dest_path}: {str(e)}")
    return ret_rm

def get_blocking_file_from_error(err: OSError) -> str:
    if err.errno != 13:
        print("not file opened error")
        return ""
    if hasattr(err, 'filename'):
        return err.filename
    match_str = re.search(r"'([^']*)'", str(err))
    if match_str is None:
        print("Failed to parse error message")
        return ""
    return match_str.group(1)

def mklink(target_path: str, dest_path: str):
    try:
        os.symlink(dest_path, target_path)
    except OSError as e:
        print(f"Failed to create symbolic link: {e}")
        return
    print(f"Symbolic link created: {dest_path} -> {target_path}")

def main_process():
    if not is_admin():
        print("Administrator privileges required for some operations")
        restart_as_admin()

    target_path = get_target_path()
    dest_path = get_dest_path(target_path)
    if dest_path == "":
        print("Failed to get destination path")
        return 1

    print(f"Checking opened files in src[{target_path}]...")
    if not mksure_no_inuse_files(target_path):
        return 2

    print(f"Src[{target_path}]->Dst[{dest_path}]. Start copy?")
    if not utils.does_user_confirm():
        return 0

    mv_done = move_path(target_path, dest_path)
    if not mv_done:
        print(f"Failed to move path: {target_path} -> {dest_path}")
        return 3
    mklink(target_path, dest_path)
    return 0
def main():
    ret = main_process()
    if ret!= 0:
        print("Program faild.")
    else:
        print("Done.")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()