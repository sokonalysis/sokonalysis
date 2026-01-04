#!/usr/bin/env python3
"""
Steghide Steganography Tool Wrapper
Complete workflow for hiding and extracting data from images
Colorful Interface
"""

import os
import sys
import subprocess
import time
import tempfile
import shutil
import getpass

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

class SteghideTool:
    def __init__(self):
        self.steghide_path = "steghide"
        self.current_dir = os.getcwd()
        self.supported_extensions = ['.jpg', '.jpeg', '.bmp', '.wav', '.au']
        self.temp_dir = None
        self.default_wordlist = "wordlist.txt"
    
    def clear_screen(self):
        """Clear screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def show_banner(self):
        """Show colorful banner"""
        self.clear_screen()
        print(tag_minus() + "STEGHIDE STEGANOGRAPHY TOOL")
        print(c_cyan("   Hide and extract data from images and audio files"))
        print()
    
    def check_tools(self):
        """Check if steghide is available"""
        self.show_banner()
        print(tag_asterisk() + "Checking for required tools...")
        
        # Check for steghide
        try:
            result = subprocess.run([self.steghide_path, "--version"], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0 or "steghide" in result.stdout.lower():
                print(tag_plus() + f"Steghide: Found at '{self.steghide_path}'")
                print(tag_info() + f"Version: {result.stdout.strip()}")
                
                # Check for wordlist
                if os.path.exists(self.default_wordlist):
                    wordcount = self.count_words(self.default_wordlist)
                    if wordcount:
                        print(tag_plus() + f"Default wordlist: '{self.default_wordlist}' ({wordcount:,} words)")
                    else:
                        print(tag_exclamation() + f"Cannot read wordlist: {self.default_wordlist}")
                else:
                    print(tag_exclamation() + f"Default wordlist not found: '{self.default_wordlist}'")
                    print(c_yellow("    Note: Wordlist is optional for brute force attacks"))
                
                return True
            else:
                print(tag_exclamation() + "Steghide not working properly")
                return False
        except FileNotFoundError:
            print(tag_exclamation() + "Steghide not found!")
            print(c_yellow("    Install with: sudo apt install steghide"))
            return False
        except Exception as e:
            print(tag_exclamation() + f"Error checking steghide: {e}")
            return False
    
    def count_words(self, filepath):
        """Count words in a file, handling different encodings"""
        if not os.path.exists(filepath):
            return 0
        
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'ascii']
        
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
                    wordcount = sum(1 for line in f if line.strip())
                return wordcount
            except UnicodeDecodeError:
                continue
        
        return 0
    
    def list_supported_files(self):
        """List supported image/audio files in current directory"""
        files = []
        
        print(c_cyan("\n📁") + " Current Directory: " + c_yellow(self.current_dir))
        print(c_yellow("📸") + " Supported formats: JPG, JPEG, BMP, WAV, AU")
        print()
        print(tag_minus() + "AVAILABLE COVER FILES")
        
        idx = 1
        for file in sorted(os.listdir('.')):
            if any(file.lower().endswith(ext) for ext in self.supported_extensions):
                if os.path.isfile(file):
                    size = os.path.getsize(file)
                    if size < 1024:
                        size_str = f"{size}B"
                    elif size < 1024*1024:
                        size_str = f"{size/1024:.1f}KB"
                    else:
                        size_str = f"{size/(1024*1024):.1f}MB"
                    
                    files.append(file)
                    print(c_yellow(f"[{idx}]") + f" {file}" + c_cyan(f" ({size_str})"))
                    idx += 1
        
        return files
    
    def list_data_files(self):
        """List data files that can be embedded - filtering out source code, binaries, and tool files"""
        files = []
        
        print(tag_minus() + "AVAILABLE DATA FILES")
        
        idx = 1
        for file in sorted(os.listdir('.')):
            if not os.path.isfile(file):
                continue
            
            # Skip specific tool files that we never want to show
            skip_files = [
                'wordlist.txt',  # Too large, not a typical data file
                'sokonalysis',   # Binary executable
                'sokonalysis_gui.py',  # GUI application
                'requirements.txt',  # Configuration file
                'build.log',     # Build log
            ]
            
            if file in skip_files:
                continue
            
            # Skip files with specific patterns in name
            skip_patterns = [
                'cracked_',  # Output files from cracking tools
                'john',      # John the Ripper related files
                'handshake', # WiFi handshake files
                'stb_',      # Library headers
                'wifi_cracked',  # WiFi cracking results
                'cracked_windows',  # Windows password cracking results
                'cracked_pdf',  # PDF cracking results
            ]
            
            if any(pattern in file.lower() for pattern in skip_patterns):
                continue
            
            # Skip source code files (Python, C/C++, etc.)
            if file.endswith(('.py', '.cpp', '.c', '.h', '.hpp', '.java', '.js', '.html', '.css', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.cs', '.ts')):
                continue
            
            # Skip executables and binaries
            if file.endswith(('.exe', '.bin', '.so', '.dll', '.dylib', '.app', '.out')):
                continue
            
            # Skip archive files
            if file.endswith(('.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz')):
                continue
            
            # Skip image/audio files (these are cover files, not data files)
            if file.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.tif', '.wav', '.au', '.mp3', '.flac', '.ogg')):
                continue
            
            # Skip configuration and log files (except .txt which we want to keep)
            if file.endswith(('.log', '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf')):
                continue
            
            # Skip markdown files
            if file.endswith(('.md', '.rst', '.tex')):
                continue
            
            # Additional check: skip files that look like source code by content
            # But allow .txt files and files without extensions
            if not file.endswith('.txt'):
                try:
                    with open(file, 'rb') as f:
                        first_bytes = f.read(200)
                        # Check for common source code indicators
                        source_indicators = [
                            b'#include', b'def ', b'class ', b'import ', 
                            b'function ', b'<?php', b'<html', b'#!/',
                            b'//', b'/*', b'#pragma', b'namespace ',
                            b'#include <', b'#include "', b'using namespace',
                            b'#define ', b'#ifndef ', b'#endif'
                        ]
                        if any(indicator in first_bytes.lower() for indicator in source_indicators):
                            continue
                except:
                    pass  # If we can't read it, include it anyway
            
            size = os.path.getsize(file)
            if size < 1024:
                size_str = f"{size}B"
            elif size < 1024*1024:
                size_str = f"{size/1024:.1f}KB"
            else:
                size_str = f"{size/(1024*1024):.1f}MB"
            
            files.append(file)
            print(c_yellow(f"[{idx}]") + f" {file}" + c_cyan(f" ({size_str})"))
            idx += 1
        
        # If no files found after filtering, show a helpful message
        if not files:
            print(tag_exclamation() + "No suitable data files found after filtering!")
            print(c_yellow("    Filtered out: source code, executables, archives, images, tool files"))
            print(c_yellow("    To embed a specific file, use 'Enter custom path' option"))
        
        return files
    
    def select_file(self, file_type="cover", prompt="Select file"):
        """Let user select a file"""
        self.show_banner()
        
        print(c_yellow("📁") + f" Current working directory: {self.current_dir}")
        
        if file_type == "cover":
            files = self.list_supported_files()
            file_desc = "cover files (images/audio)"
        else:
            files = self.list_data_files()
            file_desc = "data files"
        
        if not files:
            print(tag_exclamation() + f"No {file_desc} found in current directory!")
            print(c_yellow("\n💡") + f" Tip: Place files in: {self.current_dir}")
            print()
            
            if file_type == "cover":
                print(tag_minus() + "COVER FILE SELECTION OPTIONS")
            else:
                print(tag_minus() + "DATA FILE SELECTION OPTIONS")
                
            print(c_yellow("[1]") + " Enter file path manually")
            print(c_yellow("[2]") + " Return to main menu")
            
            choice = input(tag_gt() + "Select option (1-2): ").strip()
            if choice == "1":
                path = input(tag_gt() + f"Enter full path to {file_type} file: ").strip()
                if os.path.exists(path):
                    return path
                else:
                    print(tag_exclamation() + f"File not found: {path}")
                    input(tag_gt() + "Press Enter to continue...")
                    return None
            else:
                return None
        
        print(c_yellow(f"[{len(files)+1}]") + " Enter custom path")
        print(c_yellow(f"[{len(files)+2}]") + " Return to main menu")
        
        try:
            choice = int(input(tag_gt() + f"{prompt} (1-{len(files)+2}): "))
            
            if 1 <= choice <= len(files):
                selected = files[choice-1]
                print(tag_minus() + f"Selected: {selected}")
                return selected
            elif choice == len(files) + 1:
                path = input(tag_gt() + f"Enter full path to {file_type} file: ").strip()
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
    
    def get_password(self, action="embed"):
        """Get password from user"""
        print(tag_info() + "Password is optional but recommended for security")
        
        use_pass = input(tag_gt() + f"Use password for {action}? (y/n, default=n): ").strip().lower()
        
        if use_pass == 'y':
            password = getpass.getpass(tag_gt() + f"Enter password for {action}: ")
            if password:
                verify = getpass.getpass(tag_gt() + "Verify password: ")
                if password == verify:
                    return password
                else:
                    print(tag_exclamation() + "Passwords don't match!")
                    return None
            else:
                print(tag_exclamation() + "Empty password entered")
                return ""
        else:
            return ""
    
    def embed_data(self):
        """Embed data into a cover file"""
        self.show_banner()
        print(tag_minus() + "EMBED DATA INTO FILE")
        print()
        
        # Select cover file
        cover_file = self.select_file("cover", "Select cover file (image/audio)")
        if not cover_file:
            return
        
        # Select data file
        data_file = self.select_file("data", "Select data file to embed")
        if not data_file:
            return
        
        # Get output filename (optional)
        print(tag_info() + "By default, embeds directly into cover file (overwrites)")
        use_custom_output = input(tag_gt() + "Create separate output file? (y/n, default=n): ").strip().lower()
        
        output_file = None
        if use_custom_output == 'y':
            default_output = f"stego_{os.path.basename(cover_file)}"
            output_file = input(tag_gt() + f"Output file name (default={default_output}): ").strip()
            if not output_file:
                output_file = default_output
            
            # Check if output file already exists
            if os.path.exists(output_file):
                overwrite = input(tag_gt() + f"File '{output_file}' exists. Overwrite? (y/n): ").strip().lower()
                if overwrite != 'y':
                    print(tag_exclamation() + "Operation cancelled")
                    input(tag_gt() + "Press Enter to continue...")
                    return
        
        # Get password
        password = self.get_password("embedding")
        if password is None:  # Password mismatch
            input(tag_gt() + "Press Enter to continue...")
            return
        
        # Get compression level (optional)
        print(tag_info() + "Compression: Higher = smaller file but slower embedding")
        use_compression = input(tag_gt() + "Use compression? (y/n, default=n): ").strip().lower()
        compression = None
        if use_compression == 'y':
            compression = input(tag_gt() + "Compression level (1-9, default=9): ").strip()
            if not compression:
                compression = "9"
        
        # Get encryption algorithm (optional)
        print(tag_info() + "Encryption algorithms available in steghide:")
        print(c_yellow("    cbc") + " - Cipher Block Chaining (default)")
        print(c_yellow("    ebc") + " - Electronic Code Book")
        print(c_yellow("    ofb") + " - Output Feedback")
        print(c_yellow("    cfb") + " - Cipher Feedback")
        print(c_yellow("    ncfb") + " - N-bit Cipher Feedback")
        print(c_yellow("    nofb") + " - N-bit Output Feedback")
        
        use_encryption = input(tag_gt() + "Specify encryption algorithm? (y/n, default=n): ").strip().lower()
        algorithm = None
        if use_encryption == 'y':
            algorithm = input(tag_gt() + "Encryption algorithm (default=cbc): ").strip().lower()
            if not algorithm:
                algorithm = "cbc"
        
        # Build command - Note: -ef comes before -cf as per steghide examples
        cmd = [
            self.steghide_path,
            "embed",
            "-ef", data_file,
            "-cf", cover_file
        ]
        
        # Add output file option only if user wants separate file
        if output_file:
            cmd.extend(["-sf", output_file])
        
        # Add compression only if user wants it
        if compression:
            cmd.extend(["-z", compression])
        
        # Add encryption algorithm only if user specifies it
        if algorithm:
            cmd.extend(["-e", algorithm])
        
        # Add password if specified
        if password:
            cmd.extend(["-p", password])
        
        # Add verbose flag for more output
        cmd.append("-v")
        
        # Confirm before embedding
        self.show_banner()
        print(tag_minus() + "EMBEDDING CONFIRMATION")
        print()
        print(c_yellow("Cover file:") + f" {cover_file}")
        print(c_yellow("Data file:") + f" {data_file}")
        
        if output_file:
            print(c_yellow("Output file:") + f" {output_file}")
        else:
            print(c_yellow("Output:") + " Embedded in cover file (overwrites)")
        
        if compression:
            print(c_yellow("Compression:") + f" {compression}")
        else:
            print(c_yellow("Compression:") + " None (default)")
        
        if algorithm:
            print(c_yellow("Encryption:") + f" {algorithm}")
        else:
            print(c_yellow("Encryption:") + " Default (cbc)")
        
        print(c_yellow("Password:") + " " + ("Yes" if password else "No"))
        
        print()
        confirm = input(tag_gt() + "Proceed with embedding? (y/n): ").strip().lower()
        if confirm != 'y':
            print(tag_exclamation() + "Operation cancelled")
            input(tag_gt() + "Press Enter to continue...")
            return
        
        # Run command
        print()
        print(tag_asterisk() + "Embedding data...")
        print(tag_gt() + f"Command: {' '.join(cmd)}")
        print()
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(tag_plus() + "Embedding successful!")
                
                # Determine which file was created
                if output_file:
                    final_file = output_file
                else:
                    final_file = cover_file
                    print(tag_info() + "Data embedded directly into cover file")
                
                if os.path.exists(final_file):
                    print(tag_info() + f"Final file: {final_file}")
                
                # Show verbose output
                if result.stdout:
                    print(c_cyan("\nVerbose output:"))
                    print(result.stdout.strip())
            else:
                print(tag_exclamation() + "Embedding failed!")
                if result.stderr:
                    error_msg = result.stderr.strip()
                    print(c_red("Error: ") + error_msg)
                    # Provide helpful suggestions for common errors
                    if "algorithm" in error_msg.lower():
                        print(c_yellow("    Tip: Use one of: cbc, ebc, ofb, cfb, ncfb, nofb"))
                    elif "capacity" in error_msg.lower():
                        print(c_yellow("    Tip: Data file might be too large for this cover image"))
                    elif "already contains data" in error_msg.lower():
                        print(c_yellow("    Tip: File already has embedded data. Use -sf to create new file"))
                else:
                    print(c_red("Error: ") + result.stdout.strip())
                
        except Exception as e:
            print(tag_x() + f"Error during embedding: {e}")
        
        input(tag_gt() + "Press Enter to continue...")
    
    def extract_data(self):
        """Extract data from a stego file"""
        self.show_banner()
        print(tag_minus() + "EXTRACT DATA FROM FILE")
        print()
        
        # Select stego file
        stego_file = self.select_file("cover", "Select stego file")
        if not stego_file:
            return
        
        # Get password
        password = self.get_password("extraction")
        if password is None:  # Password mismatch
            input(tag_gt() + "Press Enter to continue...")
            return
        
        # Check if file contains embedded data
        print()
        print(tag_asterisk() + "Checking file for embedded data...")
        
        cmd_info = [self.steghide_path, "info", stego_file]
        if password:
            cmd_info.extend(["-p", password])
        
        try:
            result = subprocess.run(cmd_info, capture_output=True, text=True)
            
            if "could not extract any data" in result.stdout.lower():
                print(tag_exclamation() + "No embedded data found or wrong password")
                input(tag_gt() + "Press Enter to continue...")
                return
            
            print(tag_plus() + "Embedded data found!")
            print()
            print(c_yellow("File information:"))
            print(result.stdout)
            
        except Exception as e:
            print(tag_x() + f"Error checking file: {e}")
            input(tag_gt() + "Press Enter to continue...")
            return
        
        # Ask for extraction
        extract = input(tag_gt() + "Extract embedded data? (y/n): ").strip().lower()
        if extract != 'y':
            print(tag_exclamation() + "Extraction cancelled")
            input(tag_gt() + "Press Enter to continue...")
            return
        
        # Get output filename
        default_output = "extracted_data"
        output_file = input(tag_gt() + f"Output file name (default={default_output}): ").strip()
        if not output_file:
            output_file = default_output
        
        # Check if output file already exists
        if os.path.exists(output_file):
            overwrite = input(tag_gt() + f"File '{output_file}' exists. Overwrite? (y/n): ").strip().lower()
            if overwrite != 'y':
                print(tag_exclamation() + "Operation cancelled")
                input(tag_gt() + "Press Enter to continue...")
                return
        
        # Build extraction command with -f flag to force overwrite
        cmd_extract = [self.steghide_path, "extract", "-sf", stego_file, "-xf", output_file, "-f"]
        if password:
            cmd_extract.extend(["-p", password])
        
        # Run extraction
        print()
        print(tag_asterisk() + "Extracting data...")
        print(tag_gt() + f"Command: {' '.join(cmd_extract)}")
        print()
        
        try:
            result = subprocess.run(cmd_extract, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(tag_plus() + "Extraction successful!")
                print(tag_info() + f"Extracted file: {output_file}")
                
                # Show extracted file info
                if os.path.exists(output_file):
                    size = os.path.getsize(output_file)
                    if size < 1024:
                        size_str = f"{size}B"
                    elif size < 1024*1024:
                        size_str = f"{size/1024:.1f}KB"
                    else:
                        size_str = f"{size/(1024*1024):.1f}MB"
                    
                    print(tag_info() + f"Extracted size: {size_str}")
                    
                    # Try to determine file type
                    try:
                        import magic
                        mime = magic.Magic(mime=True)
                        file_type = mime.from_file(output_file)
                        print(tag_info() + f"File type: {file_type}")
                    except:
                        pass
            else:
                print(tag_exclamation() + "Extraction failed!")
                if result.stderr:
                    print(c_red("Error: ") + result.stderr.strip())
                else:
                    print(c_red("Error: ") + result.stdout.strip())
                
        except Exception as e:
            print(tag_x() + f"Error during extraction: {e}")
        
        input(tag_gt() + "Press Enter to continue...")
    
    def get_file_info(self):
        """Get information about a stego file"""
        self.show_banner()
        print(tag_minus() + "GET FILE INFORMATION")
        print()
        
        # Select file
        stego_file = self.select_file("cover", "Select file to analyze")
        if not stego_file:
            return
        
        # Get password (optional for info)
        print(tag_info() + "Password is optional for getting basic information")
        use_pass = input(tag_gt() + "Use password? (y/n, default=n): ").strip().lower()
        
        password = ""
        if use_pass == 'y':
            password = getpass.getpass(tag_gt() + "Enter password: ")
        
        # Build command
        cmd = [self.steghide_path, "info", stego_file]
        if password:
            cmd.extend(["-p", password])
        
        # Run command
        print()
        print(tag_asterisk() + "Getting file information...")
        print(tag_gt() + f"Command: {' '.join(cmd)}")
        print()
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(tag_plus() + "File information:")
                print()
                
                # Colorize output
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if "format:" in line.lower():
                        print(c_cyan(line))
                    elif "capacity:" in line.lower():
                        print(c_green(line))
                    elif "embedded file" in line.lower():
                        print(c_yellow(line))
                    elif "encryption:" in line.lower():
                        print(c_magenta(line))
                    elif "compression:" in line.lower():
                        print(c_blue(line))
                    else:
                        print(line)
            else:
                print(tag_exclamation() + "Failed to get file information")
                if result.stderr:
                    print(c_red("Error: ") + result.stderr.strip())
                else:
                    print(c_red("Error: ") + result.stdout.strip())
                
        except Exception as e:
            print(tag_x() + f"Error getting file info: {e}")
        
        input(tag_gt() + "Press Enter to continue...")
    
    def brute_force_extract(self):
        """Attempt to extract data using brute force or wordlist"""
        self.show_banner()
        print(tag_minus() + "BRUTE FORCE EXTRACTION")
        print(c_red("⚠") + " This may take a long time!")
        print()
        
        # Select stego file
        stego_file = self.select_file("cover", "Select stego file")
        if not stego_file:
            return
        
        # Ask for attack method
        print(tag_minus() + "SELECT ATTACK METHOD")
        print(c_yellow("[1]") + " Wordlist attack (using wordlist.txt)")
        print(c_yellow("[2]") + " Simple brute force (digits only)")
        print(c_yellow("[3]") + " Return to main menu")
        
        try:
            choice = int(input(tag_gt() + "Select option (1-3): "))
        except ValueError:
            print(tag_exclamation() + "Invalid choice")
            input(tag_gt() + "Press Enter to continue...")
            return
        
        if choice == 1:
            self.wordlist_attack(stego_file)
        elif choice == 2:
            self.simple_bruteforce(stego_file)
        elif choice == 3:
            return
        else:
            print(tag_exclamation() + "Invalid choice")
            input(tag_gt() + "Press Enter to continue...")
    
    def wordlist_attack(self, stego_file):
        """Try passwords from a wordlist"""
        print()
        print(tag_minus() + "WORDLIST ATTACK")
        
        # Check for wordlist.txt in current directory
        if os.path.exists(self.default_wordlist):
            # Get wordlist info
            wordcount = self.count_words(self.default_wordlist)
            if wordcount:
                # Show file size
                filesize = os.path.getsize(self.default_wordlist)
                if filesize < 1024:
                    size_str = f"{filesize}B"
                elif filesize < 1024*1024:
                    size_str = f"{filesize/1024:.1f}KB"
                else:
                    size_str = f"{filesize/(1024*1024):.1f}MB"
                
                print(c_yellow("📄") + f" Found wordlist: '{self.default_wordlist}'")
                print(tag_info() + f"Size: {size_str}, Words: {wordcount:,}")
                
                use_default = input(tag_gt() + f"Use '{self.default_wordlist}'? (y/n, default=y): ").strip().lower()
                
                if use_default != 'n':
                    wordlist = self.default_wordlist
                else:
                    wordlist = input(tag_gt() + "Enter path to custom wordlist: ").strip()
            else:
                print(tag_exclamation() + f"Cannot read '{self.default_wordlist}'")
                wordlist = input(tag_gt() + "Enter path to wordlist: ").strip()
        else:
            print(c_yellow("📄") + f" Default wordlist not found: '{self.default_wordlist}'")
            wordlist = input(tag_gt() + "Enter path to wordlist: ").strip()
        
        if not wordlist or not os.path.exists(wordlist):
            print(tag_exclamation() + f"Wordlist not found: {wordlist}")
            input(tag_gt() + "Press Enter to continue...")
            return
        
        # Count words in wordlist
        wordcount = self.count_words(wordlist)
        if not wordcount:
            print(tag_exclamation() + "Wordlist is empty or cannot be read")
            input(tag_gt() + "Press Enter to continue...")
            return
        
        print(tag_info() + f"Wordlist contains {wordcount:,} passwords")
        
        # Get output filename
        output_file = input(tag_gt() + "Output file name for extracted data (default=extracted): ").strip()
        if not output_file:
            output_file = "extracted"
        
        # Create temporary directory for attempts
        temp_dir = tempfile.mkdtemp(prefix="steghide_bf_")
        
        print()
        print(tag_asterisk() + "Starting wordlist attack...")
        print(c_red("⚠") + " Press Ctrl+C to stop at any time")
        print()
        
        passwords_tried = 0
        start_time = time.time()
        
        try:
            with open(wordlist, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    password = line.strip()
                    if not password:
                        continue
                    
                    passwords_tried += 1
                    
                    # Show progress every 100 attempts
                    if passwords_tried % 100 == 0:
                        elapsed = time.time() - start_time
                        rate = passwords_tried / elapsed if elapsed > 0 else 0
                        progress = (passwords_tried / wordcount) * 100
                        print(tag_info() + f"Tried {passwords_tried:,}/{wordcount:,} passwords ({progress:.1f}%, {rate:.1f}/sec)")
                    
                    # Try extraction with this password
                    temp_output = os.path.join(temp_dir, f"attempt_{passwords_tried}")
                    cmd = [self.steghide_path, "extract", "-sf", stego_file, "-xf", temp_output, "-p", password, "-f"]
                    
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if result.returncode == 0:
                            # Success!
                            elapsed = time.time() - start_time
                            print(tag_plus() + c_green(f"PASSWORD FOUND: {password}"))
                            print(tag_info() + f"Found after {passwords_tried:,} attempts ({elapsed:.1f} seconds)")
                            
                            # Copy to final output
                            shutil.copy(temp_output, output_file)
                            print(tag_info() + f"Data extracted to: {output_file}")
                            
                            # Show extracted file info
                            if os.path.exists(output_file):
                                size = os.path.getsize(output_file)
                                if size < 1024:
                                    size_str = f"{size}B"
                                elif size < 1024*1024:
                                    size_str = f"{size/1024:.1f}KB"
                                else:
                                    size_str = f"{size/(1024*1024):.1f}MB"
                                
                                print(tag_info() + f"Extracted file size: {size_str}")
                            
                            # Cleanup and return
                            shutil.rmtree(temp_dir)
                            input(tag_gt() + "Press Enter to continue...")
                            return
                            
                    except:
                        continue
            
            # If we get here, no password found
            elapsed = time.time() - start_time
            print(tag_exclamation() + f"No password found after {passwords_tried:,} attempts ({elapsed:.1f} seconds)")
            
        except KeyboardInterrupt:
            print(c_red("\n\n[x]") + " Stopped by user")
            elapsed = time.time() - start_time
            print(tag_info() + f"Tried {passwords_tried:,} passwords in {elapsed:.1f} seconds")
            print(tag_info() + f"Speed: {passwords_tried/elapsed:.1f} passwords/sec" if elapsed > 0 else "")
        
        except Exception as e:
            print(tag_x() + f"Error during wordlist attack: {e}")
        
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            input(tag_gt() + "Press Enter to continue...")
    
    def simple_bruteforce(self, stego_file):
        """Simple brute force with digits only"""
        print()
        print(tag_minus() + "SIMPLE BRUTE FORCE (DIGITS ONLY)")
        print(c_red("⚠") + " WARNING: This will try ALL digit combinations!")
        
        max_length = input(tag_gt() + "Maximum password length (default=6): ").strip()
        if not max_length:
            max_length = 6
        else:
            max_length = int(max_length)
        
        output_file = input(tag_gt() + "Output file name (default=extracted): ").strip()
        if not output_file:
            output_file = "extracted"
        
        confirm = input(tag_gt() + f"This will try up to {10**max_length:,} combinations. Continue? (y/n): ").strip().lower()
        if confirm != 'y':
            print(tag_exclamation() + "Operation cancelled")
            input(tag_gt() + "Press Enter to continue...")
            return
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="steghide_brute_")
        
        print()
        print(tag_asterisk() + "Starting brute force attack...")
        print(c_red("⚠") + " Press Ctrl+C to stop at any time")
        print()
        
        passwords_tried = 0
        start_time = time.time()
        
        try:
            # Import itertools for combinations
            import itertools
            
            for length in range(1, max_length + 1):
                print(tag_info() + f"Trying passwords of length {length}...")
                
                for combo in itertools.product('0123456789', repeat=length):
                    password = ''.join(combo)
                    passwords_tried += 1
                    
                    # Show progress
                    if passwords_tried % 1000 == 0:
                        elapsed = time.time() - start_time
                        rate = passwords_tried / elapsed if elapsed > 0 else 0
                        print(tag_info() + f"Tried {passwords_tried:,} passwords ({rate:.0f}/sec)")
                    
                    # Try extraction
                    temp_output = os.path.join(temp_dir, f"attempt_{passwords_tried}")
                    cmd = [self.steghide_path, "extract", "-sf", stego_file, "-xf", temp_output, "-p", password, "-f"]
                    
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if result.returncode == 0:
                            # Success!
                            elapsed = time.time() - start_time
                            print(tag_plus() + c_green(f"PASSWORD FOUND: {password}"))
                            print(tag_info() + f"Found after {passwords_tried} attempts ({elapsed:.1f} seconds)")
                            
                            # Copy to final output
                            shutil.copy(temp_output, output_file)
                            print(tag_info() + f"Data extracted to: {output_file}")
                            
                            # Cleanup
                            shutil.rmtree(temp_dir)
                            input(tag_gt() + "Press Enter to continue...")
                            return
                            
                    except:
                        continue
        
        except KeyboardInterrupt:
            print(c_red("\n\n[x]") + " Stopped by user")
            elapsed = time.time() - start_time
            print(tag_info() + f"Tried {passwords_tried:,} passwords in {elapsed:.1f} seconds")
        
        except Exception as e:
            print(tag_x() + f"Error during brute force: {e}")
        
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            print(tag_exclamation() + f"No password found after {passwords_tried:,} attempts")
            input(tag_gt() + "Press Enter to continue...")
    
    def main_menu(self):
        """Display main menu"""
        self.show_banner()
        print(tag_minus() + "MAIN MENU")
        
        print(c_yellow("[1]") + " Embed data into file")
        print(c_yellow("[2]") + " Extract data from file")
        print(c_yellow("[3]") + " Get file information")
        print(c_yellow("[4]") + " Brute force extraction")
        print(c_yellow("[5]") + " Exit")
        
        try:
            choice = int(input(tag_gt() + "Select option (1-5): "))
            return choice
        except ValueError:
            print(tag_exclamation() + "Please enter a number")
            input(tag_gt() + "Press Enter to continue...")
            return None
    
    def main_loop(self):
        """Main program loop"""
        if not self.check_tools():
            print(tag_exclamation() + "Please install steghide and try again")
            input(tag_gt() + "Press Enter to exit...")
            return
        
        while True:
            choice = self.main_menu()
            
            if choice == 1:
                self.embed_data()
            elif choice == 2:
                self.extract_data()
            elif choice == 3:
                self.get_file_info()
            elif choice == 4:
                self.brute_force_extract()
            elif choice == 5:
                print(tag_asterisk() + "Goodbye!")
                break
            else:
                print(tag_exclamation() + "Invalid choice")
                input(tag_gt() + "Press Enter to continue...")

def main():
    """Main function"""
    try:
        tool = SteghideTool()
        tool.main_loop()
    except KeyboardInterrupt:
        print(c_red("\n\n[x]") + " Program stopped by user")
    except Exception as e:
        print(c_red("\n[x]") + f" Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
