# RecoverAI Live Demo Guide
**Razorpay AI Buildathon — 5-Minute Pitch Walkthrough**

RecoverAI runs 100% locally in demo mode without any external API keys required.

---

## 1. Quick Start

### Terminal 1: Backend
```powershell
cd backend
.venv\Scripts\activate
python seed.py
python run.py
```

### Terminal 2: Frontend
```powershell
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

*(Alternatively, run `.\start-demo.ps1` from the project root).*

---

## 2. 5-Minute Pitch Demo Script

### Minute 0:00 – 1:00: The Problem & The Hero Metric
- Open **Dashboard**.
- Point to the **Primary Recovery Metric** hero card:
  - **₹54,089** recovered revenue.
  - Highlight the **+972.5% vs. Naive Retry** lift badge.
  - Explain: *"Standard retry systems blindly resubmit cards and fail on 100% of expired cards, abandonments, and insufficient funds. RecoverAI orchestrates the Next Best Action."*

### Minute 1:00 – 2:15: Live Pipeline Demonstration (⚡ Live Failure)
- In the **Live Pipeline Demonstration** bar on the Dashboard, click:
  - **"⚡ Insufficient Funds (₹24,999)"**
- Watch the live 5-stage pipeline modal process in real time:
  1. **Event Ingestion**: Captures the failed transaction.
  2. **Context & Memory**: Evaluates customer LTV and past recovery memory.
  3. **AI Recommendation**: Next-best action is synthesized (`SEND_PAYMENT_LINK`).
  4. **Policy Guardrail**: PolicyEngine verifies the action complies with merchant rules.
  5. **Action Execution**: Payment link is generated and outcome recorded.
- Click **"Inspect Full Case Details"** to view the contextual explanation and audit trail.

### Minute 2:15 – 3:15: Baseline vs. RecoverAI ROI
- Scroll to the **Baseline Retry vs. RecoverAI** evaluation card.
- Show the simulation-based benchmark comparison:
  - **Naive Retry**: ₹20,554 (11.9% recovery rate).
  - **RecoverAI**: ₹2,20,442 (58.5% recovery rate).
  - **Net Merchant Advantage**: **+₹1,99,888 Incremental Recovery**.
- Open the **Analytics** tab to show the bar chart comparing recovery by failure type.

### Minute 3:15 – 4:15: Merchant Policy & What-If Simulator
- Open **Recovery Policy** tab:
  - Show how merchants configure guardrails (Max Retries, High-Value Threshold, Escalation Threshold).
- Open **Simulator** tab:
  - Click the **"Strict Guardrails"** preset vs. **"Maximize Recovery"** preset.
  - Click **Run Simulation**: show how the before-and-after comparison recomputes expected recovery against live synthetic data.

### Minute 4:15 – 5:00: Auditability & Security Summary
- Open **Audit Trail** tab.
- Demonstrate that every single AI recommendation, policy verdict, and execution outcome is immutably logged with timestamps.
- Highlight: The LLM is strictly advisory; deterministic software executes only approved actions.

---

## 3. Real AI Mode (Optional)

To enable live Google Gemini 1.5 Flash reasoning:
1. Add `GEMINI_API_KEY=your-key` in `.env`.
2. Restart the backend.
3. The header badge switches from `AI: demo-rule-agent` to `AI: gemini-active`.
4. If the key is invalid or network drops, it **automatically falls back to DemoAIProvider** with zero downtime.
