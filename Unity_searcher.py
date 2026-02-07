import warnings
from UnityPy.exceptions import UnityVersionFallbackWarning
from UnityPy.helpers import TypeTreeHelper
TypeTreeHelper.read_typetree_boost = False

def custom_showwarning(message, category, filename, lineno, file=None, line=None):
    if issubclass(category, UnityVersionFallbackWarning):
        print(
            "Unity version has stripped. using fallback version...\n"
            "if you want to use custom version or program can't find unity version,\n"
            "run program with -v argument to specify unity version"
        )
    else:
        print(warnings.formatwarning(message, category, filename, lineno, line))

warnings.showwarning = custom_showwarning

import UnityPy
import os
import csv
import sys
import ctypes
import clr
import argparse

# Global variables for Mono.Cecil (loaded at runtime)
AssemblyDefinition = None
OpCodes = None


def sanitize(text: str) -> str:
    """Escape special characters for display."""
    return text.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")


def get_script_dir():
    """Get the directory of the script or executable."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def find_ggm_file(data_path):
    """Find globalgamemanagers or similar files to extract Unity version."""
    candidates = ["globalgamemanagers", "globalgamemanagers.assets", "data.unity3d"]
    for candidate in candidates:
        ggm_path = os.path.join(data_path, candidate)
        if os.path.exists(ggm_path):
            return ggm_path

    # Also check unity default resources
    resources_path = os.path.join(data_path, "Resources", "unity default resources")
    if os.path.exists(resources_path):
        return resources_path

    return None


def find_data_path(search_dir):
    """Find the _Data folder from the given directory."""
    # If search_dir itself is a _Data folder
    if search_dir.lower().endswith("_data"):
        return search_dir
    # Search for _Data subfolder
    try:
        for d in os.listdir(search_dir):
            if d.lower().endswith("_data") and os.path.isdir(os.path.join(search_dir, d)):
                return os.path.join(search_dir, d)
    except OSError:
        pass
    return None


def get_unity_version(search_dir):
    """Extract Unity version from the game data folder."""
    data_path = find_data_path(search_dir)
    if data_path is None:
        return None
    ggm_path = find_ggm_file(data_path)
    if ggm_path is None:
        return None
    try:
        env = UnityPy.load(ggm_path)
        if env.objects:
            return env.objects[0].assets_file.unity_version
    except Exception as e:
        print(f"Warning: Failed to extract Unity version: {e}")
    return None


def file_search(file_path, search_text: str, csv_writer: csv.writer):
    """Search for text in Unity asset files."""
    ret_lst = []

    try:
        env = UnityPy.load(file_path)
    except Exception as e:
        print(f"Asset loading error: {file_path}, error: {e}")
        return ret_lst

    search_lower = search_text.lower()
    search_bytes = search_text.encode("utf-8", errors="ignore")
    search_bytes_lower = search_lower.encode("utf-8", errors="ignore")

    for obj in env.objects:
        if obj.type.name in ("TextAsset", "MonoBehaviour"):
            try:
                assets_name = obj.assets_file.name
                obj_raw = obj.get_raw_data()
                obj_raw_decoded = obj_raw.decode("utf-8", errors="ignore").lower()
                obj_name = obj.peek_name() or "-"
                obj_pathid = obj.path_id

                # Check for search text in multiple ways
                if (search_lower in obj_raw_decoded
                    or search_bytes in obj_raw
                    or search_bytes_lower in obj_raw):
                    msg = f"Found! | file_path: {file_path} | assets_name: {assets_name} | path_id: {obj_pathid} | type_name: {obj.type.name} | obj_name: {obj_name}"
                    print(msg)
                    csv_writer.writerow([file_path, assets_name, obj_pathid, obj.type.name, obj_name])
                    ret_lst.append(msg)
            except Exception as e:
                pass

    return ret_lst


def dll_search(file_path, search_text: str, csv_writer: csv.writer):
    """Search for text in .NET DLL files using Mono.Cecil."""
    ret_lst = []

    if AssemblyDefinition is None or OpCodes is None:
        return ret_lst

    try:
        assembly = AssemblyDefinition.ReadAssembly(file_path)
        search_lower = search_text.lower()

        for type_def in assembly.MainModule.Types:
            all_types = [type_def]

            while all_types:
                current_type = all_types.pop()
                all_types.extend(current_type.NestedTypes)

                for method in current_type.Methods:
                    if not method.HasBody:
                        continue

                    for instr in method.Body.Instructions:
                        if instr.OpCode == OpCodes.Ldstr:
                            current_str = instr.Operand if instr.Operand else ""
                            current_str_sanitized = sanitize(current_str)
                            current_str_lower = current_str_sanitized.lower()

                            if search_lower in current_str_lower:
                                msg = f"Found! | File: {os.path.basename(file_path)} | Class: {type_def.Name} | Method: {method.Name} | Text: {current_str_sanitized}"
                                print(msg)
                                csv_writer.writerow([file_path, type_def.Name, method.Name, current_str_sanitized])
                                ret_lst.append(msg)
    except Exception as e:
        pass

    return ret_lst


def load_mono_cecil(current_dir):
    """Load Mono.Cecil.dll for DLL searching."""
    global AssemblyDefinition, OpCodes

    print("Loading Mono.Cecil.dll...")
    try:
        dll_path = os.path.join(current_dir, "Mono.Cecil.dll")
        if not os.path.exists(dll_path):
            print(f"Warning: Mono.Cecil.dll not found at {dll_path}")
            print("DLL search will be disabled.")
            return False

        clr.AddReference(dll_path)
        from Mono.Cecil import AssemblyDefinition as AD  # type: ignore
        from Mono.Cecil.Cil import OpCodes as OC  # type: ignore

        AssemblyDefinition = AD
        OpCodes = OC
        print("Mono.Cecil.dll loaded successfully!")
        return True
    except Exception as e:
        print(f"Error loading Mono.Cecil.dll: {e}")
        print("DLL search will be disabled.")
        return False


def collect_files(search_dir):
    """Collect DLL and asset files from the directory."""
    exclude_exts = {
        ".manifest", ".exe", ".txt", ".json", ".xml", ".log", ".ini", ".cfg",
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".wav", ".mp3", ".ogg",
        ".mp4", ".avi", ".mov", ".pdb", ".mdb"
    }

    dll_list = []
    asset_list = []

    for root, _, files in os.walk(search_dir):
        for fn in files:
            ext = os.path.splitext(fn)[1].lower()
            if ext in exclude_exts:
                continue

            full_path = os.path.join(root, fn)
            if ext == ".dll":
                dll_list.append(full_path)
            else:
                asset_list.append(full_path)

    return dll_list, asset_list


def update_title(current, total, description):
    """Update console title with progress."""
    ctypes.windll.kernel32.SetConsoleTitleW(f"[{current:06d} / {total:06d}] {description}")


def main():
    parser = argparse.ArgumentParser(description="Search for strings in Unity dlls, assets and assetbundles")
    parser.add_argument("-v", "--unity-version",
                        help='Unity version to use for loading assets. Example: -v "2022.3.15f1"',
                        default=None)
    parser.add_argument("-s", "--search",
                        help="Search text (if not provided, will prompt for input)",
                        default=None)
    parser.add_argument("-d", "--directory",
                        help="Directory to search (default: current directory)",
                        default=None)
    parser.add_argument("--no-dll",
                        action="store_true",
                        help="Skip DLL searching")
    args = parser.parse_args()

    current_dir = args.directory if args.directory else get_script_dir()

    print("Unity Asset Text Searcher")
    print("Made by Snowyegret, Version: 2.0.0")
    print("")
    print(f"Search directory: {current_dir}")
    print("")

    # Load Mono.Cecil for DLL searching
    cecil_loaded = False
    if not args.no_dll:
        cecil_loaded = load_mono_cecil(get_script_dir())

    # Get Unity version
    if args.unity_version:
        unity_version = args.unity_version
    else:
        unity_version = get_unity_version(current_dir)
        if unity_version is None:
            print("Warning: Could not auto-detect Unity version.")
            print("You can specify it with -v argument.")

    if unity_version:
        print(f"Unity version: {unity_version}")
        UnityPy.config.FALLBACK_UNITY_VERSION = unity_version
    print("")

    # Get search text
    if args.search:
        search_text = args.search
    else:
        search_text = input("Search text: ").strip()
        if not search_text:
            print("Error: Search text cannot be empty.")
            input("Press Enter to exit...")
            sys.exit(1)

    print(f"\nSearching for: {search_text}\n")

    # Sanitize filename for output files
    safe_filename = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in search_text)
    safe_filename = safe_filename[:50]  # Limit filename length

    # Result storage
    txt_result_lst = []
    dll_result_lst = []

    # Collect files
    dll_list, asset_list = collect_files(current_dir)

    if not args.no_dll and not cecil_loaded:
        dll_list = []  # Skip DLLs if Cecil failed to load

    total_files = len(dll_list) + len(asset_list)
    current_file = 1

    print(f"Found {len(dll_list)} DLL files and {len(asset_list)} asset files to search.\n")

    # Create output files
    asset_csv_path = os.path.join(current_dir, f"output_assets_{safe_filename}.csv")
    dll_csv_path = os.path.join(current_dir, f"output_dll_{safe_filename}.csv")
    txt_path = os.path.join(current_dir, f"output_{safe_filename}.txt")

    with open(asset_csv_path, "w", newline="", encoding="utf-8") as asset_csv_file, \
         open(dll_csv_path, "w", newline="", encoding="utf-8") as dll_csv_file, \
         open(txt_path, "w", encoding="utf-8") as txt_file:

        asset_csv_writer = csv.writer(asset_csv_file)
        dll_csv_writer = csv.writer(dll_csv_file)

        # Write CSV headers
        asset_csv_writer.writerow(["file_path", "assets_name", "path_id", "type_name", "obj_name"])
        dll_csv_writer.writerow(["file_path", "class_name", "method_name", "text"])

        # Write TXT header
        txt_file.write("[INFO]\n")
        if unity_version:
            txt_file.write(f"Unity version: {unity_version}\n")
        txt_file.write(f"Search text: {search_text}\n")
        txt_file.write(f"Search directory: {current_dir}\n\n")

        # Search DLLs
        if dll_list:
            print("Searching DLL files...")
            for dll in dll_list:
                update_title(current_file, total_files, f"Searching DLL: {os.path.basename(dll)}")
                dll_result_lst.extend(dll_search(dll, search_text, dll_csv_writer))
                current_file += 1

        # Search assets
        if asset_list:
            print("Searching asset files...")
            for asset in asset_list:
                update_title(current_file, total_files, f"Searching asset: {os.path.basename(asset)}")
                txt_result_lst.extend(file_search(asset, search_text, asset_csv_writer))
                current_file += 1

        # Write results to TXT
        txt_file.write("[SEARCH RESULTS]\n\n")

        if dll_result_lst:
            txt_file.write("[DLL RESULTS]\n")
            for result in dll_result_lst:
                txt_file.write(f"{result}\n")
            txt_file.write("\n")

        if txt_result_lst:
            txt_file.write("[ASSET RESULTS]\n")
            for result in txt_result_lst:
                txt_file.write(f"{result}\n")
            txt_file.write("\n")

        if not dll_result_lst and not txt_result_lst:
            txt_file.write("No results found.\n")

    # Reset title
    ctypes.windll.kernel32.SetConsoleTitleW("Unity Asset Text Searcher - Complete")

    # Print summary
    print("\n" + "=" * 50)
    print("Search completed!")
    print("=" * 50)
    print(f"DLL results: {len(dll_result_lst)}")
    print(f"Asset results: {len(txt_result_lst)}")
    print("")
    print("Output files:")
    print(f"  - {txt_path}")
    if txt_result_lst:
        print(f"  - {asset_csv_path}")
    if dll_result_lst:
        print(f"  - {dll_csv_path}")

    input("\nPress Enter to exit...")
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSearch cancelled by user.")
        sys.exit(0)
    except Exception as e:
        import traceback
        print(f"\nUnexpected error: {e}")
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)
