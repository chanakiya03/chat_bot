import json
import csv
import re

input_file = r"D:\projects\college_chat\backend\data\Women_Christian_data.txt"
output_file = r"D:\projects\college_chat\backend\data\Women_Christian_output.json"

college_details = {}
courses = []

with open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Split into two sections
college_lines = []
course_lines = []
course_section = False

for line in lines:
    line = line.strip()
    if not line:
        continue

    if line.startswith("Course,Course"):
        course_section = True
        continue

    if course_section:
        course_lines.append(line)
    else:
        college_lines.append(line)

# -------- COLLEGE DETAILS --------
for line in college_lines:
    if "," in line:
        key, value = line.split(",", 1)
        college_details[key.strip()] = value.strip().replace('"', '')

# -------- COURSES (Proper CSV Parsing) --------
reader = csv.reader(course_lines)

for row in reader:
    if len(row) >= 6:
        duration_number = re.sub("[^0-9]", "", row[2])
        fees_clean = row[5].replace(",", "").replace('"', '')

        courses.append({
            "course": row[0].strip(),
            "batch": row[1].strip(),
            "duration_years": duration_number,
            "stream": row[3].strip(),
            "specialization": row[4].strip(),
            "annual_fees_inr": int(fees_clean)
        })

final_data = {
    "college_details": college_details,
    "courses": courses
}

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(final_data, f, indent=4)

print("✅ TXT converted to structured JSON successfully!")