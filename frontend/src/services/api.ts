import type { Job, MatchResult, Resume, ShortlistResponse } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

interface CreateJobPayload {
  title: string;
  description: string;
  required_skills: string[];
}

interface UpdateJobPayload {
  title?: string;
  description?: string;
  required_skills?: string[];
}

export async function deleteJob(jobId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
    method: 'DELETE'
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || response.statusText);
  }
}

interface CreateResumePayload {
  candidate_name?: string;
  raw_text: string;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || response.statusText);
  }
  return response.json() as Promise<T>;
}

export async function fetchJobs(): Promise<Job[]> {
  const response = await fetch(`${API_BASE_URL}/jobs`);
  return handleResponse<Job[]>(response);
}

export async function createJob(payload: CreateJobPayload): Promise<Job> {
  const response = await fetch(`${API_BASE_URL}/jobs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });
  return handleResponse<Job>(response);
}

export async function updateJob(jobId: number, payload: UpdateJobPayload): Promise<Job> {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });
  return handleResponse<Job>(response);
}

export async function createResume(payload: CreateResumePayload): Promise<Resume> {
  const response = await fetch(`${API_BASE_URL}/resumes`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });
  return handleResponse<Resume>(response);
}

export async function uploadResume(formData: FormData): Promise<Resume> {
  const response = await fetch(`${API_BASE_URL}/resumes/upload`, {
    method: 'POST',
    body: formData
  });
  return handleResponse<Resume>(response);
}

export async function deleteResume(resumeId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/resumes/${resumeId}`, {
    method: 'DELETE'
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || response.statusText);
  }
}

export async function shortlist(jobId: number): Promise<ShortlistResponse> {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/match`, {
    method: 'POST'
  });
  return handleResponse<ShortlistResponse>(response);
}

export async function listMatches(jobId: number): Promise<MatchResult[]> {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/matches`);
  return handleResponse<MatchResult[]>(response);
}
