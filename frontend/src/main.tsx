/*
  File: main.tsx
  Purpose: Frontend application entry point.
*/

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

/*
  Function: renderApp
  Purpose: Mount the React application to the root DOM element.
*/
function renderApp() {
  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}

renderApp();