/*
  File: CitationList.tsx
  Purpose: Display citation metadata returned by the backend.
*/

import type { Citation } from "../api/ragApi";

type CitationListProps = {
  citations: Citation[];
};

/*
  Function: CitationList
  Purpose: Render the list of citations for the generated answer.
*/
function CitationList({ citations }: CitationListProps) {
  if (!citations || citations.length === 0) {
    return <p className="muted-text">No citations available.</p>;
  }

  return (
    <div className="citations-section">
      <h3>Sources</h3>

      <div className="citation-chip-list">
        {citations.map((citation, index) => (
          <div
            className="citation-chip"
            key={`${citation.doc_name}-${citation.page_number}-${index}`}
          >
            Source: {citation.doc_name}, page {citation.page_number}
          </div>
        ))}
      </div>
    </div>
  );
}

export default CitationList;