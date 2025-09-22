#!/bin/bash
echo "Build e avvio container..."
docker compose up --build -d
docker ps
