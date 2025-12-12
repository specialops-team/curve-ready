import pandas as pd
import io
import os
import tempfile
from flask import Flask, request, send_file, render_template

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir() 

# --- CORE PROCESSING FUNCTION ---

def process_curve_files(jotform_file_buffer, curve_file_buffer):
    """
    Processes the JotForm and Curve Excel files to update the 'Works' sheet 
    of the Curve file with data from the JotForm file.

    Returns: io.BytesIO buffer of the updated Excel file, or a string error message.
    """
    
    # Configuration for insertion start
    START_INDEX = 1  # Corresponds to Excel Row 3 (index 2)
    
    # List of universal exclusionary terms (case-insensitive check)
    EXCLUSIONS_LIST = ["REQUEST FROM BMI", "NOT ELIGIBLE", "NRY", "NRYI", "YTO", "OJ"] 
    
    try:
        # ---- LOAD EXCEL FILES ----
        jot = pd.read_excel(jotform_file_buffer, header=0)
        curve_excel = pd.ExcelFile(curve_file_buffer) 
        curve_sheets = {sheet_name: curve_excel.parse(sheet_name) for sheet_name in curve_excel.sheet_names}
    except Exception as e:
        return f"Error loading files: {e}"


    # ---- TARGET SHEET ----
    target_sheet_name = "Works"
    if target_sheet_name not in curve_sheets:
        return f"Error: The Curve template must contain a sheet named '{target_sheet_name}'."
        
    curve_df = curve_sheets[target_sheet_name]

    # ---- COLUMN MAPPING (JotForm Name → Curve Column Name) ----
    mapping = {
        "Title": "Title", 
        "ISWC": "ISWC", 
        "TUNECODE #": "Tunecode", 
        "Recording Release Date (CWR)": "Copyright Date", 
        "Recording Label Name": "Label Copy", 
        "Artist(s)": "Performers", 
        "Recording ISRC": "Track ISRCs"
    }

    # --- DYNAMIC COLUMN NAME FINDER (FIX FOR MISMATCHED NAMES) ---
    
    # Find the actual JotForm header names that contain the key terms
    def find_col_name(keywords):
        keywords = [k.upper() for k in keywords]
        # Iterate over jot.columns and find the first one that contains all keywords
        for col in jot.columns:
            if isinstance(col, str) and all(k in col.upper() for k in keywords):
                return col
        return None # Return None if not found

    writers_col = find_col_name(['Writers', 'Composer'])
    publishers_col = find_col_name(['Publishers', 'Names'])
    shares_col = find_col_name(['Shares'])

    # Fallback to the explicit names provided by the user if dynamic finding fails
    WRITERS_COL_NAME = writers_col if writers_col else "Writers (A) - Author (C) - Composer"
    PUBLISHERS_COL_NAME = publishers_col if publishers_col else "Publishers' Names"
    SHARES_COL_NAME = shares_col if shares_col else "Shares"
    
    # --- NOTES SPECIFIC CONFIGURATION ---
    NOTES_SOURCE_COLUMNS = [
        "EEP Master Catalog Number",
        "ISWC",
        "PORTAL LINK TO SONG - MULTI LINE",
        WRITERS_COL_NAME,       # Dynamically determined name
        PUBLISHERS_COL_NAME,    # Dynamically determined name
        SHARES_COL_NAME,        # Dynamically determined name
        "USA TEAM NOTES",
        "GLOBAL TEAM NOTES"
    ]
    
    # Columns that require their name to be inserted as a prefix in Notes
    NOTES_PREFIX_COLUMNS = [
        WRITERS_COL_NAME,
        PUBLISHERS_COL_NAME,
        SHARES_COL_NAME
    ]
    # --------------------------------------------------------------------


    # ---- HELPER FUNCTIONS ----
    
    # Multi-purpose function for joining lines with a specified separator (used for native columns)
    def join_multiline_parts(x, separator):
        if isinstance(x, str):
            parts = [i.strip() for i in str(x).replace("\r", "\n").split("\n") if i.strip()]
            return separator.join(parts)
        return x

    # Function to check for multi-line content (used for ISWC exclusion from native column)
    def is_multiline(x):
        return isinstance(x, str) and ('\n' in x or '\r' in x)

    # Universal filter (used for ISWC, Tunecode, Track ISRCs)
    def apply_universal_filter(x, exclusions=EXCLUSIONS_LIST):
        if isinstance(x, str):
            x_upper = x.upper()
            if any(e in x_upper for e in exclusions):
                return None
        return x
        
    # ---- FUNCTION TO COMBINE DATA FOR THE NOTES COLUMN ----
    def combine_notes_row(row):
        present_values = []
        
        # 1. Collect and prepare all values
        for col in NOTES_SOURCE_COLUMNS:
            value_to_add = None
            
            # Use the 'in row' check which is reliable if the column name is correct
            if col in row:
                value = row[col]
                
                # Apply universal exclusion filter ONLY to ISWC 
                if col == "ISWC":
                     value = apply_universal_filter(value)
                
                # Get string value and check for truthiness
                value_str = str(value).strip() if pd.notna(value) and value is not None else ""
                
                if value_str:
                    
                    # 1. Apply Prefix if necessary
                    prefix = ""
                    if col in NOTES_PREFIX_COLUMNS:
                        # Ensures the full, correct column name is used as the prefix
                        prefix = f"{col}: " 
                    
                    # 2. Normalize internal whitespace (join all words with a single space)
                    normalized_value = " ".join(value_str.split()) 
                    
                    # 3. Combine prefix and normalized value
                    value_to_add = prefix + normalized_value

            if value_to_add:
                present_values.append(value_to_add)

        
        # 2. Build the final string using a single space separator between columns
        return " ".join(present_values).strip()


    # ---- DYNAMIC ROW ALLOCATION SETUP ----
    rows_processed_len = len(jot)
    end_index_of_data = START_INDEX + rows_processed_len - 1
    
    rows_needed = START_INDEX + rows_processed_len
    rows_to_add = rows_needed - len(curve_df)
    
    if rows_to_add > 0:
        empty_rows = pd.DataFrame({c: [None]*rows_to_add for c in curve_df.columns})
        curve_df = pd.concat([curve_df, empty_rows], ignore_index=True)


    # ---- 1. CORE DATA INSERTION LOOP ----
    for jot_col, curve_col in mapping.items():
        # Only process if the JotForm column exists in the uploaded file
        if jot_col in jot.columns and curve_col in curve_df.columns:
            col_data = jot[jot_col].copy()

            # Apply formatting rules
            if curve_col == "Performers":
                # Uses semicolon followed by space
                col_data = col_data.apply(lambda x: join_multiline_parts(x, separator="; ")) 

            if curve_col == "Copyright Date":
                col_data = pd.to_datetime(col_data, errors='coerce').dt.strftime("%m/%d/%Y")
            
            
            # --- CUSTOM LOGIC FOR ISWC, Track ISRCs, and Tunecode ---
            
            if curve_col == "ISWC":
                # If multi-line, set to None for native column
                col_data = col_data.apply(lambda x: None if is_multiline(x) else x) 
                
                # Apply general filtering (REQUEST FROM BMI, etc.)
                col_data = col_data.apply(apply_universal_filter)
                
                # Apply length check (Prevents insertion into native column if > 15 chars)
                col_data = col_data.apply(
                    lambda x: x if isinstance(x, str) and len(x) <= 15 else None
                )

            elif curve_col == "Track ISRCs":
                # Rule: Join all ISRC codes by semicolon (NO space)
                col_data = col_data.apply(lambda x: join_multiline_parts(x, separator=";"))
                
                # Apply general filtering (NRY, NRYi, YTO)
                col_data = col_data.apply(apply_universal_filter)

            elif curve_col == "Tunecode":
                # Apply general filtering (NRY, NRYi, YTO, OJ)
                col_data = col_data.apply(apply_universal_filter)
            
            # Insert data into Curve starting at START_INDEX (index 2)
            curve_df.loc[START_INDEX : end_index_of_data, curve_col] = col_data.values


    # ---- 2. NOTES COLUMN GENERATION ----
    if "Notes" in curve_df.columns:
        notes_combined_series = jot.apply(combine_notes_row, axis=1) 
        curve_df.loc[START_INDEX : end_index_of_data, "Notes"] = notes_combined_series.values


    # ---- 3. PRIORITY WORK CONDITIONAL LOGIC ----
    JOT_PRIORITY_COL = "Popular Catalog Status"
    CURVE_PRIORITY_COL = "Priority Work"

    if JOT_PRIORITY_COL in jot.columns and CURVE_PRIORITY_COL in curve_df.columns:
        
        priority_work_data = jot[JOT_PRIORITY_COL].apply(
            lambda x: "TRUE" if isinstance(x, str) and x.strip().upper() == "POPULAR-ARTIST" else "FALSE"
        )

        curve_df.loc[START_INDEX : end_index_of_data, CURVE_PRIORITY_COL] = priority_work_data.values
    else:
        if CURVE_PRIORITY_COL in curve_df.columns:
             curve_df.loc[START_INDEX : end_index_of_data, CURVE_PRIORITY_COL] = "FALSE"
             
             
    # ---- 4. OTHER STATIC VALUES ----
    static_columns = {
        "Language": "English",
        "Territories": "WW"
    }
    
    for col, val in static_columns.items():
        if col in curve_df.columns:
            curve_df.loc[START_INDEX : end_index_of_data, col] = val


    # ---- SAVE UPDATED EXCEL WITH ALL SHEETS ----
    output_buffer = io.BytesIO()
    with pd.ExcelWriter(output_buffer, engine="openpyxl") as writer:
        for sheet_name, sheet_df in curve_sheets.items():
            if sheet_name == target_sheet_name:
                sheet_df = curve_df
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
    output_buffer.seek(0)
    return output_buffer


