#!/usr/bin/env python3
import sys
import glob
import os
from PIL import Image, ImageFont, ImageDraw
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

# --- CONFIG ---
OUTPUT_FILE = "fonts.py"
PREVIEW_TEXT = "ABC 123"

def get_char_data(font, char):
    """
    Render a character and return (width, height, bytearray_hlsb).
    """
    # Get size
    bbox = font.getbbox(char)
    if not bbox:
        # Space or empty
        # Use a default width based on 'a' or similar if possible, or just advance
        # For space, getlength is better
        width = int(font.getlength(char))
        return width, 0, bytearray()
    
    # width = bbox[2] # This might be tight, let's use getlength for advance?
    # Usually for bitmap fonts we want the tight box and draw it, but we need advance.
    # Let's stick to simple: Create an image of sufficient size, draw char, crop.
    
    # Better approach for pixel fonts:
    # Draw to a 1-bit image
    # Use getbbox for tighter bounds including vertical
    # But for fixed baseline, we usually want to draw relative to baseline.
    # PIL draws text with (0,0) as top-left of the bounding box usually? No, it's top-left of ascender?
    # Actually draw.text((x,y)) x,y is top-left.
    
    # To get consistent baseline, we should use font metrics.
    ascent, descent = font.getmetrics()
    height = ascent + descent
    width = int(font.getlength(char))
    if width == 0: width = 4 # Fallback
    
    # Create image with fixed height to keep baseline aligned
    img = Image.new('1', (width, height), 0)
    draw = ImageDraw.Draw(img)
    
    # Draw text at top-left (assuming font includes ascent space)
    # For pixel fonts, this usually works.
    # If we crop, we lose the vertical offset info!
    # So we should NOT crop vertical if we want to align them easily?
    # Or we store the y-offset.
    
    # Current simple approach: Crop everything.
    # This causes "g", "y", "j" to float up, and small chars like "-" to float up.
    # FIX: Do NOT crop vertically. Only crop horizontally.
    
    draw.text((0, 0), char, font=font, fill=1)
    
    # Crop horizontally only
    bbox = img.getbbox()
    if not bbox:
        return width, 0, bytearray()
    
    # bbox is (left, top, right, bottom)
    # We want (bbox[0], 0, bbox[2], height) to keep vertical alignment
    # Actually, let's just crop horizontally to save space, but keep full height?
    # Or crop tight and store offset?
    # The simplest for MicroPython framebuf blit is to have all chars same height or 
    # just blit them aligned to top.
    
    # Let's try keeping full height (ascent + descent) and just trimming width.
    # This ensures baseline is consistent.
    
    # Trim width
    min_x, _, max_x, _ = bbox
    # We can trim left empty space?
    # Usually for variable width font we want to trim left/right.
    
    final_img = img.crop((min_x, 0, max_x, height))
    w, h = final_img.size
    
    # Convert to MONO_HLSB (SSD1306)
    # Rows of bytes. Each byte is 8 vertical pixels? No, HLSB is horizontal.
    # SSD1306 default in MicroPython framebuf.MONO_HLSB:
    # "Horizontal, Least Significant Bit" - actually standard framebuf is usually VLSB for SSD1306 hardware,
    # BUT MicroPython's framebuf.MONO_HLSB matches the generic layout.
    # Let's match what convert_image.py did:
    # It iterated y then x. 
    # "byte_val |= (1 << (7 - bit))" -> MSB first?
    # convert_image.py used:
    # for y in range(height):
    #   for x in range(0, width, 8):
    #     ...
    # This is standard raster format (row by row).
    
    buffer = bytearray()
    for y in range(h):
        for x in range(0, w, 8):
            byte_val = 0
            for bit in range(8):
                if x + bit < w:
                    if final_img.getpixel((x + bit, y)):
                        byte_val |= (1 << (7 - bit))
            buffer.append(byte_val)
            
    return w, h, buffer

