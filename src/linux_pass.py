#!/usr/bin/env python3
"""
UNSHADOW PASSWORD CRACKER
Extract and crack passwords from /etc/passwd and /etc/shadow files
Colorful Interface
"""

import os
import sys
import subprocess
import time
import tempfile
import shutil
import re
import pwd
import spwd
import getpass
from pathlib import Path

# Check if we're in a GUI environment (no terminal)
if sys.stdout.isatty():
    # We have a real terminal, use colorama normally
    from colorama import Fore, Style, init
    init(autoreset=True)
    
    # Define our color functions
    def c_red(text): return Fore.RED + text + Style.RESET_ALL
    def c_green(text): return Fore.GREEN + text + Style.RESET_ALL
    def c_yellow(text): return Fore.YELLOW + text + Style.RESET_ALL
    def c_cyan(text): return Fore.CYAN + text + Style.RESET_ALL
    def c_blue(text): return Fore.BLUE + text + Style.RESET_ALL
    def c_magenta(text): return Fore.MAGENTA + text + Style.RESET_ALL
    def c_reset(): return Style.RESET_ALL
    
    # Tag functions with consistent spacing
    def tag_asterisk(): return Fore.YELLOW + "[*]" + Style.RESET_ALL + " "
    def tag_plus(): return Fore.GREEN + "[+]" + Style.RESET_ALL + " "
    def tag_minus(): return Fore.GREEN + "[-]" + Style.RESET_ALL + " "
    def tag_exclamation(): return Fore.RED + "[!]" + Style.RESET_ALL + " "
    def tag_gt(): return Fore.YELLOW + "[>]" + Style.RESET_ALL + " "
    def tag_x(): return Fore.RED + "[x]" + Style.RESET_ALL + " "
    def tag_info(): return Fore.CYAN + "[i]" + Style.RESET_ALL + " "
    
else:
    # We're in a GUI or redirected output, use ANSI escape codes directly
    # ANSI escape codes for colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    
    # Define our color functions
    def c_red(text): return RED + text + RESET
    def c_green(text): return GREEN + text + RESET
    def c_yellow(text): return YELLOW + text + RESET
    def c_cyan(text): return CYAN + text + RESET
    def c_blue(text): return BLUE + text + RESET
    def c_magenta(text): return MAGENTA + text + RESET
    def c_reset(): return RESET
    
    # Tag functions with consistent spacing
    def tag_asterisk(): return YELLOW + "[*]" + RESET + " "
    def tag_plus(): return GREEN + "[+]" + RESET + " "
    def tag_minus(): return GREEN + "[-]" + RESET + " "
    def tag_exclamation(): return RED + "[!]" + RESET + " "
    def tag_gt(): return YELLOW + "[>]" + RESET + " "
    def tag_x(): return RED + "[x]" + RESET + " "
    def tag_info(): return CYAN + "[i]" + RESET + " "

