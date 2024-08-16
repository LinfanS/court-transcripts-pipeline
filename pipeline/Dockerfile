FROM public.ecr.aws/lambda/python:latest

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY live_pipeline.py .
COPY extract.py .
COPY transform.py .
COPY load.py .
COPY prompts.py .
COPY judge_matching.py .
COPY judges_seed.py .

EXPOSE 5432


CMD ["live_pipeline.handler"]