# InfraPilot

InfraPilot is an **Agentic AI Infrastructure Provisioning Platform** that converts natural language into infrastructure, validates it, allows human review and iterative refinement, and finally provisions it.

The current MVP targets **Docker Compose**, while the architecture is designed to support **Terraform** and other IaC backends in the future.

## Features

- Natural language -> Infrastructure
- Intermediate `ProvisioningSpec` representation
- Docker Compose generation
- Docker Compose validation
- Human-in-the-loop approval
- Iterative modification loop
- Local Docker provisioning
- LangGraph workflow orchestration

## Usage

```bash
python main.py "I need a FastAPI backend with PostgreSQL and Redis"
```

## Pipeline

1. **Requirement Agent**: Converts natural language query into a structured `ProvisioningSpec`.
2. **Docker Generator Agent**: Generates a Docker Compose configuration from the provisioning specification.
3. **Validation Agent**: Validates the generated Compose file using `docker compose config`.
4. **Human Approval**:
    - Review the generated infrastructure.
    - Approve deployment.
    - Modify the request and regenerate.
    - Cancel the workflow.
5. **Execution Agent**: Deploys the infrastructure using Docker Compose.

LangGraph is used for orchestrating the provisioning workflow by connecting the Requirement Agent, Generator, Validator, Human Review, and Executor into a stateful graph. This enables iterative refinement and human-in-the-loop provisioning while keeping each component independently testable.

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
- Frontend dashboard for demonstration
- Instead of running docker services locally, run the commands remotely (maybe have an option to define the endpoints for Docker Engine API?)
- Change the scope from Docker to a IaC like Terraform
- Add tooling to provide docker images to choose from
