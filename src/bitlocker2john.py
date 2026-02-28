#!/usr/bin/env python3
"""
BitLocker Disk Image Password Cracker
Complete workflow using bitlocker2john for hash extraction
SOKONALYSIS - Created by Soko James
Following Sokonalysis C++ Style Guidelines for Sub-options
"""

import os
import sys
import subprocess
import time
import tempfile
import shutil
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

# Tag functions with consistent spacing - matching C++ style
def tag_asterisk(): return YELLOW + "[*]" + RESET + " "
def tag_plus(): return GREEN + "[+]" + RESET + " "
def tag_minus(): return GREEN + "[-]" + RESET + " "
def tag_exclamation(): return RED + "[!]" + RESET + " "
def tag_gt(): return YELLOW + "[>]" + RESET + " "
def tag_x(): return RED + "[x]" + RESET + " "
def tag_question(): return ORANGE + "[?]" + RESET + " "
def tag_hash(): return CYAN + "[#]" + RESET + " "

class BitLockerCracker:
    def __init__(self):
        self.john_path = "john"
        self.disk_image = None
        self.hash_file = None
        self.hashcat_file = None
        self.default_wordlist = "wordlist.txt"
        self.current_dir = os.getcwd()
        self.temp_dir = None
        self.cracked_password = None
        
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
    
    def format_size(self, size):
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}PB"
    
    def check_tools(self):
        """Check if required tools are available"""
        # Check for john (still needed for hash extraction reference)
        try:
            result = subprocess.run([self.john_path, "--version"], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode not in [0, 1]:
                return False
        except FileNotFoundError:
            return False
        
        # Check for bitlocker2john
        try:
            result = subprocess.run(['bitlocker2john', '--help'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode not in [0, 1]:
                return False
        except FileNotFoundError:
            return False
        
        # Check for wordlist
        wordlist_paths = [
            self.default_wordlist,
            "wordlists/wordlist.txt",
            "../wordlists/wordlist.txt",
            "/usr/share/wordlists/rockyou.txt"
        ]
        
        for path in wordlist_paths:
            if os.path.exists(path):
                self.default_wordlist = path
                return True
        
        return False
    
    def count_words(self, filepath):
        """Count words in a file"""
        if not os.path.exists(filepath):
            return 0
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for line in f if line.strip())
        except:
            return 0
    
    def extract_hash(self, disk_image_path):
        """Extract hash from BitLocker disk image"""
        print(tag_asterisk() + "Extracting hash from: " + YELLOW + f"{disk_image_path}" + RESET)
        print()
        
        if not os.path.exists(disk_image_path):
            self.show_error("File not found")
            return False
        
        # Create temporary file for hash
        self.temp_dir = tempfile.mkdtemp(prefix="bitlocker_hash_")
        self.hash_file = os.path.join(self.temp_dir, "bitlocker.john")
        self.hashcat_file = os.path.join(self.temp_dir, "bitlocker.hashcat")
        
        try:
            # Run bitlocker2john
            cmd = ['bitlocker2john', '-i', disk_image_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and result.stdout:
                # Extract the hash lines
                john_lines = []
                hashcat_lines = []
                
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and ('$bitlocker$' in line or '$FVE$' in line):
                        # For John (with filename)
                        if ':' not in line:
                            john_line = f"{os.path.basename(disk_image_path)}:{line}"
                            john_lines.append(john_line)
                        else:
                            john_lines.append(line)
                        
                        # For Hashcat (without filename)
                        # Remove any existing filename prefix
                        if ':' in line:
                            hashcat_line = line.split(':', 1)[1]
                        else:
                            hashcat_line = line
                        hashcat_lines.append(hashcat_line)
                
                if john_lines:
                    # Save John format hash
                    with open(self.hash_file, 'w') as f:
                        for hash_line in john_lines:
                            f.write(hash_line + '\n')
                    
                    # Save Hashcat format hash
                    with open(self.hashcat_file, 'w') as f:
                        for hash_line in hashcat_lines:
                            f.write(hash_line + '\n')
                    
                    # Also save to current directory with disk image name
                    base_name = os.path.basename(disk_image_path)
                    if '.' in base_name:
                        base_name = base_name.split('.')[0]
                    
                    # Save John format locally
                    local_john = f"{base_name}_john.txt"
                    with open(local_john, 'w') as f:
                        for hash_line in john_lines:
                            f.write(hash_line + '\n')
                    
                    # Save Hashcat format locally
                    local_hashcat = f"{base_name}_hashcat.txt"
                    with open(local_hashcat, 'w') as f:
                        for hash_line in hashcat_lines:
                            f.write(hash_line + '\n')
                    
                    # Run hashcat directly (removed success messages)
                    print(tag_asterisk() + "Starting hashcat attack...")
                    print()
                    
                    if self.run_hashcat(local_hashcat):
                        return True  # Signal that password was found and we should exit
                    
                    return True
                else:
                    self.show_error("No BitLocker hash found in output")
                    print(YELLOW + "    The disk image might not be BitLocker encrypted" + RESET)
            else:
                self.show_error("bitlocker2john failed")
                
        except subprocess.TimeoutExpired:
            self.show_error("bitlocker2john timed out after 5 minutes")
        except Exception as e:
            self.show_error(f"Error: {e}")
        
        self.cleanup()
        return False
    
    def run_hashcat(self, hash_file):
        """Run hashcat attack"""
        # Ask for wordlist
        print(BLUE + "_______________________ " + GREEN + "Wordlist Option" + BLUE + " _________________________")
        print()
        print(YELLOW + "[1]" + RESET + " Use default wordlist")
        print(YELLOW + "[2]" + RESET + " Use custom wordlist")
        print(BLUE + "_________________________________________________________________")
        print()
        
        choice = input(tag_gt() + "Select option (1-2, default=1): ").strip() or "1"
        print()  # Add spacing after input
        
        wordlist = self.default_wordlist
        if choice == "2":
            wl = input(tag_gt() + "Enter path to custom wordlist: ").strip()
            print()  # Add spacing after input
            if wl and os.path.exists(wl):
                wordlist = wl
            else:
                self.show_error(f"Wordlist not found: {wl}")
                return False
        
        if not os.path.exists(wordlist):
            self.show_error(f"Wordlist not found: {wordlist}")
            return False
        
        word_count = self.count_words(wordlist)
        print(tag_gt() + f"Using wordlist: " + CYAN + f"{wordlist}" + RESET)
        print(tag_gt() + f"Word count: " + CYAN + f"{word_count:,}" + RESET)
        print()
        
        # Build hashcat command
        cmd = [
            'hashcat',
            '-m', '22100',           # BitLocker mode
            '-a', '0',                # Wordlist attack
            '--potfile-path=bitlocker.pot',  # Save cracked passwords
            '-O',                      # Optimized kernel
            '-w', '3',                  # Workload profile
            '--force',                  # Force on CPU
            hash_file,
            wordlist
        ]
        
        print(tag_gt() + "Running hashcat... " + RED + "(this may take a while)" + RESET)
        print()
        
        try:
            start = time.time()
            
            # Run hashcat
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            # Check the potfile directly for cracked passwords
            potfile = "bitlocker.pot"
            self.cracked_password = None
            
            if os.path.exists(potfile):
                with open(potfile, 'r') as f:
                    for line in f:
                        if ':' in line:
                            # Format is hash:password
                            parts = line.strip().split(':', 1)
                            if len(parts) == 2:
                                self.cracked_password = parts[1]
                                break
            
            elapsed = time.time() - start
            
            if self.cracked_password:
                print()
                print(BLUE + "_________________________________________________________________")
                print()
                print(tag_minus() + "Cracked Password Results: " + GREEN + self.cracked_password + RESET)
                print()
                print(BLUE + "_________________________________________________________________")
                print()
                
                # Save to file
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                outfile = f"cracked_bitlocker_{timestamp}.txt"
                with open(outfile, 'w') as f:
                    f.write(f"Disk Image: {self.disk_image}\n")
                    f.write(f"Password: {self.cracked_password}\n")
                    f.write(f"Hash: {hash_file}\n")
                    f.write(f"Wordlist: {wordlist}\n")
                    f.write(f"Time: {time.ctime()}\n")
                
                return True
            else:
                print()
                print(tag_minus() + " No password found in wordlist")
                print(tag_asterisk() + " Try a different wordlist or attack mode")
            
            print()
            print(tag_minus() + f"Finished in " + YELLOW + f"{elapsed:.1f} seconds" + RESET)
            print()
            
            return False
            
        except KeyboardInterrupt:
            print()
            self.show_error("Stopped by user")
            print()
            return False
        except Exception as e:
            print()
            self.show_error(f"Error: {e}")
            print()
            return False
    
    def list_disk_images(self):
        """List disk images in current directory"""
        extensions = [
            '.img', '.iso', '.dd', '.raw', '.vhd', '.vmdk', '.dmg',
            '.IMG', '.ISO', '.DD', '.RAW', '.VHD', '.VMDK', '.DMG'
        ]
        
        disk_images = []
        
        print(BLUE + "_____________________ " + GREEN + "Available Disk Images" + BLUE + " _____________________\n")
        
        idx = 1
        for file in sorted(os.listdir('.')):
            if any(file.lower().endswith(ext.lower()) for ext in extensions):
                if os.path.isfile(file):
                    size = os.path.getsize(file)
                    size_str = self.format_size(size)
                    disk_images.append(file)
                    print(YELLOW + f"[{idx}]" + RESET + f" {file} " + CYAN + f"({size_str})" + RESET)
                    idx += 1
        
        return disk_images
    
    def select_disk_image(self):
        """Let user select a disk image"""
        disk_images = self.list_disk_images()
        
        if not disk_images:
            self.show_error("No disk images found!")
            print()
            print(YELLOW + "[1]" + RESET + " Enter disk image path manually")
            print(YELLOW + "[2]" + RESET + " Exit")
            print(BLUE + "_________________________________________________________________")
            print()
            
            choice = input(tag_gt() + "Select option (1-2): ").strip()
            print()  # Add spacing after input
            if choice == "1":
                path = input(tag_gt() + "Enter full path: ").strip()
                print()  # Add spacing after input
                if os.path.exists(path):
                    return path
                else:
                    self.show_error("File not found")
                    return None
            return None
        
        print(YELLOW + f"[{len(disk_images)+1}]" + RESET + " Enter custom path")
        print(YELLOW + f"[{len(disk_images)+2}]" + RESET + " Exit")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            choice = int(input(tag_gt() + f"Select disk image (1-{len(disk_images)+2}): "))
            print()  # Add spacing after input
            
            if 1 <= choice <= len(disk_images):
                return disk_images[choice-1]
            elif choice == len(disk_images) + 1:
                path = input(tag_gt() + "Enter full path: ").strip()
                print()  # Add spacing after input
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
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
                self.hash_file = None
                self.hashcat_file = None
            except:
                pass
    
    def main_loop(self):
        """Main program loop"""
        if not self.check_tools():
            print(tag_exclamation() + "Required tools not found. Please install john and bitlocker2john.")
            input(tag_gt() + "Press Enter to exit...")
            print()
            return
        
        while True:
            self.disk_image = self.select_disk_image()
            if not self.disk_image:
                self.cleanup()
                return
            
            print()
            password_found = self.extract_hash(self.disk_image)
            
            # If password was found, exit program
            if password_found is True:
                self.cleanup()
                return

def main():
    """Main function"""
    try:
        # Enable virtual terminal processing on Windows
        if platform.system() == "Windows":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except:
                pass
        
        cracker = BitLockerCracker()
        cracker.main_loop()
        
    except KeyboardInterrupt:
        print(RED + "\n[x] Program stopped by user" + RESET)
    except Exception as e:
        print(RED + f"\n[x] Error: {e}" + RESET)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
