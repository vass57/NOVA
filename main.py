# ============================================================
# CORROBORIA
# STEP 1 - LOAD AND INSPECT THE INPUT FILES
# ============================================================
#
# The purpose of this file right now is ONLY to:
#
#   1. Locate the input Excel files
#   2. Make sure they exist
#   3. Load them into pandas
#   4. Fix the special formatting problem in détail_du_poste.xlsx
#   5. Print information about every dataset
#
# We are NOT doing the actual corroboration yet.
#
# We are NOT comparing System A and System B yet.
#
# We are NOT applying business rules yet.
#
# We are NOT using AI yet.
#
# One disaster at a time.
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

# Path is used to work with file paths and folders.
#
# It is cleaner than writing Windows paths manually like:
#
# "C:\\Users\\vassi\\Documents\\GitHub\\NOVA\\data"
#
from pathlib import Path


# StringIO allows Python to treat a string as if it were a file.
#
# We need this because the "détail_du_poste.xlsx" file contains
# comma-separated data inside a single Excel column.
#
# We will temporarily convert that column into text and then ask
# pandas to read that text as CSV-style data.
#
from io import StringIO


# pandas is the main library we will use for tabular data.
#
# Excel worksheets become pandas DataFrames.
#
# Think of a DataFrame as basically an Excel table inside Python.
#
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

# __file__ represents the location of THIS Python file.
#
# If main.py is located here:
#
# C:\Users\vassi\OneDrive\Documents\GitHub\NOVA\main.py
#
# then:
#
# Path(__file__).resolve()
#
# represents the full path to main.py.
#
# .parent removes "main.py" and gives us:
#
# C:\Users\vassi\OneDrive\Documents\GitHub\NOVA
#
BASE_DIR = Path(__file__).resolve().parent


# Our Excel files are stored inside a folder called:
#
# data
#
# So this creates:
#
# C:\Users\vassi\OneDrive\Documents\GitHub\NOVA\data
#
DATA_DIR = BASE_DIR / "data"


# ------------------------------------------------------------
# List of input files
# ------------------------------------------------------------
#
# FILES is a Python dictionary.
#
# Dictionaries contain:
#
#     key -> value
#
#
# For example:
#
#     "source" -> path to the source Excel file
#
#
# This lets us later write:
#
#     FILES["source"]
#
# instead of repeating the entire file path.
#
FILES = {

    # --------------------------------------------------------
    # SYSTEM A
    # --------------------------------------------------------
    #
    # This is the HR/source employee extraction.
    #
    "source":
        DATA_DIR / "Employe_Source_Anonymise_VF.xlsx",


    # --------------------------------------------------------
    # SYSTEM B
    # --------------------------------------------------------
    #
    # This is the target/time-management employee extraction.
    #
    "destination":
        DATA_DIR / "Employe_Destination_Anonymise_VF.xlsx",


    # --------------------------------------------------------
    # MAPPING
    # --------------------------------------------------------
    #
    # This tells us which fields from System A correspond
    # to which fields from System B.
    #
    # It also contains business-rule-related worksheets.
    #
    "mapping":
        DATA_DIR / "Mapping.xlsx",


    # --------------------------------------------------------
    # JOB DETAILS
    # --------------------------------------------------------
    #
    # This file contains historical job/position information.
    #
    # Later, we will use it for certain business rules,
    # especially rules involving dates and organizational units.
    #
    "job_details":
        DATA_DIR / "détail_du_poste.xlsx",


    # --------------------------------------------------------
    # EMPLOYMENT REASONS
    # --------------------------------------------------------
    #
    # This is a lookup/reference dataset.
    #
    # Later, we will use it when evaluating employee status
    # and status-reason information.
    #
    "employment_reasons":
        DATA_DIR / "Motif de la situation d'emploi.xlsx",
}


# ============================================================
# CHECK THAT REQUIRED FILES EXIST
# ============================================================

