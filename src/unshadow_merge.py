#!/usr/bin/env python3
"""
UNSHADOW PASSWORD CRACKER & MERGER
Merge passwd/shadow and crack passwords for active Linux accounts
Complete workflow using unshadow for hash extraction and cracking
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
from pathlib import Path
from datetime import datetime

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

class UnshadowCrackerMerger:
    def __init__(self):
        self.john_path = "john"
        self.unshadow_path = self.find_unshadow()
        self.system_passwd = "/etc/passwd"
        self.system_shadow = "/etc/shadow"
        self.current_dir = os.getcwd()
        self.default_wordlist = "wordlist.txt"
        self.hash_file = None
        self.temp_dir = None
        self.active_users = []
        self.selected_user = None
        
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
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return None
    
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
    
    def check_permissions(self):
        """Check if running with sufficient permissions"""
        if os.geteuid() != 0:
            self.show_warning("Not running as root. Some operations may fail")
            print(tag_asterisk() + "Consider running with: " + GREEN + "sudo python3 unshadow_crack.py" + RESET)
            print()
            return False
        return True
    
    def check_system_files(self):
        """Check if system passwd and shadow files exist"""
        if not os.path.exists(self.system_passwd):
            self.show_error(f"System passwd file not found: {self.system_passwd}")
            return False
        
        if not os.path.exists(self.system_shadow):
            self.show_error(f"System shadow file not found: {self.system_shadow}")
            return False
        
        return True
    
    def check_tools(self):
        """Check if required tools are available"""
        # Check for john
        try:
            result = subprocess.run([self.john_path, "--version"], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode not in [0, 1]:
                self.show_error("John the Ripper not working properly")
                return False
        except FileNotFoundError:
            self.show_error("John the Ripper not found. Please install john.")
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
                self.show_info(f"Using wordlist: {self.default_wordlist}")
                break
        else:
            self.show_warning("No wordlist found in default locations")
        
        return True
    
    def count_words(self, filepath):
        """Count words in a file"""
        if not os.path.exists(filepath):
            return 0
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for line in f if line.strip())
        except:
            return 0
    
    def is_active_account(self, shell):
        """Check if account has a valid login shell"""
        if not shell:
            return False
        
        invalid_shells = [
            '/usr/sbin/nologin',
            '/sbin/nologin', 
            '/bin/nologin',
            '/usr/bin/nologin',
            '/bin/false',
            '/usr/bin/false',
            '/bin/sync',
            '/sbin/halt',
            '/sbin/shutdown',
            '/dev/null',
            '',
            'false',
            'nologin'
        ]
        
        return shell.strip() not in invalid_shells
    
    def is_valid_hash(self, hash_value):
        """Check if password hash is crackable"""
        if not hash_value:
            return False
        
        invalid_hashes = ['*', '!', '!!', '!*', 'x', '!$', 'NP', 'LK', '']
        
        if hash_value in invalid_hashes:
            return False
        
        valid_prefixes = [
            '$1$', '$2a$', '$2b$', '$2y$', '$5$', '$6$', '$y$',
        ]
        
        if any(hash_value.startswith(prefix) for prefix in valid_prefixes):
            return True
        
        if len(hash_value) == 13:
            return True
        
        return False
    
    def detect_hash_type(self, hash_value):
        """Detect the type of hash"""
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
        elif len(hash_value) == 13:
            return "DES"
        else:
            return "Unknown"
    
    def parse_active_users(self):
        """Parse and identify active users from system files"""
        print(tag_asterisk() + "Parsing system accounts...")
        print()
        
        try:
            with open(self.system_passwd, 'r') as f:
                passwd_lines = f.readlines()
            
            with open(self.system_shadow, 'r') as f:
                shadow_lines = f.readlines()
            
            shadow_dict = {}
            for line in shadow_lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(':')
                    if len(parts) >= 2:
                        username = parts[0]
                        hash_value = parts[1]
                        shadow_dict[username] = hash_value
            
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
                        
                        if not self.is_active_account(shell):
                            continue
                        
                        if username in shadow_dict:
                            hash_value = shadow_dict[username]
                            
                            if self.is_valid_hash(hash_value):
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
                                    'cracked': False,
                                }
                                self.active_users.append(user_info)
            
            return len(self.active_users) > 0
            
        except PermissionError:
            self.show_error("Permission denied. Run with sudo to access shadow file")
            return False
        except Exception as e:
            self.show_error(f"Error parsing files: {e}")
            return False
    
    def display_users(self):
        """Display list of active users with password hashes"""
        print(tag_asterisk() + "Found " + GREEN + f"{len(self.active_users)}" + RESET + " active account(s) with password hashes")
        print()
        
        if not self.active_users:
            return False
        
        print(CYAN + "ID  Username              UID   Hash Type" + RESET)
        print(CYAN + "--  --------              ---   ---------" + RESET)
        
        for idx, user in enumerate(self.active_users, 1):
            username = user['username']
            uid = user['uid']
            hash_type = user['hash_type']
            
            if len(username) > 20:
                username_display = username[:17] + "..."
            else:
                username_display = username.ljust(20)
            
            print(f"{idx:2d}  {username_display} {uid:4}   {hash_type}")
        
        print()
        return True
    
    def select_user(self):
        """Let user select which account to crack"""
        print(BLUE + "________________________ " + GREEN + "User Selection" + BLUE + " ________________________")
        print()
        
        print(YELLOW + f"[1-{len(self.active_users)}]" + RESET + f" Select user by ID")
        print(YELLOW + f"[{len(self.active_users)+1}]" + RESET + " Crack ALL users")
        print(YELLOW + f"[{len(self.active_users)+2}]" + RESET + " Cancel")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            choice = int(input(tag_gt() + f"Select option (1-{len(self.active_users)+2}): "))
            
            if 1 <= choice <= len(self.active_users):
                self.selected_user = self.active_users[choice-1]
                self.show_success(f"Selected user: {self.selected_user['username']}")
                return True
            elif choice == len(self.active_users) + 1:
                self.selected_user = None
                self.show_success("Selected ALL users")
                return True
            else:
                return False
                
        except ValueError:
            self.show_error("Please enter a valid number")
            return False
    
    def extract_hash(self):
        """Extract hash using unshadow for proper format"""
        print(tag_asterisk() + "Extracting hash using unshadow...")
        print()
        
        self.temp_dir = tempfile.mkdtemp(prefix="unshadow_hash_")
        self.hash_file = os.path.join(self.temp_dir, "hashes.txt")
        
        try:
            if self.unshadow_path and os.path.exists(self.unshadow_path):
                # Use actual unshadow command
                cmd = [self.unshadow_path, self.system_passwd, self.system_shadow]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and result.stdout:
                    lines_to_write = []
                    for line in result.stdout.split('\n'):
                        if line.strip():
                            # Check if this is our selected user
                            username = line.split(':')[0]
                            if self.selected_user:
                                if username == self.selected_user['username']:
                                    lines_to_write.append(line.strip())
                            else:
                                # For all users, only include active ones
                                if any(user['username'] == username for user in self.active_users):
                                    lines_to_write.append(line.strip())
                    
                    if lines_to_write:
                        with open(self.hash_file, 'w') as f:
                            for line in lines_to_write:
                                f.write(line + '\n')
                        
                        self.show_success(f"Hash extracted using unshadow! ({len(lines_to_write)} hash(es))")
                        return True
                
                # If unshadow fails, fall back to Python
                return self.extract_hash_python()
            else:
                return self.extract_hash_python()
                
        except Exception as e:
            self.show_error(f"Error with unshadow: {e}")
            return self.extract_hash_python()
    
    def extract_hash_python(self):
        """Fallback Python hash extraction"""
        print(tag_asterisk() + "Using Python hash extraction...")
        print()
        
        try:
            with open(self.hash_file, 'w') as f:
                count = 0
                for user in self.active_users:
                    if self.selected_user and user['username'] != self.selected_user['username']:
                        continue
                    
                    # Write full unshadow format
                    line = f"{user['username']}:{user['hash']}:{user['uid']}:{user['gid']}:{user['gecos']}:{user['home']}:{user['shell']}"
                    f.write(line + '\n')
                    count += 1
            
            if count > 0:
                self.show_success(f"Hash extracted! ({count} hash(es))")
                return True
            else:
                self.show_error("No valid password hashes found")
                return False
                
        except Exception as e:
            self.show_error(f"Error extracting hash: {e}")
            return False
    
    def select_attack_mode(self):
        """Select attack mode"""
        if self.selected_user:
            print(tag_asterisk() + "Target: " + YELLOW + f"{self.selected_user['username']}" + RESET + " (" + CYAN + f"{self.selected_user['hash_type']}" + RESET + ")")
        else:
            print(tag_asterisk() + "Target: " + YELLOW + f"ALL USERS" + RESET + " (" + CYAN + f"{len(self.active_users)} users" + RESET + ")")
        
        print()
        print(BLUE + "\n____________________________ " + GREEN + "Options" + BLUE + " ____________________________")
        print()

        print(YELLOW + "[1]" + RESET + " Wordlist Attack (using default wordlist)")
        print(YELLOW + "[2]" + RESET + " Wordlist Attack (custom wordlist)")
        print(YELLOW + "[3]" + RESET + " Single Crack Mode")
        print(YELLOW + "[4]" + RESET + " Incremental Mode (brute force)")
        print(YELLOW + "[5]" + RESET + " Show cracked passwords")
        print(YELLOW + "[6]" + RESET + " Select different files/user")
        print(YELLOW + "[7]" + RESET + " Exit")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            return int(input(tag_gt() + "Select option (1-7): "))
        except:
            self.show_error("Please enter a number")
            return None
    
    def run_john_command(self, cmd, attack_name):
        """Run a John the Ripper command - silenced output"""
        print(tag_asterisk() + f"{attack_name} on: " + YELLOW + f"{self.selected_user['username'] if self.selected_user else 'ALL USERS'}" + RESET)
        print()
        print(tag_asterisk() + "Starting attack... " + RED + "Press Ctrl+C to stop" + RESET)
        print()
        
        try:
            start = time.time()
            # Run silently without printing John's output
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            elapsed = time.time() - start
            print(tag_minus() + f"Finished in " + YELLOW + f"{elapsed:.1f} seconds" + RESET)
            
        except KeyboardInterrupt:
            print()
            self.show_error("Stopped by user")
            return False
        except Exception as e:
            print()
            self.show_error(f"Error: {e}")
            return False
        
        return True
    
    def run_wordlist_attack(self, custom_wordlist=None):
        """Run wordlist attack"""
        wordlist = custom_wordlist or self.default_wordlist
        
        if not os.path.exists(wordlist):
            self.show_error("Wordlist not found")
            return False
        
        word_count = self.count_words(wordlist)
        self.show_info(f"Wordlist: {wordlist} ({word_count} words)")
        
        cmd = [self.john_path, self.hash_file, "--wordlist=" + wordlist, "--format=crypt"]
        
        print()
        print(BLUE + "_____________________________ " + GREEN + "Rules" + BLUE + " _____________________________")
        print()
        print(YELLOW + "[1]" + RESET + " No rules (fastest)")
        print(YELLOW + "[2]" + RESET + " Standard rules (recommended)")
        print(YELLOW + "[3]" + RESET + " All rules (slow but thorough)")
        print(BLUE + "_________________________________________________________________")
        print()
        
        choice = input(tag_gt() + "Select rule option (1-3, default=2): ").strip() or "2"
        
        if choice == "2":
            cmd.append("--rules")
        elif choice == "3":
            cmd.append("--rules=All")
        
        return self.run_john_command(cmd, "Wordlist Attack")
    
    def run_single_mode(self):
        """Run single crack mode"""
        cmd = [self.john_path, self.hash_file, "--single", "--format=crypt"]
        return self.run_john_command(cmd, "Single Crack Mode")
    
    def run_incremental_mode(self):
        """Run incremental mode"""
        print()
        print(BLUE + "________________________ " + GREEN + "Character Sets" + BLUE + " ________________________")
        print()
        print(YELLOW + "[1]" + RESET + " Digits only (0-9)")
        print(YELLOW + "[2]" + RESET + " Lowercase letters (a-z)")
        print(YELLOW + "[3]" + RESET + " Alphanumeric (a-z, A-Z, 0-9)")
        print(YELLOW + "[4]" + RESET + " All characters")
        print(YELLOW + "[5]" + RESET + " Cancel")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            choice = int(input(tag_gt() + "Select character set (1-5): "))
            if choice == 5:
                return False
        except:
            self.show_error("Invalid choice")
            return False
        
        modes = {1: "Digits", 2: "Lower", 3: "Alnum", 4: "All"}
        mode = modes.get(choice, "Alnum")
        
        print()
        self.show_warning("This may take a VERY long time!")
        confirm = input(tag_question() + "Continue with brute force? (y/n): ").lower()
        
        if confirm != 'y':
            print(tag_asterisk() + "Cancelled")
            return False
        
        cmd = [self.john_path, self.hash_file, "--incremental=" + mode, "--format=crypt"]
        return self.run_john_command(cmd, f"Incremental Mode ({mode})")
    
    def show_results(self):
        """Show cracked passwords - exactly as specified"""
        print(tag_asterisk() + "Checking for cracked passwords...")
        print()
        
        cmd = [self.john_path, self.hash_file, "--show"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.stdout:
                # Parse the output to extract just the password
                lines = result.stdout.strip().split('\n')
                password_found = False
                password_value = ""
                cracked_user = ""
                
                for line in lines:
                    # Look for lines with username:password format
                    if ':' in line and not line.startswith(' ') and not line.startswith('1 password'):
                        # Split on first colon to get username
                        parts = line.split(':', 1)
                        if len(parts) > 1:
                            cracked_user = parts[0]
                            # The rest after username contains password and other fields
                            rest = parts[1]
                            
                            # The password is the first field after username, before the hash
                            # In unshadow format: password:hash:uid:gid:gecos:home:shell
                            # But john --show returns: password:rest
                            # We need to check if it's a hash or the actual password
                            password_parts = rest.split(':')
                            
                            # The first part should be the password (not a hash)
                            potential_password = password_parts[0]
                            
                            # Check if it looks like a hash
                            if potential_password.startswith('$') or len(potential_password) == 13:
                                # It's still a hash, password not cracked for this user
                                continue
                            else:
                                password_value = potential_password
                                password_found = True
                                break
                
                if password_found:
                    print(BLUE + "_________________________________________________________________")
                    print()
                    # Display only the password
                    print(tag_minus() + "Cracked Password Results: " + GREEN + f"{password_value}" + RESET)
                    print()
                    print(BLUE + "_________________________________________________________________")
                    
                    # Save full results to file
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = f"cracked_{timestamp}.txt"
                    with open(filename, "w") as f:
                        f.write(result.stdout)
                    
                    print()
                    print(tag_plus() + f" Results saved to: {filename}")
                    print()
                    print(BLUE + "_________________________________________________________________")
                    print()
                    
                    return True
                else:
                    print(tag_minus() + "No passwords cracked yet")
                    print(BLUE + "\n_________________________________________________________________")
                    return False
            else:
                print(tag_minus() + "No passwords cracked yet")
                print(BLUE + "\n_________________________________________________________________")
                return False
                
        except Exception as e:
            self.show_error(f"Error showing results: {e}")
            print(BLUE + "\n_________________________________________________________________")
            return False
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
                self.hash_file = None
            except:
                pass
    
    def main_loop(self):
        """Main program loop - exits completely after cracking"""
        if not self.check_tools():
            return
        
        self.check_permissions()
        
        if not self.check_system_files():
            return
        
        if not self.parse_active_users():
            self.show_error("No active accounts with password hashes found")
            return
        
        while True:
            # Display users
            if not self.display_users():
                return
            
            # Select user
            if not self.select_user():
                self.cleanup()
                return
            
            print()
            
            # Extract hash
            if not self.extract_hash():
                continue
            
            while True:
                print()
                choice = self.select_attack_mode()
                
                if choice == 1:
                    self.run_wordlist_attack()
                    password_cracked = self.show_results()
                    self.cleanup()
                    if password_cracked:
                        return
                    break
                elif choice == 2:
                    wl = input(tag_gt() + "Enter path to custom wordlist: ").strip()
                    if wl:
                        if os.path.exists(wl):
                            self.run_wordlist_attack(wl)
                            password_cracked = self.show_results()
                            self.cleanup()
                            if password_cracked:
                                return
                            break
                        else:
                            self.show_error(f"Wordlist not found: {wl}")
                    else:
                        self.show_error("No wordlist specified")
                elif choice == 3:
                    self.run_single_mode()
                    password_cracked = self.show_results()
                    self.cleanup()
                    if password_cracked:
                        return
                    break
                elif choice == 4:
                    self.run_incremental_mode()
                    password_cracked = self.show_results()
                    self.cleanup()
                    if password_cracked:
                        return
                    break
                elif choice == 5:
                    password_cracked = self.show_results()
                    if password_cracked:
                        self.cleanup()
                        return
                elif choice == 6:
                    self.cleanup()
                    break
                elif choice == 7:
                    self.cleanup()
                    return
                else:
                    self.show_error("Invalid choice")

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
        
        cracker = UnshadowCrackerMerger()
        cracker.main_loop()
        
    except KeyboardInterrupt:
        print(RED + "\n[x] Program stopped by user" + RESET)
    except Exception as e:
        print(RED + f"\n[x] Error: {e}" + RESET)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
