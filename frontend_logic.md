# FRONTEND REQUIREMENTS: TWO-SIDED PORTAL (CUSTOMER vs INTERNAL USER)

I need to build a Next.js frontend with two distinct views based on the user's role.

## 1. CUSTOMER PORTAL (The "Shopee-style" Feedback Page)
**Goal:** A clean, friendly interface for customers to read and leave reviews.
- **Action:** - A simple text area for customers to type their feedback.
    - A "Submit" button.
- **Display:**
    - A list of reviews from other customers.
    - **Crucial Constraint:** The analysis from AI must be shown as "Labels" or "Tags" (e.g., "Giao hàng", "Chất lượng"). 
    - **NO** technical jargon (No RawID, No Confidence Score, No Global Sentiment status). It should look like a standard e-commerce review section.

## 2. INTERNAL USER DASHBOARD (The "MLOps Metrics" Page)
**Goal:** For staff or developers to monitor system health and data quality.
This page must show 3 main sections:

### A. Pre-train Data Metrics (Before Training)
- Display charts (using Recharts) showing:
    - **Class Distribution:** How many samples for each Aspect (Fashion, Ship, Price...).
    - **Sentiment Balance:** Ratio of Positive/Negative/Neutral in the training set.
    - **Text Length Distribution:** Word count frequency in training data.

### B. Model Valuation (Performance Results)
- Show the **Confusion Matrix** for Sentiment (Positive, Negative, Neutral).
- A table/chart showing **F1-Score, Precision, Recall** for each Aspect.
- Highlighting the "Shortcut Learning" issue (e.g., specific alerts for the 'Ship' aspect).

### C. Live Output Analysis (System Log)
- A "Live Log" table showing what the AI is currently predicting:
    - Raw Text Input.
    - Full JSON Output from the SageMaker Endpoint.
    - Comparison between "Customer View" (clean) and "Admin View" (detailed).

## 3. TECHNICAL NOTES FOR CLAUDE
- **Next.js:** Use App Router.
- **Styling:** Tailwind CSS (Dark/Light mode support).
- **Charts:** Use `recharts` library for all data visualizations.
- **State Management:** Use React `useState` for handling the feedback submission and fetching metrics.