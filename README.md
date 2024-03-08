# Infradmin

This project aims to develop a Python application for managing your entire Docker infrastructure. 
The application provides a user-friendly interface for deploying and managing Docker containers, as well as performing common operations such as creating, deleting, and monitoring containers. 
Its purpose is to manage the entire backup system and eventually handle web deployment (OVH API, Traefik, etc.)

## Features

- Docker Container Deployment: The application allows for easy deployment of Docker containers by specifying images, ports, volumes, etc.
- Container Management: You can create, delete, and monitor running containers.
- Python Development: The application is developed using the Python programming language, enabling easy customization and extension.

## Prerequisites

Before getting started, make sure you have the following installed:

- Python (version 3.11)
- Docker (version 24.0)

A volume for the docker-compose is required and can be found in the image at this location:
/usr/src/app/infradmin/conf/docker/docker-compose.yml

A volume to the docker socket is also required:
/var/run/docker.sock

## Installation

//TO DO
