#!/usr/bin/env env python3
"""
WAV Bit Depth Converter
Converts 32-bit WAV files to 24-bit and/or 16-bit formats
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import threading
import numpy as np
import soundfile as sf
from typing import List, Tuple


class WavConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WAV Bit Depth Converter")
        self.root.geometry("700x550")
        
        # Variables
        self.folder_path = tk.StringVar()
        self.include_subdirs = tk.BooleanVar(value=False)
        self.convert_to_24bit = tk.BooleanVar(value=False)
        self.convert_to_16bit = tk.BooleanVar(value=False)
        self.is_processing = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="WAV Bit Depth Converter", 
                                font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Folder selection
        ttk.Label(main_frame, text="Source Folder:").grid(row=1, column=0, sticky=tk.W, pady=5)
        folder_entry = ttk.Entry(main_frame, textvariable=self.folder_path, width=50)
        folder_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        browse_btn = ttk.Button(main_frame, text="Browse", command=self.browse_folder)
        browse_btn.grid(row=1, column=2, pady=5)
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Subdirectories checkbox
        subdir_check = ttk.Checkbutton(options_frame, 
                                       text="Include subdirectories", 
                                       variable=self.include_subdirs)
        subdir_check.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # Conversion options
        ttk.Label(options_frame, text="Convert to:", 
                 font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=(10, 5))
        
        bit24_check = ttk.Checkbutton(options_frame, 
                                      text="24-bit", 
                                      variable=self.convert_to_24bit)
        bit24_check.grid(row=2, column=0, sticky=tk.W, padx=20)
        
        bit16_check = ttk.Checkbutton(options_frame, 
                                      text="16-bit", 
                                      variable=self.convert_to_16bit)
        bit16_check.grid(row=3, column=0, sticky=tk.W, padx=20)
        
        # Convert button
        self.convert_btn = ttk.Button(main_frame, text="Start Conversion", 
                                      command=self.start_conversion,
                                      style='Accent.TButton')
        self.convert_btn.grid(row=3, column=0, columnspan=3, pady=15)
        
        # Progress frame
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.grid(row=0, column=0, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=400)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        progress_frame.columnconfigure(0, weight=1)
        
        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=70, 
                                                  wrap=tk.WORD, state='disabled')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        main_frame.rowconfigure(5, weight=1)
        
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with WAV Files")
        if folder:
            self.folder_path.set(folder)
            
    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update_idletasks()
        
    def validate_inputs(self) -> bool:
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a source folder")
            return False
            
        if not os.path.exists(self.folder_path.get()):
            messagebox.showerror("Error", "Selected folder does not exist")
            return False
            
        if not self.convert_to_24bit.get() and not self.convert_to_16bit.get():
            messagebox.showerror("Error", "Please select at least one output bit depth (24-bit or 16-bit)")
            return False
            
        return True
        
    def find_wav_files(self, folder_path: str, include_subdirs: bool) -> List[str]:
        """Find all WAV files in the folder"""
        wav_files = []
        
        if include_subdirs:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith('.wav'):
                        wav_files.append(os.path.join(root, file))
        else:
            for file in os.listdir(folder_path):
                if file.lower().endswith('.wav'):
                    wav_files.append(os.path.join(folder_path, file))
                    
        return wav_files
        
    def get_bit_depth(self, file_path: str) -> int:
        """Get the bit depth of a WAV file"""
        try:
            info = sf.info(file_path)
            subtype = info.subtype
            
            # Map subtypes to bit depths
            if 'PCM_32' in subtype or 'FLOAT' in subtype:
                return 32
            elif 'PCM_24' in subtype:
                return 24
            elif 'PCM_16' in subtype:
                return 16
            elif 'PCM_8' in subtype:
                return 8
            else:
                return 0  # Unknown
                
        except Exception as e:
            self.log(f"Error reading {file_path}: {str(e)}")
            return 0
            
    def convert_file(self, input_path: str, output_path: str, target_bits: int) -> bool:
        """Convert a WAV file to target bit depth"""
        try:
            # Read the audio file
            data, samplerate = sf.read(input_path, dtype='float32')
            
            # Determine output subtype
            if target_bits == 24:
                subtype = 'PCM_24'
            elif target_bits == 16:
                subtype = 'PCM_16'
            else:
                return False
                
            # Write the output file
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            sf.write(output_path, data, samplerate, subtype=subtype)
            
            return True
            
        except Exception as e:
            self.log(f"Error converting {input_path}: {str(e)}")
            return False
            
    def process_files(self):
        """Main processing function"""
        try:
            folder = self.folder_path.get()
            include_subdirs = self.include_subdirs.get()
            
            self.log(f"Scanning folder: {folder}")
            self.log(f"Include subdirectories: {include_subdirs}")
            self.log("-" * 50)
            
            # Find all WAV files
            wav_files = self.find_wav_files(folder, include_subdirs)
            self.log(f"Found {len(wav_files)} WAV files")
            
            if not wav_files:
                self.log("No WAV files found!")
                messagebox.showinfo("Info", "No WAV files found in the selected folder")
                return
                
            # Filter for 32-bit files
            files_32bit = []
            for wav_file in wav_files:
                bit_depth = self.get_bit_depth(wav_file)
                if bit_depth == 32:
                    files_32bit.append(wav_file)
                    
            self.log(f"Found {len(files_32bit)} 32-bit WAV files to convert")
            self.log("-" * 50)
            
            if not files_32bit:
                self.log("No 32-bit WAV files found!")
                messagebox.showinfo("Info", "No 32-bit WAV files found to convert")
                return
                
            # Process conversions
            total_conversions = len(files_32bit) * (
                (1 if self.convert_to_24bit.get() else 0) + 
                (1 if self.convert_to_16bit.get() else 0)
            )
            current_conversion = 0
            
            self.progress_bar['maximum'] = total_conversions
            
            for wav_file in files_32bit:
                relative_path = os.path.relpath(wav_file, folder)
                file_name = os.path.basename(wav_file)
                file_dir = os.path.dirname(wav_file)
                
                self.log(f"\nProcessing: {relative_path}")
                
                # Convert to 24-bit
                if self.convert_to_24bit.get():
                    output_dir = os.path.join(file_dir, "24bit")
                    output_path = os.path.join(output_dir, file_name)
                    
                    self.progress_label.config(text=f"Converting to 24-bit: {file_name}")
                    
                    if self.convert_file(wav_file, output_path, 24):
                        self.log(f"  ✓ Converted to 24-bit: {output_path}")
                    else:
                        self.log(f"  ✗ Failed to convert to 24-bit")
                        
                    current_conversion += 1
                    self.progress_bar['value'] = current_conversion
                    self.root.update_idletasks()
                
                # Convert to 16-bit
                if self.convert_to_16bit.get():
                    output_dir = os.path.join(file_dir, "16bit")
                    output_path = os.path.join(output_dir, file_name)
                    
                    self.progress_label.config(text=f"Converting to 16-bit: {file_name}")
                    
                    if self.convert_file(wav_file, output_path, 16):
                        self.log(f"  ✓ Converted to 16-bit: {output_path}")
                    else:
                        self.log(f"  ✗ Failed to convert to 16-bit")
                        
                    current_conversion += 1
                    self.progress_bar['value'] = current_conversion
                    self.root.update_idletasks()
                    
            self.log("-" * 50)
            self.log(f"Conversion complete! Processed {len(files_32bit)} files")
            self.progress_label.config(text="Conversion complete!")
            
            messagebox.showinfo("Success", 
                              f"Successfully processed {len(files_32bit)} files!\n"
                              f"Check the log for details.")
            
        except Exception as e:
            self.log(f"Error during processing: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            
        finally:
            self.is_processing = False
            self.convert_btn.config(state='normal', text='Start Conversion')
            
    def start_conversion(self):
        """Start the conversion process"""
        if self.is_processing:
            return
            
        if not self.validate_inputs():
            return
            
        # Clear log
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
        
        # Reset progress
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Processing...")
        
        # Disable button
        self.is_processing = True
        self.convert_btn.config(state='disabled', text='Processing...')
        
        # Run in separate thread
        thread = threading.Thread(target=self.process_files, daemon=True)
        thread.start()


def main():
    root = tk.Tk()
    app = WavConverterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
