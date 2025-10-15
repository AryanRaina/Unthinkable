export interface Job {
  id: number;
  title: string;
  description: string;
  required_skills: string[];
  created_at: string;
}

export interface Resume {
  id: number;
  candidate_name: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  skills: string[];
  experience_years: number | null;
  education_entries: Record<string, unknown>[];
  created_at: string;
}

export interface MatchResult {
  id: number;
  resume_id: number;
  job_id: number;
  score: number;
  reasoning: string;
  llm_model: string | null;
  created_at: string;
  resume?: Resume;
}

export interface ShortlistResponse {
  job_id: number;
  shortlisted: MatchResult[];
}
