#!/usr/bin/env python3
import sys
import os
import subprocess
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QTextEdit, QLineEdit, QPushButton, QWidget, QMessageBox)
from PyQt5.QtCore import QProcess, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor, QColor, QTextCharFormat

class SystemCommandWorker(QThread):
    """Worker thread for executing system commands without freezing GUI"""
    output_signal = pyqtSignal(str, str)  # text, color_name
    finished_signal = pyqtSignal(int)     # exit_code
    
    def __init__(self, command):
        super().__init__()
        self.command = command
    
    def run(self):
        try:
            # Handle shell-specific commands
            if self.command.startswith('source ') or self.command.startswith('. '):
                # Source commands need to be handled by shell
                shell_cmd = f"bash -c '{self.command}'"
                process = subprocess.Popen(
                    shell_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
            else:
                # Regular commands
                process = subprocess.Popen(
                    self.command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
            
            # Read stdout in real-time
            for line in iter(process.stdout.readline, ''):
                if line:
                    self.output_signal.emit(line, '#CCCCCC')
            
            # Read stderr in real-time
            for line in iter(process.stderr.readline, ''):
                if line:
                    self.output_signal.emit(f"[ERROR] {line}", '#FF4444')
            
            process.stdout.close()
            process.stderr.close()
            return_code = process.wait()
            
            self.finished_signal.emit(return_code)
            
        except Exception as e:
            self.output_signal.emit(f"[ERROR] Failed to execute command: {str(e)}\n", '#FF4444')
            self.finished_signal.emit(-1)

class SimpleCLIGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.process = None
        self.system_process = None
        self.font_size = 12
        self.setWindowTitle('sokonalysis')
        self.setFixedSize(800, 600)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        
        # Current text format for ANSI colors
        self.current_format = QTextCharFormat()
        self.current_format.setForeground(QColor('#FFFFFF'))
        
        # ANSI color mapping - matching your C++ code colors exactly
        self.ansi_colors = {
            # Standard colors (30-37)
            '30': QColor('#000000'),  # BLACK
            '31': QColor('#FF0000'),  # RED
            '32': QColor('#00FF00'),  # GREEN
            '33': QColor('#FFFF00'),  # YELLOW
            '34': QColor('#0000FF'),  # BLUE
            '35': QColor('#FF00FF'),  # MAGENTA
            '36': QColor('#00FFFF'),  # CYAN
            '37': QColor('#FFFFFF'),  # WHITE
            
            # Bright colors (90-97) - matching your Python script
            '90': QColor('#808080'),  # GRAY
            '91': QColor('#FF0000'),  # BRIGHT RED (same as RED for consistency)
            '92': QColor('#00FF00'),  # BRIGHT GREEN (same as GREEN)
            '93': QColor('#FFFF00'),  # BRIGHT YELLOW (same as YELLOW)
            '94': QColor('#0000FF'),  # BRIGHT BLUE (same as BLUE)
            '95': QColor('#FF00FF'),  # BRIGHT MAGENTA (same as MAGENTA)
            '96': QColor('#00FFFF'),  # BRIGHT CYAN (same as CYAN)
            '97': QColor('#FFFFFF'),  # BRIGHT WHITE (same as WHITE)
            
            # Custom colors from your Python script
            '38;5;208': QColor('#FFA500'),  # ORANGE (from your C++ ORANGE)
            
            # Background colors (not commonly used in your scripts)
            '40': QColor('#000000'),  # BLACK BG
            '41': QColor('#FF0000'),  # RED BG
            '42': QColor('#00FF00'),  # GREEN BG
            '43': QColor('#FFFF00'),  # YELLOW BG
            '44': QColor('#0000FF'),  # BLUE BG
            '45': QColor('#FF00FF'),  # MAGENTA BG
            '46': QColor('#00FFFF'),  # CYAN BG
            '47': QColor('#FFFFFF'),  # WHITE BG
        }
        
        # Color attributes
        self.bold = False
        self.underline = False
        self.italic = False
        
        # Color name to QColor mapping for system messages
        # Using exact colors from your C++ and Python scripts
        self.color_map = {
            # Basic colors from C++ macros
            '#FFFFFF': QColor('#FFFFFF'),  # WHITE
            '#888888': QColor('#888888'),  # GRAY
            '#FF4444': QColor('#FF4444'),  # ERROR RED
            '#00FF00': QColor('#00FF00'),  # GREEN
            '#FFFF00': QColor('#FFFF00'),  # YELLOW
            '#FFA500': QColor('#FFA500'),  # ORANGE
            '#00FFFF': QColor('#00FFFF'),  # CYAN
            '#CCCCCC': QColor('#CCCCCC'),  # LIGHT GRAY
            
            # Colors from your C++ defines
            '#FF0000': QColor('#FF0000'),  # RED
            '#0000FF': QColor('#0000FF'),  # BLUE
            '#FF00FF': QColor('#FF00FF'),  # MAGENTA
            
            # Additional colors from Python script
            '#808080': QColor('#808080'),  # GRAY (bright black)
            '#FF8080': QColor('#FF8080'),  # BRIGHT RED variant
            '#80FF80': QColor('#80FF80'),  # BRIGHT GREEN variant
            '#FFFF80': QColor('#FFFF80'),  # BRIGHT YELLOW variant
            '#8080FF': QColor('#8080FF'),  # BRIGHT BLUE variant
            '#FF80FF': QColor('#FF80FF'),  # BRIGHT MAGENTA variant
            '#80FFFF': QColor('#80FFFF'),  # BRIGHT CYAN variant
        }
        
        self.setup_ui()
        self.start_sokonalysis()
    
    def setup_ui(self):
        self.setStyleSheet("""
            QMainWindow { 
                background-color: #0a0a0a;
            }
            QTextEdit {
                background-color: #000000;
                color: #ffffff;
                border: 1px solid #333;
                font-family: 'Courier New';
                border-radius: 5px;
            }
            QLineEdit {
                background-color: #000000;
                color: #ffffff;
                border: 1px solid #333;
                padding: 8px;
                font-family: 'Courier New';
                border-radius: 3px;
            }
            QPushButton {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 1px solid #555;
                padding: 8px 15px;
                font-family: 'Courier New';
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:disabled {
                background-color: #1a1a1a;
                color: #666666;
            }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Top control buttons row
        top_controls = QHBoxLayout()
        
        # Zoom controls
        zoom_out_btn = QPushButton("Zoom Out (-)")
        zoom_out_btn.clicked.connect(self.zoom_out)
        top_controls.addWidget(zoom_out_btn)
        
        zoom_in_btn = QPushButton("Zoom In (+)")
        zoom_in_btn.clicked.connect(self.zoom_in)
        top_controls.addWidget(zoom_in_btn)
        
        reset_zoom_btn = QPushButton("Reset Zoom")
        reset_zoom_btn.clicked.connect(self.reset_zoom)
        top_controls.addWidget(reset_zoom_btn)
        
        top_controls.addStretch()
        
        # System controls
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_screen)
        top_controls.addWidget(clear_btn)
        
        self.restart_btn = QPushButton("Restart")
        self.restart_btn.clicked.connect(self.restart_sokonalysis)
        top_controls.addWidget(self.restart_btn)
        
        system_btn = QPushButton("Commands")
        system_btn.clicked.connect(self.show_system_commands)
        top_controls.addWidget(system_btn)
        
        layout.addLayout(top_controls)
        
        # Output display
        self.output = QTextEdit()
        self.output.setFont(QFont("Courier New", self.font_size))
        self.output.setReadOnly(True)
        self.output.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.output.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        layout.addWidget(self.output)
        
        # Input area
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter sokonalysis command, system command, or 'exit' to quit...")
        self.input_field.returnPressed.connect(self.send_input)
        input_layout.addWidget(self.input_field)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_input)
        input_layout.addWidget(self.send_btn)
        
        layout.addLayout(input_layout)
    
    def zoom_in(self):
        """Increase font size"""
        if self.font_size < 20:
            self.font_size += 1
            self.update_font()
            self.append_output(f"[System] Zoom level: {self.font_size}\n", '#888888')
    
    def zoom_out(self):
        """Decrease font size"""
        if self.font_size > 8:
            self.font_size -= 1
            self.update_font()
            self.append_output(f"[System] Zoom level: {self.font_size}\n", '#888888')
    
    def reset_zoom(self):
        """Reset to default font size"""
        self.font_size = 12
        self.update_font()
        self.append_output("[System] Zoom reset to default\n", '#888888')
    
    def update_font(self):
        """Update the output font size"""
        font = QFont("Courier New", self.font_size)
        self.output.setFont(font)
    
    def apply_text_attributes(self, format):
        """Apply bold, underline, italic attributes to text format"""
        if self.bold:
            format.setFontWeight(QFont.Bold)
        else:
            format.setFontWeight(QFont.Normal)
        
        format.setFontUnderline(self.underline)
        format.setFontItalic(self.italic)
    
    def process_ansi_codes(self, text):
        """Process ANSI color codes and apply them to the text"""
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Use regex to find all ANSI escape sequences
        pattern = r'(\x1b\[[0-9;]*[a-zA-Z])'
        parts = re.split(pattern, text)
        
        for part in parts:
            if not part:
                continue
            
            # Check if this part is an ANSI escape sequence
            if part.startswith('\x1b['):
                # Process the ANSI code
                code_str = part[2:-1]  # Remove '\x1b[' and final character
                codes = code_str.split(';')
                
                for code in codes:
                    if not code:
                        continue
                    
                    # Handle reset
                    if code == '0':
                        self.current_format.setForeground(QColor('#FFFFFF'))
                        self.current_format.setBackground(QColor('#000000'))
                        self.bold = False
                        self.underline = False
                        self.italic = False
                    
                    # Handle text attributes
                    elif code == '1':
                        self.bold = True
                    elif code == '4':
                        self.underline = True
                    elif code == '3':
                        self.italic = True
                    elif code == '22':  # Reset bold
                        self.bold = False
                    elif code == '24':  # Reset underline
                        self.underline = False
                    elif code == '23':  # Reset italic
                        self.italic = False
                    
                    # Handle colors (including custom 38;5;208 for ORANGE)
                    elif code in self.ansi_colors:
                        self.current_format.setForeground(self.ansi_colors[code])
                    
                    # Handle background colors (40-47, 100-107)
                    elif code in self.ansi_colors:
                        self.current_format.setBackground(self.ansi_colors[code])
                    
                    # Handle special cases for Python script colors
                    elif code == '91':  # Bright red from Python
                        self.current_format.setForeground(QColor('#FF0000'))
                    elif code == '92':  # Bright green from Python
                        self.current_format.setForeground(QColor('#00FF00'))
                    elif code == '93':  # Bright yellow from Python
                        self.current_format.setForeground(QColor('#FFFF00'))
                    elif code == '96':  # Bright cyan from Python
                        self.current_format.setForeground(QColor('#00FFFF'))
                    elif code == '95':  # Bright magenta from Python
                        self.current_format.setForeground(QColor('#FF00FF'))
                    elif code == '94':  # Bright blue from Python
                        self.current_format.setForeground(QColor('#0000FF'))
                
                # Apply current attributes
                self.apply_text_attributes(self.current_format)
            
            else:
                # This is regular text, apply the current format
                cursor.insertText(part, self.current_format)
        
        self.output.moveCursor(QTextCursor.End)
    
    def handle_output(self):
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        self.process_ansi_codes(data)
    
    def handle_error(self):
        data = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
        self.process_ansi_codes(data)
    
    def start_sokonalysis(self):
        """Start sokonalysis process"""
        if self.process and self.process.state() == QProcess.Running:
            self.process.terminate()
            self.process.waitForFinished(1000)
        
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.readyReadStandardError.connect(self.handle_error)
        self.process.finished.connect(self.process_finished)
        
        # Try different executable names
        executables = ['./sokonalysis', './sokonalysis.exe', 'sokonalysis', 'sokonalysis.exe']
        
        for exe in executables:
            if os.path.exists(exe) or self.is_command_available(exe):
                self.process.start(exe)
                if self.process.waitForStarted(3000):
                    self.append_output(f"[System] Started: {exe}\n", '#00FF00')
                    return
        
        self.append_output("[ERROR] sokonalysis executable not found.\n", '#FF4444')
    
    def is_command_available(self, command):
        """Check if a command is available in system PATH"""
        try:
            if os.name == 'nt':
                result = subprocess.run(['where', command], capture_output=True, text=True, timeout=5)
            else:
                result = subprocess.run(['which', command], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def send_input(self):
        """Send input to sokonalysis or execute system commands"""
        text = self.input_field.text().strip()
        if not text:
            return
        
        # Show user input
        self.append_output(f"> {text}\n", '#888888')
        
        # Handle special commands
        if text.lower() in ['exit', 'quit']:
            self.close()
            return
        elif text.lower() == 'clear':
            self.clear_screen()
            self.input_field.clear()
            return
        
        # Check if it's a system command (expanded list)
        system_commands = [
            'ssh-keygen ', 'cat ', 'ssh ', 'git ', 'pacman ', 'curl ', 'cd ', 'make ', 'g++ ', './',
            'sudo ', 'apt ', 'pip ', 'python ', 'python3 ', 'source ', '. ', 'msys2', 'nproc',
            'deactivate', 'gcc', 'ln -s'
        ]
        is_system_command = any(text.startswith(cmd) for cmd in system_commands)
        
        if is_system_command:
            self.execute_system_command(text)
        elif self.process and self.process.state() == QProcess.Running:
            self.process.write(f"{text}\n".encode())
        else:
            self.append_output("[ERROR] Sokonalysis is not running. Use 'Restart' button.\n", '#FF4444')
        
        self.input_field.clear()
    
    def execute_system_command(self, command):
        """Execute system commands in a separate thread"""
        self.append_output(f"[System] Executing: {command}\n", '#FFA500')
        self.send_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)
        
        # Create and start worker thread
        self.system_worker = SystemCommandWorker(command)
        self.system_worker.output_signal.connect(self.handle_system_output)
        self.system_worker.finished_signal.connect(self.handle_system_finished)
        self.system_worker.start()
    
    def handle_system_output(self, text, color_name):
        """Handle output from system command worker"""
        self.append_output(text, color_name)
    
    def handle_system_finished(self, exit_code):
        """Handle system command completion"""
        self.send_btn.setEnabled(True)
        self.restart_btn.setEnabled(True)
        
        if exit_code == 0:
            self.append_output("[System] Command completed successfully\n", '#00FF00')
        else:
            self.append_output(f"[System] Command failed with code {exit_code}\n", '#FF4444')
    
    def clear_screen(self):
        """Clear the output screen"""
        self.output.clear()
        self.append_output("[System] Screen cleared\n", '#888888')
    
    def restart_sokonalysis(self):
        """Restart the sokonalysis process"""
        self.append_output("[System] Restarting sokonalysis...\n", '#FFFF00')
        self.start_sokonalysis()
    
    def show_system_commands(self):
        """Show available system commands"""
        commands_info = """
[System] Available Commands:

SSH & Git:
• ssh-keygen -t ed25519 -C "email"                     
• cat ~/.ssh/id_ed25519.pub                            
• ssh -T git@github.com                                
• git clone git@github.com:user/repo.git               

Windows (MSYS2):
• pacman -Syu                                          
• pacman -S base-devel mingw-w64-x86_64-toolchain git
• pacman -S mingw-w64-x86_64-gcc                       
• pacman -S mingw-w64-x86_64-nlohmann-json
• pacman -S mingw-w64-x86_64-gmp
• pacman -S mingw-w64-x86_64-curl
• pacman -S mingw-w64-x86_64-openssl

Linux:
• sudo apt update                                       
• sudo apt install libcrypto++-dev libssl-dev libcurl4-openssl-dev
• sudo apt install libgmp-dev libgmpxx4ldbl g++
• sudo apt install nlohmann-json3-dev

Build & Development:
• g++ 
• make CXX=g++ -j$(nproc)                                
• python3 -m venv pythonvenv           			 
• source pythonvenv/bin/activate                         
• pip install -r requirements.txt                        

General:
• curl                                                   
• clear                                                  
• exit                                                   
"""
        self.append_output(commands_info, '#00FFFF')
    
    def append_output(self, text, color_name=None):
        """Append text to output with optional color"""
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # First check if the text contains ANSI codes
        if '\x1b[' in text:
            self.process_ansi_codes(text)
            return
        
        if color_name and color_name in self.color_map:
            format = QTextCharFormat()
            format.setForeground(self.color_map[color_name])
            cursor.insertText(text, format)
        else:
            cursor.insertText(text)
        
        self.output.moveCursor(QTextCursor.End)
        QApplication.processEvents()  # Keep GUI responsive
    
    def process_finished(self, exit_code, exit_status):
        """Handle sokonalysis process completion"""
        self.append_output(f"[System] Sokonalysis process finished with code {exit_code}\n", '#FF4444')
    
    def closeEvent(self, event):
        """Handle application close"""
        if self.process and self.process.state() == QProcess.Running:
            self.process.terminate()
            self.process.waitForFinished(1000)
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SimpleCLIGUI()
    window.show()
    sys.exit(app.exec_())
