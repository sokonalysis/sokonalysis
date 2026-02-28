#!/usr/bin/env python3
"""
Mount BitLocker-encrypted Disk Image
Sub-option for sokonalysis - returns to main menu when done
SIMPLIFIED VERSION - Guarantees file manager opens
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
        """Mount the BitLocker image"""
        print()
        self.show_info("Mounting BitLocker image: " + YELLOW + self.disk_image + RESET)
        print()
        
        # Unmount if needed
        self.unmount_if_needed()
        
        # Create directories
        self.create_directories()
        print()
        
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
        print()
        
        # Check if dislocker-file exists
        dislocker_file = os.path.join(self.dislocker_dir, 'dislocker-file')
        if not os.path.exists(dislocker_file):
            self.show_error("dislocker-file not created!")
            return False
        
        file_size = os.path.getsize(dislocker_file)
        self.show_minus(f"dislocker-file size: {self.format_size(file_size)}")
        
        # Step 2: Mount the dislocker-file
        self.show_info("Mounting filesystem...")
        print()
        
        mounted_path = os.path.join(self.current_dir, self.mounted_dir)
        
        # Try mounting methods silently
        mount_success = False
        
        # Method 1: Simple loop mount
        if not mount_success:
            result = subprocess.run(['mount', '-o', 'loop', dislocker_file, mounted_path], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                mount_success = True
        
        # Method 2: ntfs-3g with loop
        if not mount_success:
            result = subprocess.run(['mount', '-t', 'ntfs-3g', '-o', 'loop', dislocker_file, mounted_path], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                mount_success = True
        
        # Method 3: ntfs-3g directly
        if not mount_success:
            result = subprocess.run(['ntfs-3g', '-o', 'ro,allow_other', dislocker_file, mounted_path], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                mount_success = True
        
        if not mount_success:
            self.show_error("Failed to mount filesystem!")
            return False
        
        self.show_success("Filesystem mounted successfully")
        print()
        
        # Show mounted path
        print(BLUE + "_________________________________________________________________\n")
        self.show_minus(f"Mounted Path: {YELLOW}{mounted_path}{RESET}")
        
        # Count files
        try:
            files = os.listdir(mounted_path)
            self.show_minus(f"Files found: {GREEN}{len(files)}{RESET}")
        except:
            pass
        
        print(BLUE + "_________________________________________________________________")
        print()
        
        return True
    
    def open_file_manager(self):
        """Open the mounted directory - GUARANTEED TO OPEN"""
        mounted_path = os.path.join(self.current_dir, self.mounted_dir)
        original_user = os.environ.get('SUDO_USER')
        
        print()
        self.show_info("Opening file manager...")
        
        # DETECT DESKTOP ENVIRONMENT
        desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        
        # Choose the BEST file manager for this system
        if 'kde' in desktop:
            # KDE - use dolphin
            fm_cmd = ['dolphin', mounted_path]
            fm_name = 'dolphin'
        elif 'xfce' in desktop:
            # XFCE - use thunar
            fm_cmd = ['thunar', mounted_path]
            fm_name = 'thunar'
        elif 'mate' in desktop or self.distro == 'parrot':
            # MATE or Parrot - use caja
            fm_cmd = ['caja', mounted_path]
            fm_name = 'caja'
        elif 'cinnamon' in desktop:
            # Cinnamon - use nemo
            fm_cmd = ['nemo', mounted_path]
            fm_name = 'nemo'
        elif 'gnome' in desktop or self.distro in ['kali', 'ubuntu']:
            # GNOME - use nautilus
            fm_cmd = ['nautilus', mounted_path]
            fm_name = 'nautilus'
        else:
            # Default to xdg-open
            fm_cmd = ['xdg-open', mounted_path]
            fm_name = 'xdg-open'
        
        # Check if the chosen file manager exists
        try:
            subprocess.run(['which', fm_cmd[0]], capture_output=True, check=True)
            fm_exists = True
        except:
            fm_exists = False
            # Fallback to xdg-open
            fm_cmd = ['xdg-open', mounted_path]
            fm_name = 'xdg-open'
        
        # OPEN THE FILE MANAGER
        try:
            if original_user and original_user != 'root':
                # Running as sudo - open as original user
                cmd = ['sudo', '-u', original_user] + fm_cmd
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Running as normal user
                subprocess.Popen(fm_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            self.show_success(f"Opened with {fm_name}")
            time.sleep(2)  # Give it time to open
            
        except Exception as e:
            self.show_error(f"Failed to open file manager: {e}")
            # Show manual instructions
            self.show_minus(f"Access files at: {YELLOW}{mounted_path}{RESET}")
            print(f"  {GREEN}cd \"{mounted_path}\"{RESET}")
            print(f"  {GREEN}xdg-open \"{mounted_path}\"{RESET}")
        
        print()
        return True
    
    def unmount(self):
        """Unmount the BitLocker volumes"""
        print()
        self.show_info("Unmounting...")
        
        mounted_path = os.path.join(self.current_dir, self.mounted_dir)
        dislocker_path = os.path.join(self.current_dir, self.dislocker_dir)
        
        success = True
        
        if os.path.ismount(mounted_path):
            # Try normal unmount
            result = subprocess.run(['umount', mounted_path], capture_output=True)
            if result.returncode != 0:
                # Try force unmount
                result = subprocess.run(['umount', '-f', mounted_path], capture_output=True)
                if result.returncode != 0:
                    # Try lazy unmount
                    result = subprocess.run(['umount', '-l', mounted_path], capture_output=True)
                    if result.returncode != 0:
                        self.show_error(f"Failed to unmount {mounted_path}")
                        success = False
                    else:
                        self.show_success(f"Unmounted: {mounted_path}")
                else:
                    self.show_success(f"Unmounted: {mounted_path}")
            else:
                self.show_success(f"Unmounted: {mounted_path}")
        
        # Clean up
        subprocess.run(['losetup', '-D'], capture_output=True)
        
        if success:
            self.show_success("✅ Unmount completed")
        else:
            self.show_error("❌ Unmount failed")
        
        return success
    
    def run(self):
        """Main run function"""
        print()
        
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
        
        # Open file manager - GUARANTEED
        self.open_file_manager()
        
        # Ask to unmount
        while True:
            print(tag_question() + f"Unmount? ({GREEN}y{RESET}/{RED}n{RESET}): ", end='')
            choice = input().lower().strip()
            if choice in ['y', 'yes']:
                self.unmount()
                break
            elif choice in ['n', 'no']:
                self.show_info(f"Mounted at: {os.path.join(self.current_dir, self.mounted_dir)}")
                break
            else:
                print(tag_exclamation() + "Please enter y or n")

def mount_bitlocker_suboption():
    mounter = BitLockerMounter()
    mounter.run()

if __name__ == "__main__":
    mount_bitlocker_suboption()