def generate_font_module(font_path, size, var_name):
    try:
        font = ImageFont.truetype(font_path, size)
    except Exception as e:
        print(f"Error loading font: {e}")
        return None

    # ASCII range 32-126
    chars_data = {}
    
    # We will store:
    # FONT_NAME = {
    #   'height': H,
    #   'chars': {
    #      ord('A'): (width, height, bytearray),
    #      ...
    #   }
    # }
    
    console = Console()
    console.print(f"[dim]Rendering {var_name}...[/dim]")
    
    max_h = 0
    
    for i in range(32, 127):
        char = chr(i)
        w, h, data = get_char_data(font, char)
        if w > 0:
            chars_data[i] = (w, h, data)
            if h > max_h: max_h = h
            
    # Generate Python Code
    lines = []
    lines.append(f"# Font: {os.path.basename(font_path)} ({size}px)")
    lines.append("import framebuf")
    lines.append("")
    lines.append(f"{var_name}_HEIGHT = {max_h}")
    lines.append(f"{var_name} = {{}}")
    lines.append("")
    
    for code, (w, h, data) in chars_data.items():
        byte_str = "".join([f"\\x{b:02x}" for b in data])
        lines.append(f"{var_name}[{code}] = ({w}, {h}, bytearray(b'{byte_str}'))")
        
    lines.append("")
    lines.append("# --- DRAW FUNCTION ---")
    lines.append("def draw(oled, text, x, y, font_data=None, color=1):")
    lines.append(f"    if font_data is None: font_data = {var_name}")
    lines.append("    cursor_x = x")
    lines.append("    for char in text:")
    lines.append("        code = ord(char)")
    lines.append("        if code not in font_data: continue")
    lines.append("        w, h, data = font_data[code]")
    lines.append("        if h > 0:")
    lines.append("            fb = framebuf.FrameBuffer(data, w, h, framebuf.MONO_HLSB)")
    lines.append("            oled.blit(fb, cursor_x, y + ({var_name}_HEIGHT - h), 1) # Align bottom?")
    lines.append("            # Actually usually align top. Let's just blit at y.")
    lines.append("            # oled.blit(fb, cursor_x, y)")
    lines.append("        cursor_x += w + 1")
    lines.append("")
    
    # Improved Draw Function that handles the generated dictionary
    # We'll make a generic one that gets appended
    
    return "\n".join(lines)

