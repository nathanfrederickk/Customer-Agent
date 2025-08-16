# Use AWS's Python base image with RIC pre-installed
FROM public.ecr.aws/lambda/python:3.12

WORKDIR ${LAMBDA_TASK_ROOT}

# Make all the downloaded files go to the tmp file (serverless)
ENV TRANSFORMERS_CACHE="/tmp/model_cache"
ENV HF_HOME="/tmp/model_cache"
ENV XDG_CACHE_HOME="/tmp/model_cache"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Default handler (overridden for ingestion function)
CMD ["lambda_handler.handler"]