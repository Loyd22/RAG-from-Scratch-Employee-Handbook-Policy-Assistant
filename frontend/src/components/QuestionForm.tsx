/*
  File: QuestionForm.tsx
  Purpose: Collect a policy question from the user and submit it to the backend.
*/

import { useState } from "react";

type QuestionFormProps = {
  onSubmitQuestion: (question: string) => Promise<void>;
  isLoading: boolean;
};

/*
  Function: QuestionForm
  Purpose: Render the question input form and handle local form submission.
*/
function QuestionForm({ onSubmitQuestion, isLoading }: QuestionFormProps) {
  const [question, setQuestion] = useState("");

  /*
    Function: submitQuestion
    Purpose: Validate and send the trimmed question to the parent component.
  */
  async function submitQuestion(): Promise<void> {
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || isLoading) return;

    await onSubmitQuestion(trimmedQuestion);
  }

  /*
    Function: handleSubmit
    Purpose: Prevent default form behavior and submit the question.
  */
  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await submitQuestion();
  }

  /*
    Function: handleKeyDown
    Purpose: Submit on Enter and allow Shift+Enter for new lines.
  */
  async function handleKeyDown(
    event: React.KeyboardEvent<HTMLTextAreaElement>
  ) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      await submitQuestion();
    }
  }

  return (
    <form className="question-form" onSubmit={handleSubmit}>
      <label htmlFor="question" className="form-label">
        Ask a policy question
      </label>

      <textarea
        id="question"
        className="question-input"
        placeholder="Example: What is the sick leave policy?"
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        onKeyDown={handleKeyDown}
        rows={4}
      />

      <div className="form-actions">
        <button type="submit" className="submit-button" disabled={isLoading}>
          {isLoading ? "Getting answer..." : "Ask"}
        </button>

        <span className="helper-text">
          Press Enter to submit, Shift+Enter for new line
        </span>
      </div>
    </form>
  );
}

export default QuestionForm;