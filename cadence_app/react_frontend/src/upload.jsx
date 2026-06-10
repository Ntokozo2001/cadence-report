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