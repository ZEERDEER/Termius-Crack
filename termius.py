import os
import requests
import zipfile
import shutil

def download_zip(url, download_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an error for bad responses
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

def move_app_folder(source, destination):
    app_folder = os.path.join(source, 'app')
    if os.path.exists(app_folder):
        destination_app_folder = os.path.join(destination, 'app')
        if os.path.exists(destination_app_folder):
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
    zip_url = "https://github.com/ZEERDEER/Termius-Crack/releases/download/main/TermiusCrack.zip"
    download_path = "TermiusCrack.zip"
    extract_to = "TermiusCrack"
    
    print(f"ZIP file will be downloaded to: {os.path.abspath(download_path)}")
    print(f"ZIP file will be extracted to: {os.path.abspath(extract_to)}")
    
    try:
        print("Downloading ZIP file...")
        if not download_zip(zip_url, download_path):
            return
        print("\nDownload completed.")
        
        print("Unzipping the file...")
        if not unzip_file(download_path, extract_to):
            return
        
        username = os.getlogin()
        destination = f"C:\\Users\\{username}\\AppData\\Local\\Programs\\Termius\\resources"
        
        app_folder_path = os.path.join(destination, 'app')
        if os.path.exists(app_folder_path):
            user_input = input(f"The 'app' folder already exists at {destination}. Do you want to continue? (yes/no): ").strip().lower()
            if user_input != 'yes':
                print("Process aborted by the user.")
                return
        
        print("Moving the 'app' folder...")
        if not move_app_folder(extract_to, destination):
            return
        
        app_asar_path = os.path.join(destination, 'app.asar')
        print("Deleting the 'app.asar' file...")
        delete_file(app_asar_path)
        
        delete_update = input("Do you want to delete 'app-update.yml'? (yes/no): ").strip().lower()
        if delete_update == 'yes':
            app_update_path = os.path.join(destination, 'app-update.yml')
            print("Deleting the 'app-update.yml' file...")
            delete_file(app_update_path)
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        print("Cleaning up...")
        delete_file(download_path)
        delete_folder(extract_to)
        print("Process completed.")

if __name__ == "__main__":
    main()