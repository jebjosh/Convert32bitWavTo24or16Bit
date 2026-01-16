#!/usr/bin/env python3
"""
CAF to 32-bit WAV Converter using ffmpeg
Recursively converts all .caf files in a folder to 32-bit float WAV.
"""

import subprocess
from pathlib import Path

def convert_caf_to_wav(input_path: Path, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",                # overwrite output
        "-i", str(input_path),
        "-c:a", "pcm_f32le", # 32-bit float WAV
        str(output_path)
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✓ Converted: {input_path} → {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {input_path}\n{e.stderr.decode(errors='ignore')}")
        return False

def main():
    folder = input("Enter the folder containing CAF files: ").strip()
    root = Path(folder)

    if not root.exists():
        print("Folder does not exist.")
        return

    caf_files = list(root.rglob("*.caf"))
    print(f"Found {len(caf_files)} CAF files.")

    for caf in caf_files:
        out_dir = caf.parent / "32bit_wav"
        out_path = out_dir / (caf.stem + ".wav")
        convert_caf_to_wav(caf, out_path)

    print("\nConversion complete!")

if __name__ == "__main__":
    main()
