#!/usr/bin/env python3
"""
Wi-Fi Handshake Password Cracker - Sub-component for Sokonalysis
Complete workflow using aircrack-ng and hccap2john for hash extraction
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
import json
import platform
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

class WiFiCracker:
    def __init__(self):
        self.john_path = "john"
        self.aircrack_path = "aircrack-ng"
        self.capture_file = None
        self.hash_content = None
        self.default_wordlist = "wordlist.txt"
        self.rockyou_path = "/usr/share/wordlists/rockyou.txt"
        self.current_dir = os.getcwd()
        self.target_networks = []
        self.hccap2john_path = self.find_hccap2john()
        self.cracked_password = None
        self.pot_file = os.path.expanduser("~/.john/john.pot")
        self.john_session_dir = os.path.expanduser("~/.john/sessions")
        
    def find_hccap2john(self):
        """Find hccap2john in common locations"""
        common_paths = [
            "/usr/sbin/hccap2john",
            "/usr/bin/hccap2john",
            "/usr/share/john/hccap2john",
            "/usr/share/john/hccap2john.py",
            "/usr/local/bin/hccap2john",
            "hccap2john",
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        # Try to find using system command
        try:
            cmd = ["which", "hccap2john"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except:
            pass
        
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
    
    def check_pot_file(self):
        """Check if password is already cracked in pot file"""
        if not self.hash_content:
            return None
        
        try:
            # Create a temporary file just for the check
            with tempfile.NamedTemporaryFile(mode='w', suffix='.john', delete=False) as f:
                f.write(self.hash_content)
                temp_hash_file = f.name
            
            # Run john --show to get cracked passwords
            cmd = [self.john_path, temp_hash_file, "--show", "--format=wpapsk"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Clean up temp file
            try:
                os.unlink(temp_hash_file)
            except:
                pass
            
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if ':' in line and not line.startswith(' '):
                        parts = line.split(':', 1)
                        if len(parts) >= 2:
                            password = parts[1].strip()
                            # Clean up password - remove extra info after colon
                            if ':' in password:
                                password = password.split(':')[0]
                            if password and not password.startswith('?'):
                                return password
        except Exception as e:
            pass
        
        return None
    
    def remove_pot_file(self):
        """Remove pot file in case of corruption"""
        if os.path.exists(self.pot_file):
            try:
                os.remove(self.pot_file)
                print(tag_plus() + "Pot file removed successfully")
                return True
            except Exception as e:
                print(tag_x() + f"Failed to remove pot file: {e}")
                return False
        else:
            print(tag_minus() + "Pot file does not exist")
            return False
    
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
            self.show_error("John the Ripper not found!")
            return False
        
        # Check for aircrack-ng
        try:
            result = subprocess.run([self.aircrack_path, "--help"], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode not in [0, 1]:
                self.show_error("Aircrack-ng not working properly")
                return False
        except FileNotFoundError:
            self.show_error("Aircrack-ng not found!")
            return False
        
        # Check for hccap2john
        if not self.hccap2john_path:
            self.show_error("hccap2john not found!")
            return False
        
        # Check for wordlist
        wordlist_paths = [
            self.default_wordlist,
            self.rockyou_path,
            "wordlists/wordlist.txt",
            "../wordlists/wordlist.txt"
        ]
        
        found = False
        for path in wordlist_paths:
            if os.path.exists(path):
                self.default_wordlist = path
                found = True
                break
        
        if not found:
            self.show_error("No suitable wordlist found!")
            return False
        
        return True
    
    def count_words(self, filepath):
        """Count words in a file"""
        if not os.path.exists(filepath):
            return 0
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for line in f if line.strip())
        except:
            try:
                with open(filepath, 'r', encoding='latin-1') as f:
                    return sum(1 for line in f if line.strip())
            except:
                return 0
    
    def convert_cap_to_hccap(self, cap_file):
        """Convert .cap to .hccap using aircrack-ng"""
        try:
            base_name = os.path.splitext(cap_file)[0]
            hccap_file = base_name + ".hccap"
            
            if os.path.exists(hccap_file):
                return hccap_file
            
            cmd = [self.aircrack_path, cap_file, "-J", base_name]
            
            print(tag_gt() + "Running: " + CYAN + f"{' '.join(cmd)}" + RESET)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                if os.path.exists(hccap_file):
                    size = os.path.getsize(hccap_file)
                    print(tag_plus() + f"Created: {hccap_file} ({size} bytes)")
                    return hccap_file
                else:
                    hccapx_file = base_name + ".hccapx"
                    if os.path.exists(hccapx_file):
                        size = os.path.getsize(hccapx_file)
                        print(tag_plus() + f"Created: {hccapx_file} ({size} bytes)")
                        return hccapx_file
                    else:
                        self.show_error("No .hccap/.hccapx file created")
                        return None
            else:
                self.show_error("Aircrack-ng failed")
                return None
                
        except Exception as e:
            self.show_error(f"Error converting file: {e}")
            return None
    
    def extract_hash_from_hccap(self, hccap_file):
        """Extract John-compatible hash from hccap file"""
        try:
            # Run hccap2john
            if self.hccap2john_path.endswith('.py'):
                cmd = ["python3", self.hccap2john_path, hccap_file]
            else:
                cmd = [self.hccap2john_path, hccap_file]
            
            print(tag_gt() + "Running: " + CYAN + f"{' '.join(cmd)}" + RESET)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Check output regardless of return code
            hash_output = result.stdout.strip()
            
            if hash_output:
                # Check for valid WPA hash patterns
                if any(pattern in hash_output for pattern in ["$WPAPSK$", "WPA*", "*", ":", "$HEX"]):
                    return hash_output
                else:
                    self.show_error("Output doesn't look like a valid WPA hash")
                    return None
            else:
                self.show_error("No output from hccap2john")
                return None
                
        except Exception as e:
            self.show_error(f"Error extracting hash: {e}")
            return None
    
    def extract_hashes(self, capture_path):
        """Main workflow: .cap → .hccap → hash extraction"""
        if not os.path.exists(capture_path):
            self.show_error("File not found")
            return False
        
        try:
            # Determine file type
            file_ext = os.path.splitext(capture_path)[1].lower()
            
            if file_ext in ['.hccap', '.hccapx']:
                self.show_success("File is already in hccap/hccapx format")
                hccap_file = capture_path
            else:
                hccap_file = self.convert_cap_to_hccap(capture_path)
                if not hccap_file:
                    return False
            
            # Extract hash using hccap2john
            hash_output = self.extract_hash_from_hccap(hccap_file)
            if not hash_output:
                return False
            
            # Store hash content in memory instead of saving to file
            self.hash_content = hash_output
            
            # Parse network information
            self.parse_hash_info(hash_output)
            
            return True
            
        except Exception as e:
            self.show_error(f"Error in extraction workflow: {e}")
        
        return False
    
    def parse_hash_info(self, hash_output):
        """Parse network information from hash output"""
        self.target_networks = []
        
        try:
            lines = hash_output.split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    # Extract ESSID from hash
                    if "$WPAPSK$" in line:
                        parts = line.split("$WPAPSK$")
                        if len(parts) >= 2:
                            essid = parts[0].strip()
                            network = {
                                'ESSID': essid,
                                'BSSID': 'Extracted from hash',
                                'hash_present': True
                            }
                            self.target_networks.append(network)
                    elif "*" in line:
                        parts = line.split("*")
                        if len(parts) >= 2:
                            essid = parts[0]
                            network = {
                                'ESSID': essid,
                                'BSSID': parts[1][:12] if len(parts[1]) >= 12 else 'Unknown',
                                'hash_present': True
                            }
                            self.target_networks.append(network)
            
            if self.target_networks:
                for i, network in enumerate(self.target_networks, 1):
                    essid = network.get('ESSID', 'Unknown')
                    print(YELLOW + f"[{i}]" + RESET + f" {essid}::: " + CYAN + "(Extracted from hash)" + RESET)
            else:
                self.show_info("Hash extracted successfully")
            
        except Exception as e:
            self.show_error(f"Error parsing network info: {e}")
    
    def list_capture_files(self):
        """List Wi-Fi capture files in current directory"""
        extensions = ['.pcap', '.pcapng', '.cap', '.hccap', '.hccapx']
        
        captures = []
        
        print(CYAN + "\n📁" + RESET + " Current Directory: " + YELLOW + f"{self.current_dir}" + RESET)
        print(YELLOW + "📡" + RESET + " Place Wi-Fi capture/hash files in this directory\n")
        print(BLUE + "\n__________________ " + GREEN + "Available Handshake Files" + BLUE + " ____________________\n")
        
        idx = 1
        for file in sorted(os.listdir('.')):
            if any(file.lower().endswith(ext) for ext in extensions):
                if os.path.isfile(file):
                    size = os.path.getsize(file)
                    if size < 1024:
                        size_str = f"{size}B"
                    elif size < 1024*1024:
                        size_str = f"{size/1024:.1f}KB"
                    else:
                        size_str = f"{size/(1024*1024):.1f}MB"
                    
                    captures.append(file)
                    file_type = "HCCAP" if file.lower().endswith(('.hccap', '.hccapx')) else "CAPTURE"
                    print(YELLOW + f"[{idx}]" + RESET + f" {file} " + CYAN + f"({size_str})" + RESET + MAGENTA + f" [{file_type}]" + RESET)
                    idx += 1
        
        return captures
    
    def select_capture_file(self):
        """Let user select a capture file"""
        captures = self.list_capture_files()
        
        if not captures:
            self.show_error("No Wi-Fi capture/hash files found!")
            print()
            print(YELLOW + "[1]" + RESET + " Enter file path manually")
            print(YELLOW + "[2]" + RESET + " Exit")
            print(BLUE + "_________________________________________________________________")
            print()
            
            choice = input(tag_gt() + "Select option (1-2): ").strip()
            if choice == "1":
                path = input(tag_gt() + "Enter full path: ").strip()
                if os.path.exists(path):
                    return path
                else:
                    self.show_error("File not found")
                    return None
            return None
        
        print(YELLOW + f"[{len(captures)+1}]" + RESET + " Enter custom path")
        print(YELLOW + f"[{len(captures)+2}]" + RESET + " Exit")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            choice = int(input(tag_gt() + f"Select file (1-{len(captures)+2}): "))
            
            if 1 <= choice <= len(captures):
                return captures[choice-1]
            elif choice == len(captures) + 1:
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
        print()
        print(BLUE + "\n____________________________ " + GREEN + "Options" + BLUE + " ____________________________")
        print()

        print(YELLOW + "[1]" + RESET + " Wordlist Attack (using default wordlist)")
        print(YELLOW + "[2]" + RESET + " Wordlist Attack (custom wordlist)")
        print(YELLOW + "[3]" + RESET + " Single Crack Mode")
        print(YELLOW + "[4]" + RESET + " Incremental Mode (brute force)")
        print(YELLOW + "[5]" + RESET + " Mask Attack (advanced brute force)")
        print(YELLOW + "[6]" + RESET + " Show cracked passwords")
        print(YELLOW + "[7]" + RESET + " Remove Pot File (if corrupted)")
        print(YELLOW + "[8]" + RESET + " Select different file")
        print(YELLOW + "[9]" + RESET + " Exit")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            return int(input(tag_gt() + "Select option (1-9): "))
        except:
            self.show_error("Please enter a number")
            return None
    
    def get_wordlist_info(self, wordlist_path):
        """Get information about a wordlist"""
        if not os.path.exists(wordlist_path):
            self.show_error(f"Wordlist not found: {wordlist_path}")
            return False
        
        wordcount = self.count_words(wordlist_path)
        if wordcount == 0:
            self.show_error(f"Wordlist is empty: {wordlist_path}")
            return False
        
        return True
    
    def run_john_command(self, cmd, attack_name):
        """Run a John the Ripper command"""
        print()
        print(tag_gt() + "Command: " + CYAN + f"{' '.join(cmd)}" + RESET)
        print()
        print(tag_asterisk() + "Starting attack... " + RED + "Press Ctrl+C to stop" + RESET)
        print()
        
        try:
            start = time.time()
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Capture the output to find the password
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    # Check for cracked password pattern
                    if "cracked" in line.lower() and self.target_networks:
                        # Extract password from John's output (format: "password (ESSID)")
                        match = re.search(r'^([^\s]+)\s+\(', line.strip())
                        if match:
                            self.cracked_password = match.group(1)
            
            process.wait()
            elapsed = time.time() - start
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
        wordlist = custom_wordlist or self.default_wordlist
        
        if not self.get_wordlist_info(wordlist):
            return False
        
        print()
        print(BLUE + "_____________________________ " + GREEN + "Rules" + BLUE + " _____________________________")
        print()
        print(YELLOW + "[1]" + RESET + " No rules (fastest)")
        print(YELLOW + "[2]" + RESET + " Standard rules (recommended)")
        print(YELLOW + "[3]" + RESET + " All rules (slow but thorough)")
        print(BLUE + "_________________________________________________________________")
        print()
        
        choice = input(tag_gt() + "Select rule option (1-3, default=2): ").strip() or "2"
        
        # Create a temporary file for the hash
        with tempfile.NamedTemporaryFile(mode='w', suffix='.john', delete=False) as f:
            f.write(self.hash_content)
            temp_hash_file = f.name
        
        cmd = [self.john_path, temp_hash_file, "--format=wpapsk"]
        cmd.append("--wordlist=" + wordlist)
        
        if choice == "2":
            cmd.append("--rules")
        elif choice == "3":
            cmd.append("--rules=All")
        
        # Add session name
        session_name = os.path.splitext(os.path.basename(self.capture_file))[0]
        cmd.append("--session=" + session_name)
        
        result = self.run_john_command(cmd, "Wordlist Attack")
        
        # Clean up temp file
        try:
            os.unlink(temp_hash_file)
        except:
            pass
        
        return result
    
    def run_single_mode(self):
        """Run single crack mode"""
        # Create a temporary file for the hash
        with tempfile.NamedTemporaryFile(mode='w', suffix='.john', delete=False) as f:
            f.write(self.hash_content)
            temp_hash_file = f.name
        
        cmd = [self.john_path, temp_hash_file, "--single", "--format=wpapsk"]
        session_name = os.path.splitext(os.path.basename(self.capture_file))[0]
        cmd.append("--session=" + session_name + "_single")
        
        result = self.run_john_command(cmd, "Single Crack Mode")
        
        # Clean up temp file
        try:
            os.unlink(temp_hash_file)
        except:
            pass
        
        return result
    
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
        
        # Create a temporary file for the hash
        with tempfile.NamedTemporaryFile(mode='w', suffix='.john', delete=False) as f:
            f.write(self.hash_content)
            temp_hash_file = f.name
        
        cmd = [self.john_path, temp_hash_file, "--incremental=" + mode, "--format=wpapsk"]
        session_name = os.path.splitext(os.path.basename(self.capture_file))[0]
        cmd.append("--session=" + session_name + "_inc_" + mode.lower())
        
        result = self.run_john_command(cmd, f"Incremental Mode ({mode})")
        
        # Clean up temp file
        try:
            os.unlink(temp_hash_file)
        except:
            pass
        
        return result
    
    def run_mask_attack(self):
        """Run mask attack"""
        print()
        print(BLUE + "________________________ " + GREEN + "Mask Patterns" + BLUE + " ________________________")
        print()
        print(YELLOW + "[1]" + RESET + " 8-digit phone number (?d?d?d?d?d?d?d?d)")
        print(YELLOW + "[2]" + RESET + " 10-digit phone number (?d?d?d?d?d?d?d?d?d?d)")
        print(YELLOW + "[3]" + RESET + " Common pattern: 8 chars with first capital (?u?l?l?l?l?l?l?l)")
        print(YELLOW + "[4]" + RESET + " Custom mask pattern")
        print(YELLOW + "[5]" + RESET + " Cancel")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            choice = int(input(tag_gt() + "Select pattern (1-5): "))
            if choice == 5:
                return False
        except:
            self.show_error("Invalid choice")
            return False
        
        masks = {
            1: "?d?d?d?d?d?d?d?d",
            2: "?d?d?d?d?d?d?d?d?d?d",
            3: "?u?l?l?l?l?l?l?l"
        }
        
        if choice == 4:
            print()
            print(CYAN + "Mask syntax:" + RESET)
            print("  ?l = lowercase letter [a-z]")
            print("  ?u = uppercase letter [A-Z]")
            print("  ?d = digit [0-9]")
            print("  ?s = special character [!@#$%^&*()]")
            print()
            print(CYAN + "Examples:" + RESET)
            print("  ?u?l?l?l?d?d?d?d = Capital + 3 letters + 4 digits")
            print("  ?d?d?d?d?d?d?d?d = 8 digits")
            print()
            mask = input(tag_gt() + "Enter custom mask: ").strip()
            if not mask:
                self.show_error("No mask provided")
                return False
        elif choice in masks:
            mask = masks[choice]
        else:
            self.show_error("Invalid choice")
            return False
        
        print()
        self.show_info(f"Using mask: {mask}")
        self.show_warning("This may take a VERY long time!")
        confirm = input(tag_question() + "Continue with mask attack? (y/n): ").lower()
        
        if confirm != 'y':
            print(tag_asterisk() + "Cancelled")
            return False
        
        # Create a temporary file for the hash
        with tempfile.NamedTemporaryFile(mode='w', suffix='.john', delete=False) as f:
            f.write(self.hash_content)
            temp_hash_file = f.name
        
        cmd = [self.john_path, temp_hash_file, "--mask=" + mask, "--format=wpapsk"]
        session_name = os.path.splitext(os.path.basename(self.capture_file))[0]
        cmd.append("--session=" + session_name + "_mask")
        
        result = self.run_john_command(cmd, f"Mask Attack ({mask})")
        
        # Clean up temp file
        try:
            os.unlink(temp_hash_file)
        except:
            pass
        
        return result
    
    def show_results(self):
        """Show cracked passwords"""
        print(tag_asterisk() + "Checking for cracked passwords...")
        print()
        
        # First check if we have a cracked password from the current session
        if self.cracked_password:
            print(BLUE + "_________________________________________________________________")
            print()
            print(tag_minus() + f"Cracked Password Results: " + GREEN + f"{self.cracked_password}" + RESET)
            print()
            print(BLUE + "_________________________________________________________________")
            
            # Save results to file
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"wifi_cracked_{timestamp}.txt"
            with open(filename, "w") as f:
                f.write(f"Capture File: {self.capture_file}\n")
                f.write(f"Time: {time.ctime()}\n")
                f.write(f"Cracked Password: {self.cracked_password}\n")
                if self.target_networks:
                    f.write("Target Networks:\n")
                    for network in self.target_networks:
                        f.write(f"  - {network.get('ESSID', 'Unknown')}\n")
            
            print()
            print(tag_minus() + f" Results saved to: {filename}")
            print()
            print(BLUE + "_________________________________________________________________")
            return True
        
        # Check pot file for previously cracked passwords
        pot_password = self.check_pot_file()
        if pot_password:
            self.cracked_password = pot_password
            print(BLUE + "_________________________________________________________________")
            print()
            print(tag_minus() + f"Cracked Password Results: " + GREEN + f"{self.cracked_password}" + RESET)
            print()
            print(BLUE + "_________________________________________________________________")
            
            # Save results to file
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"wifi_cracked_{timestamp}.txt"
            with open(filename, "w") as f:
                f.write(f"Capture File: {self.capture_file}\n")
                f.write(f"Time: {time.ctime()}\n")
                f.write(f"Cracked Password: {self.cracked_password}\n")
                if self.target_networks:
                    f.write("Target Networks:\n")
                    for network in self.target_networks:
                        f.write(f"  - {network.get('ESSID', 'Unknown')}\n")
            
            print()
            print(tag_minus() + f" Results saved to: {filename}")
            print()
            print(BLUE + "_________________________________________________________________")
            return True
        else:
            print(tag_minus() + "No passwords cracked yet")
            print()
            print(BLUE + "_________________________________________________________________")
            return False
    
    def cleanup(self):
        """Clean up - nothing to clean since we don't use temp files for hashes"""
        pass
    
    def main_loop(self):
        """Main program loop - entry point for Sokonalysis sub-component"""
        # No banner - this is a sub-component
        
        if not self.check_tools():
            print(tag_exclamation() + "Please install missing tools and try again")
            return
        
        while True:
            self.capture_file = self.select_capture_file()
            if not self.capture_file:
                self.cleanup()
                return
            
            print()
            if not self.extract_hashes(self.capture_file):
                continue
            
            while True:
                choice = self.select_attack_mode()
                
                if choice == 1:
                    self.run_wordlist_attack()
                    self.show_results()
                    self.cleanup()
                    return
                elif choice == 2:
                    wl = input(tag_gt() + "Enter path to custom wordlist: ").strip()
                    if wl:
                        if os.path.exists(wl):
                            self.run_wordlist_attack(wl)
                            self.show_results()
                            self.cleanup()
                            return
                        else:
                            self.show_error(f"Wordlist not found: {wl}")
                    else:
                        self.show_error("No wordlist specified")
                elif choice == 3:
                    self.run_single_mode()
                    self.show_results()
                    self.cleanup()
                    return
                elif choice == 4:
                    self.run_incremental_mode()
                    self.show_results()
                    self.cleanup()
                    return
                elif choice == 5:
                    self.run_mask_attack()
                    self.show_results()
                    self.cleanup()
                    return
                elif choice == 6:
                    self.show_results()
                    print()
                elif choice == 7:
                    self.remove_pot_file()
                    print()
                elif choice == 8:
                    self.cleanup()
                    break
                elif choice == 9:
                    self.cleanup()
                    return
                else:
                    self.show_error("Invalid choice")

def main():
    """Main function - kept for standalone testing but not used in Sokonalysis"""
    try:
        # Enable virtual terminal processing on Windows
        if platform.system() == "Windows":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except:
                pass
        
        cracker = WiFiCracker()
        cracker.main_loop()
        
    except KeyboardInterrupt:
        print(RED + "\n[x] Program stopped by user" + RESET)
    except Exception as e:
        print(RED + f"\n[x] Error: {e}" + RESET)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
