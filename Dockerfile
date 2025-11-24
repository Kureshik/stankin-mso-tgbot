FROM python:3.11-slim

# set a non-root user
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --shell /bin/bash mso_tgbot_user

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ensure files accessible by non-root
RUN chown -R mso_tgbot_user:mso_tgbot_user /app
USER mso_tgbot_user

CMD ["python", "bot.py"]
