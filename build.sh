#!/bin/bash

source .env

docker compose -f docker-compose-mock.yml down
#docker compose -f docker-compose-mock.yml build --no-cache .
docker compose -f docker-compose-mock.yml up --build

