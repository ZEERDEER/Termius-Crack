import os
import requests
import zipfile
import shutil

def download_zip(url, download_path):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    downloaded_size = 0
    with open(download_path, 'wb') as file:
        for data in response.iter_content(chunk_size=1024):
            file.write(data)
            downloaded_size += len(data)
            done = int(50 * downloaded_size / total_size)
            print(f"\r[{'=' * done}{' ' * (50 - done)}] {100 * downloaded_size / total_size:.2f}%", end='')

def unzip_file(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def move_app_folder(source, destination):
    app_folder = os.path.join(source, 'app')
    if os.path.exists(app_folder):
        shutil.move(app_folder, destination)

def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

def delete_folder(folder_path):
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        shutil.rmtree(folder_path)

def main():
    zip_url = "https://github.com/ZEERDEER/Termius-Crack/releases/download/main/TermiusCrack.zip"
    download_path = "TermiusCrack.zip"
    extract_to = "TermiusCrack"
    
    print("Downloading ZIP file...")
    download_zip(zip_url, download_path)
    print("\nDownload completed.")
    
    print("Unzipping the file...")
    unzip_file(download_path, extract_to)
    
    username = os.getlogin()
    destination = f"C:\\Users\\{username}\\AppData\\Local\\Programs\\Termius\\resources"
    
    app_asar_unpacked_path = os.path.join(destination, 'app.asar.unpacked')
    print("Deleting the 'app.asar.unpacked' folder...")
    delete_folder(app_asar_unpacked_path)
    
    print("Moving the 'app' folder...")
    move_app_folder(extract_to, destination)
    
    app_asar_path = os.path.join(destination, 'app.asar')
    print("Deleting the 'app.asar' file...")
    delete_file(app_asar_path)
    
    delete_update = input("Do you want to delete 'app-update.yml'? (yes/no): ").strip().lower()
    if delete_update == 'yes':
        app_update_path = os.path.join(destination, 'app-update.yml')
        print("Deleting the 'app-update.yml' file...")
        delete_file(app_update_path)
    
    delete_file(download_path)
    delete_folder(extract_to)
    print("Process completed.")

if __name__ == "__main__":
    main()