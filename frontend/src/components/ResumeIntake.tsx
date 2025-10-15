import { FormEvent, useState } from 'react';

interface Props {
  onUpload: (formData: FormData) => Promise<void>;
  onSubmitText: (payload: { candidateName?: string; rawText: string }) => Promise<void>;
  busy?: boolean;
}

export function ResumeIntake({ onUpload, onSubmitText, busy = false }: Props) {
  const [candidateName, setCandidateName] = useState('');
  const [resumeText, setResumeText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<'upload' | 'text'>('upload');

  const handleFileSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!file) {
      return;
    }
    const formData = new FormData();
    formData.append('file', file);
    if (candidateName.trim()) {
      formData.append('candidate_name', candidateName.trim());
    }
    await onUpload(formData);
    setFile(null);
  };

  const handleTextSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!resumeText.trim()) {
      return;
    }
    await onSubmitText({ candidateName: candidateName.trim() || undefined, rawText: resumeText });
    setResumeText('');
  };

  return (
    <section className="panel panel--form">
      <header className="panelHeader">
        <div>
          <h2>Candidate Intake</h2>
          <p>Simplify resume onboarding with uploads or quick paste.</p>
        </div>
        <div className="tabs" role="tablist" aria-label="Resume intake mode">
          <button
            type="button"
            className={`tab ${mode === 'upload' ? 'active' : ''}`}
            onClick={() => setMode('upload')}
            role="tab"
            aria-selected={mode === 'upload' ? true : false}
          >
            Upload
          </button>
          <button
            type="button"
            className={`tab ${mode === 'text' ? 'active' : ''}`}
            onClick={() => setMode('text')}
            role="tab"
            aria-selected={mode === 'text' ? true : false}
          >
            Paste Text
          </button>
        </div>
      </header>
      {mode === 'upload' ? (
        <form className="stack" onSubmit={handleFileSubmit}>
          <label className="stack">
            <span>Candidate Name (optional)</span>
            <input
              placeholder="Jane Doe"
              value={candidateName}
              onChange={(event) => setCandidateName(event.target.value)}
            />
          </label>
          <label className="stack">
            <span>Resume File (PDF/TXT)</span>
            <input
              type="file"
              accept=".pdf,.txt,.md"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              required
            />
          </label>
          <button className="primary" type="submit" disabled={busy || !file}>
            {busy ? 'Uploading…' : 'Upload Resume'}
          </button>
        </form>
      ) : (
        <form className="stack" onSubmit={handleTextSubmit}>
          <label className="stack">
            <span>Candidate Name (optional)</span>
            <input
              placeholder="Jane Doe"
              value={candidateName}
              onChange={(event) => setCandidateName(event.target.value)}
            />
          </label>
          <label className="stack">
            <span>Resume Text</span>
            <textarea
              rows={8}
              placeholder="Paste resume content here..."
              value={resumeText}
              onChange={(event) => setResumeText(event.target.value)}
            />
          </label>
          <button className="primary" type="submit" disabled={busy || !resumeText.trim()}>
            {busy ? 'Submitting…' : 'Save Text Resume'}
          </button>
        </form>
      )}
    </section>
  );
}
