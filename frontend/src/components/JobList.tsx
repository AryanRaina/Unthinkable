import type { Job } from '@/types';

interface Props {
  jobs: Job[];
  onRunMatch: (jobId: number) => void;
  loadingJobId?: number | null;
  selectedJobId?: number | null;
  onSelect?: (jobId: number) => void;
}

export function JobList({ jobs, onRunMatch, loadingJobId = null, selectedJobId = null, onSelect }: Props) {
  return (
    <section className="sidebarSection">
      <header className="sidebarSectionHeader">
        <h2>Open Roles</h2>
        <span className="chip">{jobs.length}</span>
      </header>
      {jobs.length === 0 ? (
        <p className="emptyState">Create a role to start matching resumes.</p>
      ) : (
        <ul className="jobList">
          {jobs.map((job) => {
            const isActive = job.id === selectedJobId;
            const isLoading = job.id === loadingJobId;
            const summary = job.description.length > 160 ? `${job.description.slice(0, 160)}…` : job.description;
            return (
              <li key={job.id} className={`jobListItem ${isActive ? 'active' : ''}`}>
                <div
                  className="jobListSelectable"
                  onClick={() => onSelect?.(job.id)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault();
                      onSelect?.(job.id);
                    }
                  }}
                  role="button"
                  tabIndex={0}
                >
                  <div className="jobListTitle">
                    <h3>{job.title}</h3>
                    <small>{new Date(job.created_at).toLocaleDateString()}</small>
                  </div>
                  <p className="jobListSummary">{summary}</p>
                  {job.required_skills.length > 0 && (
                    <div className="jobListTags">
                      {job.required_skills.slice(0, 5).map((skill) => (
                        <span key={skill} className="pill">
                          {skill}
                        </span>
                      ))}
                      {job.required_skills.length > 5 && (
                        <span className="pill muted">+{job.required_skills.length - 5}</span>
                      )}
                    </div>
                  )}
                </div>
                <div className="jobListFooter">
                  <button
                    className="ghost"
                    onClick={(event) => {
                      event.stopPropagation();
                      onRunMatch(job.id);
                    }}
                    disabled={isLoading}
                  >
                    {isLoading ? 'Scoring…' : 'Refresh shortlist'}
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
