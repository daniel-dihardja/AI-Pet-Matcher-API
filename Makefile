# Load environment variables from .env file
include .env
export $(shell sed 's/=.*//' .env)

.PHONY: all build test docker-build docker-tag docker-push ecr-login

all: build test docker-build docker-tag docker-push

# Install dependencies
build:
	@pip install -r requirements.txt

# Run tests
test:
	@pytest tests/

# Build Docker image
docker-build:
	@docker build -t $(IMAGE_NAME) .

# Tag Docker image
docker-tag: docker-build
	@docker tag $(IMAGE_NAME):latest $(REPO_URI)

# Login to ECR
ecr-login:
	@aws ecr get-login-password --region $(REGION) | docker login --username AWS --password-stdin $(REPO_URI)

# Push Docker image to ECR
docker-push: ecr-login docker-tag
	@docker push $(REPO_URI)