def main():
    console = Console()
    
    # 1. Search Fonts
    fonts = glob.glob("assets/*.ttf") + glob.glob("assets/*.otf")
    if not fonts:
        console.print("[red]No fonts found in assets/[/red]")
        sys.exit(1)
        
    console.print(Panel("Select a font file:", title="[bold cyan]Font Converter[/bold cyan]"))
    
    # Add option for ALL
    console.print(f" [yellow]0[/yellow]. [bold]CONVERT ALL (Batch Mode)[/bold]")
    
    for i, f in enumerate(fonts):
        console.print(f" [yellow]{i+1}[/yellow]. {os.path.basename(f)}")
        
    choice = Prompt.ask("Choose file", choices=[str(i) for i in range(len(fonts) + 1)])
    
    if choice == "0":
        # Batch mode
        # size = int(Prompt.ask("Font Size for ALL (px)", default="10"))
        
        # We wipe the file first
        with open(OUTPUT_FILE, "w") as f:
            f.write("import framebuf\n\n")
            
            # Add generic draw function immediately
            f.write("""
def draw(oled, text, x, y, font_data=None, color=1):
    # Default to FONT_REGULAR if available and font_data is None
    if font_data is None:
        if 'FONT_REGULAR' in globals():
            font_data = FONT_REGULAR
        else:
            return # No font to draw
            
    cursor_x = x
    for char in text:
        code = ord(char)
        if code not in font_data: 
            cursor_x += 4 # Default spacing for missing char
            continue
        w, h, data = font_data[code]
        if h > 0 and len(data) > 0:
            # Invert data if color=0 (Black on White)
            # But data is read-only bytes usually.
            # We can invert at blit time? SSD1306 doesn't support key=1 for inverted blit easily
            # without changing the buffer.
            # Better: Create a temporary mutable bytearray if needed?
            # Or pre-generate inverted fonts? No, waste of space.
            # SSD1306 FrameBuffer operations:
            # blit(fbuf, x, y, key)
            # If key is specified, pixels matching key are transparent.
            
            # If we want BLACK text (color=0) on WHITE background:
            # The font bitmap has 1s where the character is.
            # If we blit with color=0, we want to clear pixels?
            # FrameBuffer.blit doesn't have 'color' param, it just copies bits.
            # It copies 1s as 1s (White).
            
            # To draw BLACK text, we need to use a different raster operation (XOR, OR, AND, NOT).
            # MicroPython standard framebuf only supports simple copy with transparency key.
            
            # Workaround for BLACK text (color=0):
            # We need to invert the source bytes before blitting?
            # Or draw a white box and then XOR? framebuf doesn't do XOR easily.
            
            # BUT: We are drawing on a white background (already filled).
            # So we need to clear pixels where the font has 1s.
            # This means we need 0s where font has 1s.
            # Since we can't change the operation mode of blit, we have to invert the buffer manually.
            
            if color == 0:
                # Invert bytes on the fly
                inv_data = bytearray([~b & 0xFF for b in data])
                fb = framebuf.FrameBuffer(inv_data, w, h, framebuf.MONO_HLSB)
                # We want to draw '0's (Black) where text is.
                # But blit copies 1s.
                # If we have inverted data, we have 1s where background is.
                # If we blit that, we draw white background and keep holes?
                # No, that overwrites background.
                
                # Wait, SSD1306 driver usually maps 1->On, 0->Off.
                # If background is White (1), we want to set pixels to 0.
                # There is no "clear bits" blit in standard MicroPython framebuf.
                
                # SLOW BUT WORKING FALLBACK for color=0:
                # Iterate pixels? No too slow.
                
                # TRICK: Use 'key' for transparency.
                # If we invert the image:
                # Original: Text=1, Bg=0.
                # Inverted: Text=0, Bg=1.
                # If we blit Inverted with key=1 (White is transparent):
                # We copy only the 0s? No, key makes the MATCHING color transparent.
                # So if key=1, 1s are skipped. 0s are copied.
                # 0s are Black.
                # So if we invert the font (Text=0, Bg=1) and blit with key=1:
                # The Bg (1) is transparent.
                # The Text (0) is copied (as Black).
                # THIS IS THE WAY!
                
                # Let's implement this trick.
                inv_data = bytearray([~b & 0xFF for b in data])
                fb = framebuf.FrameBuffer(inv_data, w, h, framebuf.MONO_HLSB)
                oled.blit(fb, cursor_x, y, 1) # 1 is transparent, so 0s (Black Text) are drawn.
                
            else:
                # Normal White text
                fb = framebuf.FrameBuffer(data, w, h, framebuf.MONO_HLSB)
                oled.blit(fb, cursor_x, y, 0) # 0 is transparent, so 1s (White Text) are drawn.
                
        cursor_x += w + 1
""")
        
        console.print("\n[bold]Starting Batch Conversion...[/bold]")
        
        for f in fonts:
            base_name = os.path.basename(f).lower()
            # Guess variable name
            if "bold" in base_name or "b08" in base_name:
                var_name = "FONT_BOLD"
                # Default size for bold?
                default_size = "10"
            else:
                var_name = "FONT_REGULAR"
                default_size = "10"
                
            # Specific logic for your known files
            if "haxrcorp" in base_name: 
                var_name = "FONT_REGULAR"
                default_size = "10"
            elif "helv" in base_name: 
                var_name = "FONT_BOLD"
                default_size = "10"
            else: 
                var_name = "FONT_" + base_name.split('.')[0].upper().replace("-", "_")
            
            # Ask for size for EACH font
            s = Prompt.ask(f"Size for {base_name} ({var_name})", default=default_size)
            size = int(s)
            
            console.print(f"Processing [cyan]{base_name}[/cyan] -> [green]{var_name}[/green] @ {size}px")
            
            code = generate_font_module(f, size, var_name)
            if code:
                # Extract HEIGHT first to use in comment
                height_line = [l for l in code.splitlines() if f"{var_name}_HEIGHT =" in l][0]
                actual_height = int(height_line.split("=")[1].strip())
                
                # Append to file with accurate height in comment
                new_content = f"\n\n# --- Font: {var_name} (size: {size}px, height: {actual_height}px) ---\n"
                new_content += f"# Source: {os.path.basename(f)}\n"
                new_content += f"{height_line}\n"
                new_content += f"{var_name} = {{}}\n"
                
                # Extract Data Lines
                data_lines = [l for l in code.splitlines() if l.startswith(f"{var_name}[")]
                new_content += "\n".join(data_lines)
                
                with open(OUTPUT_FILE, "a") as out:
                    out.write(new_content)
                    
        console.print(f"[green]✓ Batch conversion complete. Saved to {OUTPUT_FILE}[/green]")
        return

    # Normal single file mode
    font_file = fonts[int(choice)-1]
    
    # 2. Settings
    size = int(Prompt.ask("Font Size (px)", default="10"))
    var_name = Prompt.ask("Variable Name (e.g. FONT_REGULAR)", default="FONT_REGULAR")
    
    # 3. Generate
    code = generate_font_module(font_file, size, var_name)
    
    if code:
        # Check if fonts.py exists
        mode = "w"
        existing_content = ""
        write_header = True
        
        if os.path.exists(OUTPUT_FILE):
            console.print(f"\n[yellow]{OUTPUT_FILE} exists.[/yellow]")
            # Smart Update Option
            # If variable exists, replace it. If not, append.
            # But simple overwrite/append is easier for user to understand IF explained.
            # "Overwrite" usually means "Overwrite File".
            # "Append" means "Add to end".
            
            action = Prompt.ask("Select action", choices=["replace_font", "overwrite_file", "append_to_file"], default="replace_font")
            
            if action == "overwrite_file":
                mode = "w"
            elif action == "append_to_file":
                mode = "a"
                write_header = False
                with open(OUTPUT_FILE, "r") as f:
                    existing_content = f.read()
            elif action == "replace_font":
                # Read file, remove old font section, append new
                mode = "w"
                write_header = False # We will write full reconstructed content
                with open(OUTPUT_FILE, "r") as f:
                    existing_content = f.read()
                
                # Remove old definition of var_name
                # We look for start marker "# --- Font: var_name" and end marker?
                # Or simpler: Regex replace?
                # Our format is:
                # # --- Font: NAME ...
                # ...
                # NAME = {}
                # ...
                # (until next # --- Font or End)
                
                # Let's do a simple line-based filter
                lines = existing_content.splitlines()
                new_lines = []
                skip = False
                found_old = False
                
                for line in lines:
                    if line.startswith(f"# --- Font: {var_name}"):
                        skip = True
                        found_old = True
                    elif skip and line.startswith("# --- Font:"):
                        skip = False
                        new_lines.append(line)
                    elif skip and line.startswith("def draw("):
                        # Don't delete draw function
                        skip = False
                        new_lines.append(line)
                    elif not skip:
                        new_lines.append(line)
                        
                if found_old:
                    console.print(f"[cyan]Removing old definition of {var_name}...[/cyan]")
                
                # Reconstruct file without the old font
                existing_content = "\n".join(new_lines) + "\n"
                
                # Now we will append the new font to this content
                # But we are in 'w' mode, so we write existing_content first
                # Then we add new_content
                
                # Actually, let's just set new_content start to existing_content
                new_content = existing_content


        # Prepare content
        # new_content = "" # DO NOT RESET new_content here, it kills replace_font logic
        
        if write_header:
            new_content += "import framebuf\n\n"
            
            # Define Generic Draw Function only once at the top (or bottom)
            # We will add it at the end if it doesn't exist, or here.
            # Let's add it at the end to be safe, or check if it exists.
            
        new_content += f"# --- Font: {var_name} ({size}px) ---\n"
        new_content += f"# Source: {os.path.basename(font_file)}\n"
        
        # Extract HEIGHT
        height_line = [l for l in code.splitlines() if f"{var_name}_HEIGHT =" in l][0]
        new_content += f"{height_line}\n"
        
        # Extract Dictionary Definition
        new_content += f"{var_name} = {{}}\n"
        
        # Extract Data Lines
        data_lines = [l for l in code.splitlines() if l.startswith(f"{var_name}[")]
        new_content += "\n".join(data_lines)
        new_content += "\n\n"
        
        # Add draw function if it's not already there (simple check)
        # Or if we are overwriting, we must add it.
        # If appending, check existing_content.
        
        draw_func_code = """
def draw(oled, text, x, y, font_data=None, color=1):
    # Default to FONT_REGULAR if available and font_data is None
    if font_data is None:
        if 'FONT_REGULAR' in globals():
            font_data = FONT_REGULAR
        else:
            return # No font to draw
            
    cursor_x = x
    for char in text:
        code = ord(char)
        if code not in font_data: 
            cursor_x += 4 # Default spacing for missing char
            continue
        w, h, data = font_data[code]
        if h > 0 and len(data) > 0:
            # Invert data if color=0 (Black on White)
            # But data is read-only bytes usually.
            # We can invert at blit time? SSD1306 doesn't support key=1 for inverted blit easily
            # without changing the buffer.
            # Better: Create a temporary mutable bytearray if needed?
            # Or pre-generate inverted fonts? No, waste of space.
            # SSD1306 FrameBuffer operations:
            # blit(fbuf, x, y, key)
            # If key is specified, pixels matching key are transparent.
            
            # If we want BLACK text (color=0) on WHITE background:
            # The font bitmap has 1s where the character is.
            # If we blit with color=0, we want to clear pixels?
            # FrameBuffer.blit doesn't have 'color' param, it just copies bits.
            # It copies 1s as 1s (White).
            
            # To draw BLACK text, we need to use a different raster operation (XOR, OR, AND, NOT).
            # MicroPython standard framebuf only supports simple copy with transparency key.
            
            # Workaround for BLACK text (color=0):
            # We need to invert the source bytes before blitting?
            # Or draw a white box and then XOR? framebuf doesn't do XOR easily.
            
            # BUT: We are drawing on a white background (already filled).
            # So we need to clear pixels where the font has 1s.
            # This means we need 0s where font has 1s.
            # Since we can't change the operation mode of blit, we have to invert the buffer manually.
            
            if color == 0:
                # Invert bytes on the fly
                inv_data = bytearray([~b & 0xFF for b in data])
                fb = framebuf.FrameBuffer(inv_data, w, h, framebuf.MONO_HLSB)
                # We want to draw '0's (Black) where text is.
                # But blit copies 1s.
                # If we have inverted data, we have 1s where background is.
                # If we blit that, we draw white background and keep holes?
                # No, that overwrites background.
                
                # Wait, SSD1306 driver usually maps 1->On, 0->Off.
                # If background is White (1), we want to set pixels to 0.
                # There is no "clear bits" blit in standard MicroPython framebuf.
                
                # SLOW BUT WORKING FALLBACK for color=0:
                # Iterate pixels? No too slow.
                
                # TRICK: Use 'key' for transparency.
                # If we invert the image:
                # Original: Text=1, Bg=0.
                # Inverted: Text=0, Bg=1.
                # If we blit Inverted with key=1 (White is transparent):
                # We copy only the 0s? No, key makes the MATCHING color transparent.
                # So if key=1, 1s are skipped. 0s are copied.
                # 0s are Black.
                # So if we invert the font (Text=0, Bg=1) and blit with key=1:
                # The Bg (1) is transparent.
                # The Text (0) is copied (as Black).
                # THIS IS THE WAY!
                
                # Let's implement this trick.
                inv_data = bytearray([~b & 0xFF for b in data])
                fb = framebuf.FrameBuffer(inv_data, w, h, framebuf.MONO_HLSB)
                oled.blit(fb, cursor_x, y, 1) # 1 is transparent, so 0s (Black Text) are drawn.
                
            else:
                # Normal White text
                fb = framebuf.FrameBuffer(data, w, h, framebuf.MONO_HLSB)
                oled.blit(fb, cursor_x, y, 0) # 0 is transparent, so 1s (White Text) are drawn.
                
        cursor_x += w + 1
"""
        
        # Check both new_content (for preserved draw) and existing_content (for appended file)
        if "def draw(" not in new_content and "def draw(" not in existing_content:
            new_content += draw_func_code

        with open(OUTPUT_FILE, mode) as f:
            f.write(new_content)
            
        console.print(f"[green]✓ Successfully wrote to {OUTPUT_FILE} (Mode: {mode})[/green]")

if __name__ == "__main__":
    main()
