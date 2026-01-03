#!/usr/bin/env python3
"""
WINDOWS PASSWORD CRACKER
Extract and crack passwords from Windows SAM and SYSTEM files
Colorful Interface
"""

import os
import sys
import subprocess
import time
import tempfile
import shutil
import re
import json
import argparse
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
        
    def clear_screen(self):
        """Clear screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def show_banner(self):
        """Show colorful banner"""
        self.clear_screen()
        print(tag_minus() + "WINDOWS PASSWORD CRACKER")
        print(c_yellow("Extract and crack passwords from Windows SAM and SYSTEM files"))
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
        
        # Check for impacket-secretsdump
        try:
            result = subprocess.run(["impacket-secretsdump", "-h"], 
                                  capture_output=True, text=True, timeout=2)
            if "secretsdump" in result.stdout.lower() or result.returncode == 0:
                print(tag_plus() + "Impacket-secretsdump: Found")
            else:
                print(tag_exclamation() + "Impacket-secretsdump not found!")
                print(c_yellow("    Install with: pip install impacket"))
                print(c_yellow("    Or download from: https://github.com/fortra/impacket"))
                return False
        except FileNotFoundError:
            print(tag_exclamation() + "Impacket-secretsdump not found!")
            print(c_yellow("    Install with: pip install impacket"))
            print(c_yellow("    Or download from: https://github.com/fortra/impacket"))
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
    
    def auto_detect_files(self):
        """Auto-detect SAM and SYSTEM files in current directory"""
        self.show_banner()
        print(tag_asterisk() + "Auto-detecting SAM and SYSTEM files...")
        
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
            print(tag_plus() + f"Found {len(sam_files)} SAM file(s):")
            for filename, path in sam_files:
                print(c_cyan(f"    {filename}"))
        
        if system_files:
            print(tag_plus() + f"Found {len(system_files)} SYSTEM file(s):")
            for filename, path in system_files:
                print(c_cyan(f"    {filename}"))
        
        # Try to auto-select
        if len(sam_files) == 1 and len(system_files) == 1:
            self.sam_file = sam_files[0][1]
            self.system_file = system_files[0][1]
            print(tag_plus() + f"Auto-selected SAM: {sam_files[0][0]}")
            print(tag_plus() + f"Auto-selected SYSTEM: {system_files[0][0]}")
            return True
        elif sam_files and system_files:
            # Let user select
            return self.select_detected_files(sam_files, system_files)
        else:
            print(tag_exclamation() + "Could not auto-detect both SAM and SYSTEM files")
            return False
    
    def select_detected_files(self, sam_files, system_files):
        """Let user select from detected files"""
        print(tag_minus() + "SELECT SAM FILE")
        for idx, (filename, path) in enumerate(sam_files, 1):
            print(c_yellow(f"[{idx}]") + f" {filename}")
        
        try:
            choice = int(input(tag_gt() + f"Select SAM file (1-{len(sam_files)}): "))
            if 1 <= choice <= len(sam_files):
                self.sam_file = sam_files[choice-1][1]
                print(tag_plus() + f"Selected SAM: {sam_files[choice-1][0]}")
            else:
                return False
        except ValueError:
            print(tag_exclamation() + "Invalid selection")
            return False
        
        print(tag_minus() + "SELECT SYSTEM FILE")
        for idx, (filename, path) in enumerate(system_files, 1):
            print(c_yellow(f"[{idx}]") + f" {filename}")
        
        try:
            choice = int(input(tag_gt() + f"Select SYSTEM file (1-{len(system_files)}): "))
            if 1 <= choice <= len(system_files):
                self.system_file = system_files[choice-1][1]
                print(tag_plus() + f"Selected SYSTEM: {system_files[choice-1][0]}")
                return True
            else:
                return False
        except ValueError:
            print(tag_exclamation() + "Invalid selection")
            return False
    
    def get_custom_files(self):
        """Get custom file paths from user"""
        self.show_banner()
        print(tag_minus() + "ENTER CUSTOM FILE PATHS")
        
        sam_path = input(tag_gt() + "Enter full path to SAM file: ").strip()
        if not os.path.exists(sam_path):
            print(tag_exclamation() + f"File not found: {sam_path}")
            return False
        
        system_path = input(tag_gt() + "Enter full path to SYSTEM file: ").strip()
        if not os.path.exists(system_path):
            print(tag_exclamation() + f"File not found: {system_path}")
            return False
        
        self.sam_file = sam_path
        self.system_file = system_path
        print(tag_plus() + f"Using SAM file: {sam_path}")
        print(tag_plus() + f"Using SYSTEM file: {system_path}")
        return True
    
    def extract_hashes(self):
        """Extract password hashes using impacket-secretsdump"""
        self.show_banner()
        print(tag_asterisk() + "Extracting password hashes...")
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="windows_pass_")
        self.output_file = os.path.join(self.temp_dir, "hashes.txt")
        
        print(tag_info() + f"Using command: impacket-secretsdump -system {self.system_file} -sam {self.sam_file} LOCAL")
        
        try:
            # Run impacket-secretsdump
            cmd = ["impacket-secretsdump", "-system", self.system_file, "-sam", self.sam_file, "LOCAL"]
            
            print(tag_gt() + "Running secretsdump...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                print(tag_exclamation() + f"secretsdump failed with error:")
                print(c_red(result.stderr))
                return False
            
            # Parse output to extract hashes
            self.parse_secretsdump_output(result.stdout)
            
            # Save hashes to file in John format
            if self.users:
                self.save_hashes_to_file()
                print(tag_plus() + f"Extracted {len(self.users)} user(s)")
                print(tag_plus() + f"Hashes saved to: {self.output_file}")
                return True
            else:
                print(tag_exclamation() + "No password hashes found in output!")
                return False
            
        except subprocess.TimeoutExpired:
            print(tag_exclamation() + "secretsdump timed out!")
            return False
        except Exception as e:
            print(tag_exclamation() + f"Error running secretsdump: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def parse_secretsdump_output(self, output):
        """Parse impacket-secretsdump output to extract hashes"""
        self.users = []
        
        # Parse lines to extract NTLM hashes
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Look for NTLM hash lines (format: username:RID:LMhash:NThash:::")
            if ':' in line and ('aad3b435b51404eeaad3b435b51404ee' in line or 
                              '$NT$' in line or 
                              'NTLM' in line.lower()):
                
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
        self.show_banner()
        print(tag_minus() + f"EXTRACTED WINDOWS USERS")
        print(c_yellow(f"SAM: {self.sam_file}"))
        print(c_yellow(f"SYSTEM: {self.system_file}"))
        print()
        
        if not self.users:
            print(tag_exclamation() + "No users with password hashes found!")
            return False
        
        print(c_cyan(f"Found {len(self.users)} user(s) with NTLM hashes:"))
        print()
        print(c_yellow("ID  USERNAME        RID     LM HASH                          NT HASH"))
        print(c_yellow("--  --------        ---     -------                          -------"))
        
        for idx, user in enumerate(self.users, 1):
            username = user['username']
            rid = user['rid']
            lm_hash = user['lm_hash']
            nt_hash = user['nt_hash']
            
            # Truncate hashes for display
            if lm_hash == 'aad3b435b51404eeaad3b435b51404ee':
                lm_display = "(empty)"
            elif len(lm_hash) > 8:
                lm_display = lm_hash[:8] + "..."
            else:
                lm_display = lm_hash
            
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
                username_display = c_green(username_display)
                lm_display = c_green(lm_display)
                nt_display = c_green(nt_display)
            
            print(f"{idx:2d}  {username_display:15} {rid:6}  {lm_display:32}  {nt_display}")
        
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
        cmd.append(self.hash_file)
        
        # Add wordlist
        cmd.append("--wordlist=" + wordlist)
        
        # Add rules
        if rule_choice == "2":
            cmd.append("--rules")
        elif rule_choice == "3":
            cmd.append("--rules=All")
        
        # Specify format for Windows NTLM hashes
        cmd.append("--format=NT")
        
        return self.run_john_command(cmd, "Wordlist Attack")
    
    def run_single_mode(self):
        """Run single crack mode"""
        if not self.hash_file or not os.path.exists(self.hash_file):
            print(tag_exclamation() + "Hash file not found or not created!")
            return False
        
        cmd = [self.john_path, self.hash_file, "--single", "--format=NT"]
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
        
        cmd = [self.john_path, self.hash_file, "--incremental=" + charset, "--format=NT"]
        return self.run_john_command(cmd, f"Incremental Mode ({charset})")
    
    def show_results(self):
        """Show cracked passwords"""
        self.show_banner()
        print(tag_asterisk() + "Checking for cracked passwords...")
        
        if not self.hash_file or not os.path.exists(self.hash_file):
            print(tag_exclamation() + "Hash file not found!")
            return
        
        cmd = [self.john_path, self.hash_file, "--show", "--format=NT"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.stdout:
                print()
                print(tag_minus() + "CRACKED PASSWORDS RESULTS")
                print()
                
                # Parse the output and update users
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if ':' in line and not line.startswith(' '):
                        parts = line.split(':')
                        if len(parts) >= 2:
                            username = parts[0]
                            password = parts[1]
                            
                            # Update user in our list
                            for user in self.users:
                                if user['username'] == username:
                                    user['cracked'] = True
                                    user['password'] = password
                                    break
                            
                            print(c_cyan(username + ":") + c_green(password))
                        else:
                            print(c_cyan(line))
                    else:
                        print(line)
                
                # Check if any passwords were actually cracked
                cracked_count = sum(1 for user in self.users if user.get('cracked', False))
                if cracked_count > 0:
                    # Save to file
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    results_file = f"cracked_windows_passwords_{timestamp}.txt"
                    
                    with open(results_file, "w") as f:
                        f.write(f"Source SAM: {self.sam_file}\n")
                        f.write(f"Source SYSTEM: {self.system_file}\n")
                        f.write(f"Time: {time.ctime()}\n")
                        f.write(f"Cracked {cracked_count} of {len(self.users)} users\n")
                        f.write("=" * 50 + "\n")
                        
                        for user in self.users:
                            if user.get('cracked', False):
                                f.write(f"{user['username']}:{user['password']}\n")
                    
                    print(tag_minus() + f"Results saved to: {results_file}")
                else:
                    print(tag_minus() + "No passwords cracked yet")
            else:
                print(tag_minus() + "No passwords cracked yet")
                
        except Exception as e:
            print(tag_x() + f"Error showing results: {e}")
    
    def select_attack_mode(self):
        """Select attack mode"""
        self.show_banner()
        
        if self.selected_user:
            print(tag_asterisk() + f"Target User: " + c_yellow(f"{self.selected_user['username']}"))
            print(tag_asterisk() + f"RID: " + c_cyan(f"{self.selected_user['rid']}"))
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
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                print(tag_info() + f"Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                print(tag_exclamation() + f"Error cleaning up: {e}")
    
    def main_loop(self):
        """Main program loop"""
        if not self.check_tools():
            print(tag_exclamation() + "Please install missing tools and try again")
            input(tag_gt() + "Press Enter to exit...")
            return
        
        while True:
            self.show_banner()
            print(tag_minus() + "SELECT FILE SOURCE")
            
            print(c_yellow("[1]") + f" Auto-detect SAM/SYSTEM files in current directory")
            print(c_yellow("[2]") + " Enter custom file paths")
            print(c_yellow("[3]") + " Exit")
            
            try:
                choice = int(input(tag_gt() + "Select option (1-3): "))
            except ValueError:
                print(tag_exclamation() + "Invalid choice")
                continue
            
            if choice == 1:
                # Auto-detect
                if not self.auto_detect_files():
                    input(tag_gt() + "Press Enter to continue...")
                    continue
            elif choice == 2:
                # Custom files
                if not self.get_custom_files():
                    input(tag_gt() + "Press Enter to continue...")
                    continue
            elif choice == 3:
                # Exit
                print(tag_asterisk() + "Goodbye!")
                self.cleanup()
                return
            else:
                continue
            
            # Extract hashes
            if not self.extract_hashes():
                print(tag_exclamation() + "Failed to extract hashes")
                input(tag_gt() + "Press Enter to continue...")
                continue
            
            # Display users
            if not self.display_users():
                input(tag_gt() + "Press Enter to continue...")
                continue
            
            # Select user to crack
            if not self.select_user():
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
    try:
        cracker = WindowsPasswordCracker()
        cracker.main_loop()
    except KeyboardInterrupt:
        print(c_red("\n\n[x]") + " Program stopped by user")
        if 'cracker' in locals():
            cracker.cleanup()
    except Exception as e:
        print(c_red("\n[x]") + f" Error: {e}")
        import traceback
        traceback.print_exc()
        if 'cracker' in locals():
            cracker.cleanup()

if __name__ == "__main__":
    main()
