const EXAMPLE_PROMPTS = [
  {
    id: "flask",
    title: "Flask + PostgreSQL + Redis",
    prompt:
      "Deploy a Flask web application with PostgreSQL database and Redis for caching. The Flask app should run on port 5000, PostgreSQL on 5432, and Redis on 6379.",
    icon: "🐍",
    color: "blue",
  },
  {
    id: "django",
    title: "Django + Celery",
    prompt:
      "Deploy a Django application with Celery worker and Redis as the message broker. Django on port 8000, Celery worker for background tasks.",
    icon: "🐍",
    color: "purple",
  },
  {
    id: "fastapi",
    title: "FastAPI + MongoDB",
    prompt:
      "Deploy a FastAPI application with MongoDB database. FastAPI on port 8000, MongoDB on 27017.",
    icon: "⚡",
    color: "cyan",
  },
  {
    id: "nodejs",
    title: "Node.js + MySQL",
    prompt:
      "Deploy a Node.js application with MySQL database. Node.js on port 3000, MySQL on 3306.",
    icon: "🟢",
    color: "emerald",
  },
  {
    id: "wordpress",
    title: "WordPress Stack",
    prompt:
      "Deploy WordPress with MySQL database and phpMyAdmin. WordPress on port 8080, MySQL on 3306, phpMyAdmin on 8081.",
    icon: "📝",
    color: "orange",
  },
  {
    id: "elk",
    title: "ELK Stack",
    prompt:
      "Deploy Elasticsearch, Logstash, and Kibana. Elasticsearch on port 9200, Kibana on 5601.",
    icon: "📊",
    color: "amber",
  },
  {
    id: "redis",
    title: "Redis Cache",
    prompt: "Deploy a single Redis instance on port 6379.",
    icon: "🟥",
    color: "red",
  },
  {
    id: "nginx",
    title: "Nginx Web Server",
    prompt: "Deploy an Nginx web server on port 80.",
    icon: "🟩",
    color: "teal",
  },
];

const ROTATING_PROMPTS = [
  "Describe your infrastructure in natural language...",
  "e.g. Deploy a Flask app with PostgreSQL and Redis...",
  "e.g. WordPress + MySQL + phpMyAdmin stack...",
  "e.g. FastAPI with MongoDB and Celery worker...",
  "e.g. Nginx reverse proxy for multiple services...",
];
