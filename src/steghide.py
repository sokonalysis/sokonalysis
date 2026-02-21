#!/usr/bin/env python3
"""
Steghide Steganography Tool Wrapper
Complete workflow for hiding and extracting data from images
SOKONALYSIS - Created by Soko James
Following Sokonalysis C++ Style Guidelines for Sub-options
"""

import os
import sys
import subprocess
import time
import tempfile
import shutil
import getpass
import platform
import threading
import math

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

class SteghideCracker:
    def __init__(self):
        self.steghide_path = "steghide"
        self.document = None
        self.hash_file = None
        self.default_wordlist = "wordlist.txt"
        self.current_dir = os.getcwd()
        self.temp_dir = None
        self.supported_extensions = ['.jpg', '.jpeg', '.bmp', '.wav', '.au']
        self.loading_active = False
        self.loading_thread = None
        
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
    
    def loading_animation(self):
        """Display a simple loading animation"""
        chars = "|/-\\"
        i = 0
        while self.loading_active:
            sys.stdout.write('\r' + tag_asterisk() + "Working... " + chars[i % 4])
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
        sys.stdout.write('\r' + ' ' * 50 + '\r')
        sys.stdout.flush()
    
    def start_loading(self):
        """Start the loading animation in a background thread"""
        self.loading_active = True
        self.loading_thread = threading.Thread(target=self.loading_animation)
        self.loading_thread.daemon = True
        self.loading_thread.start()
    
    def stop_loading(self):
        """Stop the loading animation"""
        self.loading_active = False
        if self.loading_thread:
            self.loading_thread.join(timeout=0.5)
    
    def draw_progress_bar(self, current, total, start_time, current_password=""):
        """Draw a progress bar with percentage and password count"""
        bar_length = 40
        progress = current / total if total > 0 else 0
        block = int(round(bar_length * progress))
        
        # Calculate elapsed time and speed
        elapsed = time.time() - start_time
        speed = current / elapsed if elapsed > 0 and current > 0 else 0
        
        # Calculate ETA
        if speed > 0:
            eta_seconds = (total - current) / speed
            eta_mins = int(eta_seconds // 60)
            eta_secs = int(eta_seconds % 60)
            eta_str = f"{eta_mins:02d}:{eta_secs:02d}"
        else:
            eta_str = "??:??"
        
        # Build the progress bar
        bar = GREEN + "█" * block + WHITE + "░" * (bar_length - block) + RESET
        
        # Format numbers with commas
        current_str = f"{current:,}"
        total_str = f"{total:,}"
        
        # Calculate percentage
        percent = progress * 100
        
        # Build the status line
        status = f"\r{tag_asterisk()} [{bar}] {percent:5.1f}% | {current_str}/{total_str} | {speed:5.1f} p/s | ETA: {eta_str}"
        
        # Add current password if provided (truncate if too long)
        if current_password and len(status) + len(current_password) + 5 < 120:
            # Truncate password if too long
            if len(current_password) > 30:
                display_pass = current_password[:27] + "..."
            else:
                display_pass = current_password
            status += f" | Trying: {YELLOW}{display_pass}{RESET}"
        
        sys.stdout.write(status)
        sys.stdout.flush()
    
    def check_tools(self):
        """Check if required tools are available"""
        # Check for steghide
        try:
            result = subprocess.run([self.steghide_path, "--version"], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode not in [0, 1]:
                return False
            return True
        except FileNotFoundError:
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
    
    def list_cover_files(self):
        """List image/audio files in current directory"""
        files = []
        
        print(BLUE + "\n_____________ " + GREEN + "Available Cover Files (Images/Audio)" + BLUE + " ______________\n")
        
        idx = 1
        for file in sorted(os.listdir('.')):
            if any(file.lower().endswith(ext) for ext in self.supported_extensions):
                if os.path.isfile(file):
                    files.append(file)
                    size = os.path.getsize(file)
                    if size < 1024:
                        size_str = f"{size}B"
                    elif size < 1024*1024:
                        size_str = f"{size/1024:.1f}KB"
                    else:
                        size_str = f"{size/(1024*1024):.1f}MB"
                    print(YELLOW + f"[{idx}]" + RESET + f" {file}" + CYAN + f" ({size_str})" + RESET)
                    idx += 1
        
        return files
    
    def list_data_files(self):
        """List files that can be embedded"""
        files = []
        
        print(BLUE + "\n______________ " + GREEN + "Available Data Files" + BLUE + " ______________\n")
        
        idx = 1
        for file in sorted(os.listdir('.')):
            if not os.path.isfile(file):
                continue
            
            # Skip tool files and common system files
            skip_files = [
                'wordlist.txt', 'sokonalysis', 'sokonalysis_gui.py',
                'requirements.txt', 'build.log', 'office2john.py', 'steghide.py',
                'john.pot', 'john.log', 'john.rec'
            ]
            
            if file in skip_files:
                continue
            
            # Skip files with specific patterns
            skip_patterns = [
                'cracked_', 'john', 'handshake', 'stb_', 'wifi_cracked',
                'cracked_windows', 'cracked_pdf'
            ]
            
            if any(pattern in file.lower() for pattern in skip_patterns):
                continue
            
            # Skip common file types that aren't suitable for embedding
            if file.endswith(('.py', '.cpp', '.c', '.h', '.hpp', '.java', '.js', 
                             '.html', '.css', '.php', '.rb', '.go', '.rs',
                             '.exe', '.bin', '.so', '.dll', '.dylib',
                             '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
                             '.png', '.jpg', '.jpeg', '.bmp', '.gif', '.wav',
                             '.au', '.mp3', '.flac')):
                continue
            
            # Allow .txt files and files without extensions
            size = os.path.getsize(file)
            if size < 1024:
                size_str = f"{size}B"
            elif size < 1024*1024:
                size_str = f"{size/1024:.1f}KB"
            else:
                size_str = f"{size/(1024*1024):.1f}MB"
            
            files.append(file)
            print(YELLOW + f"[{idx}]" + RESET + f" {file}" + CYAN + f" ({size_str})" + RESET)
            idx += 1
        
        return files
    
    def select_cover_file(self):
        """Let user select a cover file"""
        files = self.list_cover_files()
        
        if not files:
            self.show_error("No image/audio files found!")
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
        
        print(YELLOW + f"[{len(files)+1}]" + RESET + " Enter custom path")
        print(YELLOW + f"[{len(files)+2}]" + RESET + " Exit")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            choice = int(input(tag_gt() + f"Select cover file (1-{len(files)+2}): "))
            print()
            
            if 1 <= choice <= len(files):
                return files[choice-1]
            elif choice == len(files) + 1:
                path = input(tag_gt() + "Enter full path: ").strip()
                print()
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
    
    def select_data_file(self):
        """Let user select a data file to embed"""
        files = self.list_data_files()
        
        if not files:
            self.show_error("No suitable data files found!")
            print()
            print(YELLOW + "[1]" + RESET + " Enter file path manually")
            print(YELLOW + "[2]" + RESET + " Exit")
            print(BLUE + "_________________________________________________________________")
            print()
            
            choice = input(tag_gt() + "Select option (1-2): ").strip()
            if choice == "1":
                path = input(tag_gt() + "Enter full path: ").strip()
                print()
                if os.path.exists(path):
                    return path
                else:
                    self.show_error("File not found")
                    return None
            return None
        
        print(YELLOW + f"[{len(files)+1}]" + RESET + " Enter custom path")
        print(YELLOW + f"[{len(files)+2}]" + RESET + " Exit")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            choice = int(input(tag_gt() + f"Select data file (1-{len(files)+2}): "))
            print()
            
            if 1 <= choice <= len(files):
                return files[choice-1]
            elif choice == len(files) + 1:
                path = input(tag_gt() + "Enter full path: ").strip()
                print()
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
    
    def get_password(self, action="embed"):
        """Get password from user"""
        print()
        print(tag_asterisk() + "Password is optional but recommended for security")
        print()
        
        use_pass = input(tag_gt() + f"Use password for {action}? (y/n, default=n): ").strip().lower()
        print()
        
        if use_pass == 'y':
            password = getpass.getpass(tag_gt() + f"Enter password for {action}: ")
            if password:
                verify = getpass.getpass(tag_gt() + "Verify password: ")
                print()
                if password == verify:
                    return password
                else:
                    self.show_error("Passwords don't match!")
                    return None
            else:
                return ""
        else:
            return ""
    
    def embed_data(self):
        """Embed data into a cover file"""
        # Select cover file
        cover_file = self.select_cover_file()
        if not cover_file:
            return False
        
        # Select data file
        data_file = self.select_data_file()
        if not data_file:
            return False
        
        # Get output filename
        print(tag_asterisk() + "By default, embeds directly into cover file (overwrites)")
        print()
        use_custom_output = input(tag_gt() + "Create separate output file? (y/n, default=n): ").strip().lower()
        print()
        
        output_file = None
        if use_custom_output == 'y':
            default_output = f"stego_{os.path.basename(cover_file)}"
            output_file = input(tag_gt() + f"Output file name (default={default_output}): ").strip()
            print()
            if not output_file:
                output_file = default_output
            
            # Check if output file already exists
            if os.path.exists(output_file):
                overwrite = input(tag_gt() + f"File '{output_file}' exists. Overwrite? (y/n): ").strip().lower()
                print()
                if overwrite != 'y':
                    self.show_error("Operation cancelled")
                    return False
        
        # Get password
        password = self.get_password("embedding")
        if password is None:
            return False
        
        # Get compression level
        use_compression = input(tag_gt() + "Use compression? (y/n, default=n): ").strip().lower()
        print()
        compression = None
        if use_compression == 'y':
            compression = input(tag_gt() + "Compression level (1-9, default=9): ").strip()
            print()
            if not compression:
                compression = "9"
        
        # Build command
        cmd = [self.steghide_path, "embed", "-ef", data_file, "-cf", cover_file]
        
        if output_file:
            cmd.extend(["-sf", output_file])
        if compression:
            cmd.extend(["-z", compression])
        if password:
            cmd.extend(["-p", password])
        cmd.append("-v")
        
        # Confirm before embedding
        print(tag_asterisk() + "Embedding data...")
        print(tag_gt() + "Command: " + CYAN + f"{' '.join(cmd)}" + RESET)
        print()
        
        confirm = input(tag_gt() + "Proceed with embedding? (y/n): ").strip().lower()
        print()
        if confirm != 'y':
            self.show_error("Operation cancelled")
            return False
        
        # Run command with loading animation
        self.start_loading()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.stop_loading()
            
            if result.returncode == 0:
                self.show_success("Embedding successful!")
                
                if output_file:
                    final_file = output_file
                else:
                    final_file = cover_file
                
                if os.path.exists(final_file):
                    print()
                    print(BLUE + "_________________________________________________________________")
                    print()
                    print(tag_minus() + "Embedded Results: " + GREEN + f"{data_file}" + RESET)
                    print(BLUE + "_________________________________________________________________")
                    print()
                    print(tag_minus() + f"Final file: {final_file}")
                    print(BLUE + "_________________________________________________________________")
                
                return True
            else:
                self.show_error("Embedding failed!")
                if result.stderr:
                    error_msg = result.stderr.strip()
                    print(RED + "Error: " + RESET + error_msg)
                    
                    # Provide suggestions for common errors
                    if "capacity" in error_msg.lower():
                        print(YELLOW + "    Tip: Data file might be too large for this cover image" + RESET)
                    elif "already contains data" in error_msg.lower():
                        print(YELLOW + "    Tip: File already has embedded data. Use -sf to create new file" + RESET)
                return False
                
        except Exception as e:
            self.stop_loading()
            self.show_error(f"Error during embedding: {e}")
            return False
    
    def extract_data(self):
        """Extract data from a stego file"""
        # Select stego file
        stego_file = self.select_cover_file()
        if not stego_file:
            return False
        
        # Get password
        password = self.get_password("extraction")
        if password is None:
            return False
        
        # Check if file contains embedded data
        print(tag_asterisk() + "Checking file for embedded data...")
        
        cmd_info = [self.steghide_path, "info", stego_file]
        if password:
            cmd_info.extend(["-p", password])
        
        self.start_loading()
        try:
            result = subprocess.run(cmd_info, capture_output=True, text=True)
            self.stop_loading()
            
            if "could not extract any data" in result.stdout.lower():
                self.show_error("No embedded data found or wrong password")
                return False
            
            self.show_success("Embedded data found!")
            print()
            print(YELLOW + "File information:" + RESET)
            print(result.stdout)
            
        except Exception as e:
            self.stop_loading()
            self.show_error(f"Error checking file: {e}")
            return False
        
        # Ask for extraction
        extract = input(tag_gt() + "Extract embedded data? (y/n): ").strip().lower()
        print()
        if extract != 'y':
            self.show_error("Extraction cancelled")
            return False
        
        # Get output filename
        default_output = "extracted_data"
        output_file = input(tag_gt() + f"Output file name (default={default_output}): ").strip()
        print()
        if not output_file:
            output_file = default_output
        
        # Check if output file already exists
        if os.path.exists(output_file):
            overwrite = input(tag_gt() + f"File '{output_file}' exists. Overwrite? (y/n): ").strip().lower()
            print()
            if overwrite != 'y':
                self.show_error("Operation cancelled")
                return False
        
        # Build extraction command
        cmd_extract = [self.steghide_path, "extract", "-sf", stego_file, "-xf", output_file, "-f"]
        if password:
            cmd_extract.extend(["-p", password])
        
        # Run extraction
        print(tag_asterisk() + "Extracting data...")
        print(tag_gt() + "Command: " + CYAN + f"{' '.join(cmd_extract)}" + RESET)
        print()
        
        self.start_loading()
        try:
            result = subprocess.run(cmd_extract, capture_output=True, text=True)
            self.stop_loading()
            
            if result.returncode == 0:
                self.show_success("Extraction successful!")
                print()
                
                # Read and display the extracted file content
                extracted_content = ""
                if os.path.exists(output_file):
                    try:
                        # Try to read as text file
                        with open(output_file, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read().strip()
                            if content:
                                extracted_content = content
                            else:
                                extracted_content = "(empty file)"
                    except:
                        extracted_content = f"Binary file saved as {output_file}"
                
                print(BLUE + "_________________________________________________________________")
                print()
                print(tag_minus() + "Extracted Results: " + GREEN + extracted_content + RESET)
                print(BLUE + "_________________________________________________________________")
                print()
                print(tag_minus() + f"Extracted file: {output_file}")
                print(BLUE + "_________________________________________________________________")
                
                # Return True to indicate successful extraction - this will cause the program to exit
                return True
            else:
                self.show_error("Extraction failed!")
                if result.stderr:
                    print(RED + "Error: " + RESET + result.stderr.strip())
                return False
                
        except Exception as e:
            self.stop_loading()
            self.show_error(f"Error during extraction: {e}")
            return False
    
    def get_file_info(self):
        """Get information about a stego file"""
        # Select file
        stego_file = self.select_cover_file()
        if not stego_file:
            return False
        
        # Get password (optional for info)
        use_pass = input(tag_gt() + "Use password? (y/n, default=n): ").strip().lower()
        print()
        
        password = ""
        if use_pass == 'y':
            password = getpass.getpass(tag_gt() + "Enter password: ")
            print()
        
        # Build command
        cmd = [self.steghide_path, "info", stego_file]
        if password:
            cmd.extend(["-p", password])
        
        # Run command
        print(tag_asterisk() + "Getting file information...")
        print(tag_gt() + "Command: " + CYAN + f"{' '.join(cmd)}" + RESET)
        print()
        
        self.start_loading()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.stop_loading()
            
            if result.returncode == 0:
                self.show_success("File information:")
                print()
                print(result.stdout)
                return True
            else:
                self.show_error("Failed to get file information")
                if result.stderr:
                    print(RED + "Error: " + RESET + result.stderr.strip())
                return False
                
        except Exception as e:
            self.stop_loading()
            self.show_error(f"Error getting file info: {e}")
            return False
    
    def wordlist_attack(self, stego_file):
        """Try passwords from a wordlist"""
        # Check for wordlist.txt in current directory
        if os.path.exists(self.default_wordlist):
            wordcount = self.count_words(self.default_wordlist)
            if wordcount:
                self.show_info(f"Found wordlist: '{self.default_wordlist}' ({wordcount:,} words)")
                print()
                
                use_default = input(tag_gt() + f"Use '{self.default_wordlist}'? (y/n, default=y): ").strip().lower()
                print()
                
                if use_default != 'n':
                    wordlist = self.default_wordlist
                else:
                    wordlist = input(tag_gt() + "Enter path to custom wordlist: ").strip()
                    print()
            else:
                self.show_warning(f"Cannot read '{self.default_wordlist}'")
                wordlist = input(tag_gt() + "Enter path to wordlist: ").strip()
                print()
        else:
            self.show_info(f"Default wordlist not found: '{self.default_wordlist}'")
            wordlist = input(tag_gt() + "Enter path to wordlist: ").strip()
            print()
        
        if not wordlist or not os.path.exists(wordlist):
            self.show_error(f"Wordlist not found: {wordlist}")
            return False
        
        # Count words in wordlist
        wordcount = self.count_words(wordlist)
        if not wordcount:
            self.show_error("Wordlist is empty or cannot be read")
            return False
        
        self.show_info(f"Wordlist contains {wordcount:,} passwords")
        print()
        
        # Get output filename
        output_file = input(tag_gt() + "Output file name for extracted data (default=extracted): ").strip()
        print()
        if not output_file:
            output_file = "extracted"
        
        # Create temporary directory for attempts
        temp_dir = tempfile.mkdtemp(prefix="steghide_bf_")
        
        print(tag_asterisk() + "Starting wordlist attack...")
        print(tag_asterisk() + "Press Ctrl+C to stop at any time")
        print()
        
        passwords_tried = 0
        start_time = time.time()
        last_password = ""
        
        try:
            with open(wordlist, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    password = line.strip()
                    if not password:
                        continue
                    
                    passwords_tried += 1
                    last_password = password
                    
                    # Update progress bar every attempt (but only redraw every 100ms to avoid flicker)
                    if passwords_tried % 10 == 0 or passwords_tried == 1:
                        self.draw_progress_bar(passwords_tried, wordcount, start_time, last_password)
                    
                    # Try extraction with this password
                    temp_output = os.path.join(temp_dir, f"attempt_{passwords_tried}")
                    cmd = [self.steghide_path, "extract", "-sf", stego_file, "-xf", temp_output, "-p", password, "-f"]
                    
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if result.returncode == 0:
                            # Success!
                            elapsed = time.time() - start_time
                            print()  # New line after progress bar
                            print()
                            self.show_success(GREEN + f"PASSWORD FOUND: {password}" + RESET)
                            print()
                            self.show_info(f"Found after {passwords_tried:,} attempts ({elapsed:.1f} seconds)")
                            
                            # Copy to final output
                            shutil.copy(temp_output, output_file)
                            
                            # Read and display the extracted file content
                            extracted_content = ""
                            if os.path.exists(output_file):
                                try:
                                    # Try to read as text file
                                    with open(output_file, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read().strip()
                                        if content:
                                            extracted_content = content
                                        else:
                                            extracted_content = "(empty file)"
                                except:
                                    extracted_content = f"Binary file saved as {output_file}"
                            
                            print()
                            print(BLUE + "_________________________________________________________________")
                            print()
                            print(tag_minus() + "Extracted Results: " + GREEN + extracted_content + RESET)
                            print(BLUE + "_________________________________________________________________")
                            print()
                            print(tag_minus() + f"Extracted file: {output_file}")
                            print(BLUE + "_________________________________________________________________")
                            
                            # Cleanup and return
                            shutil.rmtree(temp_dir)
                            return True
                            
                    except:
                        continue
            
            # If we get here, no password found
            elapsed = time.time() - start_time
            print()  # New line after progress bar
            self.show_error(f"No password found after {passwords_tried:,} attempts ({elapsed:.1f} seconds)")
            return False
            
        except KeyboardInterrupt:
            print()
            self.show_error("Stopped by user")
            elapsed = time.time() - start_time
            self.show_info(f"Tried {passwords_tried:,} passwords in {elapsed:.1f} seconds")
            return False
            
        except Exception as e:
            print()
            self.show_error(f"Error during wordlist attack: {e}")
            return False
            
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def brute_force_extract(self):
        """Attempt to extract data using brute force or wordlist"""
        # Select stego file
        stego_file = self.select_cover_file()
        if not stego_file:
            return False
        
        print(BLUE + "____________________________ " + GREEN + "Options" + BLUE + " ____________________________")
        print()
        print(YELLOW + "[1]" + RESET + " Wordlist attack (using wordlist.txt)")
        print(YELLOW + "[2]" + RESET + " Return to main menu")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            choice = int(input(tag_gt() + "Select option (1-2): "))
            print()
        except ValueError:
            self.show_error("Invalid choice")
            return False
        
        if choice == 1:
            return self.wordlist_attack(stego_file)
        else:
            return False
    
    def select_operation(self):
        """Select steghide operation"""
        print()
        print(BLUE + "_______________________ " + GREEN + "Steghide Options" + BLUE + " ________________________")
        print()
        print(YELLOW + "[1]" + RESET + " Embed data into file")
        print(YELLOW + "[2]" + RESET + " Extract data from file")
        print(YELLOW + "[3]" + RESET + " Get file information")
        print(YELLOW + "[4]" + RESET + " Brute force extraction")
        print(YELLOW + "[5]" + RESET + " Exit")
        print(BLUE + "_________________________________________________________________")
        print()
        
        try:
            return int(input(tag_gt() + "Select option (1-5): "))
        except:
            self.show_error("Please enter a number")
            return None
    
    def main_loop(self):
        """Main program loop"""
        if not self.check_tools():
            self.show_error("Steghide not found. Please install: sudo apt install steghide")
            input(tag_gt() + "Press Enter to continue...")
            return
        
        while True:
            print()
            choice = self.select_operation()
            
            if choice == 1:
                self.embed_data()
                print()
                input(tag_gt() + "Press Enter to continue...")
            elif choice == 2:
                # If extraction successful, exit without asking for input
                if self.extract_data():
                    return  # Exit the program on successful extraction
                print()
                input(tag_gt() + "Press Enter to continue...")
            elif choice == 3:
                self.get_file_info()
                print()
                input(tag_gt() + "Press Enter to continue...")
            elif choice == 4:
                # If brute force successful, exit without asking for input
                if self.brute_force_extract():
                    return  # Exit the program on successful extraction
                print()
                input(tag_gt() + "Press Enter to continue...")
            elif choice == 5:
                # Exit silently
                return
            else:
                self.show_error("Invalid choice")
                print()
                input(tag_gt() + "Press Enter to continue...")

def main():
    """Main function - for standalone testing only"""
    try:
        # Enable virtual terminal processing on Windows
        if platform.system() == "Windows":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except:
                pass
        
        cracker = SteghideCracker()
        cracker.main_loop()
        
    except KeyboardInterrupt:
        print(RED + "\n[x] Program stopped by user" + RESET)
    except Exception as e:
        print(RED + f"\n[x] Error: {e}" + RESET)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # This allows the file to be imported as a module or run standalone for testing
    main()
