import dropbox
import json
import os

# Use your Access Token here
dbx = dropbox.Dropbox('')


# 1. SET YOUR STARTING FOLDER HERE
# Example: '/Safety_Project' or just '/' for root
START_PATH = '/curated_video' 

manifest = {}

def get_direct_link(entry_path):
    try:
        # Try to create a new link
        return dbx.sharing_create_shared_link(entry_path).url.replace('dl=0', 'raw=1')
    except:
        # If it already exists, fetch the existing one
        links = dbx.sharing_list_shared_links(entry_path, direct_only=True).links
        return links[0].url.replace('dl=0', 'raw=1') if links else None

def process_batch(entries):
    for entry in entries:
        # We only care about .mp4 files inside subfolders
        if isinstance(entry, dropbox.files.FileMetadata) and entry.name.lower().endswith('.mp4'):
            
            # Split path to find Case Study and Environment
            # Expected: /curated_video/Case_Study_Name/Environment_Name/video.mp4
            relative_path = entry.path_display.replace(START_PATH, "").strip("/")
            parts = relative_path.split("/")

            if len(parts) >= 3:
                case_study = parts[0]
                environment = parts[1]
                
                link = get_direct_link(entry.path_lower)
                
                if case_study not in manifest: manifest[case_study] = {}
                if environment not in manifest[case_study]: manifest[case_study][environment] = []
                
                manifest[case_study][environment].append({
                    "name": entry.name,
                    "url": link
                })
                print(f"Mapped: {case_study} > {environment} > {entry.name}")

# --- EXECUTION ---
print(f"Connecting to {START_PATH}...")
try:
    # Start the recursive search inside your specific folder
    res = dbx.files_list_folder(START_PATH, recursive=True)
    process_batch(res.entries)

    # Use the 'has_more' flag to get all 5,000+ videos
    while res.has_more:
        print("Fetching next batch...")
        res = dbx.files_list_folder_continue(res.cursor)
        process_batch(res.entries)

    # Save to JSON
    with open('manifest.json', 'w') as f:
        json.dump(manifest, f, indent=4)
    
    print("\nSUCCESS: manifest.json generated with nested structure.")

except Exception as e:
    print(f"Error: {e}")