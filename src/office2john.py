#!/usr/bin/env python3
"""
Office Document Password Cracker
Complete workflow using office2john for hash extraction
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

class OfficeCracker:
    def __init__(self):
        self.john_path = "john"
        self.document = None
        self.hash_file = None
        self.default_wordlist = "wordlist.txt"
        self.office2john_path = "/usr/share/john/office2john.py"
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
        
        # Check for office2john
        office2john_paths = [
            "/usr/share/john/office2john.py",
            "/usr/bin/office2john",
            "/usr/local/share/john/office2john.py"
        ]
        
        found = False
        for path in office2john_paths:
            if os.path.exists(path):
                self.office2john_path = path
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
    
    def extract_hash(self, document_path):
        """Extract hash from Office document"""
        print(tag_asterisk() + "Extracting hash from: " + YELLOW + f"{document_path}" + RESET)
        print()
        
        if not os.path.exists(document_path):
            self.show_error("File not found")
            return False
        
        # Create temporary file for hash
        self.temp_dir = tempfile.mkdtemp(prefix="office_hash_")
        self.hash_file = os.path.join(self.temp_dir, "office.hash")
        
        try:
            # Determine Python command
            python_cmd = "python3"
            if platform.system() == "Windows":
                python_cmd = "py -3"
            
            # Run office2john
            if self.office2john_path.endswith('.py'):
                cmd = [python_cmd, self.office2john_path, document_path]
            else:
                cmd = [self.office2john_path, document_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout:
                # Extract the hash line
                hash_lines = []
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and any(x in line for x in ['$office$', '$oldoffice$', '$msoffice$']):
                        if ':' not in line:
                            line = f"{os.path.basename(document_path)}:{line}"
                        hash_lines.append(line)
                
                if hash_lines:
                    with open(self.hash_file, 'w') as f:
                        for hash_line in hash_lines:
                            f.write(hash_line + '\n')
                    
                    self.show_success("Hash extracted successfully!")
                    return True
                else:
                    self.show_error("No hash found in output")
                    print(YELLOW + "    The document might not be password protected" + RESET)
            else:
                self.show_error("office2john failed")
                
        except Exception as e:
            self.show_error(f"Error: {e}")
        
        self.cleanup()
        return False
    
    def list_documents(self):
        """List Office documents in current directory"""
        extensions = [
            '.doc', '.docx', '.xls', '.xlsx', '.xlsm',
            '.ppt', '.pptx', '.odt', '.ods', '.odp'
        ]
        
        documents = []
        
        print(BLUE + "\n______________ " + GREEN + "Availabe Microsoft Office Documents" + BLUE + " ______________\n")
        
        idx = 1
        for file in sorted(os.listdir('.')):
            if any(file.lower().endswith(ext) for ext in extensions):
                if os.path.isfile(file):
                    documents.append(file)
                    print(YELLOW + f"[{idx}]" + RESET + f" {file}")
                    idx += 1
        
        return documents
    
    def select_document(self):
        """Let user select a document"""
        documents = self.list_documents()
        
        if not documents:
            self.show_error("No Office documents found!")
            print()
            print(YELLOW + "[1]" + RESET + " Enter document path manually")
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
        
        print(YELLOW + f"[{len(documents)+1}]" + RESET + " Enter custom path")
        print(YELLOW + f"[{len(documents)+2}]" + RESET + " Exit")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            choice = int(input(tag_gt() + f"Select document (1-{len(documents)+2}): "))
            
            if 1 <= choice <= len(documents):
                return documents[choice-1]
            elif choice == len(documents) + 1:
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
        print(tag_asterisk() + "Document: " + YELLOW + f"{self.document}" + RESET)
        print()
        print(BLUE + "\n____________________________ " + GREEN + "Options" + BLUE + " ____________________________")
        print()

        print(YELLOW + "[1]" + RESET + " Wordlist Attack (using default wordlist)")
        print(YELLOW + "[2]" + RESET + " Wordlist Attack (custom wordlist)")
        print(YELLOW + "[3]" + RESET + " Single Crack Mode")
        print(YELLOW + "[4]" + RESET + " Incremental Mode (brute force)")
        print(YELLOW + "[5]" + RESET + " Show cracked passwords")
        print(YELLOW + "[6]" + RESET + " Select different document")
        print(YELLOW + "[7]" + RESET + " Exit")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            return int(input(tag_gt() + "Select option (1-7): "))
        except:
            self.show_error("Please enter a number")
            return None
    
    def run_john_command(self, cmd, attack_name):
        """Run a John the Ripper command"""
        print(tag_asterisk() + f"{attack_name} on: " + YELLOW + f"{self.document}" + RESET)
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
        
        if not os.path.exists(wordlist):
            self.show_error("Wordlist not found")
            return False
        
        cmd = [self.john_path, self.hash_file, "--format=office", "--wordlist=" + wordlist]
        
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
        cmd = [self.john_path, self.hash_file, "--single", "--format=office"]
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
        
        cmd = [self.john_path, self.hash_file, "--incremental=" + mode, "--format=office"]
        return self.run_john_command(cmd, f"Incremental Mode ({mode})")
    
    def show_results(self):
        """Show cracked passwords - exactly as specified"""
        print(tag_asterisk() + "Checking for cracked passwords...")
        print()
        
        cmd = [self.john_path, self.hash_file, "--show", "--format=office"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.stdout:
                # Parse the output to extract the password
                lines = result.stdout.strip().split('\n')
                password_found = False
                password_value = ""
                
                for line in lines:
                    if ':' in line and not line.startswith(' '):
                        # This is a cracked password line like "filename:password"
                        parts = line.split(':', 1)
                        if len(parts) > 1:
                            password_value = parts[1].strip()
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
                    
                    # Return to main menu - don't show options again
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
            print(tag_exclamation() + "Required tools not found. Please install john and office2john.")
            return
        
        while True:
            self.document = self.select_document()
            if not self.document:
                # Exit silently without printing anything
                self.cleanup()
                return
            
            print()
            if not self.extract_hash(self.document):
                continue
            
            while True:
                print()
                choice = self.select_attack_mode()
                
                if choice == 1:
                    self.run_wordlist_attack()
                    # After showing results, break to return to main menu
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
        
        cracker = OfficeCracker()
        cracker.main_loop()
        
    except KeyboardInterrupt:
        print(RED + "\n[x] Program stopped by user" + RESET)
    except Exception as e:
        print(RED + f"\n[x] Error: {e}" + RESET)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
