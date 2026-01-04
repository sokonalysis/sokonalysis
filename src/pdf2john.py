#!/usr/bin/env python3
"""
PDF Document Password Cracker
Complete workflow using pdf2john for hash extraction
Colorful Interface
"""

import os
import sys
import subprocess
import time
import tempfile
import shutil

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

class PDFCracker:
    def __init__(self):
        self.john_path = "john"
        self.document = None
        self.hash_file = None
        self.default_wordlist = "wordlist.txt"
        self.pdf2john_path = "/usr/share/john/pdf2john.py"
        self.current_dir = os.getcwd()  # Get current directory
    
    def clear_screen(self):
        """Clear screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def show_banner(self):
        """Show colorful banner"""
        self.clear_screen()
        print(tag_minus() + "PDF DOCUMENT PASSWORD CRACKER")
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
            print(c_yellow("    Install with: sudo apt install john"))
            return False
        
        # Check for pdf2john
        if not os.path.exists(self.pdf2john_path):
            print(tag_exclamation() + f"pdf2john not found at: {self.pdf2john_path}")
            print(c_yellow("    Install with: sudo apt install john"))
            # Try alternative location
            self.pdf2john_path = "/usr/bin/pdf2john"
            if not os.path.exists(self.pdf2john_path):
                print(tag_exclamation() + f"pdf2john not found at: {self.pdf2john_path}")
                return False
            else:
                print(tag_plus() + f"pdf2john: Found at '{self.pdf2john_path}'")
        else:
            print(tag_plus() + f"pdf2john: Found at '{self.pdf2john_path}'")
        
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
    
    def extract_hash(self, document_path):
        """Extract hash from PDF document using pdf2john"""
        self.show_banner()
        print(tag_asterisk() + f"Extracting hash from: {document_path}")
        
        if not os.path.exists(document_path):
            print(tag_exclamation() + f"File not found: {document_path}")
            return False
        
        # Create temporary file for hash
        temp_dir = tempfile.mkdtemp(prefix="pdf_hash_")
        self.hash_file = os.path.join(temp_dir, "pdf.hash")
        
        try:
            # Check if pdf2john is a Python script or standalone executable
            is_python_script = self.pdf2john_path.endswith('.py')
            
            if is_python_script:
                cmd = ["python3", self.pdf2john_path, document_path]
            else:
                cmd = [self.pdf2john_path, document_path]
            
            print(tag_gt() + f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout:
                # Extract the hash line
                hash_lines = []
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and ('$pdf$' in line or line.startswith(document_path + ':')):
                        # Format the hash line for john
                        if document_path in line and ':' in line:
                            # Already formatted as filename:hash
                            hash_lines.append(line)
                        else:
                            # Just hash, add filename
                            line = f"{document_path}:{line}"
                            hash_lines.append(line)
                        print(tag_minus() + "Hash extracted successfully!")
                
                if hash_lines:
                    # Save hash to file
                    with open(self.hash_file, 'w') as f:
                        for hash_line in hash_lines:
                            f.write(hash_line + '\n')
                    
                    print(tag_minus() + "Hash saved to temporary file")
                    return True
                else:
                    print(tag_exclamation() + "No hash found in output")
                    print(tag_exclamation() + "The PDF might not be password protected")
            else:
                print(tag_exclamation() + "pdf2john failed or produced no output")
                if result.stderr:
                    print(c_red("Error: ") + result.stderr)
                
        except Exception as e:
            print(tag_x() + f"Error extracting hash: {e}")
        
        # Cleanup on failure
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
        return False
    
    def list_documents(self):
        """List PDF documents in current directory"""
        extensions = [
            '.pdf', '.PDF',
        ]
        
        documents = []
        
        print(c_cyan("\n📁") + " Current Directory: " + c_yellow(self.current_dir))
        print(c_yellow("📄") + " Place PDF documents in this directory to see them here.\n")
        print(tag_minus() + "AVAILABLE PDF DOCUMENTS")
        
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
                    
                    documents.append(file)
                    print(c_yellow(f"[{idx}]") + f" {file}" + c_cyan(f" ({size_str})"))
                    idx += 1
        
        return documents
    
    def select_document(self):
        """Let user select a document"""
        self.show_banner()
        
        print(c_yellow("📁") + f" Current working directory: {self.current_dir}")
        
        documents = self.list_documents()
        
        if not documents:
            print(tag_exclamation() + "No PDF documents found in current directory!")
            print(c_yellow("\n💡") + f" Tip: Place PDF documents in: {self.current_dir}")
            print()
            print(tag_minus() + "DOCUMENT SELECTION OPTIONS")
            print(c_yellow("[1]") + " Enter document path manually")
            print(c_yellow("[2]") + " Exit")
            
            choice = input(tag_gt() + "Select option (1-2): ").strip()
            if choice == "1":
                path = input(tag_gt() + "Enter full path to document: ").strip()
                if os.path.exists(path):
                    return path
                else:
                    print(tag_exclamation() + f"File not found: {path}")
                    input(tag_gt() + "Press Enter to continue...")
                    return None
            else:
                return None
        
        print(c_yellow(f"[{len(documents)+1}]") + " Enter custom path")
        print(c_yellow(f"[{len(documents)+2}]") + " Exit")
        
        try:
            choice = int(input(tag_gt() + f"Select document (1-{len(documents)+2}): "))
            
            if 1 <= choice <= len(documents):
                selected = documents[choice-1]
                print(tag_minus() + f"Selected: {selected}")
                return selected
            elif choice == len(documents) + 1:
                path = input(tag_gt() + "Enter full path to document: ").strip()
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
        print(tag_asterisk() + "Document: " + c_yellow(f"{self.document}"))
        print()
        print(tag_minus() + "SELECT ATTACK MODE")

        print(c_yellow("[1]") + " Wordlist Attack (using default wordlist)")
        print(c_yellow("[2]") + " Wordlist Attack (custom wordlist)")
        print(c_yellow("[3]") + " Single Crack Mode")
        print(c_yellow("[4]") + " Incremental Mode (brute force)")
        print(c_yellow("[5]") + " Show cracked passwords")
        print(c_yellow("[6]") + " Select different document")
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
        print(tag_asterisk() + f"{attack_name} on: {self.document}")
        
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
        cmd = [self.john_path, self.hash_file, "--format=pdf"]
        
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
        cmd = [self.john_path, self.hash_file, "--single", "--format=pdf"]
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
        print(tag_exclamation() + "WARNING: This may take a VERY long time!")
        
        confirm = input(tag_gt() + "Continue with brute force? (y/n): ").lower()
        if confirm != 'y':
            print(tag_asterisk() + "Cancelled")
            return False
        
        cmd = [self.john_path, self.hash_file, "--incremental=" + charset, "--format=pdf"]
        return self.run_john_command(cmd, f"Incremental Mode ({charset})")
    
    def show_results(self):
        """Show cracked passwords"""
        self.show_banner()
        print(tag_asterisk() + "Checking for cracked passwords...")
        
        cmd = [self.john_path, self.hash_file, "--show", "--format=pdf"]
        
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
                            # Show just the filename and password
                            filename = os.path.basename(parts[0])
                            print(c_cyan(f"{filename}:") + c_green(":".join(parts[1:])))
                        else:
                            print(c_cyan(line))
                    else:
                        print(line)
                
                # Check if any passwords were actually cracked
                if "password hash cracked" in result.stdout or "password hashes cracked" in result.stdout:
                    # Save to file
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    results_file = f"cracked_pdf_{timestamp}.txt"
                    
                    with open(results_file, "w") as f:
                        f.write(f"Document: {self.document}\n")
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
            # Select document
            self.document = self.select_document()
            if not self.document:
                print(tag_asterisk() + "Exiting...")
                self.cleanup()
                break
            
            # Extract hash
            print(tag_asterisk() + "Extracting hash from document...")
            if not self.extract_hash(self.document):
                print(tag_exclamation() + "Failed to extract hash from document")
                print(tag_asterisk() + "The document might not be password protected")
                input(tag_gt() + "Press Enter to continue...")
                continue
            
            # Main attack loop for this document
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
                    # Select different document
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
        cracker = PDFCracker()
        cracker.main_loop()
    except KeyboardInterrupt:
        print(c_red("\n\n[x]") + " Program stopped by user")
    except Exception as e:
        print(c_red("\n[x]") + f" Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
