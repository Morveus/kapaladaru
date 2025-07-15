# Kapaladaru

A Python-based tool that monitors a movie directory and identifies Bollywood, Indian, and Telugu films using AI.

## Overview

Kapaladaru periodically scans a specified movie directory, checks each movie folder against an AI model (Ollama) to determine if it's an Indian cinema production, and sends notifications for matches via NTFY. The tool maintains a record of already-checked movies to avoid duplicate processing.

## Features

- Automated movie directory scanning
- AI-powered identification of Indian cinema (Bollywood, Indian, Telugu films)
- Persistent tracking of processed movies
- NTFY notification integration
- Docker containerization for easy deployment
- Configurable check intervals

## How It Works

1. Scans the configured movies directory for subdirectories (each representing a movie)
2. Checks if each movie has been previously processed
3. Queries Ollama AI to identify Indian cinema
4. Sends notifications for identified movies via NTFY
5. Records processed movies to avoid re-checking

## Installation

```bash
# Clone the repository
git clone https://github.com/Morveus/kapaladaru.git
cd kapaladaru

# Build the Docker image
docker build -t morveus/kapaladaru .

# Run with docker-compose
docker-compose up -d
```

## Configuration

Update the `docker-compose.yml` file with your settings:

```yaml
environment:
  - MOVIES_DIR=/movies                    # Movie directory path
  - OLLAMA_ENDPOINT=http://ollama:11434   # Ollama API endpoint
  - OLLAMA_MODEL=llama3.2                 # Ollama model name
  - NTFY_URL=https://ntfy.sh/your-topic   # NTFY notification URL
  - CHECK_INTERVAL=3600                   # Check interval in seconds
```

## Environment Variables

- `MOVIES_DIR`: Path to the movie directory (default: `/movies`)
- `CHECKED_DIR`: Directory for storing checked movie records (default: `/checked`)
- `OLLAMA_ENDPOINT`: Ollama API endpoint URL (default: `http://localhost:11434`)
- `OLLAMA_MODEL`: Ollama model to use for identification (default: `llama3.2`)
- `NTFY_URL`: NTFY service URL for notifications (default: `https://ntfy.sh/mytopic`)
- `CHECK_INTERVAL`: Interval between checks in seconds (default: `3600`)
- `RUN_ONCE`: Run once and exit if set to 'true' (default: `false`)

## Requirements

- Docker
- Running Ollama instance
- NTFY topic (or compatible notification service)
- Movie collection organized in directories

## Usage

### With Docker Compose

```bash
docker-compose up -d
```

### With Docker Run

```bash
docker run -d \
  --name kapaladaru \
  -v /path/to/movies:/movies:ro \
  -v kapaladaru-checked:/checked \
  -e OLLAMA_ENDPOINT=http://host.docker.internal:11434 \
  -e NTFY_URL=https://ntfy.sh/your-topic \
  morveus/kapaladaru
```

## Troubleshooting

**Movies not being detected:**
- Verify Ollama is running and accessible at the configured endpoint
- Ensure movie folders are readable and properly named
- Check Docker logs: `docker logs kapaladaru`

**False positives/negatives:**
- Consider using a different Ollama model
- Ensure movie folder names include the full movie title

## Contributing

Contributions are welcome. Please submit pull requests or open issues for bug reports and feature requests.

## License

MIT License