def check_files_exist() -> None:
    """
    Verify that every required CorroborIA input file exists.

    This function does NOT open any files.

    It simply checks whether Windows can find them.

    If a file is missing, the program stops and prints a useful
    error telling us exactly which file could not be found.

    Returns
    -------
    None

    This function does not return data.
    """

    # Create an empty list.
    #
    # We will add missing files to this list.
    #
    missing_files = []


    # Loop through every file in the FILES dictionary.
    #
    # Example:
    #
    # name = "source"
    #
    # path =
    # ...\data\Employe_Source_Anonymise_VF.xlsx
    #
    for name, path in FILES.items():

        # path.exists() returns:
        #
        # True
        #     if the file exists
        #
        # False
        #     if the file cannot be found
        #
        if not path.exists():

            # If the file does not exist, add it to our
            # missing_files list.
            #
            missing_files.append(
                f"{name}: {path}"
            )


    # If missing_files contains at least one item...
    #
    if missing_files:

        # Stop the program.
        #
        # FileNotFoundError is a built-in Python error type.
        #
        # "\n".join(...)
        #
        # puts every missing file on a separate line.
        #
        raise FileNotFoundError(
            "The following required files are missing:\n"
            + "\n".join(missing_files)
        )


# ============================================================
# LOAD ONE EXCEL FILE
# ============================================================

def load_excel_file(path: Path) -> dict[str, pd.DataFrame]:
    """
    Load every worksheet from one Excel workbook.

    Parameters
    ----------
    path : Path
        Path to the Excel file.

    Returns
    -------
    dict[str, pd.DataFrame]

        A dictionary where:

            key   = worksheet name
            value = pandas DataFrame

    Example
    -------

    If an Excel file contains:

        Sheet1
        Sheet2

    this function returns something conceptually like:

        {
            "Sheet1": dataframe_1,
            "Sheet2": dataframe_2
        }
    """

    # pd.read_excel() opens an Excel workbook.
    #
    # Normally pandas loads only one worksheet.
    #
    # We use:
    #
    #     sheet_name=None
    #
    # which means:
    #
    #     "Load ALL worksheets."
    #
    return pd.read_excel(

        # File to open
        path,

        # Load every worksheet
        sheet_name=None,

        # Keep values as generic Python objects for now.
        #
        # We do NOT want pandas aggressively deciding that
        # certain identifiers are numbers, dates, etc.
        #
        # Proper normalization will happen in Step 2.
        #
        dtype=object,

        # openpyxl is the library used to read .xlsx files.
        engine="openpyxl",
    )


# ============================================================
# FIX THE JOB-DETAILS FILE
# ============================================================

