/* 
  File: ragApi.ts
  Purpose: Handle API requests for the RAG Policy Assistant frontend.
*/

export type Citation = {
  doc_name: string;
  page_number: number;
};

export type AskResponse = {
  verdict: "FOUND" | "NOT_FOUND";
  answer: string;
  citations: Citation[];
};

export type AskRequest = {
  question: string;
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/*
  Function: askPolicyQuestion
  Purpose: Send the user's question to the backend and return the RAG response.
*/
export async function askPolicyQuestion(
  payload: AskRequest
): Promise<AskResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Failed to fetch answer from the server.");
  }

  const data: AskResponse = await response.json();
  return data;
}