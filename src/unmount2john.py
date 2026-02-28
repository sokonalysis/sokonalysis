#!/usr/bin/env python3
"""
Mount BitLocker-encrypted Disk Image
Sub-option for sokonalysis - returns to main menu when done
SOKONALYSIS - Created by Soko James
"""

import os
import sys
import subprocess
import time
import getpass
import pwd
import grp
import stat
import signal

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
        
        # Get the original user who ran sudo
        self.sudo_user = os.environ.get('SUDO_USER')
        if self.sudo_user and self.sudo_user != 'root':
            self.username = self.sudo_user
            self.uid = int(os.environ.get('SUDO_UID', os.getuid()))
            self.gid = int(os.environ.get('SUDO_GID', os.getgid()))
        else:
            self.username = pwd.getpwuid(os.getuid()).pw_name
            self.uid = os.getuid()
            self.gid = os.getgid()
        
        # Store mount paths
        self.mounted_path = os.path.join(self.current_dir, self.mounted_dir)
        self.dislocker_path = os.path.join(self.current_dir, self.dislocker_dir)
        self.dislocker_file = os.path.join(self.dislocker_path, 'dislocker-file')
        
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
        """Create necessary directories with proper ownership"""
        for dir_name in [self.dislocker_dir, self.mounted_dir]:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
                self.show_minus(f"Created directory: {dir_name}")
            else:
                self.show_minus(f"Using existing directory: {dir_name}")
            
            # Set ownership to the original user
            try:
                os.chown(dir_name, self.uid, self.gid)
            except:
                pass  # Ignore if can't change ownership
            # Set permissions
            os.chmod(dir_name, 0o755)
    
    def unmount_if_needed(self):
        """Unmount if already mounted"""
        # Force unmount if mounted
        if os.path.ismount(self.mounted_path):
            self.show_minus("Unmounting previously mounted directory...")
            subprocess.run(['umount', '-f', self.mounted_path], capture_output=True)
            time.sleep(1)  # Give it time to unmount
        
        # Check if dislocker dir is mounted
        try:
            result = subprocess.run(['mountpoint', '-q', self.dislocker_path], capture_output=True)
            if result.returncode == 0:
                self.show_minus("Unmounting dislocker directory...")
                subprocess.run(['umount', '-f', self.dislocker_path], capture_output=True)
                time.sleep(1)
        except:
            pass
        
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
        
        # Create directories with proper ownership
        self.create_directories()
        print()  # Add blank line after directory creation
        
        # Step 1: Run dislocker
        self.show_info("Unlocking with dislocker...")
        
        # Use full path for dislocker
        dislocker_path = subprocess.run(['which', 'dislocker'], capture_output=True, text=True).stdout.strip()
        if not dislocker_path:
            self.show_error("dislocker not found! Please install it first.")
            self.show_info("On Debian/Ubuntu/Kali/Parrot: sudo apt install dislocker")
            return False
        
        # Run dislocker
        cmd1 = [dislocker_path, self.disk_image, '-u' + self.password, self.dislocker_dir]
        
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
        if not os.path.exists(self.dislocker_file):
            self.show_error("dislocker-file not created!")
            return False
        
        # Check file size
        try:
            file_size = os.path.getsize(self.dislocker_file)
            self.show_minus(f"dislocker-file size: {self.format_size(file_size)}")
        except:
            self.show_error("Cannot access dislocker-file")
            return False
        
        # Step 2: Mount the dislocker-file
        self.show_info("Mounting filesystem...")
        print()
        
        # Try ntfs-3g first (most common for BitLocker)
        cmd2 = [
            'ntfs-3g',
            '-o', f'uid={self.uid}',
            '-o', f'gid={self.gid}',
            '-o', 'umask=007',
            '-o', 'fmask=113',
            '-o', 'dmask=002',
            '-o', 'allow_other',
            '-o', 'ro',
            self.dislocker_file,
            self.mounted_path
        ]
        
        result = subprocess.run(cmd2, capture_output=True, text=True)
        
        if result.returncode != 0:
            self.show_info("ntfs-3g failed, trying mount with loop...")
            
            # Fallback to mount
            cmd3 = [
                'mount',
                '-o', f'loop,ro,uid={self.uid},gid={self.gid},umask=007,fmask=113,dmask=002',
                self.dislocker_file,
                self.mounted_path
            ]
            
            result = subprocess.run(cmd3, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.show_error("Failed to mount filesystem!")
                print(tag_x() + result.stderr)
                return False
        
        self.show_success("Filesystem mounted successfully")
        print()
        
        # Show mount info
        print(BLUE + "_________________________________________________________________\n")
        self.show_minus(f"Mounted Path: {YELLOW}{self.mounted_path}{RESET}")
        self.show_minus(f"Mounted as user: {GREEN}{self.username}{RESET}")
        
        # Verify mount
        if os.path.ismount(self.mounted_path):
            self.show_success("Mount verified")
        else:
            self.show_error("Mount verification failed")
            return False
        
        print(BLUE + "_________________________________________________________________")
        print()
        
        return True
    
    def open_file_manager(self):
        """Open file manager (works on any Linux system)"""
        print()
        self.show_info(f"Files are mounted at: {YELLOW}{self.mounted_path}{RESET}")
        print()
        self.show_info("You can access them with any of these commands:")
        print(f"  {GREEN}cd \"{self.mounted_path}\"{RESET}")
        print(f"  {GREEN}xdg-open \"{self.mounted_path}\"{RESET}")
        print(f"  {GREEN}nautilus \"{self.mounted_path}\"{RESET}  # GNOME")
        print(f"  {GREEN}dolphin \"{self.mounted_path}\"{RESET}   # KDE")
        print(f"  {GREEN}thunar \"{self.mounted_path}\"{RESET}    # XFCE")
        print(f"  {GREEN}pcmanfm \"{self.mounted_path}\"{RESET}   # LXDE")
        print()
        
        # Try to detect and open the appropriate file manager
        try:
            # Detect desktop environment
            desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
            
            if 'kde' in desktop:
                fm = 'dolphin'
            elif 'gnome' in desktop:
                fm = 'nautilus'
            elif 'xfce' in desktop:
                fm = 'thunar'
            elif 'cinnamon' in desktop:
                fm = 'nemo'
            elif 'mate' in desktop:
                fm = 'caja'
            elif 'lxde' in desktop or 'lxqt' in desktop:
                fm = 'pcmanfm'
            else:
                fm = 'xdg-open'
            
            # Try to open as the original user
            if self.username and self.username != 'root':
                self.show_info(f"Attempting to open with {fm}...")
                cmd = ['sudo', '-u', self.username, 'setsid', fm, self.mounted_path]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2)
        except:
            pass  # Ignore errors - we already showed manual commands
        
        return True
    
    def unmount(self):
        """Unmount the BitLocker volumes - FIXED VERSION"""
        print()
        self.show_info("Unmounting...")
        
        success = True
        
        # Step 1: Try to unmount the mounted filesystem
        if os.path.ismount(self.mounted_path):
            self.show_minus("Unmounting filesystem...")
            
            # Try normal unmount
            result = subprocess.run(['umount', self.mounted_path], capture_output=True, text=True)
            
            if result.returncode != 0:
                self.show_info("Normal unmount failed, trying force unmount...")
                # Try force unmount
                result = subprocess.run(['umount', '-f', self.mounted_path], capture_output=True, text=True)
                
                if result.returncode != 0:
                    # Try lazy unmount
                    self.show_info("Force unmount failed, trying lazy unmount...")
                    result = subprocess.run(['umount', '-l', self.mounted_path], capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        self.show_error(f"Failed to unmount {self.mounted_path}")
                        self.show_error(f"Error: {result.stderr}")
                        success = False
                    else:
                        self.show_success(f"Lazy unmounted: {self.mounted_path}")
                else:
                    self.show_success(f"Force unmounted: {self.mounted_path}")
            else:
                self.show_success(f"Unmounted: {self.mounted_path}")
        else:
            self.show_minus("Filesystem not mounted")
        
        time.sleep(1)  # Give it time to unmount
        
        # Step 2: Unmount dislocker if it's mounted
        try:
            # Check if dislocker dir is a mount point
            result = subprocess.run(['mountpoint', '-q', self.dislocker_path], capture_output=True)
            if result.returncode == 0:
                self.show_minus("Unmounting dislocker directory...")
                subprocess.run(['umount', '-f', self.dislocker_path], capture_output=True)
                self.show_success("Unmounted dislocker directory")
        except:
            pass
        
        # Step 3: Detach any loop devices
        self.show_minus("Cleaning up loop devices...")
        subprocess.run(['losetup', '-D'], capture_output=True)
        
        # Step 4: Verify unmount
        time.sleep(1)
        if os.path.ismount(self.mounted_path):
            self.show_error("Warning: Filesystem still mounted!")
            success = False
        else:
            self.show_success("Filesystem successfully unmounted")
        
        print()
        if success:
            self.show_success("✅ Unmount completed successfully")
        else:
            self.show_error("❌ Unmount had issues - you may need to manually run:")
            print(f"  sudo umount -f \"{self.mounted_path}\"")
            print(f"  sudo losetup -D")
        
        return success
    
    def run(self):
        """Main run function - returns to menu when done"""
        print()  # Add spacing from main menu
        
        # Check root
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
        print()
        
        # Ask if user wants to unmount
        while True:
            print(tag_question() + f"Do you want to unmount? ({GREEN}y{RESET}/{RED}n{RESET}): ", end='')
            choice = input().lower().strip()
            if choice in ['y', 'yes']:
                self.unmount()
                break
            elif choice in ['n', 'no']:
                self.show_info("Files will remain mounted")
                self.show_info(f"Location: {self.mounted_path}")
                self.show_info("To unmount later, run: sudo umount -f \"" + self.mounted_path + "\"")
                break
            else:
                print(tag_exclamation() + "Please enter y or n")

# Function to call from sokonalysis main menu
def mount_bitlocker_suboption():
    """Function to call from sokonalysis main menu"""
    mounter = BitLockerMounter()
    mounter.run()

if __name__ == "__main__":
    mount_bitlocker_suboption()
