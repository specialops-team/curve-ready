import pandas as pd

# Move shared constants and functions here
EXCLUSIONS_LIST = ["REQUEST FROM BMI", "NOT ELIGIBLE", "NRY", "NRYI", "YTO", "OJ"]

def get_notes_config(jot_df):
    def find_col_name(keywords):
        keywords = [k.upper() for k in keywords]
        for col in jot_df.columns:
            if isinstance(col, str) and all(k in col.upper() for k in keywords):
                return col
        return None

    writers_col = find_col_name(['Writers', 'Composer'])
    publishers_col = find_col_name(['Publishers', 'Names'])
    shares_col = find_col_name(['Shares'])

    WRITERS_COL_NAME = writers_col if writers_col else "Writers (A) - Author (C) - Composer"
    PUBLISHERS_COL_NAME = publishers_col if publishers_col else "Publishers' Names"
    SHARES_COL_NAME = shares_col if shares_col else "Shares"
    
    return [
        "EEP Master Catalog Number", "Labeled Details for Portal & YTT System",
        "PORTAL LINK TO SONG - MULTI LINE", "Release Link", "YOUTUBE TEAM",
        "ISWC", "Recording ISRC", "Title", "Artist(s)", "Genre",
        WRITERS_COL_NAME, PUBLISHERS_COL_NAME, SHARES_COL_NAME,
        "Recording Label Name", "Recording Release Date (CWR)", "Recording Title",
        "Album UPC", "Instrumental or Riddim Title (If Any)",
        "BMI WORK #", "ASCAP WORK #", "USAMECH #", "MRCODE # / SDXCODE #",
        "TUNECODE #", "SOCAN #", "MAIN ID JC #", "CANMECH #", "SUISA #",
        "USA TEAM NOTES", "GLOBAL TEAM NOTES", "Youtube Video Link (All Types)"
    ]

def generate_notes_content(row, notes_columns):
    present_values = []
    for col in notes_columns:
        if col in row:
            value = row[col]
            if col == "ISWC" and isinstance(value, str):
                if any(e in value.upper() for e in EXCLUSIONS_LIST):
                    value = None
            
            value_str = str(value).strip() if pd.notna(value) and value is not None else ""
            if value_str:
                normalized_value = " ".join(value_str.split()) 
                present_values.append(f"{col}: {normalized_value}")
    return "\n\n".join(present_values).strip()

def validate_jotform_data(df):
    """
    Validates Writer Total, Controlled (Y/N), and Capacity (A/C/AC/CA).
    Returns a list of error strings with Catalog Number and Title prefix.
    """
    errors = []
    
    def get_col(keywords):
        for col in df.columns:
            c_str = str(col).strip().upper()
            if all(k.upper() in c_str for k in keywords):
                return col
        return None

    # Identify identification columns and requirement columns
    catalog_col = get_col(["EEP", "MASTER", "CATALOG"])
    title_col = get_col(["TITLE"])
    total_writers_col = get_col(["WRITER", "TOTAL"]) or get_col(["TOTAL", "WRITERS"])
    
    valid_controlled = {"Y", "N"}
    valid_capacity = {"A", "C", "AC", "CA"}

    for index, row in df.iterrows():
        excel_row_num = index + 2
        
        # Identification Prefix for clear error reporting
        cat_val = str(row[catalog_col]).strip() if catalog_col and pd.notna(row[catalog_col]) else "Unknown ID"
        title_val = str(row[title_col]).strip() if title_col and pd.notna(row[title_col]) else "Unknown Title"
        prefix = f"{cat_val} ({title_val}) - "

        # 1. NEW: Check if Writer Total is empty or invalid
        w_count = 0
        val_total = row.get(total_writers_col)
        if total_writers_col is None or pd.isna(val_total) or str(val_total).strip() == "":
            errors.append(f"{prefix}In rows {excel_row_num} Writer Total is missing")
        else:
            try:
                w_count = int(float(val_total))
            except:
                errors.append(f"{prefix}In rows {excel_row_num} Writer Total is not a valid number")
        
        # 2. Check individual Composer details based on total count
        for i in range(1, w_count + 1):
            col_ctrl = get_col([f"COMPOSER {i}", "CONTROLLED"])
            if col_ctrl:
                val_str = str(row[col_ctrl]).strip().upper() if pd.notna(row[col_ctrl]) else ""
                if val_str not in valid_controlled:
                    errors.append(f"{prefix}In rows {excel_row_num} Composer {i} Controlled is missing or not matched")

            col_cap = get_col([f"COMPOSER {i}", "CAPACITY"])
            if col_cap:
                val_str = str(row[col_cap]).strip().upper() if pd.notna(row[col_cap]) else ""
                if val_str == "NAN": val_str = ""
                if val_str not in valid_capacity:
                    errors.append(f"{prefix}In rows {excel_row_num} Composer {i} Capacity is missing or not matched")

    return errors