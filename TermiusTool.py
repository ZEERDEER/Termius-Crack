import os
import re
import subprocess
import sys
import requests
import winreg
import time

###################
# Node.js Functions #
###################

def check_nodejs():
    """
    Check if Node.js is installed
    Returns: bool
    """
    try:
        subprocess.run(['node', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"Error checking Node.js: {e}")
        return False

def download_nodejs():
    """
    Download Node.js installer
    Returns: installer path
    """
    print('Downloading Node.js...')
    url = 'https://nodejs.org/dist/v22.11.0/node-v22.11.0-x64.msi'
    response = requests.get(url, stream=True)
    installer_path = os.path.join(os.environ['TEMP'], 'nodejs_installer.msi')
    
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024
    downloaded = 0
    
    with open(installer_path, 'wb') as f:
        for data in response.iter_content(block_size):
            downloaded += len(data)
            f.write(data)
            progress = downloaded * 100 / total_size
            done = int(50 * downloaded / total_size)
            sys.stdout.write('\r[{}{}] {:.1f}%'.format(
                '=' * done, ' ' * (50-done), progress
            ))
            sys.stdout.flush()
    print()
    
    return installer_path

def refresh_env():
    """Refresh current process environment variables"""
    try:
        # Get system environment variables
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 0, winreg.KEY_READ) as key:
            path_value = winreg.QueryValueEx(key, 'Path')[0]
            
        # Get user environment variables
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment', 0, winreg.KEY_READ) as key:
            user_path = winreg.QueryValueEx(key, 'Path')[0]
            
        # Merge system and user PATH
        full_path = f"{path_value};{user_path}"
        
        # Update current process environment variables
        os.environ['Path'] = full_path
        
        print("Environment variables refreshed")
        return True
    except Exception as e:
        print(f"Failed to refresh environment variables: {e}")
        return False

def install_nodejs():
    """
    Install Node.js
    Returns: (bool, str, str) - (success, node_path, npm_path)
    """
    try:
        # Ask user if they want to install Node.js
        install = input('Node.js is required. Install? (y/n): ').lower().strip() == 'y'
        if not install:
            return False, '', ''

        # Download and install
        installer_path = download_nodejs()
        print('Installing Node.js, please wait...')
        subprocess.run(['msiexec.exe', '/i', installer_path, '/quiet', '/norestart'], check=True)
        
        # Clean up installer
        os.remove(installer_path)
        
        # Refresh environment variables after installation
        if not refresh_env():
            print("Warning: Failed to refresh environment variables, may need to restart terminal")
        
        # Get Node.js installation path
        node_path = os.path.join(os.environ['ProgramFiles'], 'nodejs', 'node.exe')
        npm_path = os.path.join(os.environ['ProgramFiles'], 'nodejs', 'npm.cmd')
        
        if not os.path.exists(node_path) or not os.path.exists(npm_path):
            print('Node.js files not found, installation may have failed')
            return False, '', ''
            
        # Verify installation
        print('Verifying Node.js installation...')
        try:
            subprocess.run([node_path, '--version'], check=True, capture_output=True)
            print('Node.js installation verified!')
            return True, node_path, npm_path
        except subprocess.CalledProcessError:
            print('Node.js installation verification failed')
            return False, '', ''
        
    except Exception as e:
        print(f'Node.js installation failed: {str(e)}')
        return False, '', ''

def get_nodejs_path():
    """
    Get actual installation paths of Node.js and npm
    Returns: (str, str) - (node_path, npm_path)
    """
    try:
        # First, try using where command to find
        node_result = subprocess.run(['where', 'node'], 
                                   capture_output=True, 
                                   text=True)
        npm_result = subprocess.run(['where', 'npm.cmd'], 
                                  capture_output=True, 
                                  text=True)
        
        if node_result.returncode == 0 and npm_result.returncode == 0:
            node_path = node_result.stdout.splitlines()[0].strip()
            npm_path = npm_result.stdout.splitlines()[0].strip()
            # Verify found paths are usable
            if verify_nodejs_installation(node_path, npm_path):
                return node_path, npm_path
            
        # If where command fails, try looking up in registry
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Node.js', 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
                install_dir = winreg.QueryValueEx(key, 'InstallPath')[0]
                node_path = os.path.join(install_dir, 'node.exe')
                npm_path = os.path.join(install_dir, 'npm.cmd')
                if os.path.exists(node_path) and os.path.exists(npm_path):
                    # Verify found paths are usable
                    if verify_nodejs_installation(node_path, npm_path):
                        return node_path, npm_path
        except WindowsError:
            pass
            
        # Finally, try default paths
        default_paths = [
            os.environ.get('ProgramFiles'),
            os.environ.get('ProgramFiles(x86)'),
            os.environ.get('LocalAppData')
        ]
        
        for base_path in default_paths:
            if base_path:
                node_path = os.path.join(base_path, 'nodejs', 'node.exe')
                npm_path = os.path.join(base_path, 'nodejs', 'npm.cmd')
                if os.path.exists(node_path) and os.path.exists(npm_path):
                    # Verify found paths are usable
                    if verify_nodejs_installation(node_path, npm_path):
                        return node_path, npm_path
                    
        print('No usable Node.js installation found, preparing to reinstall...')
        return None, None
        
    except Exception as e:
        print(f"Error finding Node.js path: {e}")
        return None, None

def verify_nodejs_installation(node_path, npm_path):
    """Verify if Node.js installation is working"""
    try:
        subprocess.run([node_path, '--version'], 
                      check=True, 
                      capture_output=True)
        subprocess.run([npm_path, '--version'], 
                      check=True, 
                      capture_output=True)
        return True
    except Exception:
        return False

##################
# ASAR Functions #
##################

