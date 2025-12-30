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
    Validates writers' Controlled (Y/N) and Capacity (A/C/AC/CA).
    Returns a list of error strings in the format:
    "In rows {number} Composer {Number} [Column] is missing or not matched"
    """
    errors = []
    
    def get_col(keywords):
        for col in df.columns:
            c_str = str(col).strip().upper()
            if all(k.upper() in c_str for k in keywords):
                return col
        return None

    total_writers_col = get_col(["WRITER", "TOTAL"]) or get_col(["TOTAL", "WRITERS"])
    
    if total_writers_col:
        valid_controlled = {"Y", "N"}
        valid_capacity = {"A", "C", "AC", "CA"}

        for index, row in df.iterrows():
            excel_row_num = index + 2
            
            try:
                val = row[total_writers_col]
                w_count = int(float(val)) if pd.notna(val) else 0
            except:
                w_count = 0
            
            for i in range(1, w_count + 1):
                # 1. Check Controlled
                col_ctrl = get_col([f"COMPOSER {i}", "CONTROLLED"])
                if col_ctrl:
                    raw_val = row[col_ctrl]
                    val_str = str(raw_val).strip().upper() if pd.notna(raw_val) else ""
                    
                    if val_str not in valid_controlled:
                        errors.append(f"In rows {excel_row_num} Composer {i} Controlled is missing or not matched")

                # 2. Check Capacity
                col_cap = get_col([f"COMPOSER {i}", "CAPACITY"])
                if col_cap:
                    raw_val = row[col_cap]
                    val_str = str(raw_val).strip().upper() if pd.notna(raw_val) else ""
                    if val_str == "NAN": val_str = ""
                    
                    if val_str not in valid_capacity:
                        errors.append(f"In rows {excel_row_num} Composer {i} Capacity is missing or not matched")

    return errors