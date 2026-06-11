import { useState, useRef } from "react";

const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:ital,wght@0,300;0,400;1,300&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #e6e8ed;
    --surface: #eb1515;
    --surface-2: #1c1f27;
    --border: #2a2d38;
    --accent: #e8ff47;
    --accent-dim: #b8cc2f;
    --text: #c9d2d6;
    --muted: #191a1e;
    --danger: #ff5e5e;
    --success: #47e8a0;
    --radius: 4px;
    --radius-lg: 12px;
  }

  .app-root {
    font-family: 'DM Mono', monospace;
    background: transparent;
    min-height: 100vh;
    color: var(--text);
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding: 40px 16px 80px;
    position: relative;
    overflow-x: hidden;
  }

  .app-root::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
      radial-gradient(ellipse 60% 40% at 15% 10%, rgba(232,255,71,0.07) 0%, transparent 60%),
      radial-gradient(ellipse 40% 60% at 85% 90%, rgba(71,232,160,0.05) 0%, transparent 60%);
    pointer-events: none;
  }

  .shell {
    width: 100%;
    max-width: 780px;
    position: relative;
  }

  /* ── HEADER ── */
  .eyebrow {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    font-weight: 400;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--accent);
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
  }
  .eyebrow::before {
    content: '';
    display: block;
    width: 28px;
    height: 1px;
    background: var(--accent);
  }

  .page-title {
    font-family: 'Syne', sans-serif;
    font-size: clamp(28px, 5vw, 48px);
    font-weight: 800;
    line-height: 1.08;
    letter-spacing: -0.02em;
    color: var(--text);
    margin-bottom: 16px;
  }

  .lead {
    font-size: 14px;
    line-height: 1.7;
    color: var(--muted);
    max-width: 520px;
    margin-bottom: 40px;
  }

  /* ── CARD ── */
  .card {
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    overflow: hidden;
    background: white;
  }

  .card-header {
    background: #eb1515;
    color: white;
    padding: 40px 40px 32px;
  }

  .card-body {
    padding: 36px 40px;
    display: flex;
    flex-direction: column;
    gap: 32px;
  }

  @media (max-width: 560px) {
    .card-header, .card-body { padding: 24px 20px; }
  }

  /* ── SECTION LABELS ── */
  .section-label {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 10px;
  }

  .section-copy {
    font-size: 13px;
    line-height: 1.65;
    color: var(--muted);
    margin-bottom: 24px;
  }

  /* ── FILE DROP ── */
  .drop-zone {
    border: 1.5px dashed var(--border);
    border-radius: var(--radius-lg);
    padding: 36px 28px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    cursor: pointer;
    transition: border-color 0.2s, background 0.2s;
    text-align: center;
    position: relative;
  }
  .drop-zone:hover, .drop-zone.drag-over {
    border-color: var(--accent);
    background: rgba(232,255,71,0.04);
  }
  .drop-zone input[type="file"] {
    position: absolute;
    inset: 0;
    opacity: 0;
    cursor: pointer;
    width: 100%;
    height: 100%;
  }

  .drop-icon {
    width: 44px;
    height: 44px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
  }

  .drop-label {
    font-family: 'Syne', sans-serif;
    font-size: 14px;
    font-weight: 600;
    color: var(--text);
  }
  .drop-label span { color: var(--accent); }
  .drop-sub {
    font-size: 12px;
    color: var(--muted);
  }

  .file-chip {
    display: flex;
    align-items: center;
    gap: 10px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 8px 16px;
    font-size: 13px;
    color: var(--text);
    margin-top: 8px;
  }
  .file-chip-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--accent);
    flex-shrink: 0;
  }

  /* ── FLASH ── */
  .flash-list {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 20px;
  }
  .flash-item {
    background: rgba(255,94,94,0.08);
    border: 1px solid rgba(255,94,94,0.3);
    border-radius: var(--radius);
    padding: 10px 14px;
    font-size: 13px;
    color: var(--danger);
  }
  .flash-item.success {
    background: rgba(71,232,160,0.08);
    border-color: rgba(71,232,160,0.3);
    color: var(--success);
  }

  /* ── BUTTON ── */
  .btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-family: 'Syne', sans-serif;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.03em;
    padding: 14px 28px;
    border-radius: var(--radius);
    border: none;
    cursor: pointer;
    transition: opacity 0.15s, transform 0.1s;
    text-decoration: none;
  }
  .btn:active { transform: scale(0.98); }
  .btn:disabled { opacity: 0.45; cursor: not-allowed; }

  .btn-primary {
    background: var(--accent);
    color: #0c0d0f;
  }
  .btn-primary:hover:not(:disabled) { background: var(--accent-dim); }

  .btn-secondary {
    background: var(--surface-2);
    color: var(--text);
    border: 1px solid var(--border);
  }
  .btn-secondary:hover { border-color: var(--accent); color: var(--accent); }

  .actions { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }

  /* ── PROGRESS ── */
  .progress-bar-wrap {
    height: 3px;
    background: var(--surface-2);
    border-radius: 99px;
    overflow: hidden;
    margin-top: 16px;
  }
  .progress-bar {
    height: 100%;
    background: var(--accent);
    border-radius: 99px;
    transition: width 0.4s ease;
  }

  /* ── RESULT STATS ── */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 12px;
  }
  .stat-cell {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px;
  }
  .stat-cell span {
    display: block;
    font-size: 11px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 6px;
  }
  .stat-cell strong {
    font-family: 'Syne', sans-serif;
    font-size: 28px;
    font-weight: 800;
    color: var(--accent);
  }

  /* ── ACTION GRID ── */
  .action-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 24px;
  }

  /* ── IFRAME ── */
  .preview-frame {
    width: 100%;
    height: 1850px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: #fff;
    margin-top: 12px;
    overflow: hidden;
    scrollbar-width: none;
  }

  .preview-frame::-webkit-scrollbar {
  display: none;
}

  /* ── FOOTER NOTE ── */
  .footer-note {
    font-size: 12px;
    color: var(--muted);
    font-style: italic;
    border-top: 1px solid var(--border);
    padding-top: 20px;
    margin-top: 8px;
  }

  /* ── SPINNER ── */
  @keyframes spin { to { transform: rotate(360deg); } }
  .spinner {
    width: 16px; height: 16px;
    border: 2px solid rgba(12,13,15,0.3);
    border-top-color: #0c0d0f;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    flex-shrink: 0;
  }

  /* ── PAGE FADE ── */
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .fade-up { animation: fadeUp 0.5s ease both; }
  .fade-up-2 { animation: fadeUp 0.5s 0.1s ease both; }
  .fade-up-3 { animation: fadeUp 0.5s 0.2s ease both; }
