# InfraPilot

InfraPilot is an **Agentic AI Infrastructure Provisioning Platform** that converts natural language into infrastructure, validates it, allows human review and iterative refinement, and finally provisions it.

The current MVP targets **Docker Compose**, while the architecture is designed to support **Terraform** and other IaC backends in the future.

## Features

- Natural language -> Infrastructure
- Intermediate `ProvisioningSpec` representation
- Intelligent Docker image discovery via Docker Hub
- LLM-assisted image and tag selection
- Docker Compose generation
- Docker Compose validation
- Human-in-the-loop approval
- Iterative modification loop
- Local Docker provisioning
- LangGraph workflow orchestration

## Requirements
- Python 3.11+
- Docker
- Docker Compose
- Openrouter/Gemini API key *(model should support tooling, and response_format)*

## Environment Variables

The following variables need to be configured in the environment:

| Variable             | Required            | Description                                                                |
| -------------------- | ------------------- | -------------------------------------------------------------------------- |
| `LLM_PROVIDER`       | No                  | LLM provider to use. Supported values: `openrouter` (default) or `gemini`. |
| `OPENROUTER_API_KEY` | If using OpenRouter | Your OpenRouter API key.                                                   |
| `OPENROUTER_MODEL`   | If using OpenRouter | Model to use (e.g. `openai/gpt-5`, default is `nvidia/nemotron-3-super-120b-a12b:free`, its free and supports tooling and structured output).           |
| `GEMINI_API_KEY`     | If using Gemini     | Your Google Gemini API key.                                                |
| `GEMINI_MODEL`       | If using Gemini     | Gemini model name (default `gemini-3.6-flash`).                                 |

Example:

```env
# Choose the LLM provider (defaults to "openrouter" if omitted)
LLM_PROVIDER=openrouter

# OpenRouter configuration
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openai/gpt-5

# Gemini configuration (only required when LLM_PROVIDER=gemini)
GEMINI_API_KEY=
GEMINI_MODEL=
```


## Usage
Make sure the required packages are installed
```bash
pip install -r requirements.txt
```
To run the CLI
```bash
python -m engine.main
```

https://github.com/user-attachments/assets/2c02325d-809e-4864-bca8-aad0222082bf

## Pipeline

1. **Requirement Agent**: 
    * Converts natural language query into a structured `ProvisioningSpec`.

2. **Image Fetcher Agent**

   * Queries Docker Hub to discover relevant images for each service.
   * Uses an LLM to evaluate search results and choose the most appropriate image and tag based on the original requirements.
   * Enriches the `ProvisioningSpec` with verified Docker images, avoiding outdated or hallucinated image names and versions.

3. **Docker Generator Agent**: 
    * Generates a Docker Compose configuration from the provisioning specification.

4. **Validation Agent**: 
    * Validates the generated Compose file using `docker compose config`.

5. **Human Approval**:
    * Review the generated infrastructure.
    * Approve deployment.
    * Modify the request and regenerate.
    * Cancel the workflow.

6. **Execution Agent**: 
    * Deploys the infrastructure using Docker Compose.

LangGraph is used for orchestrating the provisioning workflow by connecting the Requirement Agent, Image Fetcher Agent, Generator, Validator, Human Review, and Executor into a stateful graph. 

This separation of responsibilities allows each agent to focus on a single task while enabling iterative refinement and human-in-the-loop provisioning. 

![Architecture Diagram](./docs/diagrams/architechture.svg)

## Example

```
Describe your infrastructure:

> Deploy an nginx server with Redis

✓ Requirement extracted
✓ Compose generated
✓ Validation passed

Review:

Services
- nginx
- redis

1. Approve
2. Modify
3. Cancel

> 2

What would you like to change?

> Expose nginx on port 8080

...

✓ Deployment successful
```


### Future Plans:
- Better error handling
- Frontend dashboard for demonstration
- Instead of running docker services locally, run the commands remotely (maybe have an option to define the endpoints for Docker Engine API?)
- Change the scope from Docker to a IaC like Terraform

