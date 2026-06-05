import os



def convert_to_cisco_funnel(input_path: str, output_dir: str) -> str:
    """Read the workbook at input_path, transform to Cisco Funnel format,
    and write an Excel file into output_dir. Returns the output filename.

    This function imports pandas lazily and raises a RuntimeError with
    instructions if pandas is not available. That allows the Flask app to
    start even when pandas isn't installed; conversion will fail with a
    clear message.
    """
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            "pandas is not installed in the environment. Install dependencies with: pip install -r requirements.txt (prefer Python 3.11 for prebuilt wheels)"
        ) from exc

    df = pd.read_excel(input_path, engine="openpyxl")

    # Clean column names
    df.columns = df.columns.str.strip()

    # Rename to match Cisco Funnel structure
    df = df.rename(columns={
        "Opportunity Number": "OPP Number",
        "FY Qrt List": "FY Qrt list",
        "Schedule Comments": "Extra Notes",
        "LOB / 2BDM Name": "LOB / BDM Name"
    })

    # Ensure columns exist and add defaults
    df["Billing Status"] = df.get("Billing Status", "No")
    df["Source"] = df.get("Source", "Upside Deal")
    df["Extra Notes"] = df.get("Extra Notes", "")
    df["Medium high chase"] = ""

    # Deal Status Mapping
    def map_source(row):
        if row.get("Deal Status") == "Commit":
            return "Backlog Deal"
        elif row.get("Deal Status") == "Upside":
            return "Upside Deal"
        else:
            return "Pipeline"

    df["Source"] = df.apply(map_source, axis=1)

    # Priority classification (Medium high chase)
    def classify_priority(prob):
        try:
            prob = float(prob)
        except Exception:
            return "Low"
        if prob >= 70:
            return "High"
        elif prob >= 40:
            return "Medium"
        else:
            return "Low"

    if "Deal Probability" in df.columns:
        df["Medium high chase"] = df["Deal Probability"].apply(classify_priority)
    else:
        df["Medium high chase"] = ""

    # Filter for Cadence view
    df_cadence = df[df.get("Deal Status").isin(["Upside", "Commit"])].copy() if "Deal Status" in df.columns else df.copy()

    cadence_cols = [
        "Medium high chase",
        "LOB INPUT",
        "Customer Name",
        "Sales Vertical",
        "OPP Number",
        "Gross Revenue",
        "Expected Net Revenue",
        "GP Value",
        "GP %",
        "Deal Status",
        "Billing Month",
        "FY Qrt list",
        "Billing Status",
        "Source",
        "Deal Probability",
        "Extra Notes",
        "Presales Name",
        "LOB / BDM Name",
        "Deal Type",
        "Opportunity Name",
    ]

    # Keep only columns that exist to avoid KeyError
    existing_cols = [c for c in cadence_cols if c in df_cadence.columns]
    df_cadence = df_cadence[existing_cols]

    # Totals
    totals = {
        "Gross Revenue": [df_cadence["Gross Revenue"].sum()] if "Gross Revenue" in df_cadence.columns else [0],
        "Expected Net Revenue": [df_cadence["Expected Net Revenue"].sum()] if "Expected Net Revenue" in df_cadence.columns else [0],
        "GP Value": [df_cadence["GP Value"].sum()] if "GP Value" in df_cadence.columns else [0],
    }
    totals_df = pd.DataFrame(totals)

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    out_name = f"CiscoFunnel_{base_name}.xlsx"
    out_path = os.path.join(output_dir, out_name)

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df_cadence.to_excel(writer, sheet_name="Current Cadence", index=False)
        totals_df.to_excel(writer, sheet_name="Totals", index=False)

    return out_name
