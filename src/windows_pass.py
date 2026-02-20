#!/usr/bin/env python3
"""
WINDOWS PASSWORD CRACKER
Extract and crack passwords from Windows SAM and SYSTEM files
SOKONALYSIS - Created by Soko James
Following Sokonalysis C++ Style Guidelines for Sub-options
"""

import os
import sys
import subprocess
import time
import tempfile
import shutil
import re
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
def tag_info(): return CYAN + "[i]" + RESET + " "

class WindowsPasswordCracker:
    def __init__(self):
        self.john_path = "john"
        self.hash_file = None
        self.default_wordlist = "wordlist.txt"
        self.current_dir = os.getcwd()
        self.sam_file = None
        self.system_file = None
        self.users = []
        self.selected_user = None
        self.hashes_extracted = False
        self.temp_dir = None
        self.output_file = None
        
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
    
    def check_tools(self):
        """Check if required tools are available"""
        # Check for john
        try:
            result = subprocess.run([self.john_path, "--version"], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode not in [0, 1]:
                return False
        except FileNotFoundError:
            return False
        
        # Check for impacket-secretsdump
        try:
            result = subprocess.run(["impacket-secretsdump", "-h"], 
                                  capture_output=True, text=True, timeout=2)
            if "secretsdump" not in result.stdout.lower() and result.returncode != 0:
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
    
    def auto_detect_files(self):
        """Auto-detect SAM and SYSTEM files in current directory"""
        print(tag_asterisk() + "Auto-detecting SAM and SYSTEM files...")
        print()
        
        sam_files = []
        system_files = []
        
        # Look for files with various extensions
        for file in os.listdir(self.current_dir):
            file_lower = file.lower()
            file_path = os.path.join(self.current_dir, file)
            
            if os.path.isfile(file_path):
                # Check for SAM files
                if file_lower in ['sam', 'sam.bak', 'sam.txt', 'sam.reg'] or \
                   file_lower.endswith('.sam') or 'sam' in file_lower:
                    sam_files.append((file, file_path))
                
                # Check for SYSTEM files
                if file_lower in ['system', 'system.bak', 'system.txt', 'system.reg'] or \
                   file_lower.endswith('.system') or 'system' in file_lower:
                    system_files.append((file, file_path))
        
        # Display found files
        if sam_files:
            self.show_success(f"Found {len(sam_files)} SAM file(s):")
            for filename, path in sam_files:
                print(CYAN + f"    {filename}" + RESET)
        
        if system_files:
            self.show_success(f"Found {len(system_files)} SYSTEM file(s):")
            for filename, path in system_files:
                print(CYAN + f"    {filename}" + RESET)
        
        # Try to auto-select
        if len(sam_files) == 1 and len(system_files) == 1:
            self.sam_file = sam_files[0][1]
            self.system_file = system_files[0][1]
            self.show_success(f"Auto-selected SAM: {sam_files[0][0]}")
            self.show_success(f"Auto-selected SYSTEM: {system_files[0][0]}")
            return True
        elif sam_files and system_files:
            # Let user select
            return self.select_detected_files(sam_files, system_files)
        else:
            self.show_error("Could not auto-detect both SAM and SYSTEM files")
            return False
    
    def select_detected_files(self, sam_files, system_files):
        """Let user select from detected files"""
        print(tag_minus() + "SELECT SAM FILE")
        for idx, (filename, path) in enumerate(sam_files, 1):
            print(YELLOW + f"[{idx}]" + RESET + f" {filename}")
        
        try:
            choice = int(input(tag_gt() + f"Select SAM file (1-{len(sam_files)}): "))
            if 1 <= choice <= len(sam_files):
                self.sam_file = sam_files[choice-1][1]
                self.show_success(f"Selected SAM: {sam_files[choice-1][0]}")
            else:
                return False
        except ValueError:
            self.show_error("Invalid selection")
            return False
        
        print()
        print(tag_minus() + "SELECT SYSTEM FILE")
        for idx, (filename, path) in enumerate(system_files, 1):
            print(YELLOW + f"[{idx}]" + RESET + f" {filename}")
        
        try:
            choice = int(input(tag_gt() + f"Select SYSTEM file (1-{len(system_files)}): "))
            if 1 <= choice <= len(system_files):
                self.system_file = system_files[choice-1][1]
                self.show_success(f"Selected SYSTEM: {system_files[choice-1][0]}")
                return True
            else:
                return False
        except ValueError:
            self.show_error("Invalid selection")
            return False
    
    def get_custom_files(self):
        """Get custom file paths from user"""
        print(tag_minus() + "ENTER CUSTOM FILE PATHS")
        print()
        
        sam_path = input(tag_gt() + "Enter full path to SAM file: ").strip()
        if not os.path.exists(sam_path):
            self.show_error(f"File not found: {sam_path}")
            return False
        
        system_path = input(tag_gt() + "Enter full path to SYSTEM file: ").strip()
        if not os.path.exists(system_path):
            self.show_error(f"File not found: {system_path}")
            return False
        
        self.sam_file = sam_path
        self.system_file = system_path
        self.show_success(f"Using SAM file: {sam_path}")
        self.show_success(f"Using SYSTEM file: {system_path}")
        return True
    
    def extract_hashes(self):
        """Extract password hashes using impacket-secretsdump"""
        print(tag_asterisk() + "Extracting password hashes...")
        print()
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="windows_pass_")
        self.output_file = os.path.join(self.temp_dir, "hashes.txt")
        
        print(tag_info() + f"Using command: impacket-secretsdump -system {self.system_file} -sam {self.sam_file} LOCAL")
        print()
        
        try:
            # Run impacket-secretsdump
            cmd = ["impacket-secretsdump", "-system", self.system_file, "-sam", self.sam_file, "LOCAL"]
            
            print(tag_gt() + "Running secretsdump...")
            print()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.show_error(f"secretsdump failed")
                if result.stderr:
                    print(RED + result.stderr + RESET)
                return False
            
            # Parse output to extract hashes
            self.parse_secretsdump_output(result.stdout)
            
            # Save hashes to file in John format
            if self.users:
                self.save_hashes_to_file()
                self.show_success(f"Extracted {len(self.users)} user(s)")
                self.show_success(f"Hashes saved to: {self.output_file}")
                return True
            else:
                self.show_error("No password hashes found in output!")
                return False
            
        except subprocess.TimeoutExpired:
            self.show_error("secretsdump timed out!")
            return False
        except Exception as e:
            self.show_error(f"Error running secretsdump: {e}")
            return False
    
    def parse_secretsdump_output(self, output):
        """Parse impacket-secretsdump output to extract hashes"""
        self.users = []
        
        # Parse lines to extract NTLM hashes
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Look for NTLM hash lines (format: username:RID:LMhash:NThash:::
            if ':' in line and ('aad3b435b51404eeaad3b435b51404ee' in line):
                
                # Check for standard format: username:rid:lmhash:nthash:::
                if line.count(':') >= 4:
                    parts = line.split(':')
                    username = parts[0]
                    
                    # Skip empty usernames or machine accounts
                    if not username or username.endswith('$'):
                        continue
                    
                    rid = parts[1] if len(parts) > 1 else ""
                    lm_hash = parts[2] if len(parts) > 2 else ""
                    nt_hash = parts[3] if len(parts) > 3 else ""
                    
                    # Only add if we have an NT hash
                    if nt_hash and nt_hash != 'aad3b435b51404eeaad3b435b51404ee' and len(nt_hash) == 32:
                        user_info = {
                            'username': username,
                            'rid': rid,
                            'lm_hash': lm_hash,
                            'nt_hash': nt_hash,
                            'hash_string': f"{username}:{rid}:{lm_hash}:{nt_hash}:::",
                            'cracked': False,
                            'password': None
                        }
                        self.users.append(user_info)
    
    def save_hashes_to_file(self):
        """Save extracted hashes to file in John format"""
        with open(self.output_file, 'w') as f:
            for user in self.users:
                # Write in format: username:rid:lmhash:nthash:::
                f.write(user['hash_string'] + '\n')
        
        self.hash_file = self.output_file
        self.hashes_extracted = True
    
    def display_users(self):
        """Display list of users with password hashes"""
        print(tag_minus() + "EXTRACTED WINDOWS USERS")
        print()
        print(tag_info() + f"SAM: {self.sam_file}")
        print(tag_info() + f"SYSTEM: {self.system_file}")
        print()
        
        if not self.users:
            self.show_error("No users with password hashes found!")
            return False
        
        self.show_success(f"Found {len(self.users)} user(s) with NTLM hashes:")
        print()
        print(YELLOW + "ID  USERNAME        RID     NT HASH" + RESET)
        print(YELLOW + "--  --------        ---     -------" + RESET)
        
        for idx, user in enumerate(self.users, 1):
            username = user['username']
            rid = user['rid']
            nt_hash = user['nt_hash']
            
            # Truncate hash for display
            if len(nt_hash) > 8:
                nt_display = nt_hash[:8] + "..."
            else:
                nt_display = nt_hash
            
            # Truncate long usernames
            if len(username) > 12:
                username_display = username[:12] + "..."
            else:
                username_display = username
            
            # Color based on hash type
            if user.get('cracked', False):
                username_display = GREEN + username_display + RESET
                nt_display = GREEN + nt_display + RESET
            
            print(f"{idx:2d}  {username_display:15} {rid:6}  {nt_display}")
        
        print()
        return True
    
    def select_user(self):
        """Let user select which account to crack"""
        if len(self.users) == 1:
            # Only one user, auto-select
            self.selected_user = self.users[0]
            self.show_success(f"Auto-selected user: {self.selected_user['username']}")
            return True
        
        # Colored header matching the style of Options header
        print(BLUE + "_____________________ " + GREEN + "User Selection" + BLUE + " ____________________________" + RESET)
        print()
        print(YELLOW + f"[1-{len(self.users)}]" + RESET + f" Select user by ID")
        print(YELLOW + f"[{len(self.users)+1}]" + RESET + " Crack ALL users")
        print(YELLOW + f"[{len(self.users)+2}]" + RESET + " Cancel")
        print(BLUE + "_________________________________________________________________" + RESET)
        print()
        
        try:
            choice = int(input(tag_gt() + f"Select option (1-{len(self.users)+2}): "))
            print()
            
            if 1 <= choice <= len(self.users):
                self.selected_user = self.users[choice-1]
                self.show_success(f"Selected user: {self.selected_user['username']}")
                return True
            elif choice == len(self.users) + 1:
                self.selected_user = None  # Means all users
                self.show_success("Selected ALL users")
                return True
            else:
                return False
                
        except ValueError:
            self.show_error("Please enter a valid number")
            return False
    
    def get_wordlist_info(self, wordlist_path):
        """Get information about a wordlist"""
        if not os.path.exists(wordlist_path):
            self.show_error(f"Wordlist not found: {wordlist_path}")
            return False
        
        wordcount = self.count_words(wordlist_path)
        if wordcount == 0:
            self.show_error(f"Wordlist is empty: {wordlist_path}")
            return False
        
        filesize = os.path.getsize(wordlist_path)
        if filesize < 1024:
            size_str = f"{filesize}B"
        elif filesize < 1024*1024:
            size_str = f"{filesize/1024:.1f}KB"
        else:
            size_str = f"{filesize/(1024*1024):.1f}MB"
        
        self.show_success(f"Wordlist: {wordlist_path}")
        self.show_success(f"Size: {size_str}, Words: {wordcount}")
        return True
    
    def run_john_command(self, cmd, attack_name):
        """Run a John the Ripper command"""
        print(tag_asterisk() + f"{attack_name} starting...")
        print()
        
        if self.selected_user:
            print(tag_info() + f"Target user: {YELLOW}{self.selected_user['username']}{RESET}")
        else:
            print(tag_info() + f"Target: {YELLOW}{len(self.users)} users{RESET}")
        
        print(tag_gt() + "Command: " + CYAN + f"{' '.join(cmd)}" + RESET)
        print()
        print(tag_asterisk() + "Starting attack... " + RED + "Press Ctrl+C to stop" + RESET)
        print()
        
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
                    if "cracked" in line.lower():
                        print(tag_plus() + " " + GREEN + line.strip() + RESET)
                    elif "warning" in line.lower():
                        print(tag_exclamation() + " " + ORANGE + line.strip() + RESET)
                    elif "error" in line.lower():
                        print(tag_x() + " " + RED + line.strip() + RESET)
                    else:
                        print(line.strip())
            
            process.wait()
            elapsed = time.time() - start_time
            print()
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
        # Check if hash file exists
        if not self.hash_file or not os.path.exists(self.hash_file):
            self.show_error("Hash file not found or not created!")
            return False
        
        wordlist = custom_wordlist if custom_wordlist else self.default_wordlist
        
        if not self.get_wordlist_info(wordlist):
            return False
        
        print()
        print(BLUE + "_____________________________ " + GREEN + "Rules" + BLUE + " _____________________________" + RESET)
        print()
        print(YELLOW + "[1]" + RESET + " No rules (fastest)")
        print(YELLOW + "[2]" + RESET + " Standard rules (recommended)")
        print(YELLOW + "[3]" + RESET + " All rules (slow but thorough)")
        print(BLUE + "_________________________________________________________________" + RESET)
        print()
        
        rule_choice = input(tag_gt() + "Select rule option (1-3, default=2): ").strip() or "2"
        print()
        
        # Build command
        cmd = [self.john_path, self.hash_file, "--format=NT", "--wordlist=" + wordlist]
        
        # Add rules
        if rule_choice == "2":
            cmd.append("--rules")
        elif rule_choice == "3":
            cmd.append("--rules=All")
        
        return self.run_john_command(cmd, "Wordlist Attack")
    
    def run_single_mode(self):
        """Run single crack mode"""
        if not self.hash_file or not os.path.exists(self.hash_file):
            self.show_error("Hash file not found or not created!")
            return False
        
        cmd = [self.john_path, self.hash_file, "--single", "--format=NT"]
        return self.run_john_command(cmd, "Single Crack Mode")
    
    def run_incremental_mode(self):
        """Run incremental mode"""
        if not self.hash_file or not os.path.exists(self.hash_file):
            self.show_error("Hash file not found or not created!")
            return False
        
        print()
        print(BLUE + "________________________ " + GREEN + "Character Sets" + BLUE + " ________________________" + RESET)
        print()
        print(YELLOW + "[1]" + RESET + " Digits only (0-9)")
        print(YELLOW + "[2]" + RESET + " Lowercase letters (a-z)")
        print(YELLOW + "[3]" + RESET + " Alphanumeric (a-z, A-Z, 0-9)")
        print(YELLOW + "[4]" + RESET + " All characters")
        print(YELLOW + "[5]" + RESET + " Cancel")
        print(BLUE + "_________________________________________________________________" + RESET)
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
        
        cmd = [self.john_path, self.hash_file, "--incremental=" + mode, "--format=NT"]
        return self.run_john_command(cmd, f"Incremental Mode ({mode})")
    
    def show_results(self):
        """Show cracked passwords - exactly as specified"""
        print(tag_asterisk() + "Checking for cracked passwords...")
        print()
        
        if not self.hash_file or not os.path.exists(self.hash_file):
            self.show_error("Hash file not found!")
            return False
        
        cmd = [self.john_path, self.hash_file, "--show", "--format=NT"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.stdout:
                # Parse the output to extract the password
                lines = result.stdout.strip().split('\n')
                password_found = False
                password_value = ""
                
                for line in lines:
                    if ':' in line and not line.startswith(' '):
                        # This is a cracked password line like "username:password"
                        parts = line.split(':', 1)
                        if len(parts) > 1:
                            username = parts[0]
                            password = parts[1]
                            
                            # Update user in our list
                            for user in self.users:
                                if user['username'] == username:
                                    user['cracked'] = True
                                    user['password'] = password
                            
                            # If this is the selected user or we're showing all
                            if self.selected_user is None or self.selected_user['username'] == username:
                                # Extract just the password (not the hash)
                                if ':' in password:
                                    password_parts = password.split(':')
                                    password_value = password_parts[0]
                                else:
                                    password_value = password
                                password_found = True
                
                if password_found:
                    print(BLUE + "_________________________________________________________________" + RESET)
                    print()
                    print(tag_minus() + "Cracked Passwords Results: " + GREEN + password_value + RESET)
                    print()
                    print(BLUE + "_________________________________________________________________" + RESET)
                    
                    # Save results to file
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = f"cracked_{timestamp}.txt"
                    with open(filename, "w") as f:
                        f.write(result.stdout)
                    
                    print()
                    print(tag_plus() + f" Results saved to: {filename}")
                    print()
                    print(BLUE + "_________________________________________________________________" + RESET)
                    
                    return True
                else:
                    print(tag_minus() + "No passwords cracked yet")
            else:
                print(tag_minus() + "No passwords cracked yet")
                
        except Exception as e:
            self.show_error(f"Error showing results: {e}")
        
        print(BLUE + "\n_________________________________________________________________" + RESET)
        return False
    
    def select_attack_mode(self):
        """Select attack mode"""
        print(tag_asterisk() + "Target: " + YELLOW + f"{self.selected_user['username'] if self.selected_user else 'ALL USERS'}" + RESET)
        print()
        print(BLUE + "____________________________ " + GREEN + "Options" + BLUE + " ____________________________" + RESET)
        print()

        print(YELLOW + "[1]" + RESET + " Wordlist Attack (using default wordlist)")
        print(YELLOW + "[2]" + RESET + " Wordlist Attack (custom wordlist)")
        print(YELLOW + "[3]" + RESET + " Single Crack Mode")
        print(YELLOW + "[4]" + RESET + " Incremental Mode (brute force)")
        print(YELLOW + "[5]" + RESET + " Show cracked passwords")
        print(YELLOW + "[6]" + RESET + " Select different user/file")
        print(YELLOW + "[7]" + RESET + " Exit")
        print(BLUE + "_________________________________________________________________" + RESET)
        print()
        
        try:
            return int(input(tag_gt() + "Select option (1-7): "))
        except:
            self.show_error("Please enter a number")
            return None
    
    def select_file_source(self):
        """Select file source method"""
        # Colored header matching the style of Options header
        print(BLUE + "_______________________ " + GREEN + "File Source" + BLUE + " _____________________________" + RESET)
        print()
        print(YELLOW + "[1]" + RESET + " Auto-detect SAM/SYSTEM files in current directory")
        print(YELLOW + "[2]" + RESET + " Enter custom file paths")
        print(YELLOW + "[3]" + RESET + " Exit")
        print(BLUE + "_________________________________________________________________" + RESET)
        print()
        
        try:
            return int(input(tag_gt() + "Select option (1-3): "))
        except:
            self.show_error("Please enter a number")
            return None
    
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
        """Main program loop"""
        if not self.check_tools():
            print(tag_exclamation() + "Required tools not found. Please install john and impacket.")
            return
        
        while True:
            choice = self.select_file_source()
            
            if choice == 1:
                # Auto-detect
                print()
                if not self.auto_detect_files():
                    input(tag_gt() + "Press Enter to continue...")
                    continue
            elif choice == 2:
                # Custom files
                print()
                if not self.get_custom_files():
                    input(tag_gt() + "Press Enter to continue...")
                    continue
            elif choice == 3:
                # Exit silently
                self.cleanup()
                return
            else:
                continue
            
            # Extract hashes
            print()
            if not self.extract_hashes():
                self.cleanup()
                input(tag_gt() + "Press Enter to continue...")
                continue
            
            # Display users
            print()
            if not self.display_users():
                self.cleanup()
                input(tag_gt() + "Press Enter to continue...")
                continue
            
            # Select user to crack
            if not self.select_user():
                self.cleanup()
                continue
            
            # Main attack loop for selected user(s)
            while True:
                print()
                choice = self.select_attack_mode()
                
                if choice == 1:
                    self.run_wordlist_attack()
                    if self.show_results():
                        self.cleanup()
                        return
                elif choice == 2:
                    wl = input(tag_gt() + "Enter path to custom wordlist: ").strip()
                    if wl:
                        if os.path.exists(wl):
                            self.run_wordlist_attack(custom_wordlist=wl)
                            if self.show_results():
                                self.cleanup()
                                return
                        else:
                            self.show_error(f"Wordlist not found: {wl}")
                    else:
                        self.show_error("No wordlist specified")
                elif choice == 3:
                    self.run_single_mode()
                    if self.show_results():
                        self.cleanup()
                        return
                elif choice == 4:
                    self.run_incremental_mode()
                    if self.show_results():
                        self.cleanup()
                        return
                elif choice == 5:
                    if self.show_results():
                        self.cleanup()
                        return
                elif choice == 6:
                    self.cleanup()
                    break
                elif choice == 7:
                    # Exit silently
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
        
        cracker = WindowsPasswordCracker()
        cracker.main_loop()
        
    except KeyboardInterrupt:
        print(RED + "\n[x] Program stopped by user" + RESET)
    except Exception as e:
        print(RED + f"\n[x] Error: {e}" + RESET)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
