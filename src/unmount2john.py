#!/usr/bin/env python3
"""
Mount BitLocker-encrypted Disk Image
Sub-option for sokonalysis - returns to main menu when done
UNIVERSAL VERSION - Works on Kali, Parrot, Ubuntu, Debian, etc.
SOKONALYSIS - Created by Soko James
"""

import os
import sys
import subprocess
import time
import getpass
import platform

# ANSI color codes
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
CYAN = '\033[36m'
BLUE = '\033[34m'
ORANGE = '\033[38;5;208m'
RESET = '\033[0m'

def tag_asterisk(): return YELLOW + "[*]" + RESET + " "
def tag_plus(): return GREEN + "[+]" + RESET + " "
def tag_minus(): return GREEN + "[-]" + RESET + " "
def tag_exclamation(): return RED + "[!]" + RESET + " "
def tag_gt(): return YELLOW + "[>]" + RESET + " "
def tag_x(): return RED + "[x]" + RESET + " "
def tag_question(): return ORANGE + "[?]" + RESET + " "

class BitLockerMounter:
    def __init__(self):
        self.disk_image = None
        self.password = None
        self.dislocker_dir = "dislocker"
        self.mounted_dir = "mounted"
        self.current_dir = os.getcwd()
        self.distro = self.detect_distro()
        
    def detect_distro(self):
        """Detect which Linux distribution we're running on"""
        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read().lower()
                if 'kali' in content:
                    return 'kali'
                elif 'parrot' in content:
                    return 'parrot'
                elif 'ubuntu' in content:
                    return 'ubuntu'
                elif 'debian' in content:
                    return 'debian'
                else:
                    return 'other'
        except:
            return 'unknown'
    
    def show_error(self, message): print(tag_x() + message)
    def show_success(self, message): print(tag_plus() + message)
    def show_info(self, message): print(tag_asterisk() + message)
    def show_minus(self, message): print(tag_minus() + message)
    
    def check_root(self):
        """Check if running as root"""
        if os.geteuid() != 0:
            print(tag_exclamation() + "This script requires root privileges for mounting.")
            print(tag_gt() + "Please run sokonalysis with sudo.")
            return False
        return True
    
    def format_size(self, size):
        """Format file size human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}PB"
    
    def list_disk_images(self):
        """List disk images in current directory"""
        extensions = ['.dd', '.img', '.iso', '.raw', '.vhd', '.vmdk', '.dmg']
        disk_images = []
        
        print(BLUE + "_____________________ " + GREEN + "Available Disk Images" + BLUE + " _____________________\n")
        
        idx = 1
        for file in sorted(os.listdir('.')):
            if any(file.lower().endswith(ext) for ext in extensions):
                if os.path.isfile(file):
                    size = os.path.getsize(file)
                    size_str = self.format_size(size)
                    disk_images.append(file)
                    print(YELLOW + f"[{idx}]" + RESET + f" {file} " + CYAN + f"({size_str})" + RESET)
                    idx += 1
        
        print(YELLOW + f"[{idx}]" + RESET + " Enter custom path")
        print(YELLOW + f"[{idx+1}]" + RESET + " Return to Main Menu")
        print(BLUE + "_________________________________________________________________")
        print()
        
        return disk_images, idx
    
    def select_disk_image(self):
        """Let user select a disk image"""
        disk_images, last_idx = self.list_disk_images()
        
        try:
            choice = int(input(tag_gt() + f"Select disk image (1-{last_idx+1}): "))
            
            if 1 <= choice <= len(disk_images):  # Regular image selection
                return disk_images[choice-1]
            elif choice == len(disk_images) + 1:  # Custom path
                path = input(tag_gt() + "Enter full path: ").strip()
                if os.path.exists(path):
                    return path
                else:
                    self.show_error("File not found")
                    input(tag_gt() + "Press Enter to continue...")
                    return None
            else:  # Return to main menu
                return "RETURN_TO_MENU"
        except ValueError:
            self.show_error("Invalid choice")
            input(tag_gt() + "Press Enter to continue...")
            return None
    
    def get_password(self):
        """Get password from user"""
        print()
        print(tag_question() + "Enter BitLocker password (input will be hidden):")
        print()
        self.password = getpass.getpass(tag_gt() + "Password: ")
        return self.password is not None
    
    def create_directories(self):
        """Create necessary directories"""
        for dir_name in [self.dislocker_dir, self.mounted_dir]:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
                self.show_minus(f"Created directory: {dir_name}")
            else:
                self.show_minus(f"Using existing directory: {dir_name}")
    
    def unmount_if_needed(self):
        """Unmount if already mounted"""
        mounted_path = os.path.join(self.current_dir, self.mounted_dir)
        dislocker_path = os.path.join(self.current_dir, self.dislocker_dir)
        
        if os.path.ismount(mounted_path):
            self.show_minus("Unmounting previously mounted directory...")
            subprocess.run(['umount', mounted_path], capture_output=True)
        
        if os.path.ismount(dislocker_path):
            self.show_minus("Unmounting dislocker directory...")
            subprocess.run(['umount', dislocker_path], capture_output=True)
        
        # Detach any loop devices
        try:
            subprocess.run(['losetup', '-D'], capture_output=True)
        except:
            pass
    
    def mount_bitlocker(self):
        """Mount the BitLocker image - UNIVERSAL METHOD"""
        print()
        self.show_info("Mounting BitLocker image: " + YELLOW + self.disk_image + RESET)
        print()
        self.show_info(f"Detected distribution: {GREEN}{self.distro}{RESET}")
        print()
        
        # Unmount if needed
        self.unmount_if_needed()
        
        # Create directories
        self.create_directories()
        print()  # Add blank line after directory creation
        
        # Step 1: Run dislocker
        self.show_info("Unlocking with dislocker...")
        cmd1 = ['dislocker', self.disk_image, '-u' + self.password, self.dislocker_dir]
        
        result = subprocess.run(cmd1, capture_output=True, text=True)
        if result.returncode != 0:
            self.show_error("Failed to unlock BitLocker volume!")
            if "incorrect" in result.stderr.lower():
                self.show_error("Incorrect password")
            else:
                print(tag_x() + result.stderr)
            return False
        
        self.show_success("BitLocker unlocked successfully")
        print()  # Add blank line after success
        
        # Check if dislocker-file exists
        dislocker_file = os.path.join(self.dislocker_dir, 'dislocker-file')
        if not os.path.exists(dislocker_file):
            self.show_error("dislocker-file not created!")
            return False
        
        file_size = os.path.getsize(dislocker_file)
        self.show_minus(f"dislocker-file size: {self.format_size(file_size)}")
        
        # Step 2: Mount the dislocker-file - DISTRO-SPECIFIC METHOD
        self.show_info("Mounting filesystem...")
        print()  # Add blank line before mount
        
        mounted_path = os.path.join(self.current_dir, self.mounted_dir)
        
        # Try different mount methods based on distro
        mount_success = False
        
        # Method 1: Simple loop mount (works on Kali)
        if not mount_success:
            self.show_info("Trying method 1: Simple loop mount...")
            cmd2 = ['mount', '-o', 'loop', dislocker_file, mounted_path]
            result = subprocess.run(cmd2, capture_output=True, text=True)
            if result.returncode == 0:
                mount_success = True
                self.show_success("Mounted with loop device")
        
        # Method 2: ntfs-3g with loop (works on most systems)
        if not mount_success:
            self.show_info("Trying method 2: ntfs-3g with loop...")
            cmd2 = ['mount', '-t', 'ntfs-3g', '-o', 'loop', dislocker_file, mounted_path]
            result = subprocess.run(cmd2, capture_output=True, text=True)
            if result.returncode == 0:
                mount_success = True
                self.show_success("Mounted with ntfs-3g + loop")
        
        # Method 3: ntfs-3g with uid/gid (works on Parrot)
        if not mount_success:
            self.show_info("Trying method 3: ntfs-3g with permissions...")
            cmd2 = ['ntfs-3g', '-o', 'ro,allow_other', dislocker_file, mounted_path]
            result = subprocess.run(cmd2, capture_output=True, text=True)
            if result.returncode == 0:
                mount_success = True
                self.show_success("Mounted with ntfs-3g + permissions")
        
        # Method 4: mount with uid/gid (universal fallback)
        if not mount_success:
            self.show_info("Trying method 4: mount with uid/gid...")
            uid = os.getuid()
            gid = os.getgid()
            cmd2 = ['mount', '-o', f'loop,ro,uid={uid},gid={gid}', dislocker_file, mounted_path]
            result = subprocess.run(cmd2, capture_output=True, text=True)
            if result.returncode == 0:
                mount_success = True
                self.show_success("Mounted with uid/gid options")
        
        if not mount_success:
            self.show_error("Failed to mount filesystem with all methods!")
            print(tag_x() + result.stderr)
            return False
        
        self.show_success("Filesystem mounted successfully")
        print()  # Add blank line after mount
        
        # Show mounted path
        print(BLUE + "_________________________________________________________________\n")
        self.show_minus(f"Mounted Path: {YELLOW}{mounted_path}{RESET}")
        self.show_minus(f"Distribution: {GREEN}{self.distro}{RESET}")
        
        # Test access
        try:
            files = os.listdir(mounted_path)
            self.show_success(f"Found {len(files)} files/directories")
        except:
            self.show_error("Warning: Cannot list files - may need different permissions")
        
        print(BLUE + "_________________________________________________________________")
        print()
        
        return True
    
    def open_file_manager(self):
        """Open the mounted directory in file manager - UNIVERSAL METHOD"""
        mounted_path = os.path.join(self.current_dir, self.mounted_dir)
        
        # Try different file managers
        file_managers = [
            ['nautilus', mounted_path],   # GNOME
            ['dolphin', mounted_path],    # KDE
            ['nemo', mounted_path],       # Cinnamon
            ['thunar', mounted_path],     # XFCE
            ['pcmanfm', mounted_path],    # LXDE/LXQT
            ['caja', mounted_path],       # MATE
            ['xdg-open', mounted_path]    # Default
        ]
        
        # On Parrot, try sudo -u for file manager
        if self.distro == 'parrot':
            original_user = os.environ.get('SUDO_USER')
            if original_user:
                self.show_info(f"Attempting to open as {original_user}...")
                for fm in file_managers:
                    try:
                        cmd = ['sudo', '-u', original_user] + fm
                        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        self.show_info(f"Tried to open with {fm[0]}")
                        time.sleep(1)
                    except:
                        continue
        
        # Try normal opening (works on Kali)
        for fm in file_managers:
            try:
                # Check if file manager exists
                subprocess.run(['which', fm[0]], capture_output=True, check=True)
                subprocess.Popen(fm, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.show_info(f"Attempted to open with {fm[0]}")
                time.sleep(1)
            except:
                continue
        
        # Always show manual instructions
        print()
        self.show_info("If file manager didn't open, access manually:")
        print(f"  {GREEN}cd \"{mounted_path}\"{RESET}")
        print(f"  {GREEN}ls -la \"{mounted_path}\"{RESET}")
        print(f"  {GREEN}xdg-open \"{mounted_path}\"{RESET}")
        print()
        
        return True
    
    def unmount(self):
        """Unmount the BitLocker volumes - UNIVERSAL METHOD"""
        print()
        self.show_info("Unmounting...")
        
        mounted_path = os.path.join(self.current_dir, self.mounted_dir)
        dislocker_path = os.path.join(self.current_dir, self.dislocker_dir)
        
        success = True
        
        # Try multiple unmount methods
        if os.path.ismount(mounted_path):
            self.show_minus("Unmounting filesystem...")
            
            # Method 1: Normal unmount
            result = subprocess.run(['umount', mounted_path], capture_output=True)
            if result.returncode == 0:
                self.show_success(f"Unmounted: {mounted_path}")
            else:
                # Method 2: Force unmount
                self.show_info("Trying force unmount...")
                result = subprocess.run(['umount', '-f', mounted_path], capture_output=True)
                if result.returncode == 0:
                    self.show_success(f"Force unmounted: {mounted_path}")
                else:
                    # Method 3: Lazy unmount
                    self.show_info("Trying lazy unmount...")
                    result = subprocess.run(['umount', '-l', mounted_path], capture_output=True)
                    if result.returncode == 0:
                        self.show_success(f"Lazy unmounted: {mounted_path}")
                    else:
                        self.show_error(f"Failed to unmount {mounted_path}")
                        success = False
        
        # Unmount dislocker directory if mounted
        if os.path.ismount(dislocker_path):
            subprocess.run(['umount', '-f', dislocker_path], capture_output=True)
            self.show_minus("Unmounted dislocker directory")
        
        # Detach loop devices
        subprocess.run(['losetup', '-D'], capture_output=True)
        
        if success:
            self.show_success("✅ Unmount completed successfully")
        else:
            self.show_error("❌ Some volumes could not be unmounted")
            self.show_info(f"Try manually: sudo umount -f \"{mounted_path}\"")
        
        return success
    
    def run(self):
        """Main run function - returns to menu when done"""
        print()  # Add spacing from main menu
        
        # Show distro info
        self.show_info(f"Running on: {GREEN}{self.distro}{RESET}")
        print()
        
        # Check root (but don't exit, just return)
        if not self.check_root():
            input(tag_gt() + "Press Enter to return to main menu...")
            return
        
        # Select disk image
        self.disk_image = self.select_disk_image()
        if self.disk_image == "RETURN_TO_MENU":
            print(tag_asterisk() + "Returning to main menu...")
            return
        if not self.disk_image:
            return
        
        # Get password
        if not self.get_password():
            input(tag_gt() + "Press Enter to return to main menu...")
            return
        
        # Mount
        if not self.mount_bitlocker():
            input(tag_gt() + "Press Enter to return to main menu...")
            return
        
        # Open file manager
        self.open_file_manager()
        print()  # Add blank line after file manager message
        
        # Ask if user wants to unmount (with colored y/n)
        while True:
            print(tag_question() + f"Do you want to unmount? ({GREEN}y{RESET}/{RED}n{RESET}): ", end='')
            choice = input().lower().strip()
            if choice in ['y', 'yes']:
                self.unmount()
                break
            elif choice in ['n', 'no']:
                self.show_info("Files will remain mounted")
                self.show_info(f"You can access them at: {os.path.join(self.current_dir, self.mounted_dir)}")
                break
            else:
                print(tag_exclamation() + "Please enter y or n")
        

# No main function - this will be called from sokonalysis menu
def mount_bitlocker_suboption():
    """Function to call from sokonalysis main menu"""
    mounter = BitLockerMounter()
    mounter.run()

# If run directly, still work without the warning messages
if __name__ == "__main__":
    mount_bitlocker_suboption()
