/*
  File: AnswerCard.tsx
  Purpose: Show the backend response including verdict, answer, and citations.
*/

import type { AskResponse } from "../api/ragApi";
import CitationList from "./CitationList";
import StatusBadge from "./StatusBadge";

type AnswerCardProps = {
  result: AskResponse | null;
  isLoading: boolean;
};

/*
  Function: AnswerCard
  Purpose: Render the answer card, loading state, or empty state.
*/
function AnswerCard({ result, isLoading }: AnswerCardProps) {
  if (isLoading) {
    return (
      <section className="answer-card centered-state">
        <p className="loading-text">
          Searching the handbook and generating an answer...
        </p>
      </section>
    );
  }

  if (!result) {
    return (
      <section className="answer-card centered-state">
        <p className="muted-text">
          Ask a question above to see the answer and source here.
        </p>
      </section>
    );
  }

  return (
    <section className="answer-card">
      <div className="answer-header">
        <h2>Result</h2>
        <StatusBadge verdict={result.verdict} />
      </div>

      <div className="answer-body">
        <h3>Answer</h3>
        <p>{result.answer}</p>
      </div>

      <CitationList citations={result.citations} />
    </section>
  );
}

export default AnswerCard;