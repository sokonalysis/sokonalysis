#!/usr/bin/env python3
import sys
import os
import subprocess
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
        self.setWindowTitle('Sokonalysis')
        self.setFixedSize(800, 600)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        
        # Current text format for ANSI colors
        self.current_format = QTextCharFormat()
        self.current_format.setForeground(QColor('#FFFFFF'))
        
        # ANSI color mapping
        self.ansi_colors = {
            '30': QColor('#000000'), '31': QColor('#FF0000'), '32': QColor('#00FF00'),
            '33': QColor('#FFFF00'), '34': QColor('#0000FF'), '35': QColor('#FF00FF'),
            '36': QColor('#00FFFF'), '37': QColor('#FFFFFF'), '90': QColor('#808080'),
            '91': QColor('#FF8080'), '92': QColor('#80FF80'), '93': QColor('#FFFF80'),
            '94': QColor('#8080FF'), '95': QColor('#FF80FF'), '96': QColor('#80FFFF'),
            '97': QColor('#FFFFFF'),
        }
        
        # Color name to QColor mapping
        self.color_map = {
            '#FFFFFF': QColor('#FFFFFF'), '#888888': QColor('#888888'),
            '#FF4444': QColor('#FF4444'), '#00FF00': QColor('#00FF00'),
            '#FFFF00': QColor('#FFFF00'), '#FFA500': QColor('#FFA500'),
            '#00FFFF': QColor('#00FFFF'), '#CCCCCC': QColor('#CCCCCC')
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
        clear_btn = QPushButton("Clear Screen")
        clear_btn.clicked.connect(self.clear_screen)
        top_controls.addWidget(clear_btn)
        
        self.restart_btn = QPushButton("Restart")
        self.restart_btn.clicked.connect(self.restart_sokonalysis)
        top_controls.addWidget(self.restart_btn)
        
        system_btn = QPushButton("System Commands")
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
    
    def process_ansi_codes(self, text):
        """Process ANSI color codes and apply them to the text"""
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        i = 0
        while i < len(text):
            if text[i] == '\x1b' and i + 1 < len(text) and text[i + 1] == '[':
                i += 2
                code_str = ""
                while i < len(text) and text[i] not in 'mHJK':
                    code_str += text[i]
                    i += 1
                i += 1
                
                if code_str:
                    codes = code_str.split(';')
                    for code in codes:
                        if code in self.ansi_colors:
                            self.current_format.setForeground(self.ansi_colors[code])
                        elif code == '0':
                            self.current_format.setForeground(QColor('#FFFFFF'))
            else:
                cursor.insertText(text[i], self.current_format)
                i += 1
    
    def handle_output(self):
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        self.process_ansi_codes(data)
        self.output.moveCursor(QTextCursor.End)
    
    def handle_error(self):
        data = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
        self.process_ansi_codes(data)
        self.output.moveCursor(QTextCursor.End)
    
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
