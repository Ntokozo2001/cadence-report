function ResultPage({ result, onReset }) {
  const {
    workbook_url,
    report_url,
    cisco_url,
    report_error,
    report_summary,
  } = result;

  return (
    <div className="shell">
      <div className="card fade-up">
        <div className="card-header fade-up">
          <div className="eyebrow">Processing complete</div>
          <h1 className="page-title">Your workbook and<br />report are ready</h1>
          <p className="lead">
            The workbook was refreshed successfully, and an HTML report with graphs
            and insights was created from the analyzed data.
          </p>
        </div>

        <div className="card-body fade-up-2">
          {/* Downloads */}
          <div>
            <div className="section-label">Downloads</div>
            <p className="section-copy">
              Use the links below to get the refreshed workbook or open the report in your browser.
            </p>

            <div className="action-grid">
              {workbook_url && (
                <a className="btn btn-primary" href={workbook_url} download>
                  ↓ Download workbook
                </a>
              )}
              {report_url && (
                <a className="btn btn-secondary" href={report_url} target="_blank" rel="noopener noreferrer">
                  ↗ Open HTML report
                </a>
              )}
              {cisco_url && (
                <a className="btn btn-secondary" href={cisco_url} download>
                  ↓ Download Cisco Funnel Excel
                </a>
              )}
            </div>

            {report_error && (
              <ul className="flash-list" role="status" aria-live="polite">
                <li className="flash-item">Report generation warning: {report_error}</li>
              </ul>
            )}

            {report_summary && (
              <div className="stats-grid">
                <div className="stat-cell"><span>Sheets analyzed</span><strong>{report_summary.sheet_count}</strong></div>
                <div className="stat-cell"><span>Total rows</span><strong>{report_summary.row_count}</strong></div>
                <div className="stat-cell"><span>Numeric fields</span><strong>{report_summary.numeric_fields}</strong></div>
                <div className="stat-cell"><span>Categorical fields</span><strong>{report_summary.categorical_fields}</strong></div>
              </div>
            )}
          </div>

          {/* Report Preview */}
          {report_url && (
            <div>
              <div className="section-label">Preview</div>
              <p className="section-copy">
                The report is embedded below so you can inspect the graphs and insights without leaving the page.
              </p>
              <iframe
                className="preview-frame"
                src={report_url}
                title="Generated workbook report"
              />
            </div>
          )}

          <div className="actions">
            <button className="btn btn-secondary" onClick={onReset}>
              ← Upload another file
            </button>
          </div>

          <p className="footer-note">
            Tip: if you want to process another file, click the button above to submit a new workbook.
          </p>
        </div>
      </div>
    </div>
  );
}