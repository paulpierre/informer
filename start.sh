#!/bin/bash

# Startup all the containers at once
docker-compose --env-file ./informer.env up --build
