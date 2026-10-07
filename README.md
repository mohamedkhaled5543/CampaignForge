# CampaignForge AI

## Project

CampaignForge AI is an AI-powered marketing campaign generator.

It takes a product brief and turns it into a complete marketing campaign. The system first understands the product, then uses a marketing knowledge base to build a campaign strategy, generates multiple strategic directions, and finally creates platform-specific content for Instagram and TikTok.

### How it works

```text
Product Brief
     ↓
Product Understanding
     ↓
Marketing Strategy + RAG Knowledge Base
     ↓
3 Strategic Directions
     ↓
Selected Direction
     ↓
Instagram + TikTok Content
     ↓
AI-Generated Advertising Image
```

The system uses one campaign state throughout the process, so all generated content stays consistent with the original product and strategy.

---

## Tech Used

* **Python**
* **FastAPI** — backend API
* **LangChain** — LLM chains and structured outputs
* **Mistral-Nemo** — primary LLM through Kaggle/Colab
* **Google Gemini** — fallback LLM
* **RAG** — marketing knowledge retrieval
* **Hugging Face Embeddings (MiniLM)** — document embeddings
* **FAISS** — vector similarity search
* **Pydantic** — structured data validation
* **Sentence Transformers** — embeddings
* **PyPDF** — PDF processing
* **HTML / CSS / JavaScript** — frontend
* **Docker** — deployment

---

## How to Use

### 1. Clone the repository

```bash
git clone https://github.com/mohamedkhaled5543/CampaignForge.git
cd CampaignForge
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file:

```env
PROVIDER=auto
GOOGLE_API_KEY=your_google_api_key
COLAB_API_URL=your_kaggle_or_colab_ngrok_url
```

### 4. Add the marketing knowledge base

Place the marketing knowledge PDF inside:

```text
knowledge_base/
```

### 5. Run the application

```bash
uvicorn app.main:app --reload --port 8000
```

Then open:

```text
http://127.0.0.1:8000
```

### 6. Create a campaign

Enter:

* Product name
* Product description
* Target audience
* Campaign goal
* Brand tone
* Optional offer or price
* Optional key differentiator

CampaignForge will generate the product understanding, strategy, strategic directions, social media content, and advertising image.
