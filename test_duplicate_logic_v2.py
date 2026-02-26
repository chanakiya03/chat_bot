
import re

# Simple slugify mock
def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def mock_loader():
    colleges = []
    college_slugs = {}
    
    # Simulate disk loading (with a duplicate name Bharath/biher)
    disk_files = [
        {"name": "Hindustan Institute of Technology and Science (HITS)", "file": "Hindustan_output.json"},
        {"name": "Women's Christian College (WCC)", "file": "Women_Christian_output.json"},
        {"name": "Bharath Institute of Higher Education and Research (BIHER)", "file": "biher_output.json"},
        {"name": "Bharath Institute of Higher Education and Research (BIHER)", "file": "Bharath_output.json"}
    ]
    
    print("--- Disk Scan ---")
    for df in disk_files:
        name = df["name"]
        slug = slugify(name)
        if slug in college_slugs:
            print(f"Skipping duplicate on disk: {slug} (from {df['file']})")
            continue
        
        entry = {"key": slug, "name": name, "source": "disk"}
        colleges.append(entry)
        college_slugs[slug] = entry
        print(f"Added from disk: {slug}")
        
    # Simulate DB loading (Enrichment)
    db_colls = [
        {"name": "Hindustan Institute of Technology and Science (HITS)", "slug": slugify("Hindustan Institute of Technology and Science (HITS)")},
        {"name": "Ethiraj College for Women", "slug": slugify("Ethiraj College for Women")}
    ]
    
    print("\n--- DB Enrichment ---")
    for dc in db_colls:
        if dc["slug"] in college_slugs:
            print(f"Skipping duplicate from DB: {dc['slug']}")
        else:
            print(f"Adding new from DB: {dc['slug']}")
            entry = {"key": dc["slug"], "name": dc["name"], "source": "db"}
            colleges.append(entry)
            college_slugs[dc["slug"]] = entry
            
    return colleges

colleges = mock_loader()
print(f"\nFinal College List Count: {len(colleges)}")
print(f"Colleges: {[c['name'] for c in colleges]}")

# Verification
if len(colleges) == 4:
    print("\n✅ PASSED: No duplicates and correct count (HITS, WCC, BIHER, Ethiraj).")
else:
    print("\n❌ FAILED: Duplicate detection failed.")