`;

/* ─────────────────────────── UPLOAD PAGE ─────────────────────────── */
function UploadPage({ onSuccess }) {
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [flashes, setFlashes] = useState([]);
  const inputRef = useRef();

  const handleFile = (f) => {
    const allowed = [".xls", ".xlsx", ".xlsm", ".xlsb"];
    if (!f) return;
    const ext = "." + f.name.split(".").pop().toLowerCase();
    if (!allowed.includes(ext)) {
      setFlashes([`"${f.name}" is not a supported format. Please upload an .xls, .xlsx, .xlsm, or .xlsb file.`]);
      return;
    }
    setFlashes([]);
    setFile(f);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const handleSubmit = async () => {
    if (!file) { setFlashes(["Please select a workbook first."]); return; }
    setLoading(true);
    setProgress(10);

    // Simulate upload progress
    const tick = setInterval(() => {
      setProgress((p) => (p < 85 ? p + Math.random() * 12 : p));
    }, 400);

    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("/upload", { method: "POST", body: formData });
      clearInterval(tick);
      setProgress(100);

      if (!res.ok) {
        const text = await res.text();
        setFlashes([text || "Upload failed. Please try again."]);
        setLoading(false);
        return;
      }

      const data = await res.json();
      setTimeout(() => onSuccess(data), 300);
    } catch {
      clearInterval(tick);
      setFlashes(["Network error — check your connection and try again."]);
      setLoading(false);
      setProgress(0);
    }
  };

  return (
    <div className="shell">
      <div className="card fade-up">
        <div className="card-header fade-up">
          <div className="eyebrow">Cadence Report Uploader</div>
          <h1 className="page-title">Upload Excel files<br />with Power Query</h1>
          <p className="lead">
            Choose a workbook, submit it for processing, and download the refreshed
            file once the Power Query steps complete.
          </p>
        </div>

        <div className="card-body fade-up-2">
          <div>
            <div className="section-label">Select a workbook</div>
            <p className="section-copy">
              Supported formats include .xls, .xlsx, .xlsm, and .xlsb. The uploaded
              file is processed and returned as a refreshed workbook.
            </p>

            {flashes.length > 0 && (
              <ul className="flash-list" role="status" aria-live="polite">
                {flashes.map((m, i) => <li key={i} className="flash-item">{m}</li>)}
              </ul>
            )}

            <div
              className={`drop-zone${dragOver ? " drag-over" : ""}`}
              onClick={() => !loading && inputRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              role="button"
              tabIndex={0}
              aria-label="Upload Excel workbook"
              onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".xls,.xlsx,.xlsm,.xlsb"
                style={{ display: "none" }}
                onChange={(e) => handleFile(e.target.files[0])}
                disabled={loading}
              />
              <div className="drop-icon">📊</div>
              <div className="drop-label">
                <span>Browse</span> or drag &amp; drop
              </div>
              <div className="drop-sub">.xls · .xlsx · .xlsm · .xlsb</div>
            </div>

            {file && (
              <div className="file-chip">
                <span className="file-chip-dot" />
                {file.name}
                <span style={{ marginLeft: "auto", color: "var(--muted)", fontSize: 11 }}>
                  {(file.size / 1024).toFixed(0)} KB
                </span>
              </div>
            )}

            {loading && (
              <div className="progress-bar-wrap">
                <div className="progress-bar" style={{ width: `${progress}%` }} />
              </div>
            )}
          </div>

          <div>
            <div className="actions">
              <button
                className="btn btn-primary"
                onClick={handleSubmit}
                disabled={loading || !file}
              >
                {loading ? <><span className="spinner" />Processing…</> : "Upload & Process"}
              </button>
            </div>
          </div>

          <p className="footer-note">
            Tip: close the workbook before uploading if Excel has it open locally.
          </p>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────── RESULT PAGE ─────────────────────────── */
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
                scrolling="no"
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

/* ─────────────────────────── ROOT ─────────────────────────── */
export default function App() {
  const [result, setResult] = useState(null);

  return (
    <>
      <style>{styles}</style>
      <div className="app-root">
        {result
          ? <ResultPage result={result} onReset={() => setResult(null)} />
          : <UploadPage onSuccess={setResult} />}
      </div>
    </>
  );
}