class UnshadowCracker:
    def __init__(self):
        self.john_path = "john"
        self.hash_file = None
        self.default_wordlist = "wordlist.txt"
        self.current_dir = os.getcwd()
        self.passwd_file = None
        self.shadow_file = None
        self.users = []
        self.selected_user = None
        self.unshadowed_file = None
        self.unshadow_path = self.find_unshadow()  # Auto-detect on init
        self.default_src_dir = self.current_dir  # Use current directory instead of fixed path
    
    def find_unshadow(self):
        """Find unshadow utility in common locations"""
        common_paths = [
            "/usr/sbin/unshadow",
            "/usr/bin/unshadow",
            "/usr/share/john/unshadow",
            "/usr/local/bin/unshadow",
            "/usr/local/sbin/unshadow",
            "/opt/john/run/unshadow",
            "unshadow",
        ]
        
        print(tag_asterisk() + "Searching for unshadow utility...")
        for path in common_paths:
            if os.path.exists(path):
                print(tag_plus() + f"Found at: {path}")
                return path
        
        print(tag_info() + "unshadow not found, will use Python implementation")
        return None
    
    def clear_screen(self):
        """Clear screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def show_banner(self):
        """Show colorful banner"""
        self.clear_screen()
        print(tag_minus() + "UNSHADOW PASSWORD CRACKER")
        print(c_yellow("Extract and crack passwords from passwd/shadow files"))
        print()
    
    def check_tools(self):
        """Check if required tools are available"""
        self.show_banner()
        print(tag_asterisk() + "Checking for required tools...")
        
        # Check for john
        try:
            result = subprocess.run([self.john_path, "--version"], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode in [0, 1]:
                print(tag_plus() + f"John the Ripper: Found at '{self.john_path}'")
            else:
                print(tag_exclamation() + "John the Ripper not working properly")
                return False
        except FileNotFoundError:
            print(tag_exclamation() + "John the Ripper not found!")
            print(c_yellow("    Install with: sudo apt install john  (Debian/Ubuntu)"))
            print(c_yellow("                  sudo yum install john  (RedHat/Fedora)"))
            print(c_yellow("                  sudo pacman -S john    (Arch)"))
            return False
        
        # Check for wordlist
        if os.path.exists(self.default_wordlist):
            wordcount = self.count_words(self.default_wordlist)
            if wordcount:
                print(tag_plus() + f"Default wordlist: '{self.default_wordlist}' ({wordcount} words)")
            else:
                print(tag_exclamation() + f"Cannot read wordlist: {self.default_wordlist}")
        else:
            print(tag_exclamation() + f"Default wordlist not found: '{self.default_wordlist}'")
            print(c_yellow("    Please create a file named '") + c_cyan("wordlist.txt") + c_yellow("' with passwords"))
            return False

        return True
    
    def count_words(self, filepath):
        """Count words in a file, handling different encodings"""
        if not os.path.exists(filepath):
            return 0
        
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    wordcount = sum(1 for line in f if line.strip())
                return wordcount
            except UnicodeDecodeError:
                continue
        
        return 0
    
    def select_file_source(self):
        """Select source of passwd/shadow files"""
        self.show_banner()
        print(tag_minus() + "SELECT FILE SOURCE")
        
        print(c_yellow("[1]") + f" Use files from current directory: {self.current_dir}")
        print(c_yellow("[2]") + " Enter custom file paths")
        print(c_yellow("[3]") + " Exit")
        
        try:
            choice = int(input(tag_gt() + "Select option (1-3): "))
            return choice
        except ValueError:
            print(tag_exclamation() + "Please enter a number")
            input(tag_gt() + "Press Enter to continue...")
            return None
    
    def check_current_directory(self):
        """Check and display files in current directory"""
        self.show_banner()
        
        print(c_yellow("📁") + " Checking current directory: " + c_cyan(self.current_dir))
        print()
        
        # List files in directory
        try:
            files = os.listdir(self.current_dir)
        except Exception as e:
            print(tag_exclamation() + f"Cannot read directory: {e}")
            return False
        
        # Look for passwd and shadow files
        passwd_files = []
        shadow_files = []
        
        for file in sorted(files):
            file_path = os.path.join(self.current_dir, file)
            if os.path.isfile(file_path):
                # Check for passwd files (exact name or variations)
                if file.lower() in ['passwd', 'passwd.txt', 'passwd.bak', 'password', 'passwords'] or 'passwd' in file.lower():
                    size = os.path.getsize(file_path)
                    size_str = self.format_size(size)
                    passwd_files.append((file, size_str, file_path))
                
                # Check for shadow files
                if file.lower() in ['shadow', 'shadow.txt', 'shadow.bak', 'passwd.shadow'] or 'shadow' in file.lower():
                    size = os.path.getsize(file_path)
                    size_str = self.format_size(size)
                    shadow_files.append((file, size_str, file_path))
        
        if not passwd_files and not shadow_files:
            print(tag_exclamation() + "No passwd or shadow files found in current directory!")
            print()
            print(c_yellow("📦") + " Place your files in this directory:")
            print(c_cyan(f"    {self.current_dir}/"))
            print()
            print(tag_minus() + "Expected files:")
            print(c_yellow("    passwd") + " - User account information")
            print(c_yellow("    shadow") + " - Encrypted password hashes")
            print()
            print(tag_minus() + "Files found in directory:")
            for file in files[:20]:  # Show first 20 files
                if os.path.isfile(os.path.join(self.current_dir, file)):
                    print(f"    {file}")
            if len(files) > 20:
                print(f"    ... and {len(files) - 20} more files")
            return False
        
        print(tag_minus() + "FOUND FILES")
        
        if passwd_files:
            print(c_green("📄") + " PASSWD FILES:")
            for idx, (filename, size_str, path) in enumerate(passwd_files, 1):
                print(c_yellow(f"  [{idx}]") + f" {filename}" + c_cyan(f" ({size_str})"))
        
        if shadow_files:
            print(c_green("🔒") + " SHADOW FILES:")
            for idx, (filename, size_str, path) in enumerate(shadow_files, 1):
                print(c_yellow(f"  [{idx}]") + f" {filename}" + c_cyan(f" ({size_str})"))
        
        print()
        return True
    
    def format_size(self, size):
        """Format file size in human readable format"""
        if size < 1024:
            return f"{size}B"
        elif size < 1024*1024:
            return f"{size/1024:.1f}KB"
        else:
            return f"{size/(1024*1024):.1f}MB"
    
    def select_files_from_current(self):
        """Let user select passwd and shadow files from current directory"""
        if not self.check_current_directory():
            return False
        
        # Get list of files again
        try:
            files = os.listdir(self.current_dir)
        except Exception as e:
            print(tag_exclamation() + f"Cannot read directory: {e}")
            return False
        
        passwd_files = []
        shadow_files = []
        
        for file in files:
            file_path = os.path.join(self.current_dir, file)
            if os.path.isfile(file_path):
                if file.lower() in ['passwd', 'passwd.txt', 'passwd.bak', 'password', 'passwords'] or 'passwd' in file.lower():
                    passwd_files.append((file, file_path))
                if file.lower() in ['shadow', 'shadow.txt', 'shadow.bak', 'passwd.shadow'] or 'shadow' in file.lower():
                    shadow_files.append((file, file_path))
        
        # Auto-select if only one of each
        if len(passwd_files) == 1 and len(shadow_files) == 1:
            self.passwd_file = passwd_files[0][1]
            self.shadow_file = shadow_files[0][1]
            print(tag_plus() + f"Auto-selected passwd: {passwd_files[0][0]}")
            print(tag_plus() + f"Auto-selected shadow: {shadow_files[0][0]}")
            return True
        
        # Let user select passwd file
        if len(passwd_files) > 1:
            print(tag_minus() + "SELECT PASSWD FILE")
            for idx, (filename, path) in enumerate(passwd_files, 1):
                print(c_yellow(f"[{idx}]") + f" {filename}")
            
            try:
                choice = int(input(tag_gt() + f"Select passwd file (1-{len(passwd_files)}): "))
                if 1 <= choice <= len(passwd_files):
                    self.passwd_file = passwd_files[choice-1][1]
                    print(tag_plus() + f"Selected: {passwd_files[choice-1][0]}")
                else:
                    return False
            except ValueError:
                print(tag_exclamation() + "Invalid selection")
                return False
        elif len(passwd_files) == 1:
            self.passwd_file = passwd_files[0][1]
            print(tag_plus() + f"Using passwd: {passwd_files[0][0]}")
        else:
            print(tag_exclamation() + "No passwd files found!")
            return False
        
        # Let user select shadow file
        if len(shadow_files) > 1:
            print(tag_minus() + "SELECT SHADOW FILE")
            for idx, (filename, path) in enumerate(shadow_files, 1):
                print(c_yellow(f"[{idx}]") + f" {filename}")
            
            try:
                choice = int(input(tag_gt() + f"Select shadow file (1-{len(shadow_files)}): "))
                if 1 <= choice <= len(shadow_files):
                    self.shadow_file = shadow_files[choice-1][1]
                    print(tag_plus() + f"Selected: {shadow_files[choice-1][0]}")
                else:
                    return False
            except ValueError:
                print(tag_exclamation() + "Invalid selection")
                return False
        elif len(shadow_files) == 1:
            self.shadow_file = shadow_files[0][1]
            print(tag_plus() + f"Using shadow: {shadow_files[0][0]}")
        else:
            print(tag_exclamation() + "No shadow files found!")
            return False
        
        return True
    
    def get_custom_files(self):
        """Get custom file paths from user"""
        self.show_banner()
        print(tag_minus() + "ENTER CUSTOM FILE PATHS")
        
        passwd_path = input(tag_gt() + "Enter full path to passwd file: ").strip()
        if not os.path.exists(passwd_path):
            print(tag_exclamation() + f"File not found: {passwd_path}")
            return False
        
        shadow_path = input(tag_gt() + "Enter full path to shadow file: ").strip()
        if not os.path.exists(shadow_path):
            print(tag_exclamation() + f"File not found: {shadow_path}")
            return False
        
        # Check if trying to access system shadow file
        if shadow_path == '/etc/shadow':
            if os.geteuid() != 0:  # Not root
                print(tag_exclamation() + "PERMISSION DENIED: Cannot read /etc/shadow without root privileges!")
                print(c_yellow("    To access system shadow file, you must run this script as root:"))
                print(c_cyan("    sudo python3 linux_pass.py"))
                print()
                print(c_yellow("    Alternatively, you can:"))
                print(c_yellow("    1. Copy /etc/shadow to your home directory (requires root)"))
                print(c_yellow("    2. Use option 1 with passwd/shadow files from current directory"))
                return False
        
        # Check if we have permission to read the shadow file
        try:
            with open(shadow_path, 'r') as f:
                test_line = f.readline()
                if not test_line:
                    print(tag_exclamation() + f"Shadow file appears empty: {shadow_path}")
                    return False
        except PermissionError as e:
            print(tag_exclamation() + f"PERMISSION DENIED: Cannot read {shadow_path}")
            print(c_yellow(f"    Error: {e}"))
            print(c_yellow("    You may need to run as root or check file permissions"))
            return False
        except Exception as e:
            print(tag_exclamation() + f"Cannot read shadow file: {e}")
            return False
        
        self.passwd_file = passwd_path
        self.shadow_file = shadow_path
        print(tag_plus() + f"Using passwd file: {passwd_path}")
        print(tag_plus() + f"Using shadow file: {shadow_path}")
        return True
    
    def parse_users(self):
        """Parse users from passwd and shadow files"""
        self.users = []
        
        try:
            # Read passwd file
            with open(self.passwd_file, 'r') as f:
                passwd_lines = f.readlines()
            
            # Read shadow file
            with open(self.shadow_file, 'r') as f:
                shadow_lines = f.readlines()
            
            # Create dictionary of shadow entries
            shadow_dict = {}
            for line in shadow_lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(':')
                    if len(parts) >= 2:
                        username = parts[0]
                        hash_value = parts[1]
                        shadow_dict[username] = hash_value
            
            # Match passwd entries with shadow entries
            for line in passwd_lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(':')
                    if len(parts) >= 7:
                        username = parts[0]
                        uid = parts[2]
                        gid = parts[3]
                        gecos = parts[4]
                        home = parts[5]
                        shell = parts[6]
                        
                        # Check if user has a shadow entry with password hash
                        if username in shadow_dict:
                            hash_value = shadow_dict[username]
                            
                            # Skip users with no password hash
                            if hash_value and hash_value not in ['*', '!', '!!', '!*', 'x', '', '!$']:
                                # Determine hash type
                                hash_type = self.detect_hash_type(hash_value)
                                
                                user_info = {
                                    'username': username,
                                    'uid': uid,
                                    'gid': gid,
                                    'gecos': gecos,
                                    'home': home,
                                    'shell': shell,
                                    'hash': hash_value,
                                    'hash_type': hash_type,
                                    'cracked': False
                                }
                                self.users.append(user_info)
            
            # If no users found, check if we need to filter system users
            if not self.users:
                print(tag_exclamation() + "No users with crackable password hashes found!")
                print(c_yellow("    System users often have '!' or '*' instead of passwords"))
                return False
            
            # Filter out system users if we have many users
            if len(self.users) > 10:
                print(tag_info() + f"Found {len(self.users)} users, filtering system users...")
                regular_users = []
                for user in self.users:
                    uid = int(user['uid'])
                    # Regular users typically have UID >= 1000
                    if uid >= 1000:
                        regular_users.append(user)
                    # Also include root (UID 0)
                    elif uid == 0:
                        regular_users.append(user)
                
                if regular_users:
                    print(tag_plus() + f"Filtered to {len(regular_users)} regular user(s)")
                    self.users = regular_users
            
            return len(self.users) > 0
            
        except Exception as e:
            print(tag_x() + f"Error parsing files: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def detect_hash_type(self, hash_value):
        """Detect the type of hash"""
        if not hash_value:
            return "No password"
        
        # Common hash patterns
        if hash_value.startswith('$1$'):
            return "MD5"
        elif hash_value.startswith('$2a$') or hash_value.startswith('$2b$') or hash_value.startswith('$2y$'):
            return "Blowfish"
        elif hash_value.startswith('$5$'):
            return "SHA-256"
        elif hash_value.startswith('$6$'):
            return "SHA-512"
        elif hash_value.startswith('$y$'):
            return "Yescrypt"
        elif hash_value.startswith('$argon2'):
            return "Argon2"
        elif len(hash_value) == 13:
            return "DES"
        elif hash_value.startswith('$md5$'):
            return "Sun MD5"
        elif hash_value.startswith('$sha1$'):
            return "SHA-1"
        elif ':' in hash_value:  # Might be in format $id$salt$hash
            parts = hash_value.split('$')
            if len(parts) > 1:
                return f"Unknown (ID: {parts[1]})"
        
        return "Unknown"
    
    def display_users(self):
        """Display list of users with password hashes"""
        self.show_banner()
        print(tag_minus() + f"LOADED USERS FROM FILES")
        print(c_yellow(f"passwd: {self.passwd_file}"))
        print(c_yellow(f"shadow: {self.shadow_file}"))
        print()
        
        if not self.users:
            print(tag_exclamation() + "No users with password hashes found!")
            return False
        
        print(c_cyan(f"Found {len(self.users)} user(s) with password hashes:"))
        print()
        print(c_yellow("ID  USERNAME        UID   HASH TYPE    CRACKED"))
        print(c_yellow("--  --------        ---   ---------    -------"))
        
        for idx, user in enumerate(self.users, 1):
            username = user['username']
            uid = user['uid']
            hash_type = user['hash_type']
            cracked = c_green("YES") if user.get('cracked', False) else c_red("NO")
            
            # Truncate long usernames
            if len(username) > 12:
                username_display = username[:12] + "..."
            else:
                username_display = username
            
            print(f"{idx:2d}  {username_display:15} {uid:4}  {hash_type:11}  {cracked}")
        
        print()
        return True
    
    def select_user(self):
        """Let user select which account to crack"""
        if len(self.users) == 1:
            # Only one user, auto-select
            self.selected_user = self.users[0]
            print(tag_plus() + f"Auto-selected user: {self.selected_user['username']}")
            return True
        
        print(tag_minus() + "USER SELECTION")
        print(c_yellow(f"[1-{len(self.users)}]") + f" Select user by ID")
        print(c_yellow(f"[{len(self.users)+1}]") + " Crack ALL users")
        print(c_yellow(f"[{len(self.users)+2}]") + " Cancel")
        
        try:
            choice = int(input(tag_gt() + f"Select option (1-{len(self.users)+2}): "))
            
            if 1 <= choice <= len(self.users):
                self.selected_user = self.users[choice-1]
                print(tag_plus() + f"Selected user: {self.selected_user['username']}")
                return True
            elif choice == len(self.users) + 1:
                self.selected_user = None  # Means all users
                print(tag_plus() + "Selected ALL users")
                return True
            else:
                return False
                
        except ValueError:
            print(tag_exclamation() + "Please enter a valid number")
            return False
    
    def create_unshadowed_file(self):
        """Create unshadowed file for John"""
        temp_dir = tempfile.mkdtemp(prefix="unshadow_")
        self.unshadowed_file = os.path.join(temp_dir, "unshadowed.txt")
        self.hash_file = os.path.join(temp_dir, "hashes.txt")  # Initialize hash_file here
        
        try:
            if self.unshadow_path:
                # Use system unshadow utility
                cmd = [self.unshadow_path, self.passwd_file, self.shadow_file]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and result.stdout:
                    with open(self.unshadowed_file, 'w') as f:
                        f.write(result.stdout)
                    print(tag_plus() + f"Created unshadowed file: {self.unshadowed_file}")
                    
                    # Also create hash file
                    with open(self.hash_file, 'w') as f:
                        f.write(result.stdout)
                    
                    print(tag_plus() + f"Created hash file: {self.hash_file}")
                    return True
                else:
                    print(tag_exclamation() + "unshadow utility failed, using Python method")
            
            # Use Python implementation
            with open(self.unshadowed_file, 'w') as outfile:
                # Read passwd file
                with open(self.passwd_file, 'r') as f:
                    passwd_lines = f.readlines()
                
                # Read shadow file
                with open(self.shadow_file, 'r') as f:
                    shadow_lines = f.readlines()
                
                # Create dictionary of shadow entries
                shadow_dict = {}
                for line in shadow_lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split(':')
                        if len(parts) >= 2:
                            username = parts[0]
                            shadow_dict[username] = line
                
                # Combine matching entries
                for line in passwd_lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split(':')
                        if len(parts) >= 7:
                            username = parts[0]
                            if username in shadow_dict:
                                # Replace password field (second field) with shadow password
                                passwd_parts = line.split(':')
                                shadow_parts = shadow_dict[username].split(':')
                                
                                # Create combined line
                                combined = f"{passwd_parts[0]}:{shadow_parts[1]}"
                                for i in range(2, len(passwd_parts)):
                                    combined += f":{passwd_parts[i]}"
                                
                                # Filter if we're only targeting specific user
                                if self.selected_user and username != self.selected_user['username']:
                                    continue
                                
                                outfile.write(combined + '\n')
            
            print(tag_plus() + f"Created unshadowed file: {self.unshadowed_file}")
            
            # Create hash file for John (simpler format)
            hash_count = 0
            with open(self.hash_file, 'w') as outfile:
                # Read the unshadowed file
                with open(self.unshadowed_file, 'r') as infile:
                    for line in infile:
                        line = line.strip()
                        if line:
                            parts = line.split(':')
                            if len(parts) >= 2:
                                username = parts[0]
                                hash_value = parts[1]
                                # Filter out invalid hashes
                                if hash_value and hash_value not in ['*', '!', '!!', '!*', 'x', '', '!$']:
                                    # Write in format: username:hash
                                    outfile.write(f"{username}:{hash_value}\n")
                                    hash_count += 1
            
            print(tag_plus() + f"Created hash file with {hash_count} hash(es): {self.hash_file}")
            
            if hash_count == 0:
                print(tag_exclamation() + "No valid password hashes found!")
                print(c_yellow("    Check if your shadow file contains actual password hashes"))
                print(c_yellow("    System users often have '!' or '*' instead of passwords"))
                return False
                
            return True
            
        except Exception as e:
            print(tag_x() + f"Error creating unshadowed file: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def select_attack_mode(self):
        """Select attack mode"""
        self.show_banner()
        
        if self.selected_user:
            print(tag_asterisk() + f"Target User: " + c_yellow(f"{self.selected_user['username']}"))
            print(tag_asterisk() + f"Hash Type: " + c_cyan(f"{self.selected_user['hash_type']}"))
        else:
            print(tag_asterisk() + f"Target: " + c_yellow("ALL USERS"))
            print(tag_asterisk() + f"Users: " + c_cyan(f"{len(self.users)} users"))
        
        print()
        print(tag_minus() + "SELECT ATTACK MODE")

        print(c_yellow("[1]") + " Wordlist Attack (using default wordlist)")
        print(c_yellow("[2]") + " Wordlist Attack (custom wordlist)")
        print(c_yellow("[3]") + " Single Crack Mode")
        print(c_yellow("[4]") + " Incremental Mode (brute force)")
        print(c_yellow("[5]") + " Show cracked passwords")
        print(c_yellow("[6]") + " Select different user/file")
        print(c_yellow("[7]") + " Exit")
        
        try:
            choice = int(input(tag_gt() + "Select option (1-7): "))
            return choice
        except ValueError:
            print(tag_exclamation() + "Please enter a number")
            input(tag_gt() + "Press Enter to continue...")
            return None
    
    def get_wordlist_info(self, wordlist_path):
        """Get information about a wordlist"""
        if not os.path.exists(wordlist_path):
            print(tag_exclamation() + f"Wordlist not found: {wordlist_path}")
            return False
        
        wordcount = self.count_words(wordlist_path)
        if wordcount == 0:
            print(tag_exclamation() + f"Wordlist is empty: {wordlist_path}")
            return False
        
        filesize = os.path.getsize(wordlist_path)
        if filesize < 1024:
            size_str = f"{filesize}B"
        elif filesize < 1024*1024:
            size_str = f"{filesize/1024:.1f}KB"
        else:
            size_str = f"{filesize/(1024*1024):.1f}MB"
        
        print(tag_plus() + f"Wordlist: {wordlist_path}")
        print(tag_plus() + f"Size: {size_str}, Words: {wordcount}")
        return True
    
    def run_john_command(self, cmd, attack_name):
        """Run a John the Ripper command"""
        self.show_banner()
        
        if self.selected_user:
            print(tag_asterisk() + f"{attack_name} on user: {self.selected_user['username']}")
        else:
            print(tag_asterisk() + f"{attack_name} on {len(self.users)} users")
        
        # Debug: Check cmd list
        print(tag_gt() + "Command components:")
        for i, item in enumerate(cmd):
            if item is None:
                print(c_red(f"  [{i}] None"))
            else:
                print(c_green(f"  [{i}] {item}"))
        
        # Filter out None values
        cmd = [item for item in cmd if item is not None]
        
        print(tag_gt() + f"Command: {' '.join(cmd)}")
        print()
        print(tag_asterisk() + "Starting attack... " + c_red("Press Ctrl+C to stop"))
        
        try:
            start_time = time.time()
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Print output in real-time
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    # Color different types of output
                    if "Press 'q' or Ctrl-C to abort" in line:
                        print(c_yellow(line.strip()))
                    elif "session aborted" in line.lower():
                        print(c_red(line.strip()))
                    elif "password hash cracked" in line.lower():
                        print(tag_plus() + " " + line.strip())
                    elif "guesses:" in line.lower():
                        print(c_cyan(line.strip()))
                    elif "remaining:" in line.lower():
                        print(c_yellow(line.strip()))
                    elif "Loaded" in line and "password hash" in line:
                        print(c_magenta(line.strip()))
                    else:
                        print(line.strip())
            
            process.wait()
            elapsed = time.time() - start_time
            
            print(tag_minus() + f"Finished in {elapsed:.1f} seconds")
            
        except KeyboardInterrupt:
            print(c_red("\n\n[x]") + " Stopped by user")
            return False
        except Exception as e:
            print(c_red("\n[x]") + f" Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True
    
    def run_wordlist_attack(self, custom_wordlist=None):
        """Run wordlist attack"""
        # Check if hash file exists
        if not self.hash_file or not os.path.exists(self.hash_file):
            print(tag_exclamation() + "Hash file not found or not created!")
            print(c_yellow(f"    Hash file path: {self.hash_file}"))
            return False
        
        wordlist = custom_wordlist if custom_wordlist else self.default_wordlist
        
        if not self.get_wordlist_info(wordlist):
            return False
        
        print()
        print(tag_minus() + "RULE OPTIONS")
        print(c_yellow("[1]") + " No rules (fastest)")
        print(c_yellow("[2]") + " Standard rules (recommended)")
        print(c_yellow("[3]") + " All rules (slow but thorough)")
        
        rule_choice = input(tag_gt() + "Select rule option (1-3, default=2): ").strip() or "2"
        
        # Build command
        cmd = [self.john_path]
        
        # Add hash file
        if self.hash_file:
            cmd.append(self.hash_file)
        else:
            print(tag_exclamation() + "Hash file path is None!")
            return False
        
        # Add wordlist
        cmd.append("--wordlist=" + wordlist)
        
        # Add rules
        if rule_choice == "2":
            cmd.append("--rules")
        elif rule_choice == "3":
            cmd.append("--rules=All")
        
        # Add format if needed (John usually auto-detects)
        # cmd.append("--format=sha512crypt")  # For SHA-512
        
        return self.run_john_command(cmd, "Wordlist Attack")
    
    def run_single_mode(self):
        """Run single crack mode"""
        if not self.hash_file or not os.path.exists(self.hash_file):
            print(tag_exclamation() + "Hash file not found or not created!")
            return False
        
        cmd = [self.john_path, self.hash_file, "--single"]
        return self.run_john_command(cmd, "Single Crack Mode")
    
    def run_incremental_mode(self):
        """Run incremental mode"""
        if not self.hash_file or not os.path.exists(self.hash_file):
            print(tag_exclamation() + "Hash file not found or not created!")
            return False
        
        print(tag_minus() + "INCREMENTAL MODE OPTIONS")
        print(c_yellow("[1]") + " Digits only (0-9)")
        print(c_yellow("[2]") + " Lowercase letters (a-z)")
        print(c_yellow("[3]") + " Alphanumeric (a-z, A-Z, 0-9)")
        print(c_yellow("[4]") + " All characters")
        print(c_yellow("[5]") + " Cancel")
        
        try:
            choice = int(input(tag_gt() + "Select character set (1-5): "))
        except ValueError:
            print(tag_exclamation() + "Invalid choice")
            return False
        
        if choice == 5:
            return False
        
        charsets = {
            1: "Digits",
            2: "Low",
            3: "Alnum",
            4: "All"
        }
        
        if choice not in charsets:
            print(tag_exclamation() + "Invalid choice")
            return False
        
        charset = charsets[choice]
        
        print(tag_asterisk() + f"Using character set: {charset}")
        print(tag_exclamation() + "WARNING: This may take a VERY long time!")
        
        confirm = input(tag_gt() + "Continue with brute force? (y/n): ").lower()
        if confirm != 'y':
            print(tag_asterisk() + "Cancelled")
            return False
        
        cmd = [self.john_path, self.hash_file, "--incremental=" + charset]
        return self.run_john_command(cmd, f"Incremental Mode ({charset})")
    
    def show_results(self):
        """Show cracked passwords"""
        self.show_banner()
        print(tag_asterisk() + "Checking for cracked passwords...")
        
        if not self.hash_file or not os.path.exists(self.hash_file):
            print(tag_exclamation() + "Hash file not found!")
            return
        
        cmd = [self.john_path, self.hash_file, "--show"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.stdout:
                print()
                print(tag_minus() + "CRACKED PASSWORDS RESULTS")
                print()
                
                # Colorize the output
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if ':' in line and not line.startswith(' '):
                        parts = line.split(':')
                        if len(parts) >= 2:
                            # Mark user as cracked in our list
                            username = parts[0]
                            for user in self.users:
                                if user['username'] == username:
                                    user['cracked'] = True
                                    break
                            
                            print(c_cyan(parts[0] + ":") + c_green(":".join(parts[1:])))
                        else:
                            print(c_cyan(line))
                    else:
                        print(line)
                
                # Check if any passwords were actually cracked
                if "password hash cracked" in result.stdout or "password hashes cracked" in result.stdout:
                    # Save to file
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    results_file = f"cracked_passwords_{timestamp}.txt"
                    
                    with open(results_file, "w") as f:
                        f.write(f"Source passwd: {self.passwd_file}\n")
                        f.write(f"Source shadow: {self.shadow_file}\n")
                        f.write(f"Time: {time.ctime()}\n")
                        f.write("=" * 50 + "\n")
                        f.write(result.stdout)
                    
                    print(tag_minus() + f"Results saved to: {results_file}")
                else:
                    print(tag_minus() + "No passwords cracked yet")
            else:
                print(tag_minus() + "No passwords cracked yet")
                
        except Exception as e:
            print(tag_x() + f"Error showing results: {e}")
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.hash_file and os.path.exists(os.path.dirname(self.hash_file)):
            try:
                shutil.rmtree(os.path.dirname(self.hash_file))
            except:
                pass
        
        # Also cleanup any temporary passwd/shadow files created for current user
        temp_dirs = ["/tmp/unshadow_", "/tmp/7z_hash_", "/tmp/zip_hash_", "/tmp/rar_hash_"]
        for temp_dir_prefix in temp_dirs:
            for item in os.listdir('/tmp'):
                if item.startswith(temp_dir_prefix.replace('/tmp/', '')):
                    try:
                        shutil.rmtree(os.path.join('/tmp', item))
                    except:
                        pass
    
    def main_loop(self):
        """Main program loop"""
        if not self.check_tools():
            print(tag_exclamation() + "Please install missing tools and try again")
            input(tag_gt() + "Press Enter to exit...")
            return
        
        while True:
            # Select file source
            source_choice = self.select_file_source()
            
            if source_choice == 1:
                # Current directory (auto-detect)
                if not self.select_files_from_current():
                    input(tag_gt() + "Press Enter to continue...")
                    continue
            elif source_choice == 2:
                # Custom files
                if not self.get_custom_files():
                    input(tag_gt() + "Press Enter to continue...")
                    continue
            elif source_choice == 3:
                # Exit
                print(tag_asterisk() + "Goodbye!")
                self.cleanup()
                return
            else:
                continue
            
            # Parse users from files
            print(tag_asterisk() + "Parsing users from files...")
            if not self.parse_users():
                print(tag_exclamation() + "Failed to parse users from files")
                input(tag_gt() + "Press Enter to continue...")
                continue
            
            # Display users
            if not self.display_users():
                input(tag_gt() + "Press Enter to continue...")
                continue
            
            # Select user to crack
            if not self.select_user():
                continue
            
            # Create unshadowed file
            print(tag_asterisk() + "Creating combined password file for John...")
            if not self.create_unshadowed_file():
                print(tag_exclamation() + "Failed to create unshadowed file")
                input(tag_gt() + "Press Enter to continue...")
                continue
            
            # Main attack loop for selected user(s)
            while True:
                choice = self.select_attack_mode()
                
                if choice == 1:
                    # Wordlist attack with default wordlist
                    self.run_wordlist_attack()
                    self.show_results()
                    input(tag_gt() + "Press Enter to continue...")
                elif choice == 2:
                    # Wordlist attack with custom wordlist
                    wordlist = input(tag_gt() + "Enter path to custom wordlist: ").strip()
                    if wordlist:
                        if os.path.exists(wordlist):
                            self.run_wordlist_attack(custom_wordlist=wordlist)
                            self.show_results()
                        else:
                            print(tag_exclamation() + f"Wordlist not found: {wordlist}")
                    else:
                        print(tag_exclamation() + "No wordlist specified")
                    input(tag_gt() + "Press Enter to continue...")
                elif choice == 3:
                    # Single crack mode
                    self.run_single_mode()
                    self.show_results()
                    input(tag_gt() + "Press Enter to continue...")
                elif choice == 4:
                    # Incremental mode
                    self.run_incremental_mode()
                    self.show_results()
                    input(tag_gt() + "Press Enter to continue...")
                elif choice == 5:
                    # Show results
                    self.show_results()
                    input(tag_gt() + "Press Enter to continue...")
                elif choice == 6:
                    # Select different user/file
                    self.cleanup()
                    break
                elif choice == 7:
                    # Exit
                    print(tag_asterisk() + "Goodbye!")
                    self.cleanup()
                    return
                else:
                    print(tag_exclamation() + "Invalid choice")
                    input(tag_gt() + "Press Enter to continue...")

def main():
    """Main function"""
    # Check if running as root for system shadow access
    if os.geteuid() == 0:
        print(tag_plus() + "Running with root privileges")
    else:
        print(tag_info() + "Running without root privileges")
        print(c_yellow("    Some features may require root (sudo) access"))
    
    try:
        cracker = UnshadowCracker()
        cracker.main_loop()
    except KeyboardInterrupt:
        print(c_red("\n\n[x]") + " Program stopped by user")
        cracker.cleanup()
    except Exception as e:
        print(c_red("\n[x]") + f" Error: {e}")
        import traceback
        traceback.print_exc()
        cracker.cleanup()

if __name__ == "__main__":
    main()
