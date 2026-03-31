#!/usr/bin/env python3
"""
BitLocker VHDX Recovery Tool
Complete workflow for BitLocker-encrypted VHDX files
SOKONALYSIS - Created by Soko James
Following Sokonalysis C++ Style Guidelines for Sub-options
"""

import os
import sys
import subprocess
import time
import platform

# ANSI color codes - matching C++ style from main.cpp
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
CYAN = '\033[36m'
BLUE = '\033[34m'
MAGENTA = '\033[35m'
ORANGE = '\033[38;5;208m'
WHITE = '\033[37m'
BOLD = '\033[1m'
RESET = '\033[0m'

# Disable colors on Windows if needed
if platform.system() == "Windows":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        pass

# Tag functions with consistent spacing - matching C++ style
def tag_asterisk(): return YELLOW + "[*]" + RESET + " "
def tag_plus(): return GREEN + "[+]" + RESET + " "
def tag_minus(): return GREEN + "[-]" + RESET + " "
def tag_exclamation(): return RED + "[!]" + RESET + " "
def tag_gt(): return YELLOW + "[>]" + RESET + " "
def tag_x(): return RED + "[x]" + RESET + " "
def tag_question(): return ORANGE + "[?]" + RESET + " "
def tag_hash(): return CYAN + "[#]" + RESET + " "

