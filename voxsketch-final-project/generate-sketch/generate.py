import os

# --- CONFIGURATION ---
# This path points to the folder shown in your screenshot
TARGET_FOLDER = os.path.join("static", "components", "female", "hairs")

# This is the path prefix used inside the build_path() string in your final code
CODE_PATH_PREFIX = "components/male/hairs"

def clean_key_name(filename):
    """
    Creates a readable key from the filename.
    Example: "shortcurlyhair.png" -> "short curly hair"
    """
    name = os.path.splitext(filename)[0].lower()
    
    # If the filename is squashed like "flathair", we usually just keep it 
    # or try to insert spaces. For now, we use the filename as the key 
    # but ensure "hair" is at the end.
    
    # Remove hyphens/underscores if present
    name = name.replace("-", " ").replace("_", " ")
    
    # Ensure it ends with "hair" if it's not already there
    if "hair" not in name:
        name += " hair"
        
    return name

def generate_hair_map():
    if not os.path.exists(TARGET_FOLDER):
        print(f"❌ Error: Could not find folder '{TARGET_FOLDER}'")
        print("   Please run this script from the 'generate-sketch' root folder.")
        return

    print(f"Scanning: {TARGET_FOLDER}...\n")
    print("-" * 40)
    print('"hair": {')

    # Get all png/jpg files sorted alphabetically
    files = sorted([f for f in os.listdir(TARGET_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])

    for f in files:
        key = clean_key_name(f)
        # Generate the line: "key": build_path("path/to/file.png"),
        print(f'    "{key}": build_path("{CODE_PATH_PREFIX}/{f}"),')

    # Add standard blank options
    print('    "no hair": BLANK_PATH,')
    print('    "none": BLANK_PATH,')
    print('    "bald": BLANK_PATH,')
    print('    "no": BLANK_PATH,')
    print('},')
    print("-" * 40)

if __name__ == "__main__":
    generate_hair_map()