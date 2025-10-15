import { FormEvent, useEffect, useState } from 'react';

type JobFormValues = {
  title: string;
  description: string;
  requiredSkills: string[];
};

interface Props {
  mode?: 'create' | 'edit';
  onSubmit: (payload: JobFormValues) => Promise<void>;
  busy?: boolean;
  initialValues?: JobFormValues;
  heading?: string;
  subheading?: string;
  hideHeader?: boolean;
  onCancel?: () => void;
}

export function JobForm({
  mode = 'create',
  onSubmit,
  busy = false,
  initialValues,
  heading,
  subheading,
  hideHeader = false,
  onCancel,
}: Props) {
  const [title, setTitle] = useState(initialValues?.title ?? '');
  const [description, setDescription] = useState(initialValues?.description ?? '');
  const [skills, setSkills] = useState(initialValues ? initialValues.requiredSkills.join(', ') : '');

  const skillsKey = initialValues?.requiredSkills?.join('|') ?? '';

  useEffect(() => {
    if (mode === 'edit' && initialValues) {
      setTitle(initialValues.title);
      setDescription(initialValues.description);
      setSkills(initialValues.requiredSkills.join(', '));
    }
    if (mode === 'edit' && !initialValues) {
      setTitle('');
      setDescription('');
      setSkills('');
    }
  }, [mode, initialValues?.title, initialValues?.description, skillsKey]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const requiredSkills = skills
      .split(',')
      .map((skill) => skill.trim())
      .filter(Boolean);
    await onSubmit({
      title: title.trim(),
      description: description.trim(),
      requiredSkills,
    });
    if (mode === 'create') {
      setTitle('');
      setDescription('');
      setSkills('');
    }
  };

  const handleReset = () => {
    if (initialValues) {
      setTitle(initialValues.title);
      setDescription(initialValues.description);
      setSkills(initialValues.requiredSkills.join(', '));
    } else {
      setTitle('');
      setDescription('');
      setSkills('');
    }
  };

  const headerTitle = heading ?? (mode === 'edit' ? 'Edit Job' : 'Create Job');
  const headerCopy =
    subheading ??
    (mode === 'edit'
      ? 'Update the selected job to keep requirements current.'
      : 'Add a job description to match resumes against.');
  const submitLabel = busy ? 'Saving…' : mode === 'edit' ? 'Save Changes' : 'Create Job';
  const showCancel = typeof onCancel === 'function';

  const containerClasses = ['panel', 'panel--form'];
  if (mode === 'edit') {
    containerClasses.push('panel--formInline');
  }

  return (
    <section className={containerClasses.join(' ')}>
      {!hideHeader && (
        <header className="panelHeader">
          <h2>{headerTitle}</h2>
          <p>{headerCopy}</p>
        </header>
      )}
      <form className="stack" onSubmit={handleSubmit}>
        <label className="stack">
          <span>Job Title</span>
          <input
            required
            placeholder="Senior Backend Engineer"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
        </label>
        <label className="stack">
          <span>Description</span>
          <textarea
            required
            rows={4}
            placeholder="Describe responsibilities, required experience, and nice-to-haves."
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
        </label>
        <label className="stack">
          <span>Required Skills (comma separated)</span>
          <input
            placeholder="Python, FastAPI, AWS"
            value={skills}
            onChange={(event) => setSkills(event.target.value)}
          />
        </label>
        {mode === 'edit' ? (
          <div className="actions">
            {showCancel && (
              <button className="ghost" type="button" onClick={onCancel} disabled={busy}>
                Cancel
              </button>
            )}
            <button className="secondary" type="button" onClick={handleReset} disabled={busy}>
              Reset
            </button>
            <button className="primary" type="submit" disabled={busy}>
              {submitLabel}
            </button>
          </div>
        ) : (
          <button className="primary" type="submit" disabled={busy}>
            {submitLabel}
          </button>
        )}
      </form>
    </section>
  );
}