class BitLockerVHDXCracker:
    def __init__(self):
        self.vhdx_file = None
        self.drive_letter = None
        self.current_dir = os.getcwd()
        
        # Detect if running in WSL
        self.is_wsl = self.check_wsl()
        self.os_type = "Windows" if platform.system() == "Windows" or self.is_wsl else "Linux"
        
    def check_wsl(self):
        """Check if running in WSL"""
        try:
            with open('/proc/version', 'r') as f:
                version = f.read().lower()
                return 'microsoft' in version or 'wsl' in version
        except:
            return False
        
    def show_error(self, message):
        """Display error message in red with [x] tag"""
        print(tag_x() + message)
    
    def show_success(self, message):
        """Display success message in green with [+] tag"""
        print(tag_plus() + message)
    
    def show_info(self, message):
        """Display info message in cyan with [#] tag"""
        print(tag_hash() + message)
    
    def show_warning(self, message):
        """Display warning message in orange with [!] tag"""
        print(tag_exclamation() + message)
    
    def mount_vhdx_windows(self, vhdx_path):
        """Mount VHDX on Windows (or via PowerShell in WSL)"""
        try:
            # Convert path to Windows format
            if self.is_wsl:
                # Convert /mnt/c/path to C:\path
                if vhdx_path.startswith('/mnt/'):
                    drive = vhdx_path[5].upper()
                    path_part = vhdx_path[7:]
                    windows_path = drive + ":\\" + path_part.replace('/', '\\')
                else:
                    # Use wslpath to convert
                    result = subprocess.run(["wslpath", "-w", vhdx_path], 
                                           capture_output=True, text=True)
                    windows_path = result.stdout.strip()
            else:
                windows_path = os.path.abspath(vhdx_path)
            
            # Mount using PowerShell
            mount_cmd = f'Mount-DiskImage -ImagePath "{windows_path}"'
            result = subprocess.run(["powershell", "-Command", mount_cmd], 
                                   capture_output=True, text=True)
            
            if result.returncode != 0:
                self.show_error(f"Failed to mount VHDX: {result.stderr}")
                return None
            
            # Wait a moment for the drive to initialize
            time.sleep(3)
            
            # Get the drive letter
            get_letter = f'(Get-DiskImage -ImagePath "{windows_path}" | Get-Disk | Get-Partition | Get-Volume).DriveLetter'
            result = subprocess.run(["powershell", "-Command", get_letter], 
                                   capture_output=True, text=True)
            
            if result.stdout.strip():
                drive_letter = result.stdout.strip()
                self.show_success(f"VHDX mounted as drive {drive_letter}:")
                return drive_letter
            
            # Try alternative method - list all volumes
            list_volumes = 'Get-Volume | Where-Object {$_.FileSystem -eq "Unknown" -or $_.FileSystem -eq "BitLocker"} | Select-Object DriveLetter'
            result = subprocess.run(["powershell", "-Command", list_volumes], 
                                   capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if line.strip() and len(line.strip()) == 1 and line.strip().isalpha():
                    drive_letter = line.strip()
                    self.show_success(f"VHDX mounted as drive {drive_letter}:")
                    return drive_letter
            
            return None
            
        except Exception as e:
            self.show_error(f"Failed to mount VHDX: {e}")
            return None
    
    def mount_vhdx_linux(self, vhdx_path):
        """Mount VHDX on native Linux using qemu-nbd"""
        try:
            # Check if nbd module is loaded
            subprocess.run(["sudo", "modprobe", "nbd"], capture_output=True)
            
            # Use qemu-nbd to mount
            nbd_device = "/dev/nbd0"
            cmd = ["sudo", "qemu-nbd", "-c", nbd_device, vhdx_path]
            result = subprocess.run(cmd, capture_output=True)
            
            if result.returncode != 0:
                self.show_error("Failed to mount with qemu-nbd")
                return None
            
            time.sleep(1)
            
            # Check for partitions
            result = subprocess.run(["sudo", "partx", "-l", nbd_device], 
                                   capture_output=True, text=True)
            
            # Look for BitLocker partition
            for line in result.stdout.split('\n'):
                if "BitLocker" in line or "NTFS" in line:
                    parts = line.split()
                    if len(parts) >= 1:
                        return f"{nbd_device}p1"
            
            return nbd_device
            
        except Exception as e:
            self.show_error(f"Failed to mount VHDX: {e}")
            return None
    
    def mount_vhdx(self, vhdx_path):
        """Mount VHDX file (cross-platform)"""
        print(tag_asterisk() + "Mounting VHDX: " + YELLOW + f"{vhdx_path}" + RESET)
        print()
        
        if self.os_type == "Windows":
            self.drive_letter = self.mount_vhdx_windows(vhdx_path)
            if self.drive_letter:
                return True
        else:
            self.drive_letter = self.mount_vhdx_linux(vhdx_path)
            if self.drive_letter:
                return True
        
        self.show_error("Failed to mount VHDX")
        return False
    
    def unmount_vhdx_windows(self):
        """Unmount VHDX on Windows"""
        if self.vhdx_file:
            try:
                if self.is_wsl:
                    # Convert path to Windows format
                    if self.vhdx_file.startswith('/mnt/'):
                        drive = self.vhdx_file[5].upper()
                        path_part = self.vhdx_file[7:]
                        windows_path = drive + ":\\" + path_part.replace('/', '\\')
                    else:
                        result = subprocess.run(["wslpath", "-w", self.vhdx_file], 
                                               capture_output=True, text=True)
                        windows_path = result.stdout.strip()
                else:
                    windows_path = os.path.abspath(self.vhdx_file)
                
                unmount_cmd = f'Dismount-DiskImage -ImagePath "{windows_path}"'
                subprocess.run(["powershell", "-Command", unmount_cmd], 
                              capture_output=True)
            except:
                pass
    
    def unmount_vhdx_linux(self):
        """Unmount VHDX on Linux"""
        if self.drive_letter and self.drive_letter.startswith("/dev/nbd"):
            subprocess.run(["sudo", "qemu-nbd", "-d", self.drive_letter.split('p')[0]], 
                         capture_output=True)
    
    def unmount_vhdx(self):
        """Unmount VHDX file"""
        if self.os_type == "Windows":
            self.unmount_vhdx_windows()
        else:
            self.unmount_vhdx_linux()
    
    def unlock_bitlocker(self, recovery_key=None, password=None):
        """Unlock BitLocker drive"""
        if not self.drive_letter:
            self.show_error("No drive mounted")
            return False
        
        print(tag_asterisk() + "Unlocking BitLocker on drive: " + YELLOW + f"{self.drive_letter}:" + RESET)
        print()
        
        if recovery_key:
            # Unlock with recovery key
            cmd = f'Unlock-BitLocker -MountPoint "{self.drive_letter}:" -RecoveryPassword "{recovery_key}"'
            result = subprocess.run(["powershell", "-Command", cmd], 
                                   capture_output=True, text=True)
            
            if result.returncode == 0:
                self.show_success("Drive unlocked successfully!")
                return True
            else:
                self.show_error(f"Failed to unlock: {result.stderr}")
                return False
        
        elif password:
            # Unlock with password
            cmd = f'$pass = ConvertTo-SecureString "{password}" -AsPlainText -Force; Unlock-BitLocker -MountPoint "{self.drive_letter}:" -Password $pass'
            result = subprocess.run(["powershell", "-Command", cmd], 
                                   capture_output=True, text=True)
            
            if result.returncode == 0:
                self.show_success("Drive unlocked successfully!")
                return True
            else:
                self.show_error(f"Failed to unlock: {result.stderr}")
                return False
        else:
            self.show_error("No recovery key or password provided")
            return False
    
    def list_vhdx_files(self):
        """List VHDX files in current directory"""
        extensions = ['.vhdx', '.vhd']
        
        files = []
        
        print(BLUE + "\n_____________________ " + GREEN + "Available VHDX Files" + BLUE + " ______________________\n")
        
        idx = 1
        for file in sorted(os.listdir('.')):
            if any(file.lower().endswith(ext) for ext in extensions):
                if os.path.isfile(file):
                    files.append(file)
                    size = os.path.getsize(file)
                    if size < 1024:
                        size_str = f"{size}B"
                    elif size < 1024*1024:
                        size_str = f"{size/1024:.1f}KB"
                    elif size < 1024*1024*1024:
                        size_str = f"{size/(1024*1024):.1f}MB"
                    else:
                        size_str = f"{size/(1024*1024*1024):.1f}GB"
                    
                    print(YELLOW + f"[{idx}]" + RESET + f" {file} " + CYAN + f"({size_str})" + RESET)
                    idx += 1
        
        return files
    
    def select_vhdx(self):
        """Let user select a VHDX file"""
        files = self.list_vhdx_files()
        
        if not files:
            self.show_error("No VHDX files found in current directory!")
            print()
            print(YELLOW + "[1]" + RESET + " Enter file path manually")
            print(YELLOW + "[0]" + RESET + " Exit")
            print(BLUE + "_________________________________________________________________")
            print()
            
            choice = input(tag_gt() + "Select option: ").strip()
            if choice == "1":
                path = input(tag_gt() + "Enter full path: ").strip()
                if os.path.exists(path):
                    return path
                else:
                    self.show_error("File not found")
                    return None
            return None
        
        print(YELLOW + f"[{len(files)+1}]" + RESET + " Enter custom path")
        print(YELLOW + "[0]" + RESET + " Exit")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            choice = int(input(tag_gt() + "Select option: "))
            
            if choice == 0:
                return None
            elif 1 <= choice <= len(files):
                return files[choice-1]
            elif choice == len(files) + 1:
                path = input(tag_gt() + "Enter full path: ").strip()
                if os.path.exists(path):
                    return path
                else:
                    self.show_error("File not found")
                    return None
            else:
                return None
        except:
            self.show_error("Invalid choice")
            return None
    
    def select_attack_mode(self):
        """Select attack mode"""
        print(tag_asterisk() + "VHDX: " + YELLOW + f"{self.vhdx_file}" + RESET)
        print()
        print(BLUE + "\n____________________________ " + GREEN + "Options" + BLUE + " ____________________________")
        print()

        print(YELLOW + "[1]" + RESET + " Mount VHDX and unlock with recovery key")
        print(YELLOW + "[2]" + RESET + " Mount VHDX and unlock with password")
        print(YELLOW + "[3]" + RESET + " Select different VHDX")
        print(YELLOW + "[0]" + RESET + " Exit")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            return int(input(tag_gt() + "Select option: "))
        except:
            self.show_error("Please enter a number")
            return None
    
    def search_flag(self):
        """Search for flag on unlocked drive"""
        if not self.drive_letter:
            return
        
        print(tag_asterisk() + "Searching for flag files...")
        print()
        
        # Search for flag files
        search_cmd = f'Get-ChildItem -Path "{self.drive_letter}:\\" -Recurse -Force -ErrorAction SilentlyContinue | Where-Object {{$_.Name -match "flag|ZED|ctf|key|secret|readme"}} | Select-Object FullName, Length'
        result = subprocess.run(["powershell", "-Command", search_cmd], 
                               capture_output=True, text=True)
        
        if result.stdout.strip():
            print(tag_plus() + "Found matching files:")
            print(result.stdout)
            
            # Try to read text files for flag patterns
            read_cmd = f'Get-ChildItem -Path "{self.drive_letter}:\\" -Recurse -Force -ErrorAction SilentlyContinue -Include *.txt, *.xml, *.json, *.ini, *.cfg, *.log, *.md | Select-String -Pattern "ZED\\{{[^}}]+\\}}|flag\\{{[^}}]+\\}}|CTF\\{{[^}}]+\\}}" -ErrorAction SilentlyContinue'
            result = subprocess.run(["powershell", "-Command", read_cmd], 
                                   capture_output=True, text=True)
            
            if result.stdout.strip():
                print()
                print(tag_plus() + "Found flag patterns:")
                print(result.stdout)
                return True
        else:
            print(tag_minus() + "No flag-related files found")
        
        return False
    
    def browse_drive(self):
        """Open drive in explorer"""
        if self.drive_letter:
            print()
            browse = input(tag_question() + f"Open {self.drive_letter}: in File Explorer? (y/n): ").lower()
            if browse == 'y':
                subprocess.run(["explorer", f"{self.drive_letter}:\\"])
    
    def main_loop(self):
        """Main program loop"""
        while True:
            self.vhdx_file = self.select_vhdx()
            if not self.vhdx_file:
                return
            
            print()
            
            while True:
                choice = self.select_attack_mode()
                
                if choice == 1:
                    # Mount and unlock with recovery key
                    if self.mount_vhdx(self.vhdx_file):
                        print()
                        print(tag_asterisk() + "Enter recovery key (format: XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX)")
                        recovery_key = input(tag_gt() + "Recovery key: ").strip()
                        if recovery_key:
                            if self.unlock_bitlocker(recovery_key=recovery_key):
                                print()
                                print(tag_plus() + "Drive unlocked! You can now access files at " + 
                                      YELLOW + f"{self.drive_letter}:" + RESET)
                                print()
                                self.search_flag()
                                self.browse_drive()
                                print()
                                print(tag_gt() + "Press Enter to continue...")
                                input()
                            else:
                                self.show_error("Failed to unlock")
                        else:
                            self.show_error("No recovery key provided")
                
                elif choice == 2:
                    # Mount and unlock with password
                    if self.mount_vhdx(self.vhdx_file):
                        print()
                        password = input(tag_gt() + "Enter password: ").strip()
                        if password:
                            if self.unlock_bitlocker(password=password):
                                print()
                                print(tag_plus() + "Drive unlocked! You can now access files at " + 
                                      YELLOW + f"{self.drive_letter}:" + RESET)
                                print()
                                self.search_flag()
                                self.browse_drive()
                                print()
                                print(tag_gt() + "Press Enter to continue...")
                                input()
                            else:
                                self.show_error("Failed to unlock")
                        else:
                            self.show_error("No password provided")
                
                elif choice == 3:
                    # Select different VHDX
                    self.unmount_vhdx()
                    break
                
                elif choice == 0:
                    # Exit
                    self.unmount_vhdx()
                    return
                
                else:
                    self.show_error("Invalid choice")

def main():
    """Main function"""
    try:
        cracker = BitLockerVHDXCracker()
        cracker.main_loop()
        
    except KeyboardInterrupt:
        print(RED + "\n[x] Program stopped by user" + RESET)
    except Exception as e:
        print(RED + f"\n[x] Error: {e}" + RESET)

if __name__ == "__main__":
    main()
