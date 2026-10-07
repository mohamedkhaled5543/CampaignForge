FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH PYTHONUNBUFFERED=1
USER user
WORKDIR /home/user/app
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt
COPY --chown=user . .
# Build the FAISS index now so the first visit is fast (skipped if the PDF is missing)
RUN python -m app.rag.build_index || echo "No PDF at build time: index will be built on first request"
EXPOSE 7860
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
