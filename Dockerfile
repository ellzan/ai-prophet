FROM python:3.11-slim

# Prophet (lewat cmdstanpy) butuh compiler C++ untuk build cmdstan.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bangun cmdstan sekali saat image dibuat, supaya request pertama ke API
# tidak lambat gara-gara compile cmdstan saat runtime.
RUN python -c "import cmdstanpy; cmdstanpy.install_cmdstan()"

COPY . .

# Latih model saat build image, supaya artifacts/ selalu ikut ter-deploy.
RUN python scripts/train.py

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
