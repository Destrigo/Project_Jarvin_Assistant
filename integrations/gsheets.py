"""Google Sheets integration — read and write spreadsheet data."""
from googleapiclient.discovery import build
from integrations.google_auth import get_credentials


def _service():
    return build("sheets", "v4", credentials=get_credentials())


def sheets_read(spreadsheet_id: str, range_: str = "Sheet1") -> dict:
    """Read cells from a Google Sheet.

    spreadsheet_id: the ID from the sheet URL (the long alphanumeric string)
    range_: A1 notation, e.g. 'Sheet1', 'Sheet1!A1:E20', 'Budget!B2:F'
    """
    svc = _service()
    result = svc.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_,
        valueRenderOption="FORMATTED_VALUE",
    ).execute()

    values = result.get("values", [])
    if not values:
        return {"spreadsheet_id": spreadsheet_id, "range": range_, "rows": [], "count": 0}

    # if first row looks like headers, return as list-of-dicts
    headers = values[0] if values else []
    rows = []
    for row in values[1:]:
        # pad short rows
        padded = row + [""] * (len(headers) - len(row))
        rows.append(dict(zip(headers, padded)))

    return {
        "spreadsheet_id": spreadsheet_id,
        "range": result.get("range", range_),
        "headers": headers,
        "rows": rows,
        "count": len(rows),
    }


def sheets_write(spreadsheet_id: str, range_: str, values: list[list]) -> dict:
    """Write values to a Google Sheet range.

    values: 2D array of values, e.g. [["Name", "Age"], ["Alice", 30]]
    """
    svc = _service()
    body = {"values": values}
    result = svc.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_,
        valueInputOption="USER_ENTERED",
        body=body,
    ).execute()

    return {
        "spreadsheet_id": spreadsheet_id,
        "updated_range":  result.get("updatedRange", range_),
        "updated_rows":   result.get("updatedRows", 0),
        "updated_cells":  result.get("updatedCells", 0),
    }


def sheets_append(spreadsheet_id: str, range_: str, values: list[list]) -> dict:
    """Append rows to a Google Sheet (below existing data)."""
    svc = _service()
    body = {"values": values}
    result = svc.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=range_,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body,
    ).execute()

    updates = result.get("updates", {})
    return {
        "spreadsheet_id": spreadsheet_id,
        "appended_range": updates.get("updatedRange", range_),
        "appended_rows":  updates.get("updatedRows", 0),
    }
