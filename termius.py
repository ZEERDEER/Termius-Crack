import os
import requests
import zipfile
import shutil
import json

INSTALLER_VERSION = "1.5.0"

def get_version_from_package_json(app_path, unpacked_path):
    version = "Unknown version"
    if os.path.exists(app_path):
        version = read_version_from_json(app_path)
        if version != "Unknown version":
            return f"{version} CRACKED"
    elif os.path.exists(unpacked_path):
        version = read_version_from_json(unpacked_path)
        if version != "Unknown version":
            return f"{version} NORMAL"
    return version

def read_version_from_json(package_json_path):
    try:
        with open(package_json_path, 'r') as file:
            data = json.load(file)
            return data.get("version", "Unknown version")
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error reading version from package.json: {e}")
    return "Unknown version"

def get_latest_github_release_version(repo_url):
    api_url = f"https://api.github.com/repos/{repo_url}/releases/latest"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        release_info = response.json()
        release_name = release_info.get("name", "Unknown version")
        version = release_name.split()[-1] if release_name else "Unknown version"
        return version
    except requests.exceptions.RequestException as e:
        print(f"Error fetching release version from GitHub: {e}")
        return "Unknown version"

def download_zip(url, download_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        with open(download_path, 'wb') as file:
            for data in response.iter_content(chunk_size=1024):
                file.write(data)
                downloaded_size += len(data)
                done = int(50 * downloaded_size / total_size)
                print(f"\r[{'=' * done}{' ' * (50 - done)}] {100 * downloaded_size / total_size:.2f}%", end='')
    except requests.exceptions.RequestException as e:
        print(f"\nError downloading file: {e}")
        return False
    return True

def unzip_file(zip_path, extract_to):
    if not os.path.exists(zip_path):
        print(f"ZIP file not found: {zip_path}")
        return False
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    except zipfile.BadZipFile:
        print("Error: Bad ZIP file.")
        return False
    return True

def move_app_folder(source, destination, action):
    app_folder = os.path.join(source, 'app')
    if os.path.exists(app_folder):
        destination_app_folder = os.path.join(destination, 'app')
        if os.path.exists(destination_app_folder):
            if action == 'update':
                print("Overwriting the 'app' folder as part of the update process.")
                delete_folder(destination_app_folder)
            else:
                user_input = input(f"The 'app' folder already exists at {destination}. Do you want to overwrite it? (yes/no): ").strip().lower()
                if user_input == 'yes':
                    delete_folder(destination_app_folder)
                else:
                    print("Process aborted by the user.")
                    return False
        try:
            shutil.move(app_folder, destination)
        except shutil.Error as e:
            print(f"Error moving folder: {e}")
            return False
    else:
        print(f"App folder not found in {source}")
        return False
    return True

def delete_file(file_path):
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            print(f"Error deleting file {file_path}: {e}")

def delete_folder(folder_path):
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        try:
            shutil.rmtree(folder_path)
        except OSError as e:
            print(f"Error deleting folder {folder_path}: {e}")

def main():
    username = os.getlogin()
    app_path = f"C:\\Users\\{username}\\AppData\\Local\\Programs\\Termius\\resources\\app\\package.json"
    unpacked_path = f"C:\\Users\\{username}\\AppData\\Local\\Programs\\Termius\\resources\\app.asar.unpacked\\package.json"
    current_version = get_version_from_package_json(app_path, unpacked_path)
    print(f"Current Installer version:{INSTALLER_VERSION}")
    print(f"Current Termius version: {current_version}")

    repo_url = "ZEERDEER/Termius-Crack"
    latest_version = get_latest_github_release_version(repo_url)
    print(f"Latest Termius Crack version available: {latest_version}")

    print("\nNote: This script will crack the Termius software. Be aware that cracking software is illegal and can result in severe consequences.")

    zip_url = "https://github.com/ZEERDEER/Termius-Crack/releases/download/main/TermiusCrack.zip"
    download_path = "TermiusCrack.zip"
    extract_to = "TermiusCrack"
    
    print(f"ZIP file will be downloaded to: {os.path.abspath(download_path)}")
    print(f"ZIP file will be extracted to: {os.path.abspath(extract_to)}")
    
    action = input("Do you want to install or update the cracked version of the app? (install/update): ").strip().lower()
    if action not in ['install', 'update']:
        print("Invalid option. Please choose 'install' or 'update'.")
        return
    
    try:
        print("Downloading ZIP file...")
        if not download_zip(zip_url, download_path):
            return
        print("\nDownload completed.")
        
        print("Unzipping the file...")
        if not unzip_file(download_path, extract_to):
            return
        
        destination = f"C:\\Users\\{username}\\AppData\\Local\\Programs\\Termius\\resources"
        
        if action == 'update':
            app_folder_path = os.path.join(destination, 'app')
            app_asar_unpacked_path = os.path.join(destination, 'app.asar.unpacked')
            
            if not os.path.exists(app_folder_path) and os.path.exists(app_asar_unpacked_path):
                print("Crack is not installed. Please use the install function instead.")
                return
            elif os.path.exists(app_folder_path) and not os.path.exists(app_asar_unpacked_path):
                print("Proceeding with update by overwriting the 'app' folder.")
            elif os.path.exists(app_folder_path) and os.path.exists(app_asar_unpacked_path):
                print("Both 'app' and 'app.asar.unpacked' folders exist. Please read the README for instructions on how to use and fix this.")
                return
        
        print("Moving the 'app' folder...")
        if not move_app_folder(extract_to, destination, action):
            return
        
        app_asar_path = os.path.join(destination, 'app.asar')
        print("Deleting the 'app.asar' file...")
        delete_file(app_asar_path)
        
        if action == 'install':
            app_asar_unpacked_path = os.path.join(destination, 'app.asar.unpacked')
            print("Deleting the 'app.asar.unpacked' folder...")
            delete_folder(app_asar_unpacked_path)
        
        delete_update = input("Do you want to delete 'app-update.yml'? (yes/no): ").strip().lower()
        if delete_update == 'yes':
            app_update_path = os.path.join(destination, 'app-update.yml')
            print("Deleting the 'app-update.yml' file...")
            delete_file(app_update_path)

        delete_package_json = input("Do you want to delete 'package.json' (located in the resources folder, exist in new app folder, not used anymore)? (yes/no): ").strip().lower()
        if delete_package_json == 'yes':
            package_json_path = os.path.join(destination, 'package.json')
            print("Deleting the 'package.json' file...")
            delete_file(package_json_path)
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        print("Cleaning up...")
        delete_file(download_path)
        delete_folder(extract_to)
        print("Process completed.")

if __name__ == "__main__":
    main()