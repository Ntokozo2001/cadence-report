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
uv run python app.py
```

If you are using an activated virtual environment instead of `uv`, run:

```bash
venv\Scripts\python.exe app.py
```

3. Open `http://127.0.0.1:5000` and upload an Excel file.

The app will return the refreshed workbook and generate an HTML report with charts and data insights.

## CCW GraphQL API

You can proxy GraphQL requests to CCW through this app by setting these environment variables before starting the server:

- `CCW_GRAPHQL_URL`: the CCW GraphQL endpoint
- `CCW_API_TOKEN`: the access token used in the `Authorization: Bearer ...` header

Then POST JSON to `http://127.0.0.1:5000/api/ccw/graphql` with a body like:

```json
{
	"query": "query GetExample { me { id } }",
	"variables": {},
	"operationName": "GetExample"
}
```
