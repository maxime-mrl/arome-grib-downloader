FROM python
WORKDIR /app

# Get dependencies needed
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
