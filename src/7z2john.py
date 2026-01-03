#!/usr/bin/env python3
"""
7-Zip File Password Cracker
Complete workflow using 7z2john for hash extraction
Colorful Interface
"""

import os
import sys
import subprocess
import time
import tempfile
import shutil
import re

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

class SevenZipCracker:
    def __init__(self):
        self.john_path = "john"
        self.archive = None
        self.hash_file = None
        self.default_wordlist = "wordlist.txt"
        self.sevenz2john_path = self.find_sevenz2john()  # Auto-detect on init
        self.current_dir = os.getcwd()
    
    def find_sevenz2john(self):
        """Find 7z2john in common locations across different Linux distributions"""
        common_paths = [
            # Debian/Ubuntu/Kali/Parrot (John Jumbo)
            "/usr/sbin/7z2john",
            "/usr/bin/7z2john",
            "/usr/share/john/7z2john",
            
            # John Jumbo specific paths
            "/usr/share/john/7z2john.pl",  # Perl version
            "/usr/local/share/john/7z2john.pl",
            "/opt/john/run/7z2john.pl",
            
            # RedHat/Fedora/CentOS
            "/usr/local/bin/7z2john",
            "/usr/local/sbin/7z2john",
            
            # Arch Linux
            "/opt/john/7z2john",
            
            # Source compilation
            "/usr/local/share/john/7z2john",
            "/opt/john/run/7z2john",
            
            # Python script versions
            "/usr/share/john/7z2john.py",
            "/usr/local/share/john/7z2john.py",
            
            # Alternative names
            "7z2john",
            "7z2john.pl",
        ]
        
        print(tag_asterisk() + "Searching for 7z2john...")
        for path in common_paths:
            if os.path.exists(path):
                print(tag_plus() + f"Found at: {path}")
                return path
        
        print(tag_exclamation() + "7z2john not found in common locations")
        print(c_yellow("Note: 7z2john is usually part of John the Ripper Jumbo version"))
        print(c_yellow("Install with: git clone https://github.com/openwall/john -b bleeding-jumbo"))
        return None
    
    def clear_screen(self):
        """Clear screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def show_banner(self):
        """Show colorful banner"""
        self.clear_screen()
        print(tag_minus() + "7-ZIP FILE PASSWORD CRACKER")
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
                # Check if it's Jumbo version (needed for 7z support)
                if "jumbo" in result.stdout.lower():
                    print(tag_plus() + "Detected John the Ripper Jumbo version")
                else:
                    print(tag_exclamation() + "Warning: Standard John may not support 7-Zip hashes")
                    print(c_yellow("    Consider installing John Jumbo version for better 7z support"))
            else:
                print(tag_exclamation() + "John the Ripper not working properly")
                return False
        except FileNotFoundError:
            print(tag_exclamation() + "John the Ripper not found!")
            print(c_yellow("    Install with: sudo apt install john  (Debian/Ubuntu)"))
            print(c_yellow("                  sudo yum install john  (RedHat/Fedora)"))
            print(c_yellow("                  sudo pacman -S john    (Arch)"))
            return False
        
        # Check for 7z2john
        if not self.sevenz2john_path:
            print(tag_exclamation() + "7z2john not found!")
            print(c_yellow("    7z2john is part of John the Ripper Jumbo version"))
            print(c_yellow("    Install John Jumbo: git clone https://github.com/openwall/john -b bleeding-jumbo"))
            print(c_yellow("    Then build and install it"))
            return False
        else:
            print(tag_plus() + f"7z2john: Found at '{self.sevenz2john_path}'")
        
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
    
    def extract_hash(self, archive_path):
        """Extract hash from 7-Zip file using 7z2john"""
        self.show_banner()
        print(tag_asterisk() + f"Extracting hash from: {archive_path}")
        
        if not os.path.exists(archive_path):
            print(tag_exclamation() + f"File not found: {archive_path}")
            return False
        
        # Create temporary file for hash
        temp_dir = tempfile.mkdtemp(prefix="7z_hash_")
        self.hash_file = os.path.join(temp_dir, "7z.hash")
        
        try:
            # Check file type first
            file_ext = os.path.splitext(archive_path)[1].lower()
            valid_extensions = ['.7z', '.7z.001', '.7z.002', '.7z.003']
            
            if file_ext not in ['.7z', '.001', '.002', '.003'] and not any(archive_path.lower().endswith(ext) for ext in valid_extensions):
                print(tag_exclamation() + f"File doesn't appear to be a 7-Zip archive: {archive_path}")
                print(c_yellow("    7-Zip files typically have .7z extension"))
            
            # Run 7z2john - could be Perl or Python script
            if self.sevenz2john_path.endswith('.pl'):
                cmd = ["perl", self.sevenz2john_path, archive_path]
            elif self.sevenz2john_path.endswith('.py'):
                cmd = ["python3", self.sevenz2john_path, archive_path]
            else:
                cmd = [self.sevenz2john_path, archive_path]
            
            print(tag_gt() + f"Running: {' '.join(cmd)}")
            
            # Run with timeout
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and result.stdout:
                # Extract the hash line - 7-Zip has specific formats
                hash_lines = []
                output_lines = result.stdout.split('\n')
                
                # 7-Zip hash patterns
                hash_patterns = [
                    r'\$7z\$[^:\s]+',       # 7-Zip format
                    r'\$7z\$\d+\/[^:\s]+',  # 7-Zip with iterations
                    r'[a-fA-F0-9]{64,}',    # SHA-256 hash
                    r'[a-fA-F0-9]{128,}',   # Longer hashes
                ]
                
                for line in output_lines:
                    line = line.strip()
                    if line:
                        # Debug: show what we're parsing
                        if len(line) > 50:
                            print(c_cyan(f"Processing line: {line[:80]}..."))
                        else:
                            print(c_cyan(f"Processing line: {line}"))
                        
                        # Check for hash patterns
                        for pattern in hash_patterns:
                            if re.search(pattern, line):
                                # Add filename for john if not already present
                                if ':' not in line or line.count(':') < 2:
                                    line = f"{line}:{os.path.basename(archive_path)}"
                                hash_lines.append(line)
                                print(tag_minus() + f"Found hash: {line[:60]}...")
                                break
                        else:
                            # Check for $7z$ at the beginning
                            if line.startswith('$7z$'):
                                if ':' not in line or line.count(':') < 2:
                                    line = f"{line}:{os.path.basename(archive_path)}"
                                hash_lines.append(line)
                                print(tag_minus() + f"Found 7-Zip hash: {line[:60]}...")
                
                if not hash_lines:
                    # Alternative approach: look for any line with $7z$ or hex string
                    for line in output_lines:
                        line = line.strip()
                        if line and ('$7z$' in line or len(line) > 50):
                            # Check if it might be a hash
                            if '$7z$' in line or (re.match(r'^[a-fA-F0-9]+$', line) and len(line) > 32):
                                # Add filename for john if needed
                                if line.count(':') < 2:
                                    line = f"{line}:{os.path.basename(archive_path)}"
                                hash_lines.append(line)
                                print(tag_minus() + f"Using line as hash: {line[:60]}...")
                                break
                
                if hash_lines:
                    # Save hash to file
                    with open(self.hash_file, 'w') as f:
                        for hash_line in hash_lines:
                            f.write(hash_line + '\n')
                    
                    print(tag_plus() + f"Hash saved to temporary file: {self.hash_file}")
                    
                    # Display the hash for debugging
                    with open(self.hash_file, 'r') as f:
                        hash_content = f.read()
                        print(c_yellow("\nExtracted hash:"))
                        print(hash_content)
                    
                    return True
                else:
                    print(tag_exclamation() + "No hash found in output")
                    print(c_yellow("\nRaw 7z2john output:"))
                    print(result.stdout[:500])
                    
                    # Try to save any output that looks like a hash
                    if result.stdout.strip():
                        lines = result.stdout.strip().split('\n')
                        for line in lines:
                            if line.strip() and ('$7z$' in line or len(line.strip()) > 40):
                                print(tag_asterisk() + f"Trying to use: {line[:60]}...")
                                with open(self.hash_file, 'w') as f:
                                    f.write(line.strip())
                                print(tag_plus() + f"Saved as hash: {self.hash_file}")
                                return True
                    
                    # Try alternative method: save entire output as hash
                    print(tag_asterisk() + "Trying alternative method...")
                    with open(self.hash_file, 'w') as f:
                        f.write(result.stdout.strip())
                    print(tag_plus() + f"Saved raw output as hash: {self.hash_file}")
                    return True
            else:
                print(tag_exclamation() + f"7z2john failed with return code: {result.returncode}")
                if result.stderr:
                    print(c_red("Error output:"))
                    print(result.stderr[:200])
                
                # Try alternative: use 7z tool directly to test if file is encrypted
                print(tag_asterisk() + "Testing with 7z tool...")
                try:
                    test_cmd = ["7z", "l", "-slt", archive_path]
                    test_result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=10)
                    if "Encrypted = +" in test_result.stdout:
                        print(tag_plus() + "File is encrypted (according to 7z tool)")
                        print(tag_exclamation() + "But 7z2john failed to extract hash")
                        print(c_yellow("    This may be a very new 7-Zip format or corrupted file"))
                    elif "Encrypted = -" in test_result.stdout:
                        print(tag_minus() + "File is NOT encrypted")
                        return False
                except:
                    pass
                
        except subprocess.TimeoutExpired:
            print(tag_exclamation() + "7z2john timed out after 60 seconds")
            print(c_yellow("    Large or complex 7z files may take longer to process"))
        except Exception as e:
            print(tag_x() + f"Error extracting hash: {e}")
            import traceback
            traceback.print_exc()
        
        # Cleanup on failure
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        
        return False
    
    def list_7z_files(self):
        """List 7-Zip files in current directory"""
        extensions = ['.7z', '.7z.001', '.7z.002', '.7z.003', '.7z.004', '.7z.005']
        
        sevenz_files = []
        
        print(c_cyan("\n📁") + " Current Directory: " + c_yellow(self.current_dir))
        print(c_yellow("📦") + " Place 7-Zip files in this directory to see them here.\n")
        print(tag_minus() + "AVAILABLE 7-ZIP FILES")
        
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
                    
                    sevenz_files.append(file)
                    print(c_yellow(f"[{idx}]") + f" {file}" + c_cyan(f" ({size_str})"))
                    idx += 1
        
        return sevenz_files
    
    def select_7z_file(self):
        """Let user select a 7-Zip file"""
        self.show_banner()
        
        print(c_yellow("📁") + f" Current working directory: {self.current_dir}")
        
        sevenz_files = self.list_7z_files()
        
        if not sevenz_files:
            print(tag_exclamation() + "No 7-Zip files found in current directory!")
            print(c_yellow("\n💡") + f" Tip: Place 7z files in: {self.current_dir}")
            print()
            print(tag_minus() + "7-ZIP SELECTION OPTIONS")
            print(c_yellow("[1]") + " Enter 7z file path manually")
            print(c_yellow("[2]") + " Exit")
            
            choice = input(tag_gt() + "Select option (1-2): ").strip()
            if choice == "1":
                path = input(tag_gt() + "Enter full path to 7z file: ").strip()
                if os.path.exists(path):
                    return path
                else:
                    print(tag_exclamation() + f"File not found: {path}")
                    input(tag_gt() + "Press Enter to continue...")
                    return None
            else:
                return None
        
        print(c_yellow(f"[{len(sevenz_files)+1}]") + " Enter custom path")
        print(c_yellow(f"[{len(sevenz_files)+2}]") + " Exit")
        
        try:
            choice = int(input(tag_gt() + f"Select 7z file (1-{len(sevenz_files)+2}): "))
            
            if 1 <= choice <= len(sevenz_files):
                selected = sevenz_files[choice-1]
                print(tag_minus() + f"Selected: {selected}")
                return selected
            elif choice == len(sevenz_files) + 1:
                path = input(tag_gt() + "Enter full path to 7z file: ").strip()
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
        print(tag_asterisk() + "7-Zip File: " + c_yellow(f"{self.archive}"))
        print()
        print(tag_minus() + "SELECT ATTACK MODE")

        print(c_yellow("[1]") + " Wordlist Attack (using default wordlist)")
        print(c_yellow("[2]") + " Wordlist Attack (custom wordlist)")
        print(c_yellow("[3]") + " Single Crack Mode")
        print(c_yellow("[4]") + " Incremental Mode (brute force)")
        print(c_yellow("[5]") + " Show cracked passwords")
        print(c_yellow("[6]") + " Select different 7z file")
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
        print(tag_asterisk() + f"{attack_name} on: {self.archive}")
        
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
                    elif "7-Zip" in line:
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
        
        # Build command
        cmd = [self.john_path, self.hash_file]
        
        # Add wordlist
        cmd.append("--wordlist=" + wordlist)
        
        # Add rules
        if rule_choice == "2":
            cmd.append("--rules")
        elif rule_choice == "3":
            cmd.append("--rules=All")
        
        # 7-Zip often requires format specification
        cmd.append("--format=7z")
        
        return self.run_john_command(cmd, "Wordlist Attack")
    
    def run_single_mode(self):
        """Run single crack mode"""
        cmd = [self.john_path, self.hash_file, "--single", "--format=7z"]
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
        
        charsets = {
            1: "Digits",
            2: "Lower",
            3: "Alnum",
            4: "All"
        }
        
        if choice not in charsets:
            print(tag_exclamation() + "Invalid choice")
            return False
        
        charset = charsets[choice]
        
        print(tag_asterisk() + f"Using character set: {charset}")
        print(tag_exclamation() + "WARNING: 7-Zip cracking can be VERY slow!")
        print(c_yellow("    7-Zip uses many iterations for key derivation"))
        
        confirm = input(tag_gt() + "Continue with brute force? (y/n): ").lower()
        if confirm != 'y':
            print(tag_asterisk() + "Cancelled")
            return False
        
        cmd = [self.john_path, self.hash_file, "--incremental=" + charset, "--format=7z"]
        return self.run_john_command(cmd, f"Incremental Mode ({charset})")
    
    def show_results(self):
        """Show cracked passwords"""
        self.show_banner()
        print(tag_asterisk() + "Checking for cracked passwords...")
        
        cmd = [self.john_path, self.hash_file, "--show", "--format=7z"]
        
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
                            print(c_cyan(parts[0] + ":") + c_green(":".join(parts[1:])))
                        else:
                            print(c_cyan(line))
                    else:
                        print(line)
                
                # Check if any passwords were actually cracked
                if "password hash cracked" in result.stdout or "password hashes cracked" in result.stdout:
                    # Save to file
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    results_file = f"cracked_{timestamp}.txt"
                    
                    with open(results_file, "w") as f:
                        f.write(f"7-Zip File: {self.archive}\n")
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
    
    def main_loop(self):
        """Main program loop"""
        if not self.check_tools():
            print(tag_exclamation() + "Please install missing tools and try again")
            input(tag_gt() + "Press Enter to exit...")
            return
        
        while True:
            # Select 7z file
            self.archive = self.select_7z_file()
            if not self.archive:
                print(tag_asterisk() + "Exiting...")
                self.cleanup()
                break
            
            # Extract hash
            print(tag_asterisk() + "Extracting hash from 7-Zip file...")
            if not self.extract_hash(self.archive):
                print(tag_exclamation() + "Failed to extract hash from 7-Zip file")
                
                # Offer manual hash input
                print(tag_minus() + "You can manually extract the hash with:")
                print(c_yellow(f"    {self.sevenz2john_path} \"{self.archive}\""))
                print(tag_minus() + "Then create a hash file manually and continue")
                
                manual_hash = input(tag_gt() + "Enter hash manually (or press Enter to skip): ").strip()
                if manual_hash:
                    # Create temporary file for manual hash
                    temp_dir = tempfile.mkdtemp(prefix="7z_hash_")
                    self.hash_file = os.path.join(temp_dir, "7z.hash")
                    with open(self.hash_file, 'w') as f:
                        f.write(manual_hash + '\n')
                    print(tag_plus() + f"Manual hash saved to: {self.hash_file}")
                else:
                    input(tag_gt() + "Press Enter to continue...")
                    continue
            
            # Main attack loop for this 7z file
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
                    # Select different 7z file
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
        cracker = SevenZipCracker()
        cracker.main_loop()
    except KeyboardInterrupt:
        print(c_red("\n\n[x]") + " Program stopped by user")
    except Exception as e:
        print(c_red("\n[x]") + f" Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
