# Cadence Report Automation

This small Flask app allows uploading an Excel workbook that contains Power Query (M) queries. The app will open Excel via COM automation, refresh Power Query queries, and return the processed workbook.

Requirements:
- Windows with Microsoft Excel installed
- Python 3.9+ and dependencies from `requirements.txt`

Quick start:

1. Create a virtual environment and install:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. Run the app:

```bash
python app.py
```

3. Open `http://127.0.0.1:5000` and upload an Excel file.