def fix_comma_separated_sheet(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Repair a worksheet where comma-separated data has been
    stored inside ONE Excel column.

    ------------------------------------------------------------
    WHY DO WE NEED THIS?
    ------------------------------------------------------------

    When we loaded détail_du_poste.xlsx, pandas reported:

        Rows: 114
        Columns: 1

    And the ONE column was named:

        IdentifiantPoste,
        IdentifiantEmploi,
        CodeDirectionAffectée,
        DateEffetAffectation,
        ...

    That tells us something went wrong with the structure.

    Those are supposed to be separate columns.

    The file basically contains CSV-style text inside Excel.

    ------------------------------------------------------------
    WHAT THIS FUNCTION DOES
    ------------------------------------------------------------

    It transforms something like:

        ONE COLUMN

        IdentifiantPoste,IdentifiantEmploi,CodeDirection
        123,456,ABC
        789,101,DEF

    into:

        IdentifiantPoste | IdentifiantEmploi | CodeDirection
        ------------------------------------------------------
        123               | 456               | ABC
        789               | 101               | DEF

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame that might contain the formatting problem.

    Returns
    -------
    pd.DataFrame
        Corrected DataFrame if needed.

        Otherwise, the original DataFrame is returned unchanged.
    """

    # --------------------------------------------------------
    # CHECK NUMBER OF COLUMNS
    # --------------------------------------------------------
    #
    # If the worksheet already contains multiple columns,
    # it probably does not have this problem.
    #
    # So we return the DataFrame unchanged.
    #
    if len(df.columns) != 1:
        return df


    # --------------------------------------------------------
    # GET THE ONLY COLUMN NAME
    # --------------------------------------------------------
    #
    # df.columns contains all column names.
    #
    # [0] means:
    #
    #     give me the FIRST column
    #
    column_name = str(df.columns[0])


    # --------------------------------------------------------
    # CHECK WHETHER THE HEADER CONTAINS COMMAS
    # --------------------------------------------------------
    #
    # Our broken job-details file has a header like:
    #
    # IdentifiantPoste,IdentifiantEmploi,CodeDirection...
    #
    # If there are no commas, it may simply be a legitimate
    # one-column worksheet.
    #
    if "," not in column_name:
        return df


    # --------------------------------------------------------
    # REBUILD THE ORIGINAL COMMA-SEPARATED TEXT
    # --------------------------------------------------------
    #
    # Start with the current column name because that is
    # actually the REAL CSV header.
    #
    rows = [column_name]


    # df.iloc[:, 0]
    #
    # means:
    #
    #     all rows
    #     from column number 0
    #
    # In other words:
    #
    #     give me every value from the only column
    #
    for value in df.iloc[:, 0]:

        # pd.isna(value) checks whether something is missing.
        #
        # Missing values can appear as NaN inside pandas.
        #
        if pd.isna(value):

            # If the row is empty, add an empty string.
            rows.append("")

        else:

            # Otherwise convert the value into text.
            rows.append(str(value))


    # --------------------------------------------------------
    # JOIN THE ROWS INTO ONE TEXT BLOCK
    # --------------------------------------------------------
    #
    # "\n" means newline.
    #
    # So:
    #
    # "\n".join(rows)
    #
    # creates something like:
    #
    # header1,header2,header3
    # value1,value2,value3
    # value4,value5,value6
    #
    csv_text = "\n".join(rows)


    # --------------------------------------------------------
    # CONVERT THAT TEXT INTO A PROPER DATAFRAME
    # --------------------------------------------------------
    #
    # StringIO makes our Python string behave like a file.
    #
    # pandas can then use read_csv() on it.
    #
    corrected_df = pd.read_csv(

        StringIO(csv_text),

        # Our separator is a comma.
        sep=",",

        # Again, keep types generic for now.
        #
        # Step 2 will normalize the values properly.
        #
        dtype=object,
    )


    # Give the repaired DataFrame back to the caller.
    return corrected_df


# ============================================================
# LOAD ALL CORROBORIA DATA
# ============================================================

def load_all_data() -> dict[str, dict[str, pd.DataFrame]]:
    """
    Load all CorroborIA input workbooks.

    The result has this general structure:

        workbooks
        │
        ├── source
        │   └── worksheet
        │       └── DataFrame
        │
        ├── destination
        │   └── worksheet
        │       └── DataFrame
        │
        ├── mapping
        │   ├── Mapping
        │   ├── Règles situation d'emploi
        │   ├── Jointure - Détail du poste
        │   └── Jointure - Motif des situations
        │
        ├── job_details
        │   └── Feuil1
        │
        └── employment_reasons
            └── Sheet1

    Returns
    -------
    dict[str, dict[str, pd.DataFrame]]
        All loaded datasets.
    """

    # --------------------------------------------------------
    # FIRST MAKE SURE EVERY FILE EXISTS
    # --------------------------------------------------------

    check_files_exist()


    # --------------------------------------------------------
    # CREATE OUR MAIN DATA CONTAINER
    # --------------------------------------------------------
    #
    # This starts empty.
    #
    # We will fill it with each workbook.
    #
    workbooks = {}


    # --------------------------------------------------------
    # LOOP THROUGH EVERY REQUIRED FILE
    # --------------------------------------------------------

    for name, path in FILES.items():

        # Print progress so we know what Python is loading.
        #
        print(
            f"Loading {name}: {path.name}"
        )


        # ----------------------------------------------------
        # LOAD THE WORKBOOK
        # ----------------------------------------------------
        #
        # Remember:
        #
        # load_excel_file()
        #
        # returns ALL worksheets from that workbook.
        #
        sheets = load_excel_file(path)


        # ----------------------------------------------------
        # SPECIAL FIX FOR JOB DETAILS
        # ----------------------------------------------------
        #
        # We discovered that détail_du_poste.xlsx contains
        # comma-separated data in a single Excel column.
        #
        # Therefore ONLY this workbook needs the repair.
        #
        if name == "job_details":

            # Loop through every worksheet inside the workbook.
            #
            for sheet_name, df in sheets.items():

                # Replace the worksheet DataFrame with the
                # repaired version.
                #
                sheets[sheet_name] = (
                    fix_comma_separated_sheet(df)
                )


        # ----------------------------------------------------
        # STORE THE WORKBOOK
        # ----------------------------------------------------
        #
        # Example:
        #
        # workbooks["source"] = {
        #     "Employe_Source": DataFrame(...)
        # }
        #
        workbooks[name] = sheets


    # Return everything.
    return workbooks


# ============================================================
# INSPECT LOADED DATA
# ============================================================

def inspect_workbooks(
    workbooks: dict[str, dict[str, pd.DataFrame]]
) -> None:
    """
    Print useful information about every loaded workbook.

    This does NOT modify any data.

    It simply helps us understand:

        - worksheet names
        - number of rows
        - number of columns
        - column names
    """

    # Print a blank line and a separator.
    print("\n" + "=" * 70)

    # Print a title.
    print("CORROBORIA - INPUT DATA SUMMARY")

    # Print another separator.
    print("=" * 70)


    # --------------------------------------------------------
    # LOOP THROUGH WORKBOOKS
    # --------------------------------------------------------

    for workbook_name, sheets in workbooks.items():

        # Example:
        #
        # [SOURCE]
        #
        print(
            f"\n[{workbook_name.upper()}]"
        )


        # ----------------------------------------------------
        # LOOP THROUGH WORKSHEETS
        # ----------------------------------------------------

        for sheet_name, df in sheets.items():

            # Print worksheet name.
            print(
                f"\n  Sheet: {sheet_name}"
            )


            # len(df)
            #
            # returns the number of rows.
            #
            print(
                f"  Rows: {len(df)}"
            )


            # len(df.columns)
            #
            # returns the number of columns.
            #
            print(
                f"  Columns: {len(df.columns)}"
            )


            # Print heading before listing columns.
            print(
                "  Column names:"
            )


            # Loop through every column name.
            for column in df.columns:

                print(
                    f"    - {column}"
                )


# ============================================================
# OPTIONAL DATA PREVIEW
# ============================================================

def preview_workbooks(
    workbooks: dict[str, dict[str, pd.DataFrame]],
    number_of_rows: int = 5,
) -> None:
    """
    Print the first few rows of every worksheet.

    df.head(5)

    means:

        show the first five rows.

    This is useful while developing because it lets us see
    what the actual values look like.

    Parameters
    ----------
    workbooks
        All loaded workbooks.

    number_of_rows
        Number of rows to display from each worksheet.
    """

    print("\n" + "=" * 70)
    print("CORROBORIA - DATA PREVIEW")
    print("=" * 70)


    for workbook_name, sheets in workbooks.items():

        for sheet_name, df in sheets.items():

            print("\n" + "-" * 70)

            print(
                f"{workbook_name.upper()} -> {sheet_name}"
            )

            print("-" * 70)

            # df.head(number_of_rows)
            #
            # displays only the first few records.
            #
            print(
                df.head(number_of_rows)
            )


# ============================================================
# MAIN PROGRAM
# ============================================================

# __name__ is a special Python variable.
#
# When we run:
#
#     py main.py
#
# Python sets:
#
#     __name__ = "__main__"
#
#
# This means the code below runs when main.py is executed
# directly.
#
# Later, if another Python file imports functions from main.py,
# this section will NOT automatically run.
#
if __name__ == "__main__":

    # --------------------------------------------------------
    # STEP 1A
    # LOAD THE INPUT DATA
    # --------------------------------------------------------

    workbooks = load_all_data()


    # --------------------------------------------------------
    # STEP 1B
    # INSPECT THE STRUCTURE
    # --------------------------------------------------------

    inspect_workbooks(workbooks)


    # --------------------------------------------------------
    # STEP 1C
    # SHOW SAMPLE DATA
    # --------------------------------------------------------
    #
    # This displays the first 5 rows of each worksheet.
    #
    # It is useful right now while we're developing.
    #
    # Later, we can remove this once the project is finished.
    #
    preview_workbooks(
        workbooks,
        number_of_rows=5,
    )


    # --------------------------------------------------------
    # SUCCESS MESSAGE
    # --------------------------------------------------------

    print(
        "\nAll files loaded successfully."
    )