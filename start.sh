#!/bin/bash

echo "Build e avvio container..."

docker compose up --build -d

# Mostra i container in esecuzione
docker ps
