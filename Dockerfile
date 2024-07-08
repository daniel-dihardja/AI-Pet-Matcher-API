# Use an official Python runtime as a parent image
FROM public.ecr.aws/lambda/python:3.11

# Copy the requirements file into the container
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code and templates into the container
COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY prompt_templates/ ${LAMBDA_TASK_ROOT}/prompt_templates/

# Set the CMD to your handler
CMD [ "src.lambda_function.lambda_handler" ]
