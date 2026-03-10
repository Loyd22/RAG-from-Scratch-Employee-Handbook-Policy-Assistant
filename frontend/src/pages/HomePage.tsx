/*
  File: HomePage.tsx
  Purpose: Main page for the RAG Policy Assistant frontend.
*/

import { useState } from "react";
import { askPolicyQuestion, type AskResponse } from "../api/ragApi";
import AnswerCard from "../components/AnswerCard";
import QuestionForm from "../components/QuestionForm";

/*
  Function: HomePage
  Purpose: Manage the page state and connect the form to the backend API.
*/
function HomePage() {
  const [result, setResult] = useState<AskResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  /*
    Function: handleSubmitQuestion
    Purpose: Send the user's question to the backend and store the response.
  */
  async function handleSubmitQuestion(question: string): Promise<void> {
    try {
      setIsLoading(true);
      setErrorMessage("");

      const response = await askPolicyQuestion({ question });
      setResult(response);
    } catch (error) {
      console.error("Error while asking policy question:", error);
      setErrorMessage("Could not get an answer from the server.");
      setResult(null);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="page-container">
      <section className="hero-section">
        <h1>RAG Policy Assistant</h1>
        <p className="hero-text">
          Ask questions about the employee handbook and get grounded answers
          with citations.
        </p>
      </section>

      <QuestionForm
        onSubmitQuestion={handleSubmitQuestion}
        isLoading={isLoading}
      />

      {errorMessage ? <p className="error-text">{errorMessage}</p> : null}

      <AnswerCard result={result} isLoading={isLoading} />
    </main>
  );
}

export default HomePage;