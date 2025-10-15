import type { MatchResult } from '@/types';

interface Props {
  matches: MatchResult[];
  jobTitle?: string;
  onRemoveCandidate?: (resumeId: number) => void;
  removingResumeId?: number | null;
}

export function ShortlistPanel({ matches, jobTitle, onRemoveCandidate, removingResumeId }: Props) {
  return (
    <section className="panel panel--shortlist">
      <header className="panelHeader">
        <div>
          <h2>{jobTitle ? `Shortlist · ${jobTitle}` : 'Shortlist'}</h2>
          <p>Compare top candidates with transparent scoring insights.</p>
        </div>
        <span className="chip">{matches.length} shortlisted</span>
      </header>
      {matches.length === 0 ? (
        <p className="emptyState">Run a match to generate your first shortlist.</p>
      ) : (
        <ul className="shortlist">
          {matches.map((match, index) => {
            const lines = match.reasoning.split('\n').filter(Boolean);
            const resumeId = match.resume?.id ?? match.resume_id;
            const isRemoving = removingResumeId === resumeId;
            return (
              <li key={match.id} className="shortlistItem">
                <div className="shortlistScore">
                  <span>{match.score.toFixed(1)}</span>
                  <small>{match.llm_model ?? 'Heuristic'}</small>
                  <small>Rank {index + 1}</small>
                </div>
                <div className="shortlistContent">
                  <header className="shortlistHeader">
                    <div className="shortlistHeaderMain">
                      <h3>{match.resume?.candidate_name ?? 'Unnamed Candidate'}</h3>
                      {match.resume?.skills && match.resume.skills.length > 0 && (
                        <div className="skillsInline">
                          {match.resume.skills.slice(0, 6).map((skill) => (
                            <span key={skill} className="pill">
                              {skill}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    {onRemoveCandidate && (
                      <button
                        className="danger"
                        type="button"
                        onClick={() => onRemoveCandidate(resumeId)}
                        disabled={isRemoving}
                      >
                        {isRemoving ? 'Removing…' : 'Remove'}
                      </button>
                    )}
                  </header>
                  {lines.length > 0 && (
                    <ul className="shortlistReasoning">
                      {lines.map((line, lineIndex) => (
                        <li key={lineIndex}>{line}</li>
                      ))}
                    </ul>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
