#!/usr/bin/env python3
"""
Wi-Fi Handshake Password Cracker
Complete workflow using aircrack-ng and hccap2john for hash extraction
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
from datetime import datetime

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
    def tag_wifi(): return Fore.CYAN + "[📶]" + Style.RESET_ALL + " "
    
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
    def tag_wifi(): return CYAN + "[📶]" + RESET + " "

class WiFiCracker:
    def __init__(self):
        self.john_path = "john"
        self.aircrack_path = "aircrack-ng"
        self.capture_file = None
        self.hash_file = None
        self.default_wordlist = "wordlist.txt"
        self.rockyou_path = "/usr/share/wordlists/rockyou.txt"
        self.current_dir = os.getcwd()
        self.target_networks = []
        self.john_format = "wpapsk"
        self.hccap2john_path = self.find_hccap2john()
        
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
    
    def clear_screen(self):
        """Clear screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def show_banner(self):
        """Show colorful banner"""
        self.clear_screen()
        print(tag_wifi() + c_cyan("WI-FI HANDSHAKE PASSWORD CRACKER"))
        print(c_yellow("=" * 50))
        print(c_cyan("Workflow: .cap → .hccap → hccap2john → John"))
        print()
    
    def check_tools(self):
        """Check if required tools are available"""
        self.show_banner()
        print(tag_asterisk() + "Checking for required tools...")
        
        tools_available = True
        
        # Check for John the Ripper
        try:
            result = subprocess.run([self.john_path, "--version"], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode in [0, 1]:
                version_line = result.stdout.split('\n')[0] if result.stdout else "John the Ripper"
                print(tag_plus() + f"John the Ripper: Found ({version_line[:50]}...)")
                
                result = subprocess.run([self.john_path, "--list=formats"], 
                                      capture_output=True, text=True, timeout=2)
                if "wpapsk" in result.stdout:
                    print(tag_plus() + "WPA-PSK format support: Available")
                else:
                    print(tag_exclamation() + "WPA-PSK format not found in John")
                    tools_available = False
            else:
                print(tag_exclamation() + "John the Ripper not working properly")
                tools_available = False
        except FileNotFoundError:
            print(tag_exclamation() + "John the Ripper not found!")
            print(c_yellow("    Install with: sudo apt install john"))
            tools_available = False
        
        # Check for aircrack-ng
        try:
            result = subprocess.run(["which", "aircrack-ng"], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout.strip():
                self.aircrack_path = result.stdout.strip()
                print(tag_plus() + f"Aircrack-ng: Found at '{self.aircrack_path}'")
            else:
                print(tag_exclamation() + "Aircrack-ng not found!")
                print(c_yellow("    Install with: sudo apt install aircrack-ng"))
                tools_available = False
        except:
            print(tag_exclamation() + "Aircrack-ng not found!")
            print(c_yellow("    Install with: sudo apt install aircrack-ng"))
            tools_available = False
        
        # Check for hccap2john
        if not self.hccap2john_path:
            print(tag_exclamation() + "hccap2john not found!")
            print(c_yellow("    It's included with John the Ripper"))
            print(c_yellow("    Common locations: /usr/sbin/hccap2john, /usr/bin/hccap2john"))
            tools_available = False
        else:
            print(tag_plus() + f"hccap2john: Found at '{self.hccap2john_path}'")
        
        # Check for wordlist
        wordlist_found = False
        for wordlist_path in [self.default_wordlist, self.rockyou_path]:
            if os.path.exists(wordlist_path):
                wordcount = self.count_words(wordlist_path)
                if wordcount:
                    print(tag_plus() + f"Wordlist: '{wordlist_path}' ({wordcount} words)")
                    wordlist_found = True
                    if wordlist_path == self.rockyou_path:
                        self.default_wordlist = self.rockyou_path
                    break
        
        if not wordlist_found:
            print(tag_exclamation() + "No suitable wordlist found!")
            print(c_yellow("    Please create a file named '") + c_cyan("wordlist.txt") + 
                  c_yellow("' or install rockyou.txt"))
            tools_available = False
        
        return tools_available
    
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
            print(tag_minus() + f"Converting {cap_file} to .hccap format...")
            
            base_name = os.path.splitext(cap_file)[0]
            hccap_file = base_name + ".hccap"
            
            if os.path.exists(hccap_file):
                print(tag_plus() + f".hccap file already exists: {hccap_file}")
                return hccap_file
            
            cmd = [self.aircrack_path, cap_file, "-J", base_name]
            
            print(tag_gt() + f"Running: {' '.join(cmd)}")
            
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
                        print(tag_exclamation() + f"No .hccap/.hccapx file created")
                        return None
            else:
                print(tag_exclamation() + f"Aircrack-ng failed")
                return None
                
        except Exception as e:
            print(tag_x() + f"Error converting file: {e}")
            return None
    
    def extract_hash_from_hccap(self, hccap_file):
        """Extract John-compatible hash from hccap file"""
        try:
            print(tag_minus() + f"Extracting hash from {hccap_file}...")
            
            # Run hccap2john
            if self.hccap2john_path.endswith('.py'):
                cmd = ["python3", self.hccap2john_path, hccap_file]
            else:
                cmd = [self.hccap2john_path, hccap_file]
            
            print(tag_gt() + f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Check output regardless of return code
            hash_output = result.stdout.strip()
            
            if hash_output:
                # Check for valid WPA hash patterns
                if any(pattern in hash_output for pattern in ["$WPAPSK$", "WPA*", "*", ":", "$HEX"]):
                    print(tag_plus() + "Hash extracted successfully!")
                    print(c_cyan("Hash format: ") + hash_output[:80] + "...")
                    return hash_output
                else:
                    print(tag_exclamation() + "Output doesn't look like a valid WPA hash")
                    print(c_yellow(f"Output: {hash_output[:100]}"))
                    return None
            else:
                print(tag_exclamation() + "No output from hccap2john")
                if result.stderr:
                    print(c_red(f"Error: {result.stderr[:200]}"))
                return None
                
        except Exception as e:
            print(tag_x() + f"Error extracting hash: {e}")
            return None
    
    def extract_hashes(self, capture_path):
        """Main workflow: .cap → .hccap → hash extraction"""
        self.show_banner()
        print(tag_asterisk() + f"Processing capture file: {capture_path}")
        
        if not os.path.exists(capture_path):
            print(tag_exclamation() + f"File not found: {capture_path}")
            return False
        
        # Create temporary directory for hash files
        temp_dir = tempfile.mkdtemp(prefix="wifi_hash_")
        self.hash_file = os.path.join(temp_dir, "wifi_hash.john")
        
        try:
            # Determine file type
            file_ext = os.path.splitext(capture_path)[1].lower()
            
            if file_ext in ['.hccap', '.hccapx']:
                print(tag_plus() + "File is already in hccap/hccapx format")
                hccap_file = capture_path
            else:
                hccap_file = self.convert_cap_to_hccap(capture_path)
                if not hccap_file:
                    print(tag_exclamation() + "Failed to convert capture file")
                    return False
            
            # Extract hash using hccap2john
            hash_output = self.extract_hash_from_hccap(hccap_file)
            if not hash_output:
                print(tag_exclamation() + "Failed to extract hash")
                return False
            
            # Save hash to file for John
            with open(self.hash_file, 'w') as f:
                f.write(hash_output)
            
            print(tag_plus() + f"Hash saved to temporary file")
            
            # Parse network information
            self.parse_hash_info(hash_output)
            
            return True
            
        except Exception as e:
            print(tag_x() + f"Error in extraction workflow: {e}")
        
        # Cleanup on failure
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
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
                print(tag_minus() + f"Found {len(self.target_networks)} target network(s):")
                for i, network in enumerate(self.target_networks, 1):
                    essid = network.get('ESSID', 'Unknown')
                    bssid = network.get('BSSID', 'Unknown')
                    print(c_yellow(f"  [{i}]") + f" {essid} ({bssid})")
            else:
                print(tag_minus() + "Hash extracted successfully")
            
        except Exception as e:
            print(tag_exclamation() + f"Error parsing network info: {e}")
    
    def list_capture_files(self):
        """List Wi-Fi capture files in current directory"""
        extensions = ['.pcap', '.pcapng', '.cap', '.hccap', '.hccapx']
        
        captures = []
        
        print(c_cyan("\n📁") + " Current Directory: " + c_yellow(self.current_dir))
        print(c_yellow("📡") + " Place Wi-Fi capture/hash files in this directory\n")
        print(tag_minus() + "AVAILABLE FILES")
        
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
                    print(c_yellow(f"[{idx}]") + f" {file}" + c_cyan(f" ({size_str})") + c_magenta(f" [{file_type}]"))
                    idx += 1
        
        return captures
    
    def select_capture_file(self):
        """Let user select a capture file"""
        self.show_banner()
        
        print(c_yellow("📁") + f" Current working directory: {self.current_dir}")
        
        captures = self.list_capture_files()
        
        if not captures:
            print(tag_exclamation() + "No Wi-Fi capture/hash files found!")
            print(c_yellow("\n💡") + f" Place files in: {self.current_dir}")
            print()
            print(tag_minus() + "FILE SELECTION OPTIONS")
            print(c_yellow("[1]") + " Enter file path manually")
            print(c_yellow("[2]") + " Exit")
            
            choice = input(tag_gt() + "Select option (1-2): ").strip()
            if choice == "1":
                path = input(tag_gt() + "Enter full path to file: ").strip()
                if os.path.exists(path):
                    return path
                else:
                    print(tag_exclamation() + f"File not found: {path}")
                    input(tag_gt() + "Press Enter to continue...")
                    return None
            else:
                return None
        
        print(c_yellow(f"[{len(captures)+1}]") + " Enter custom path")
        print(c_yellow(f"[{len(captures)+2}]") + " Exit")
        
        try:
            choice = int(input(tag_gt() + f"Select file (1-{len(captures)+2}): "))
            
            if 1 <= choice <= len(captures):
                selected = captures[choice-1]
                print(tag_minus() + f"Selected: {selected}")
                return selected
            elif choice == len(captures) + 1:
                path = input(tag_gt() + "Enter full path to file: ").strip()
                if os.path.exists(path):
                    print(tag_minus() + f"Selected: {path}")
                    return path
                else:
                    print(tag_exclamation() + f"File not found: {path}")
                    input(tag_gt() + "Press Enter to continue...")
                    return None
            else:
                return None
                
        except ValueError:
            print(tag_exclamation() + "Please enter a valid number")
            input(tag_gt() + "Press Enter to continue...")
            return None
    
    def select_attack_mode(self):
        """Select attack mode"""
        self.show_banner()
        print(tag_asterisk() + "File: " + c_yellow(f"{self.capture_file}"))
        if self.target_networks:
            print(tag_asterisk() + f"Networks: {len(self.target_networks)} target(s)")
            for network in self.target_networks:
                essid = network.get('ESSID', 'Unknown')
                bssid = network.get('BSSID', 'Unknown')
                print(c_cyan(f"    • {essid} ({bssid})"))
        print()
        print(tag_minus() + "SELECT ATTACK MODE")

        print(c_yellow("[1]") + " Wordlist Attack (using default wordlist)")
        print(c_yellow("[2]") + " Wordlist Attack (custom wordlist)")
        print(c_yellow("[3]") + " Single Crack Mode")
        print(c_yellow("[4]") + " Incremental Mode (brute force)")
        print(c_yellow("[5]") + " Mask Attack (advanced brute force)")
        print(c_yellow("[6]") + " Show cracked passwords")
        print(c_yellow("[7]") + " Select different file")
        print(c_yellow("[8]") + " Exit")
        
        try:
            choice = int(input(tag_gt() + "Select option (1-8): "))
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
        print(tag_asterisk() + f"{attack_name} on: {self.capture_file}")
        
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
            
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    if "Press 'q' or Ctrl-C to abort" in line:
                        print(c_yellow(line.strip()))
                    elif "session aborted" in line.lower():
                        print(c_red(line.strip()))
                    elif "password hash cracked" in line.lower() or "cracked" in line.lower():
                        print(tag_plus() + " " + line.strip())
                    elif "guesses:" in line.lower():
                        print(c_cyan(line.strip()))
                    elif "remaining:" in line.lower():
                        print(c_yellow(line.strip()))
                    elif "LOADED" in line:
                        print(c_green(line.strip()))
                    elif "No password hashes loaded" in line:
                        print(c_red(line.strip()))
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
            return False
        
        return True
    
    def run_wordlist_attack(self, custom_wordlist=None):
        """Run wordlist attack"""
        wordlist = custom_wordlist if custom_wordlist else self.default_wordlist
        
        if not self.get_wordlist_info(wordlist):
            return False
        
        print()
        print(tag_minus() + "RULE OPTIONS")
        print(c_yellow("[1]") + " No rules (fastest)")
        print(c_yellow("[2]") + " Standard rules (recommended)")
        print(c_yellow("[3]") + " All rules (slow but thorough)")
        
        rule_choice = input(tag_gt() + "Select rule option (1-3, default=2): ").strip() or "2"
        
        cmd = [self.john_path, self.hash_file, "--format=wpapsk"]
        cmd.append("--wordlist=" + wordlist)
        
        if rule_choice == "2":
            cmd.append("--rules")
        elif rule_choice == "3":
            cmd.append("--rules=All")
        
        session_name = os.path.splitext(os.path.basename(self.capture_file))[0]
        cmd.append("--session=" + session_name)
        
        return self.run_john_command(cmd, "Wordlist Attack")
    
    def run_single_mode(self):
        """Run single crack mode"""
        cmd = [self.john_path, self.hash_file, "--single", "--format=wpapsk"]
        session_name = os.path.splitext(os.path.basename(self.capture_file))[0]
        cmd.append("--session=" + session_name + "_single")
        return self.run_john_command(cmd, "Single Crack Mode")
    
    def run_incremental_mode(self):
        """Run incremental mode"""
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
        
        charsets = {1: "Digits", 2: "Lower", 3: "Alnum", 4: "All"}
        
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
        
        cmd = [self.john_path, self.hash_file, "--incremental=" + charset, "--format=wpapsk"]
        session_name = os.path.splitext(os.path.basename(self.capture_file))[0]
        cmd.append("--session=" + session_name + "_inc_" + charset.lower())
        return self.run_john_command(cmd, f"Incremental Mode ({charset})")
    
    def run_mask_attack(self):
        """Run mask attack"""
        print(tag_minus() + "MASK ATTACK PATTERNS")
        print(c_yellow("[1]") + " 8-digit phone number (?d?d?d?d?d?d?d?d)")
        print(c_yellow("[2]") + " 10-digit phone number (?d?d?d?d?d?d?d?d?d?d)")
        print(c_yellow("[3]") + " Common pattern: 8 chars with first capital (?u?l?l?l?l?l?l?l)")
        print(c_yellow("[4]") + " Custom mask pattern")
        print(c_yellow("[5]") + " Cancel")
        
        try:
            choice = int(input(tag_gt() + "Select pattern (1-5): "))
        except ValueError:
            print(tag_exclamation() + "Invalid choice")
            return False
        
        if choice == 5:
            return False
        
        masks = {
            1: "?d?d?d?d?d?d?d?d",
            2: "?d?d?d?d?d?d?d?d?d?d",
            3: "?u?l?l?l?l?l?l?l"
        }
        
        if choice == 4:
            print(c_yellow("\nMask syntax:"))
            print("  ?l = lowercase letter [a-z]")
            print("  ?u = uppercase letter [A-Z]")
            print("  ?d = digit [0-9]")
            print("  ?s = special character [!@#$%^&*()]")
            print(c_yellow("\nExamples:"))
            print("  ?u?l?l?l?d?d?d?d = Capital + 3 letters + 4 digits")
            print("  ?d?d?d?d?d?d?d?d = 8 digits")
            print()
            mask = input(tag_gt() + "Enter custom mask: ").strip()
            if not mask:
                print(tag_exclamation() + "No mask provided")
                return False
        elif choice in masks:
            mask = masks[choice]
        else:
            print(tag_exclamation() + "Invalid choice")
            return False
        
        print(tag_asterisk() + f"Using mask: {mask}")
        print(tag_exclamation() + "WARNING: This may take a long time!")
        
        confirm = input(tag_gt() + "Continue with mask attack? (y/n): ").lower()
        if confirm != 'y':
            print(tag_asterisk() + "Cancelled")
            return False
        
        cmd = [self.john_path, self.hash_file, "--mask=" + mask, "--format=wpapsk"]
        session_name = os.path.splitext(os.path.basename(self.capture_file))[0]
        cmd.append("--session=" + session_name + "_mask")
        return self.run_john_command(cmd, f"Mask Attack ({mask})")
    
    def show_results(self):
        """Show cracked passwords"""
        self.show_banner()
        print(tag_asterisk() + "Checking for cracked passwords...")
        
        cmd = [self.john_path, self.hash_file, "--show", "--format=wpapsk"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.stdout:
                print()
                print(tag_minus() + "CRACKED PASSWORDS RESULTS")
                print()
                
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if ':' in line and not line.startswith(' '):
                        parts = line.split(':')
                        if len(parts) >= 2:
                            essid_part = parts[0]
                            password = parts[1]
                            
                            if "*" in essid_part:
                                essid = essid_part.split('*')[0]
                                print(c_cyan(f"{essid}:") + c_green(password))
                            else:
                                print(c_cyan(parts[0] + ":") + c_green(password))
                        else:
                            print(c_cyan(line))
                    elif "password hash" in line and "cracked" in line:
                        print(c_green(line))
                    else:
                        print(line)
                
                if "password hash cracked" in result.stdout:
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    results_file = f"wifi_cracked_{timestamp}.txt"
                    
                    with open(results_file, "w") as f:
                        f.write(f"Capture File: {self.capture_file}\n")
                        f.write(f"Time: {time.ctime()}\n")
                        if self.target_networks:
                            f.write("Target Networks:\n")
                            for network in self.target_networks:
                                f.write(f"  - {network.get('ESSID', 'Unknown')}\n")
                        f.write("=" * 50 + "\n")
                        f.write(result.stdout)
                    
                    print(tag_minus() + f"Results saved to: {results_file}")
                    
                    print(c_yellow("\n💡") + " Cracked Password Summary:")
                    for line in lines:
                        if ':' in line and not line.startswith(' '):
                            parts = line.split(':')
                            if len(parts) >= 2:
                                essid = parts[0]
                                password = parts[1]
                                if '*' in essid:
                                    essid = essid.split('*')[0]
                                print(c_green(f"  WiFi: {essid} → Password: {password}"))
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
    
    def main_loop(self):
        """Main program loop"""
        if not self.check_tools():
            print(tag_exclamation() + "Please install missing tools and try again")
            input(tag_gt() + "Press Enter to exit...")
            return
        
        while True:
            self.capture_file = self.select_capture_file()
            if not self.capture_file:
                print(tag_asterisk() + "Exiting...")
                self.cleanup()
                break
            
            print(tag_asterisk() + "Processing file...")
            if not self.extract_hashes(self.capture_file):
                print(tag_exclamation() + "Failed to process file")
                input(tag_gt() + "Press Enter to continue...")
                continue
            
            while True:
                choice = self.select_attack_mode()
                
                if choice == 1:
                    self.run_wordlist_attack()
                    self.show_results()
                    input(tag_gt() + "Press Enter to continue...")
                elif choice == 2:
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
                    self.run_single_mode()
                    self.show_results()
                    input(tag_gt() + "Press Enter to continue...")
                elif choice == 4:
                    self.run_incremental_mode()
                    self.show_results()
                    input(tag_gt() + "Press Enter to continue...")
                elif choice == 5:
                    self.run_mask_attack()
                    self.show_results()
                    input(tag_gt() + "Press Enter to continue...")
                elif choice == 6:
                    self.show_results()
                    input(tag_gt() + "Press Enter to continue...")
                elif choice == 7:
                    self.cleanup()
                    break
                elif choice == 8:
                    print(tag_asterisk() + "Goodbye!")
                    self.cleanup()
                    return
                else:
                    print(tag_exclamation() + "Invalid choice")
                    input(tag_gt() + "Press Enter to continue...")

def main():
    """Main function"""
    try:
        cracker = WiFiCracker()
        cracker.main_loop()
    except KeyboardInterrupt:
        print(c_red("\n\n[x]") + " Program stopped by user")
        cracker.cleanup()
    except Exception as e:
        print(c_red("\n[x]") + f" Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
