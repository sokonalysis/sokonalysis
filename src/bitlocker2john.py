#!/usr/bin/env python3
"""
BitLocker Disk Image Password Cracker
Complete workflow using bitlocker2john for hash extraction
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

class BitLockerCracker:
    def __init__(self):
        self.john_path = "john"
        self.disk_image = None
        self.hash_file = None
        self.default_wordlist = "wordlist.txt"
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
    
    def format_size(self, size):
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}PB"
    
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
        
        # Check for bitlocker2john
        try:
            result = subprocess.run(['bitlocker2john', '--help'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode not in [0, 1]:
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
    
    def extract_hash(self, disk_image_path):
        """Extract hash from BitLocker disk image"""
        print(tag_asterisk() + "Extracting hash from: " + YELLOW + f"{disk_image_path}" + RESET)
        print()
        
        if not os.path.exists(disk_image_path):
            self.show_error("File not found")
            return False
        
        # Create temporary file for hash
        self.temp_dir = tempfile.mkdtemp(prefix="bitlocker_hash_")
        self.hash_file = os.path.join(self.temp_dir, "bitlocker.hash")
        
        try:
            # Run bitlocker2john
            cmd = ['bitlocker2john', '-i', disk_image_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and result.stdout:
                # Extract the hash lines
                hash_lines = []
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and ('$bitlocker$' in line or '$FVE$' in line):
                        if ':' not in line:
                            line = f"{os.path.basename(disk_image_path)}:{line}"
                        hash_lines.append(line)
                
                if hash_lines:
                    with open(self.hash_file, 'w') as f:
                        for hash_line in hash_lines:
                            f.write(hash_line + '\n')
                    
                    # Also save to current directory with disk image name
                    base_name = os.path.basename(disk_image_path)
                    if '.' in base_name:
                        base_name = base_name.split('.')[0]
                    local_hash = f"{base_name}_hash.txt"
                    
                    with open(local_hash, 'w') as f:
                        for hash_line in hash_lines:
                            f.write(hash_line + '\n')
                    
                    self.show_success("Hash extracted successfully!")
                    print(tag_minus() + f"Hash saved to: " + YELLOW + f"{local_hash}" + RESET)
                    return True
                else:
                    self.show_error("No BitLocker hash found in output")
                    print(YELLOW + "    The disk image might not be BitLocker encrypted" + RESET)
            else:
                self.show_error("bitlocker2john failed")
                
        except subprocess.TimeoutExpired:
            self.show_error("bitlocker2john timed out after 5 minutes")
        except Exception as e:
            self.show_error(f"Error: {e}")
        
        self.cleanup()
        return False
    
    def list_disk_images(self):
        """List disk images in current directory"""
        extensions = [
            '.img', '.iso', '.dd', '.raw', '.vhd', '.vmdk', '.dmg',
            '.IMG', '.ISO', '.DD', '.RAW', '.VHD', '.VMDK', '.DMG'
        ]
        
        disk_images = []
        
        print(BLUE + "_____________________ " + GREEN + "Available Disk Images" + BLUE + " _____________________\n")
        
        idx = 1
        for file in sorted(os.listdir('.')):
            if any(file.lower().endswith(ext.lower()) for ext in extensions):
                if os.path.isfile(file):
                    size = os.path.getsize(file)
                    size_str = self.format_size(size)
                    disk_images.append(file)
                    print(YELLOW + f"[{idx}]" + RESET + f" {file} " + CYAN + f"({size_str})" + RESET)
                    idx += 1
        
        return disk_images
    
    def select_disk_image(self):
        """Let user select a disk image"""
        disk_images = self.list_disk_images()
        
        if not disk_images:
            self.show_error("No disk images found!")
            print()
            print(YELLOW + "[1]" + RESET + " Enter disk image path manually")
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
        
        print(YELLOW + f"[{len(disk_images)+1}]" + RESET + " Enter custom path")
        print(YELLOW + f"[{len(disk_images)+2}]" + RESET + " Exit")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            choice = int(input(tag_gt() + f"Select disk image (1-{len(disk_images)+2}): "))
            
            if 1 <= choice <= len(disk_images):
                return disk_images[choice-1]
            elif choice == len(disk_images) + 1:
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
        print(tag_asterisk() + "Disk Image: " + YELLOW + f"{self.disk_image}" + RESET)
        print()
        print(BLUE + "\n____________________________ " + GREEN + "Options" + BLUE + " ____________________________")
        print()

        print(YELLOW + "[1]" + RESET + " Wordlist Attack (using default wordlist)")
        print(YELLOW + "[2]" + RESET + " Wordlist Attack (custom wordlist)")
        print(YELLOW + "[3]" + RESET + " Single Crack Mode")
        print(YELLOW + "[4]" + RESET + " Incremental Mode (brute force)")
        print(YELLOW + "[5]" + RESET + " Show cracked passwords")
        print(YELLOW + "[6]" + RESET + " Select different disk image")
        print(YELLOW + "[7]" + RESET + " Exit")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            return int(input(tag_gt() + "Select option (1-7): "))
        except:
            self.show_error("Please enter a number")
            return None
    
    def run_john_command(self, cmd, attack_name):
        """Run a John the Ripper command - stops after finding first password"""
        # Remove --max-crack=1 if present (some John versions don't support it)
        cmd = [arg for arg in cmd if "--max-crack" not in arg]
        
        print(tag_asterisk() + f"{attack_name} on: " + YELLOW + f"{self.disk_image}" + RESET)
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
            
            password_found = False
            output_lines = []
            
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    output_lines.append(line)
                    
                    # Check if this line contains a cracked password (format: "password (filename)")
                    if '(' in line and ')' in line and not line.startswith(' '):
                        # This is likely a cracked password line
                        print(tag_plus() + " " + GREEN + line.strip() + RESET)
                        password_found = True
                        # Give it a moment to finish writing
                        time.sleep(0.5)
                        # Terminate the process
                        process.terminate()
                        break
                    elif "cracked" in line.lower() or "password hash cracked" in line.lower():
                        print(tag_plus() + " " + GREEN + line.strip() + RESET)
                        password_found = True
                    elif "warning" in line.lower():
                        # Don't show warnings about max-crack
                        if "max-crack" not in line.lower():
                            print(tag_exclamation() + " " + ORANGE + line.strip() + RESET)
                    elif "error" in line.lower() or "failed" in line.lower():
                        print(tag_x() + " " + RED + line.strip() + RESET)
                    elif "session aborted" in line.lower():
                        print(tag_x() + " " + RED + line.strip() + RESET)
                    elif "no password hashes left" in line.lower():
                        print(tag_minus() + " " + CYAN + line.strip() + RESET)
                    elif "max cracks reached" not in line.lower():
                        # Filter out other common noise
                        if not any(x in line.lower() for x in ['guesses:', 'remaining:', 'format', 'default input']):
                            print(line.strip())
            
            # If we didn't find a password and process is still running, wait for it
            if not password_found and process.poll() is None:
                process.wait()
            
            elapsed = time.time() - start
            print()
            print(tag_minus() + f"Finished in " + YELLOW + f"{elapsed:.1f} seconds" + RESET)
            
            return password_found
            
        except KeyboardInterrupt:
            print()
            process.terminate()
            self.show_error("Stopped by user")
            return False
        except Exception as e:
            print()
            self.show_error(f"Error: {e}")
            return False
    
    def run_wordlist_attack(self, custom_wordlist=None):
        """Run wordlist attack"""
        wordlist = custom_wordlist or self.default_wordlist
        
        if not os.path.exists(wordlist):
            self.show_error("Wordlist not found")
            return False
        
        cmd = [self.john_path, self.hash_file, "--format=bitlocker", "--wordlist=" + wordlist]
        
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
        
        password_found = self.run_john_command(cmd, "Wordlist Attack")
        return password_found
    
    def run_single_mode(self):
        """Run single crack mode"""
        cmd = [self.john_path, self.hash_file, "--single", "--format=bitlocker"]
        password_found = self.run_john_command(cmd, "Single Crack Mode")
        return password_found
    
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
        
        cmd = [self.john_path, self.hash_file, "--incremental=" + mode, "--format=bitlocker"]
        password_found = self.run_john_command(cmd, f"Incremental Mode ({mode})")
        return password_found
    
    def show_results(self):
        """Show cracked passwords"""
        print(tag_asterisk() + "Checking for cracked passwords...")
        print()
        
        cmd = [self.john_path, self.hash_file, "--show", "--format=bitlocker"]
        
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
                    filename = f"cracked_bitlocker_{timestamp}.txt"
                    
                    with open(filename, "w") as f:
                        f.write(f"Disk Image: {self.disk_image}\n")
                        f.write(f"Time: {time.ctime()}\n")
                        f.write("=" * 50 + "\n")
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
            print(tag_exclamation() + "Required tools not found. Please install john and bitlocker2john.")
            input(tag_gt() + "Press Enter to exit...")
            return
        
        while True:
            self.disk_image = self.select_disk_image()
            if not self.disk_image:
                self.cleanup()
                return
            
            print()
            if not self.extract_hash(self.disk_image):
                continue
            
            while True:
                print()
                choice = self.select_attack_mode()
                password_found = False
                
                if choice == 1:
                    password_found = self.run_wordlist_attack()
                    if password_found:
                        self.show_results()
                        self.cleanup()
                        return  # Exit completely
                    else:
                        self.show_results()
                        break  # Return to main menu if no password found
                elif choice == 2:
                    wl = input(tag_gt() + "Enter path to custom wordlist: ").strip()
                    if wl:
                        if os.path.exists(wl):
                            password_found = self.run_wordlist_attack(wl)
                            if password_found:
                                self.show_results()
                                self.cleanup()
                                return  # Exit completely
                            else:
                                self.show_results()
                                break  # Return to main menu if no password found
                        else:
                            self.show_error(f"Wordlist not found: {wl}")
                    else:
                        self.show_error("No wordlist specified")
                elif choice == 3:
                    password_found = self.run_single_mode()
                    if password_found:
                        self.show_results()
                        self.cleanup()
                        return  # Exit completely
                    else:
                        self.show_results()
                        break  # Return to main menu if no password found
                elif choice == 4:
                    password_found = self.run_incremental_mode()
                    if password_found:
                        self.show_results()
                        self.cleanup()
                        return  # Exit completely
                    else:
                        self.show_results()
                        break  # Return to main menu if no password found
                elif choice == 5:
                    if self.show_results():
                        self.cleanup()
                        return  # Exit completely if passwords were shown
                    break
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
        
        cracker = BitLockerCracker()
        cracker.main_loop()
        
    except KeyboardInterrupt:
        print(RED + "\n[x] Program stopped by user" + RESET)
    except Exception as e:
        print(RED + f"\n[x] Error: {e}" + RESET)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
