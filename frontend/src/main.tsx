import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import i18n from "./i18n";

// i18n is initialized as a side effect

createRoot(document.getElementById("root")!).render(<App />);
