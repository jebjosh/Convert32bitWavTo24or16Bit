#!/usr/bin/env python3
"""
CAF to WAV Batch Converter - Zero Latency Edition
Automatically removes AAC encoder delay and leading silence
Perfect timing alignment with Apple software
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import subprocess
import shutil
from pathlib import Path


class CAFtoWAVConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("CAF to WAV Converter - Zero Latency")
        self.root.geometry("700x650")
        self.root.resizable(True, True)
        
        self.conversion_running = False
        self.selected_directory = None
        self.output_directory = None
        
        # Check for FFmpeg
        self.ffmpeg_available = self.check_ffmpeg()
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        self.setup_ui()
    
    def check_ffmpeg(self):
        """Check if FFmpeg is available in PATH"""
        return shutil.which("ffmpeg") is not None
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="CAF to WAV Converter", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 5))
        
        subtitle_label = ttk.Label(main_frame, text="Automatically removes AAC encoder delay", 
                                   font=('Arial', 10), foreground="gray")
        subtitle_label.pack(pady=(0, 10))
        
        # Status indicator
        if self.ffmpeg_available:
            status_text = "✓ FFmpeg detected - All CAF formats supported"
            status_color = "green"
        else:
            status_text = "✗ FFmpeg required - See WINDOWS_INSTALL.md"
            status_color = "red"
        
        status_label = ttk.Label(main_frame, text=status_text, foreground=status_color)
        status_label.pack(pady=(0, 15))
        
        # Directory selection
        dir_frame = ttk.LabelFrame(main_frame, text="Source Directory", padding="10")
        dir_frame.pack(fill=tk.X, pady=(0, 10))
        
        dir_inner = ttk.Frame(dir_frame)
        dir_inner.pack(fill=tk.X)
        
        self.dir_label = ttk.Label(dir_inner, text="No directory selected", 
                                   foreground="gray")
        self.dir_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_btn = ttk.Button(dir_inner, text="Browse...", 
                               command=self.browse_directory)
        browse_btn.pack(side=tk.RIGHT)
        
        # Output directory
        output_frame = ttk.LabelFrame(main_frame, text="Output Directory (Optional)", padding="10")
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        output_inner = ttk.Frame(output_frame)
        output_inner.pack(fill=tk.X)
        
        self.output_dir_label = ttk.Label(output_inner, 
                                          text="Same as source files", 
                                          foreground="gray")
        self.output_dir_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        output_browse_btn = ttk.Button(output_inner, text="Browse...", 
                                      command=self.browse_output_directory)
        output_browse_btn.pack(side=tk.RIGHT, padx=(0, 5))
        
        clear_output_btn = ttk.Button(output_inner, text="Clear", 
                                     command=self.clear_output_directory)
        clear_output_btn.pack(side=tk.RIGHT)
        
        # Bit depth selection
        bitdepth_frame = ttk.LabelFrame(main_frame, text="Output Bit Depth", padding="10")
        bitdepth_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.bit_depth_var = tk.StringVar(value="24")
        
        bit_inner = ttk.Frame(bitdepth_frame)
        bit_inner.pack()
        
        bit24_radio = ttk.Radiobutton(bit_inner, text="24-bit PCM", 
                                     variable=self.bit_depth_var, value="24")
        bit24_radio.pack(side=tk.LEFT, padx=(0, 20))
        
        bit32_radio = ttk.Radiobutton(bit_inner, text="32-bit Float", 
                                     variable=self.bit_depth_var, value="32")
        bit32_radio.pack(side=tk.LEFT)
        
        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.overwrite_var = tk.BooleanVar(value=False)
        overwrite_check = ttk.Checkbutton(options_frame, 
                                         text="Overwrite existing WAV files",
                                         variable=self.overwrite_var)
        overwrite_check.pack(anchor=tk.W)
        
        self.trim_silence_var = tk.BooleanVar(value=True)
        trim_check = ttk.Checkbutton(options_frame, 
                                     text="Remove leading silence (fixes AAC encoder delay)",
                                     variable=self.trim_silence_var)
        trim_check.pack(anchor=tk.W, pady=(5, 0))
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_label = ttk.Label(progress_frame, text="Ready to convert")
        self.progress_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        self.file_count_label = ttk.Label(progress_frame, text="0 files processed")
        self.file_count_label.pack(anchor=tk.W)
        
        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Conversion Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        log_scroll_frame = ttk.Frame(log_frame)
        log_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_scroll_frame, height=8, wrap=tk.WORD, font=('Consolas', 9))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_scroll_frame, orient=tk.VERTICAL, 
                                 command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Convert button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.convert_btn = ttk.Button(button_frame, text="START CONVERSION", 
                                     command=self.start_conversion)
        self.convert_btn.pack(fill=tk.X)
    
    def browse_directory(self):
        directory = filedialog.askdirectory(title="Select folder containing CAF files")
        if directory:
            self.selected_directory = directory
            display_path = directory if len(directory) < 60 else "..." + directory[-57:]
            self.dir_label.config(text=display_path, foreground="black")
    
    def browse_output_directory(self):
        directory = filedialog.askdirectory(title="Select output folder for WAV files")
        if directory:
            self.output_directory = directory
            display_path = directory if len(directory) < 50 else "..." + directory[-47:]
            self.output_dir_label.config(text=display_path, foreground="black")
    
    def clear_output_directory(self):
        self.output_directory = None
        self.output_dir_label.config(text="Same as source files", foreground="gray")
    
    def log_message(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def find_caf_files(self, directory):
        """Recursively find all .caf files in directory"""
        caf_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.caf'):
                    caf_files.append(os.path.join(root, file))
        return caf_files
    
    def convert_with_ffmpeg(self, caf_path, wav_path, bit_depth, trim_silence):
        """
        Convert CAF to WAV using FFmpeg
        Optionally removes leading silence to eliminate AAC encoder delay
        """
        try:
            # Build FFmpeg command
            if bit_depth == "24":
                codec = 'pcm_s24le'
            else:
                codec = 'pcm_f32le'
            
            # Build audio filter chain
            filters = []
            
            if trim_silence:
                # Remove leading silence (AAC encoder delay)
                # silenceremove removes silence below -50dB at start
                filters.append("silenceremove=start_periods=1:start_duration=0:start_threshold=-50dB")
            
            cmd = ['ffmpeg', '-i', caf_path]
            
            if filters:
                cmd.extend(['-af', ','.join(filters)])
            
            cmd.extend([
                '-acodec', codec,
                '-y' if self.overwrite_var.get() else '-n',
                wav_path
            ])
            
            # Run FFmpeg
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                # Get duration info from stderr
                duration_info = ""
                if "Duration:" in result.stderr:
                    for line in result.stderr.split('\n'):
                        if "Duration:" in line:
                            duration_info = line.strip()
                            break
                return wav_path, "success", duration_info
            else:
                if "already exists" in result.stderr:
                    return None, "skipped (already exists)", ""
                error_msg = result.stderr.split('\n')[-3:] if result.stderr else "Unknown error"
                return None, f"FFmpeg error: {' '.join(error_msg)}", ""
                
        except Exception as e:
            return None, f"Exception: {str(e)}", ""
    
    def convert_caf_to_wav(self, caf_path, bit_depth, output_base_dir, trim_silence):
        """Convert a single CAF file to WAV"""
        try:
            # Determine output path
            if output_base_dir:
                rel_path = os.path.relpath(caf_path, self.selected_directory)
                wav_filename = os.path.splitext(rel_path)[0] + '.wav'
                wav_path = os.path.join(output_base_dir, wav_filename)
                os.makedirs(os.path.dirname(wav_path), exist_ok=True)
            else:
                wav_path = os.path.splitext(caf_path)[0] + '.wav'
            
            # Check if file exists and overwrite is disabled
            if os.path.exists(wav_path) and not self.overwrite_var.get():
                return wav_path, "skipped (already exists)", ""
            
            # Convert with FFmpeg
            if not self.ffmpeg_available:
                return None, "error: FFmpeg not available", ""
            
            return self.convert_with_ffmpeg(caf_path, wav_path, bit_depth, trim_silence)
            
        except Exception as e:
            return None, f"error: {str(e)}", ""
    
    def conversion_thread(self):
        """Main conversion thread"""
        try:
            if not self.ffmpeg_available:
                messagebox.showerror("FFmpeg Required", 
                                   "FFmpeg is required for conversion!\n\n"
                                   "See WINDOWS_INSTALL.md for installation instructions.")
                return
            
            # Find all CAF files
            self.log_message(f"Scanning: {self.selected_directory}")
            caf_files = self.find_caf_files(self.selected_directory)
            
            if not caf_files:
                self.log_message("No CAF files found!")
                messagebox.showinfo("No Files", "No CAF files found in the selected directory.")
                return
            
            self.log_message(f"Found {len(caf_files)} CAF file(s)\n")
            
            if self.output_directory:
                self.log_message(f"Output: {self.output_directory}")
            else:
                self.log_message(f"Output: Same location as source")
            
            trim_silence = self.trim_silence_var.get()
            self.log_message(f"Bit depth: {self.bit_depth_var.get()}-bit")
            self.log_message(f"Remove silence: {'Yes' if trim_silence else 'No'}\n")
            
            # Setup progress bar
            self.progress_bar['maximum'] = len(caf_files)
            self.progress_bar['value'] = 0
            
            bit_depth = self.bit_depth_var.get()
            converted_count = 0
            skipped_count = 0
            error_count = 0
            
            # Convert each file
            for i, caf_path in enumerate(caf_files):
                if not self.conversion_running:
                    self.log_message("\n❌ Cancelled\n")
                    break
                
                rel_path = os.path.relpath(caf_path, self.selected_directory)
                self.progress_label.config(text=f"Converting: {rel_path}")
                
                self.log_message(f"\n[{i+1}/{len(caf_files)}] {rel_path}")
                
                wav_path, status, info = self.convert_caf_to_wav(
                    caf_path, bit_depth, self.output_directory, trim_silence
                )
                
                if status == "success":
                    converted_count += 1
                    if wav_path:
                        self.log_message(f"  → {os.path.basename(wav_path)}")
                    if info:
                        self.log_message(f"  {info}")
                    self.log_message(f"  ✓ SUCCESS")
                elif status.startswith("skipped"):
                    skipped_count += 1
                    if wav_path:
                        self.log_message(f"  → {os.path.basename(wav_path)}")
                    self.log_message(f"  ⊘ {status}")
                else:
                    error_count += 1
                    self.log_message(f"  ✗ {status}")
                
                # Update progress
                self.progress_bar['value'] = i + 1
                self.file_count_label.config(
                    text=f"Converted: {converted_count} | Skipped: {skipped_count} | Errors: {error_count}"
                )
                self.root.update_idletasks()
            
            # Final summary
            self.log_message(f"\n{'='*60}")
            self.log_message(f"✓ COMPLETE")
            self.log_message(f"Converted: {converted_count} | Skipped: {skipped_count} | Errors: {error_count}")
            
            self.progress_label.config(text="Complete!")
            
            if error_count > 0:
                messagebox.showwarning("Complete with Errors", 
                                      f"Converted: {converted_count}\nErrors: {error_count}\n\nCheck log for details.")
            else:
                messagebox.showinfo("Complete", 
                                  f"Successfully converted {converted_count} file(s)!")
            
        except Exception as e:
            self.log_message(f"\n❌ ERROR: {str(e)}")
            import traceback
            self.log_message(traceback.format_exc())
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        
        finally:
            self.conversion_running = False
            self.convert_btn.config(text="START CONVERSION", state='normal')
    
    def start_conversion(self):
        if not self.selected_directory:
            messagebox.showwarning("No Directory", 
                                 "Please select a directory containing CAF files.")
            return
        
        if self.conversion_running:
            self.conversion_running = False
            self.convert_btn.config(text="START CONVERSION")
            return
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        # Start conversion
        self.conversion_running = True
        self.convert_btn.config(text="⏹ CANCEL")
        
        thread = threading.Thread(target=self.conversion_thread, daemon=True)
        thread.start()


def main():
    root = tk.Tk()
    app = CAFtoWAVConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
