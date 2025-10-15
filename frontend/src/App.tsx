import { useCallback, useEffect, useMemo, useState } from 'react';
import { JobForm } from '@/components/JobForm';
import { ResumeIntake } from '@/components/ResumeIntake';
import { JobList } from '@/components/JobList';
import { ShortlistPanel } from '@/components/ShortlistPanel';
import {
  createJob,
  createResume,
  deleteJob,
  deleteResume,
  fetchJobs,
  listMatches,
  shortlist,
  updateJob,
  uploadResume
} from '@/services/api';
import type { Job, MatchResult } from '@/types';

interface Toast {
  text: string;
  tone: 'success' | 'error';
}

export default function App() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [matchesByJob, setMatchesByJob] = useState<Record<number, MatchResult[]>>({});
  const [toast, setToast] = useState<Toast | null>(null);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [creatingJob, setCreatingJob] = useState(false);
  const [updatingJobId, setUpdatingJobId] = useState<number | null>(null);
  const [uploadingResume, setUploadingResume] = useState(false);
  const [matchingJobId, setMatchingJobId] = useState<number | null>(null);
  const [deletingJobId, setDeletingJobId] = useState<number | null>(null);
  const [removingResumeId, setRemovingResumeId] = useState<number | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  const selectedJob = useMemo(
    () => jobs.find((job) => job.id === selectedJobId) ?? null,
    [jobs, selectedJobId]
  );

  const showToast = useCallback((text: string, tone: Toast['tone'] = 'success') => {
    setToast({ text, tone });
  }, []);

  const loadJobs = useCallback(async () => {
    setLoadingJobs(true);
    try {
      const data = await fetchJobs();
      setJobs(data);
      if (data.length > 0 && !selectedJobId) {
        setSelectedJobId(data[0].id);
      }
      if (data.length === 0) {
        setIsEditing(false);
      }
    } catch (error) {
      console.error(error);
      showToast('Unable to load jobs. Check backend connection.', 'error');
    } finally {
      setLoadingJobs(false);
    }
  }, [selectedJobId, showToast]);

  useEffect(() => {
    loadJobs().catch((error) => console.error(error));
  }, [loadJobs]);

  const handleCreateJob = async ({ title, description, requiredSkills }: { title: string; description: string; requiredSkills: string[]; }) => {
    try {
      setCreatingJob(true);
      const job = await createJob({ title, description, required_skills: requiredSkills });
      setJobs((current) => [job, ...current]);
      setSelectedJobId(job.id);
      setIsCreateOpen(false);
      setIsEditing(false);
      showToast('Job created successfully.');
    } catch (error) {
      console.error(error);
      showToast('Failed to create job.', 'error');
    } finally {
      setCreatingJob(false);
    }
  };

  const handleUpdateJob = async (
    jobId: number,
    { title, description, requiredSkills }: { title: string; description: string; requiredSkills: string[]; }
  ) => {
    try {
      setUpdatingJobId(jobId);
      const updated = await updateJob(jobId, {
        title,
        description,
        required_skills: requiredSkills,
      });
      setJobs((current) => current.map((job) => (job.id === jobId ? updated : job)));
      setMatchesByJob((current) => {
        if (!(jobId in current)) {
          return current;
        }
        const { [jobId]: _removed, ...rest } = current;
        return rest;
      });
      setIsEditing(false);
      showToast('Job updated successfully.');
    } catch (error) {
      console.error(error);
      showToast('Failed to update job.', 'error');
    } finally {
      setUpdatingJobId(null);
    }
  };

  const handleDeleteJob = async (jobId: number) => {
    if (deletingJobId !== null || !window.confirm('Delete this job and its shortlist? This cannot be undone.')) {
      return;
    }
    try {
      setDeletingJobId(jobId);
      await deleteJob(jobId);
      setMatchesByJob((current) => {
        if (!(jobId in current)) {
          return current;
        }
        const { [jobId]: _removed, ...rest } = current;
        return rest;
      });
      let nextSelection: number | null = null;
      setJobs((current) => {
        const updated = current.filter((job) => job.id !== jobId);
        nextSelection = updated.length > 0 ? updated[0].id : null;
        if (updated.length === 0) {
          setIsEditing(false);
        }
        return updated;
      });
      setSelectedJobId((currentSelected) =>
        currentSelected === jobId ? nextSelection : currentSelected
      );
      showToast('Job deleted.');
    } catch (error) {
      console.error(error);
      showToast('Failed to delete job.', 'error');
    } finally {
      setDeletingJobId(null);
    }
  };

  const handleUpload = async (formData: FormData) => {
    try {
      setUploadingResume(true);
      await uploadResume(formData);
      showToast('Resume uploaded and parsed.');
    } catch (error) {
      console.error(error);
      showToast('Failed to upload resume.', 'error');
    } finally {
      setUploadingResume(false);
    }
  };

  const handleSubmitText = async (payload: { candidateName?: string; rawText: string }) => {
    try {
      setUploadingResume(true);
      await createResume({
        candidate_name: payload.candidateName,
        raw_text: payload.rawText
      });
      showToast('Text resume saved.');
    } catch (error) {
      console.error(error);
      showToast('Failed to submit resume text.', 'error');
    } finally {
      setUploadingResume(false);
    }
  };

  const handleRunMatch = async (jobId: number) => {
    try {
      setMatchingJobId(jobId);
      const result = await shortlist(jobId);
      setMatchesByJob((current) => ({
        ...current,
        [jobId]: result.shortlisted
      }));
      setSelectedJobId(jobId);
      setIsEditing(false);
      showToast('Shortlist updated.');
    } catch (error) {
      console.error(error);
      showToast('Failed to compute shortlist.', 'error');
    } finally {
      setMatchingJobId(null);
    }
  };

  const handleDeleteResume = async (resumeId: number) => {
    if (removingResumeId !== null || !window.confirm('Remove this candidate and delete their resume?')) {
      return;
    }
    try {
      setRemovingResumeId(resumeId);
      await deleteResume(resumeId);
      setMatchesByJob((current) => {
        let changed = false;
        const next: Record<number, MatchResult[]> = {};
        for (const [jobKey, matchList] of Object.entries(current)) {
          const filtered = matchList.filter((match) => (match.resume?.id ?? match.resume_id) !== resumeId);
          if (filtered.length !== matchList.length) {
            changed = true;
          }
          next[Number(jobKey)] = filtered;
        }
        return changed ? next : current;
      });
      showToast('Candidate removed.');
    } catch (error) {
      console.error(error);
      showToast('Failed to remove candidate.', 'error');
    } finally {
      setRemovingResumeId(null);
    }
  };

  const handleSelectJob = async (jobId: number) => {
    setSelectedJobId(jobId);
    setIsEditing(false);
    if (matchesByJob[jobId]) {
      return;
    }
    try {
      const data = await listMatches(jobId);
      if (data.length) {
        setMatchesByJob((current) => ({ ...current, [jobId]: data }));
      }
    } catch (error) {
      console.error(error);
      showToast('Unable to load previous matches.', 'error');
    }
  };

  const shortlistData = selectedJobId ? matchesByJob[selectedJobId] ?? [] : [];

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="sidebarBrand">
          <div className="brandMark">SR</div>
          <div>
            <h1>Smart Resume Screener</h1>
            <p>Match candidates to roles with confidence.</p>
          </div>
        </div>
        <div className="sidebarActions">
          <button
            className="primary"
            type="button"
            onClick={() => setIsCreateOpen((open) => !open)}
            disabled={loadingJobs}
          >
            {isCreateOpen ? 'Close form' : 'New job'}
          </button>
          <span className="sidebarHint">
            {loadingJobs
              ? 'Loading roles…'
              : jobs.length
              ? `${jobs.length} active ${jobs.length === 1 ? 'role' : 'roles'}`
              : 'No roles yet'}
          </span>
        </div>
        {isCreateOpen && (
          <div className="sidebarDrawer">
            <JobForm
              onSubmit={handleCreateJob}
              busy={creatingJob}
              heading="Create a job"
              subheading="Capture responsibilities and required skills for this role."
            />
          </div>
        )}
        <JobList
          jobs={jobs}
          onRunMatch={handleRunMatch}
          loadingJobId={matchingJobId}
          selectedJobId={selectedJobId}
          onSelect={handleSelectJob}
        />
      </aside>
      <main className="workspace">
        {toast && (
          <div className={`toast ${toast.tone}`} role="status">
            <span>{toast.text}</span>
            <button onClick={() => setToast(null)} aria-label="Dismiss notification">
              ×
            </button>
          </div>
        )}
        {selectedJob ? (
          <>
            <header className="workspaceHeader">
              <div>
                <p className="workspaceEyebrow">Active job</p>
                <h2>{selectedJob.title}</h2>
              </div>
              <div className="workspaceActions">
                <button
                  className="ghost"
                  type="button"
                  onClick={() => setIsEditing((value) => !value)}
                >
                  {isEditing ? 'Close editor' : 'Edit details'}
                </button>
                <button
                  className="danger"
                  type="button"
                  onClick={() => handleDeleteJob(selectedJob.id)}
                  disabled={deletingJobId === selectedJob.id}
                >
                  {deletingJobId === selectedJob.id ? 'Deleting…' : 'Delete role'}
                </button>
                <button
                  className="primary"
                  type="button"
                  onClick={() => handleRunMatch(selectedJob.id)}
                  disabled={matchingJobId === selectedJob.id}
                >
                  {matchingJobId === selectedJob.id ? 'Scoring…' : 'Refresh shortlist'}
                </button>
              </div>
            </header>
            <div className="workspaceGrid">
              <section className="panel panel--detail">
                <div className="panelHeader">
                  <div>
                    <h3>Role Overview</h3>
                    <p>Created {new Date(selectedJob.created_at).toLocaleString()}</p>
                  </div>
                </div>
                {isEditing ? (
                  <JobForm
                    mode="edit"
                    hideHeader
                    initialValues={{
                      title: selectedJob.title,
                      description: selectedJob.description,
                      requiredSkills: selectedJob.required_skills,
                    }}
                    busy={updatingJobId === selectedJob.id}
                    onSubmit={(values) => handleUpdateJob(selectedJob.id, values)}
                    onCancel={() => setIsEditing(false)}
                  />
                ) : (
                  <div className="jobOverview">
                    <p>{selectedJob.description}</p>
                    {selectedJob.required_skills.length > 0 && (
                      <div className="jobOverviewTags">
                        {selectedJob.required_skills.map((skill) => (
                          <span key={skill} className="pill">
                            {skill}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </section>
              <ResumeIntake
                onUpload={handleUpload}
                onSubmitText={handleSubmitText}
                busy={uploadingResume}
              />
            </div>
            <ShortlistPanel
              matches={shortlistData}
              jobTitle={selectedJob.title}
              onRemoveCandidate={handleDeleteResume}
              removingResumeId={removingResumeId}
            />
          </>
        ) : (
          <section className="panel panel--empty">
            <h2>Select a role</h2>
            <p>Use the sidebar to add a job or review an existing one.</p>
          </section>
        )}
      </main>
    </div>
  );
}
