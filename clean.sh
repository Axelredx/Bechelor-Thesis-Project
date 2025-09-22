#!/bin/bash
# clean.sh - Ripulisce Docker per il progetto

echo "Attenzione: verranno rimossi container e immagini del progetto"

# Ferma i container del progetto
docker compose down

# Rimuove immagini del progetto
docker rmi -f bechelor-thesis-project-backend bechelor-thesis-project-frontend mongo:6.0 2>/dev/null

# Rimuove container residui che potrebbero creare conflitti
docker rm -f backend frontend my_mongodb 2>/dev/null

# Pulisce volumi legati al progetto
docker volume rm bechelor-thesis-project_mongo_data 2>/dev/null

# Pulisce cache build Docker
docker builder prune -af

# Pulisce risorse Docker inutilizzate
docker system prune -af
docker volume prune -f

# Rimuove eventuali container rimasti (se esistono)
docker rm -f my_mongodb backend frontend


echo "Pulizia completata."
