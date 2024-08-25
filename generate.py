import requests
import re
import json
import csv

# URL to the JavaScript file
js_file_url = "https://sscasn.bkn.go.id/_next/static/chunks/app/page-9c36313db567966c.js"

# Notify if the URL was found
print(f"JavaScript file URL found: {js_file_url}")

# Step 2: Fetch the JavaScript file
response_js = requests.get(js_file_url)

if response_js.status_code == 200:
    # Extract the JSON parts using regex
    content = response_js.text

    # Notify that the file was fetched successfully
    print(f"JavaScript file fetched successfully, size: {len(content)} bytes")

    # List of variable names to target
    variable_names = ['t', 'T', 'R', 'P', 'O', 'L', 'u', 'M', 'U', 'G', 'l']

    # Initialize dictionaries to hold the extracted data
    tingkat_pendidikan_data = None
    program_studi_data = {}

    # Loop through each variable name and search for its pattern
    for var_name in variable_names:
        pattern = fr'{var_name}\s*=\s*JSON\.parse\(\s*(\'|\")(\[.*?\])(\'|\")\s*\)'
        match = re.search(pattern, content)

        if match:
            print(f"Pattern for {var_name} found in the JavaScript content!")

            # Extract the JSON string
            json_str = match.group(2)  # Get the content within the quotes

            # Parse the JSON data
            try:
                data = json.loads(json_str)
                print(f"Extracted data for {var_name}: {data}")

                # Store data in the appropriate dictionary
                if var_name == 't':  # Assume 't' is for tingkat_pendidikan_data
                    tingkat_pendidikan_data = data
                else:  # All other variables are for program_studi_data
                    program_studi_data[var_name] = data

            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON data for {var_name}: {e}")
        else:
            print(f"Pattern for {var_name} not found in the JavaScript content.")

    # Step 3: Combine and save the final output

    if tingkat_pendidikan_data and program_studi_data:
        # Create a lookup dictionary for tingkat_pendidikan_data
        tingkat_pendidikan_lookup = {item["id"]: item["nama"] for item in tingkat_pendidikan_data}

        # Prepare final combined data
        combined_data = []

        for var_name, items in program_studi_data.items():
            for item in items:
                tingkat_pendidikan_id = item.get("tingkat_pendidikan_id", "")
                tingkat_pendidikan_nama = tingkat_pendidikan_lookup.get(tingkat_pendidikan_id, "")
                combined_data.append([
                    item.get("cepat_kode", ""),
                    item.get("nama", ""),
                    tingkat_pendidikan_id,
                    tingkat_pendidikan_nama
                ])

        # Save the combined data to a final CSV file
        final_output_file = "gabungan.csv"
        with open(final_output_file, mode="w", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["cepat_kode", "program_studi_nama", "tingkat_pendidikan_id", "tingkat_pendidikan_nama"])
            csv_writer.writerows(combined_data)

        print(f"Final combined data saved to {final_output_file}")

else:
    print(f"Failed to retrieve JavaScript file. Status code: {response_js.status_code}")
