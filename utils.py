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