import time
import os
import pythoncom
import win32com.client

def _wait_for_refresh(wb, timeout=120):
    start = time.time()
    while True:
        refreshing = False
        try:
            for ws in wb.Worksheets:
                try:
                    # QueryTables (legacy) attached to sheets
                    qts = ws.QueryTables
                    for i in range(1, qts.Count + 1):
                        qt = qts.Item(i)
                        if getattr(qt, 'Refreshing', False):
                            refreshing = True
                            break
                except Exception:
                    pass
                try:
                    # ListObjects loaded by Power Query have QueryTable
                    los = ws.ListObjects
                    for j in range(1, los.Count + 1):
                        lo = los.Item(j)
                        try:
                            qt = lo.QueryTable
                            if getattr(qt, 'Refreshing', False):
                                refreshing = True
                                break
                        except Exception:
                            pass
                except Exception:
                    pass
            if not refreshing:
                break
        except Exception:
            # If enumerating worksheets fails, break to avoid infinite loop
            break
        if time.time() - start > timeout:
            break
        time.sleep(1)

def refresh_power_query_workbook(src_path, out_path=None, timeout=120):
    if out_path is None:
        out_path = src_path
    # Ensure absolute paths
    src_path = os.path.abspath(src_path)
    out_path = os.path.abspath(out_path)

    # COM must be initialized on the current thread
    pythoncom.CoInitialize()
    excel = win32com.client.DispatchEx('Excel.Application')
    excel.Visible = False
    excel.DisplayAlerts = False
    try:
        wb = excel.Workbooks.Open(src_path, UpdateLinks=0)
        # Refresh all Power Query / connections
        wb.RefreshAll()
        # Wait for refresh completion
        _wait_for_refresh(wb, timeout=timeout)
        # Save workbook as xlsx (preserve macro-enabled if needed)
        wb.SaveAs(out_path)
        wb.Close(SaveChanges=False)
    finally:
        try:
            excel.Quit()
        except Exception:
            pass
        pythoncom.CoUninitialize()
