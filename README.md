# Autonomous Procurement Negotiation System

An enterprise-grade agentic workflow designed to automate vendor contract analysis and negotiation strategy. This project demonstrates a secure, human-in-the-loop architecture for deploying Generative AI in regulated procurement environments.

## System Architecture & Capabilities

* **Multi-Agent Orchestration:** Utilises CrewAI to coordinate three specialised agents (Researcher, Risk Analyst, Lead Negotiator) performing parallel processing of unstructured data.
* **Real-Time Market Intelligence:** Integrates Perplexity API to cross-reference contractual terms with live financial indicators (e.g. stock performance, bankruptcy filings), providing data-backed leverage for negotiations.
* **Governance Framework:** Implements a mandatory 'Human-on-the-Loop' workflow. The system proposes strategic options, requiring executive review and amendment before finalising communication.
* **Security & Compliance:** Built with strict environment variable management (.env) and ephemeral file handling to ensure no persistence of sensitive contract data.

## Technical Stack

* **Orchestration Framework:** CrewAI (Python)
* **Model Layer:** Hybrid architecture using GPT-4o for orchestration and Perplexity/Claude 3.5 Sonnet for deep research and analysis.
* **Frontend:** Streamlit.
* **Tools:** SerperDev, Custom File Readers, ScrapeWebsiteTool.

## Local Deployment

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR-USERNAME/autonomous-procurement-negotiator.git](https://github.com/YOUR-USERNAME/autonomous-procurement-negotiator.git)
    cd autonomous-procurement-negotiator
    ```

2.  **Environment Setup:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Configuration:**
    Create a `.env` file in the root directory to manage credentials securely:
    ```ini
    OPENAI_API_KEY=sk-...
    SERPER_API_KEY=...
    PERPLEXITY_API_KEY=pplx-...
    ```

4.  **Execution:**
    ```bash
    streamlit run app.py
    ```

---