import React, { useState } from "react";
import ReactDOM from "react-dom/client";
import axios from "axios";

function App() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await axios.post("http://localhost:8000/predict", { text });
      const payload = response.data?.data ?? null;

      if (payload?.aspects) {
        console.log("ABSA aspects", payload.aspects);
      }

      setResult(payload);
    } catch (requestError) {
      setError("Khong the gui yeu cau den backend.");
      console.error(requestError);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ fontFamily: "sans-serif", padding: "2rem", maxWidth: "720px", margin: "0 auto" }}>
      <h1>Sentiment Analysis</h1>
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: "1rem" }}>
        <textarea
          rows="6"
          placeholder="Nhap phan hoi khach hang"
          value={text}
          onChange={(event) => setText(event.target.value)}
          style={{ padding: "0.75rem", fontSize: "1rem" }}
        />
        <button type="submit" disabled={loading || !text.trim()} style={{ padding: "0.75rem 1rem" }}>
          {loading ? "Dang gui..." : "Phan tich"}
        </button>
      </form>
      {error ? <p style={{ color: "crimson" }}>{error}</p> : null}
      {result ? (
        <section style={{ marginTop: "2rem" }}>
          <h2>Ket qua</h2>
          <p><strong>Noi dung:</strong> {result.text}</p>
          <p><strong>Cam xuc tong the:</strong> {result.overall_sentiment}</p>
        </section>
      ) : null}
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