# --- FLASK ROUTES ---

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_files_route():
    
    if 'jotform_file' not in request.files:
        return "Error: JotForm file is required.", 400

    jotform_file = request.files['jotform_file']

    if jotform_file.filename == '':
        return "Error: Please select the JotForm file.", 400
        
    # --- DYNAMIC FILENAME GENERATION (FINAL SUFFIX) ---
    original_filename = jotform_file.filename
    name, ext = os.path.splitext(original_filename)
    output_file_name = f"{name}_curve_ready_step1{ext}"
    # --- END DYNAMIC FILENAME GENERATION ---


    jotform_buffer = io.BytesIO(jotform_file.read())
    
    # Load the static Curve Template
    try:
        template_path = os.path.join(app.root_path, 'static', 'curve.xlsx')

        with open(template_path, 'rb') as f:
            curve_template_buffer = io.BytesIO(f.read())
            
    except FileNotFoundError:
        return "Error: Static 'curve.xlsx' template not found in the static folder. Ensure it is placed directly inside the 'static' directory.", 500
    except Exception as e:
        return f"Error reading static template: {e}", 500


    # Process the files
    result = process_curve_files(jotform_buffer, curve_template_buffer)

    if isinstance(result, str):
        # Return error message as plain text
        return f"Processing Failed: {result}", 500
    else:
        return send_file(
            result, 
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
            as_attachment=True, 
            download_name=output_file_name
        )

if __name__ == '__main__':
    app.run(debug=True)