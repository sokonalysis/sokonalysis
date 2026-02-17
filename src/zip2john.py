#!/usr/bin/env python3
"""
ZIP File Password Cracker
Complete workflow using zip2john for hash extraction
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
RED = '\033[31m'      # Changed from \033[91m to \033[31m
GREEN = '\033[32m'    # Changed from \033[92m to \033[32m
YELLOW = '\033[33m'   # Changed from \033[93m to \033[33m
CYAN = '\033[36m'     # Changed from \033[96m to \033[36m
BLUE = '\033[34m'     # Changed from \033[94m to \033[34m
MAGENTA = '\033[35m'  # Changed from \033[95m to \033[35m
ORANGE = '\033[38;5;208m'  # Keeping ORANGE same
WHITE = '\033[37m'    # Changed from \033[97m to \033[37m
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

class ZipCracker:
    def __init__(self):
        self.john_path = "john"
        self.archive = None
        self.hash_file = None
        self.default_wordlist = "wordlist.txt"
        self.zip2john_path = "/usr/share/john/zip2john.py"
        self.current_dir = os.getcwd()
        self.temp_dir = None
        
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
        
        # Check for zip2john
        zip2john_paths = [
            "/usr/share/john/zip2john.py",
            "/usr/bin/zip2john",
            "/usr/sbin/zip2john",
            "/usr/local/bin/zip2john",
            "/usr/local/share/john/zip2john.py",
            "/opt/john/run/zip2john"
        ]
        
        found = False
        for path in zip2john_paths:
            if os.path.exists(path):
                self.zip2john_path = path
                found = True
                break
        
        if not found:
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
    
    def extract_hash(self, archive_path):
        """Extract hash from ZIP file"""
        print(tag_asterisk() + "Extracting hash from: " + YELLOW + f"{archive_path}" + RESET)
        print()
        
        if not os.path.exists(archive_path):
            self.show_error("File not found")
            return False
        
        # Create temporary file for hash
        self.temp_dir = tempfile.mkdtemp(prefix="zip_hash_")
        self.hash_file = os.path.join(self.temp_dir, "zip.hash")
        
        try:
            # Determine Python command
            python_cmd = "python3"
            if platform.system() == "Windows":
                python_cmd = "py -3"
            
            # Run zip2john
            if self.zip2john_path.endswith('.py'):
                cmd = [python_cmd, self.zip2john_path, archive_path]
            else:
                cmd = [self.zip2john_path, archive_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout:
                # Extract the hash line
                hash_lines = []
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and any(x in line for x in ['$pkzip$', '$zip2$', '$zip$', '$pkzip2$']):
                        if ':' not in line:
                            line = f"{os.path.basename(archive_path)}:{line}"
                        hash_lines.append(line)
                
                if hash_lines:
                    with open(self.hash_file, 'w') as f:
                        for hash_line in hash_lines:
                            f.write(hash_line + '\n')
                    
                    self.show_success("Hash extracted successfully!")
                    return True
                else:
                    self.show_error("No hash found in output")
                    print(YELLOW + "    The ZIP file might not be password protected" + RESET)
            else:
                self.show_error("zip2john failed")
                
        except Exception as e:
            self.show_error(f"Error: {e}")
        
        self.cleanup()
        return False
    
    def list_archives(self):
        """List ZIP files in current directory"""
        extensions = ['.zip']
        
        archives = []
        
        print(BLUE + "\n____________________ " + GREEN + "Available ZIP Archives" + BLUE + " _____________________\n")
        
        idx = 1
        for file in sorted(os.listdir('.')):
            if any(file.lower().endswith(ext) for ext in extensions):
                if os.path.isfile(file):
                    archives.append(file)
                    
                    # Show file size
                    size = os.path.getsize(file)
                    if size < 1024:
                        size_str = f"{size}B"
                    elif size < 1024*1024:
                        size_str = f"{size/1024:.1f}KB"
                    else:
                        size_str = f"{size/(1024*1024):.1f}MB"
                    
                    print(YELLOW + f"[{idx}]" + RESET + f" {file} " + CYAN + f"({size_str})" + RESET)
                    idx += 1
        
        return archives
    
    def select_archive(self):
        """Let user select a ZIP file"""
        archives = self.list_archives()
        
        if not archives:
            self.show_error("No ZIP files found!")
            print()
            print(YELLOW + "[1]" + RESET + " Enter archive path manually")
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
        
        print(YELLOW + f"[{len(archives)+1}]" + RESET + " Enter custom path")
        print(YELLOW + f"[{len(archives)+2}]" + RESET + " Exit")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            choice = int(input(tag_gt() + f"Select archive (1-{len(archives)+2}): "))
            
            if 1 <= choice <= len(archives):
                return archives[choice-1]
            elif choice == len(archives) + 1:
                path = input(tag_gt() + "Enter full path: ").strip()
                if os.path.exists(path):
                    return path
                else:
                    self.show_error("File not found")
                    return None
            else:
                # Exit silently - just return None without printing anything
                return None
        except:
            self.show_error("Invalid choice")
            return None
    
    def select_attack_mode(self):
        """Select attack mode"""
        print(tag_asterisk() + "Archive: " + YELLOW + f"{self.archive}" + RESET)
        print()
        print(BLUE + "\n____________________________ " + GREEN + "Options" + BLUE + " ____________________________")
        print()

        print(YELLOW + "[1]" + RESET + " Wordlist Attack (using default wordlist)")
        print(YELLOW + "[2]" + RESET + " Wordlist Attack (custom wordlist)")
        print(YELLOW + "[3]" + RESET + " Single Crack Mode")
        print(YELLOW + "[4]" + RESET + " Incremental Mode (brute force)")
        print(YELLOW + "[5]" + RESET + " Show cracked passwords")
        print(YELLOW + "[6]" + RESET + " Select different archive")
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
        print(tag_asterisk() + f"{attack_name} on: " + YELLOW + f"{self.archive}" + RESET)
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
        
        cmd = [self.john_path, self.hash_file, "--wordlist=" + wordlist]
        
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
        
        cmd = [self.john_path, self.hash_file, "--incremental=" + mode]
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
                
                for line in lines:
                    # Look for the line with format "filename:password"
                    if ':' in line and not line.startswith(' ') and not line.startswith('1 password'):
                        parts = line.split(':', 1)
                        if len(parts) > 1:
                            # Get just the password part - everything before the first comma or double colon
                            raw_password = parts[1].strip()
                            
                            # Extract only the password (before any special characters)
                            if '::' in raw_password:
                                password_value = raw_password.split('::')[0].strip()
                            elif ',' in raw_password:
                                password_value = raw_password.split(',')[0].strip()
                            elif ':' in raw_password:
                                password_value = raw_password.split(':')[0].strip()
                            else:
                                password_value = raw_password
                            
                            password_found = True
                            break
                
                if password_found:
                    print(BLUE + "_________________________________________________________________")
                    print()
                    # Display just the password value with the [-] tag
                    print(tag_minus() + "Cracked Password Results: " + GREEN + password_value + RESET)
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
            print(tag_exclamation() + "Required tools not found. Please install john and zip2john.")
            return
        
        while True:
            self.archive = self.select_archive()
            if not self.archive:
                # Exit silently without printing anything
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
                    password_cracked = self.show_results()
                    self.cleanup()
                    if password_cracked:
                        return  # Exit completely
                    break  # Break to outer loop to select another archive
                elif choice == 2:
                    wl = input(tag_gt() + "Enter path to custom wordlist: ").strip()
                    if wl:
                        if os.path.exists(wl):
                            self.run_wordlist_attack(wl)
                            password_cracked = self.show_results()
                            self.cleanup()
                            if password_cracked:
                                return  # Exit completely
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
                        return  # Exit completely
                    break
                elif choice == 4:
                    self.run_incremental_mode()
                    password_cracked = self.show_results()
                    self.cleanup()
                    if password_cracked:
                        return  # Exit completely
                    break
                elif choice == 5:
                    password_cracked = self.show_results()
                    if password_cracked:
                        self.cleanup()
                        return  # Exit completely
                elif choice == 6:
                    self.cleanup()
                    break
                elif choice == 7:
                    # Exit silently without printing "Goodbye!"
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
        
        cracker = ZipCracker()
        cracker.main_loop()
        
    except KeyboardInterrupt:
        print(RED + "\n[x] Program stopped by user" + RESET)
    except Exception as e:
        print(RED + f"\n[x] Error: {e}" + RESET)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
