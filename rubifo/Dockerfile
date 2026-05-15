FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ src/
COPY migrations/ migrations/
COPY .env .env.example ./

# Create log directory
RUN mkdir -p /var/log/rubifo

# Run bot
CMD ["python", "-m", "src.bot.main"]