def install_asar(npm_path):
    """
    Install asar globally
    Args: npm_path - Full path to npm executable
    Returns: bool
    """
    try:
        print(f'Installing asar using npm...')
        
        result = subprocess.run(
            [npm_path, 'install', '-g', 'asar'],
            shell=False,
            check=True,
            capture_output=True,
            text=True
        )
        
        print('asar installed successfully!')
        return True
        
    except subprocess.CalledProcessError as e:
        print(f'asar installation failed: {e.stderr if e.stderr else str(e)}')
        return False
    except Exception as e:
        print(f'asar installation failed: {str(e)}')
        return False

def main(disable_update=False):
    """Main function"""
    # 1. Check and install Node.js
    if not check_nodejs():
        success, node_path, npm_path = install_nodejs()
        if not success:
            print('Node.js not installed, exiting')
            sys.exit(1)
    else:
        node_path, npm_path = get_nodejs_path()
        if not node_path or not npm_path:
            success, node_path, npm_path = install_nodejs()
            if not success:
                print('Node.js installation failed, exiting')
                sys.exit(1)
        else:
            print('Node.js installed')

    # 2. Install asar
    print('Installing asar...')
    if not install_asar(npm_path):
        print('asar installation failed, exiting')
        sys.exit(1)
    
    print('Waiting for variable refresh...')
    time.sleep(5)
    refresh_env()
    
    # 3. Check files and processes
    asar_cmd = os.path.join(os.environ['APPDATA'], 'npm', 'asar.cmd')
    if not os.path.exists(asar_cmd):
        print('asar command not found')
        sys.exit(1)
    
    # Add auto-update prompt here, before file modifications
    disable_update = input('Disable auto-update? (y/n): ').lower().strip() == 'y'
    print('Auto-update will be ' + ('disabled' if disable_update else 'enabled'))
    
    base_path = os.path.join(os.path.expanduser("~"), 'AppData', 'Local', 'Programs', 'Termius', 'resources')
    asar_file = os.path.join(base_path, 'app.asar')
    extract_dir = os.path.join(base_path, 'app')

    print('Checking Termius process...')
    try:
        subprocess.run(['taskkill', '/F', '/IM', 'Termius.exe'], 
                      capture_output=True,
                      text=True)
        print('Termius closed, waiting for process exit...')
        time.sleep(2)
    except subprocess.CalledProcessError:
        print('Termius not running, continuing...')

    # 4. Extract and modify files
    if not os.path.exists(asar_file):
        print(f'Error: File not found {asar_file}')
        sys.exit(1)

    try:
        print('Extracting app.asar file...')
        result = subprocess.run([asar_cmd, 'extract', asar_file, extract_dir], 
                              capture_output=True, 
                              text=True,
                              check=True)
        print('app.asar extracted successfully!')
        
        # Delete app.asar file
        max_retries = 3
        retry_delay = 2
        for i in range(max_retries):
            try:
                if os.path.exists(asar_file):
                    os.remove(asar_file)
                    print('app.asar deleted')
                break
            except PermissionError:
                if i < max_retries - 1:
                    print(f'Delete failed, retrying... ({i+1}/{max_retries})')
                    time.sleep(retry_delay)
                else:
                    print('Warning: Cannot delete app.asar file, but crack will still work')
                    break
    except Exception as e:
        print(f'Error extracting or deleting file: {str(e)}')
        sys.exit(1)

    # 5. Disable auto update and complete modifications
    if disable_update:
        update_file = os.path.join(base_path, 'app-update.yml')
        if os.path.exists(update_file):
            os.remove(update_file)
            print('app-update.yml deleted, auto update disabled')
        else:
            print('app-update.yml not found')

    # Modify main program file
    assets_dir = os.path.join(extract_dir, 'background-process', 'assets')
    for root, dirs, files in os.walk(assets_dir):
        for file in files:
            if file.startswith('main-') and file.endswith('.js'):
                file_path = os.path.join(root, file)
                
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace specified content
                old_code = "const e=await this.api.bulkAccount();"
                new_code = '''
var e=await this.api.bulkAccount();
e.account.pro_mode=true;
e.account.need_to_update_subscription=false;
e.account.current_period={
    "from": "2022-01-01T00:00:00",
    "until": "2099-01-01T00:00:00"
};
e.account.plan_type="Premium";
e.account.user_type="Premium";
e.student=null;
e.trial=null;
e.account.authorized_features.show_trial_section=false;
e.account.authorized_features.show_subscription_section=true;
e.account.authorized_features.show_github_account_section=false;
e.account.expired_screen_type=null;
e.personal_subscription={
    "now": new Date().toISOString().slice(0, -5),
    "status": "SUCCESS",
    "platform": "stripe",
    "current_period": {
        "from": "2022-01-01T00:00:00",
        "until": "2099-01-01T00:00:00"
    },
    "revokable": true,
    "refunded": false,
    "cancelable": true,
    "reactivatable": false,
    "currency": "usd",
    "created_at": "2022-01-01T00:00:00",
    "updated_at": new Date().toISOString().slice(0, -5),
    "valid_until": "2099-01-01T00:00:00",
    "auto_renew": true,
    "price": 12.0,
    "verbose_plan_name": "Termius Pro Monthly",
    "plan_type": "SINGLE",
    "is_expired": false
};
e.access_objects=[{
    "period": {
        "start": "2022-01-01T00:00:00",
        "end": "2099-01-01T00:00:00"
    },
    "title": "Pro"
}];
'''

                new_content = re.sub(re.escape(old_code), new_code, content)

                # Write back modified file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

    print("Complete!")
    input("\nPress any key to exit...")

if __name__ == "__main__":
    main(disable_update=True)
