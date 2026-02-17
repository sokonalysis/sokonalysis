#!/usr/bin/env python3
"""
RAR File Password Cracker
Complete workflow using rar2john for hash extraction
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

class RARCracker:
    def __init__(self):
        self.john_path = "john"
        self.archive = None
        self.hash_file = None
        self.default_wordlist = "wordlist.txt"
        self.rar2john_path = self.find_rar2john()
        self.current_dir = os.getcwd()
        self.temp_dir = None
    
    def find_rar2john(self):
        """Find rar2john in common locations across different Linux distributions"""
        common_paths = [
            # Debian/Ubuntu/Kali/Parrot
            "/usr/sbin/rar2john",
            "/usr/bin/rar2john",
            "/usr/share/john/rar2john",
            
            # RedHat/Fedora/CentOS
            "/usr/local/bin/rar2john",
            "/usr/local/sbin/rar2john",
            
            # Arch Linux
            "/opt/john/rar2john",
            
            # Source compilation
            "/usr/local/share/john/rar2john",
            "/opt/john/run/rar2john",
            
            # Python script versions
            "/usr/share/john/rar2john.py",
            "/usr/local/share/john/rar2john.py",
            
            # In PATH
            "rar2john",
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
        
        # Check for rar2john
        if not self.rar2john_path:
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
    
    def extract_hash(self, archive_path):
        """Extract hash from RAR file using rar2john"""
        print(tag_asterisk() + "Extracting hash from: " + YELLOW + f"{archive_path}" + RESET)
        print()
        
        if not os.path.exists(archive_path):
            self.show_error("File not found")
            return False
        
        # Create temporary file for hash
        self.temp_dir = tempfile.mkdtemp(prefix="rar_hash_")
        self.hash_file = os.path.join(self.temp_dir, "rar.hash")
        
        try:
            # Run rar2john - check if it's a Python script
            if self.rar2john_path.endswith('.py'):
                python_cmd = "python3"
                if platform.system() == "Windows":
                    python_cmd = "py -3"
                cmd = [python_cmd, self.rar2john_path, archive_path]
            else:
                cmd = [self.rar2john_path, archive_path]
            
            # Run with timeout
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout:
                # Extract the hash line - improved pattern matching
                hash_lines = []
                output_lines = result.stdout.split('\n')
                
                # First, try to find hash patterns
                hash_patterns = [
                    r'\$RAR3\$[^:\s]+',      # RAR3 format
                    r'\$RAR5\$[^:\s]+',      # RAR5 format  
                    r'\$rar\$[^:\s]+',       # Old format
                    r'\$rar2\$[^:\s]+',      # RAR2 format
                    r'[a-fA-F0-9]{32,}:\d+', # MD5 hash with salt
                ]
                
                for line in output_lines:
                    line = line.strip()
                    if line:
                        # Check for hash patterns
                        for pattern in hash_patterns:
                            if re.search(pattern, line):
                                # Add filename for john if not already present
                                if ':' not in line or line.count(':') < 2:
                                    line = f"{line}:{os.path.basename(archive_path)}"
                                hash_lines.append(line)
                                break
                
                if not hash_lines:
                    # Alternative approach: take the first non-empty line that looks like a hash
                    for line in output_lines:
                        line = line.strip()
                        if line and len(line) > 20 and ('$' in line or ':' in line):
                            # Check if it might be a hash
                            if '$RAR' in line or '$rar' in line or ':' in line:
                                # Add filename for john if needed
                                if line.count(':') < 2:
                                    line = f"{line}:{os.path.basename(archive_path)}"
                                hash_lines.append(line)
                                break
                
                if hash_lines:
                    # Save hash to file
                    with open(self.hash_file, 'w') as f:
                        for hash_line in hash_lines:
                            f.write(hash_line + '\n')
                    
                    self.show_success("Hash extracted successfully!")
                    return True
                else:
                    self.show_error("No hash found in output")
                    print(YELLOW + "    The archive might not be password protected" + RESET)
                    
                    # Try alternative method: save entire output as hash
                    if result.stdout.strip():
                        print(tag_asterisk() + "Trying alternative method...")
                        with open(self.hash_file, 'w') as f:
                            f.write(result.stdout.strip())
                        self.show_success("Hash extracted successfully!")
                        return True
            else:
                self.show_error("rar2john failed")
                
        except subprocess.TimeoutExpired:
            self.show_error("rar2john timed out after 30 seconds")
        except Exception as e:
            self.show_error(f"Error: {e}")
        
        self.cleanup()
        return False
    
    def list_rars(self):
        """List RAR files in current directory"""
        extensions = ['.rar', '.part01.rar', '.part001.rar', '.part1.rar', '.r00', '.r01']
        
        rars = []
        
        print(BLUE + "\n______________________ " + GREEN + "Available RAR Files" + BLUE + " _____________________\n")
        
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
                    
                    rars.append(file)
                    print(YELLOW + f"[{idx}]" + RESET + f" {file}" + CYAN + f" ({size_str})" + RESET)
                    idx += 1
        
        return rars
    
    def select_rar(self):
        """Let user select a RAR file"""
        rars = self.list_rars()
        
        if not rars:
            self.show_error("No RAR files found!")
            print()
            print(YELLOW + "[1]" + RESET + " Enter RAR file path manually")
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
        
        print(YELLOW + f"[{len(rars)+1}]" + RESET + " Enter custom path")
        print(YELLOW + f"[{len(rars)+2}]" + RESET + " Exit")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            choice = int(input(tag_gt() + f"Select RAR file (1-{len(rars)+2}): "))
            
            if 1 <= choice <= len(rars):
                return rars[choice-1]
            elif choice == len(rars) + 1:
                path = input(tag_gt() + "Enter full path: ").strip()
                if os.path.exists(path):
                    return path
                else:
                    self.show_error("File not found")
                    return None
            else:
                return None
                
        except ValueError:
            self.show_error("Invalid choice")
            return None
    
    def select_attack_mode(self):
        """Select attack mode"""
        print(tag_asterisk() + "RAR File: " + YELLOW + f"{self.archive}" + RESET)
        print()
        print(BLUE + "\n____________________________ " + GREEN + "Options" + BLUE + " ____________________________")
        print()

        print(YELLOW + "[1]" + RESET + " Wordlist Attack (using default wordlist)")
        print(YELLOW + "[2]" + RESET + " Wordlist Attack (custom wordlist)")
        print(YELLOW + "[3]" + RESET + " Single Crack Mode")
        print(YELLOW + "[4]" + RESET + " Incremental Mode (brute force)")
        print(YELLOW + "[5]" + RESET + " Show cracked passwords")
        print(YELLOW + "[6]" + RESET + " Select different RAR file")
        print(YELLOW + "[7]" + RESET + " Exit")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            return int(input(tag_gt() + "Select option (1-7): "))
        except ValueError:
            self.show_error("Please enter a number")
            return None
    
    def get_wordlist_info(self, wordlist_path):
        """Get information about a wordlist"""
        if not os.path.exists(wordlist_path):
            self.show_error("Wordlist not found")
            return False
        
        wordcount = self.count_words(wordlist_path)
        if wordcount == 0:
            self.show_error("Wordlist is empty")
            return False
        
        return True
    
    def run_john_command(self, cmd, attack_name):
        """Run a John the Ripper command"""
        # Suppress the attack name and command display
        # print(tag_asterisk() + f"{attack_name} on: " + YELLOW + f"{self.archive}" + RESET)
        # print()
        # print(tag_gt() + "Command: " + CYAN + f"{' '.join(cmd)}" + RESET)
        # print()
        # print(tag_asterisk() + "Starting attack... " + RED + "Press Ctrl+C to stop" + RESET)
        # print()
        
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
        wordlist = custom_wordlist if custom_wordlist else self.default_wordlist
        
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
        
        rule_choice = input(tag_gt() + "Select rule option (1-3, default=2): ").strip() or "2"
        
        # Build command
        cmd = [self.john_path, self.hash_file]
        
        # Add wordlist
        cmd.append("--wordlist=" + wordlist)
        
        # Add rules
        if rule_choice == "2":
            cmd.append("--rules")
        elif rule_choice == "3":
            cmd.append("--rules=All")
        
        return self.run_john_command(cmd, "Wordlist Attack")
    
    def run_single_mode(self):
        """Run single crack mode"""
        cmd = [self.john_path, self.hash_file, "--single"]
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
        except ValueError:
            self.show_error("Invalid choice")
            return False
        
        if choice == 5:
            return False
        
        charsets = {
            1: "Digits",
            2: "Lower",
            3: "Alnum",
            4: "All"
        }
        
        if choice not in charsets:
            self.show_error("Invalid choice")
            return False
        
        charset = charsets[choice]
        
        print()
        print(tag_asterisk() + f"Using character set: {charset}")
        self.show_warning("This may take a VERY long time!")
        confirm = input(tag_question() + "Continue with brute force? (y/n): ").lower()
        
        if confirm != 'y':
            print(tag_asterisk() + "Cancelled")
            return False
        
        cmd = [self.john_path, self.hash_file, "--incremental=" + charset]
        return self.run_john_command(cmd, f"Incremental Mode ({charset})")
    
    def show_results(self):
        """Show cracked passwords"""
        print(tag_asterisk() + "Checking for cracked passwords...")
        print()
        
        cmd = [self.john_path, self.hash_file, "--show"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                password_found = False
                password_value = ""
                
                for line in lines:
                    if ':' in line and not line.startswith(' '):
                        parts = line.split(':', 1)
                        if len(parts) > 1:
                            # Get only the password part, strip any filename suffix
                            full_value = parts[1].strip()
                            # Extract just the password (remove filename after colon)
                            if ':' in full_value:
                                password_value = full_value.split(':', 1)[0].strip()
                            else:
                                password_value = full_value
                            password_found = True
                            break
                
                if password_found:
                    print(BLUE + "_________________________________________________________________")
                    print()
                    print(tag_minus() + "Cracked Password Results: " + GREEN + password_value + RESET)
                    print()
                    print(BLUE + "_________________________________________________________________")
                    
                    # Save results to file
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = f"cracked_{timestamp}.txt"
                    with open(filename, "w") as f:
                        f.write(result.stdout)
                    
                    print()
                    print(tag_plus() + f" Results saved to: {filename}")
                    print()
                    print(BLUE + "_________________________________________________________________")
                    
                    return True
                else:
                    print(tag_minus() + "No passwords cracked yet")
            else:
                print(tag_minus() + "No passwords cracked yet")
                
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
        """Main program loop"""
        if not self.check_tools():
            print(tag_exclamation() + "Required tools not found. Please install john and rar2john.")
            return
        
        while True:
            self.archive = self.select_rar()
            if not self.archive:
                self.cleanup()
                return
            
            print()
            if not self.extract_hash(self.archive):
                continue
            
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
                            self.run_wordlist_attack(wl)
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
        
        cracker = RARCracker()
        cracker.main_loop()
        
    except KeyboardInterrupt:
        print(RED + "\n[x] Program stopped by user" + RESET)
    except Exception as e:
        print(RED + f"\n[x] Error: {e}" + RESET)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
