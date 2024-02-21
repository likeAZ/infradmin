# Infradmin

Ce projet vise à développer une application en Python qui permet de gérer toute votre infrastructure Docker. L'application fournit une interface conviviale pour déployer et gérer des conteneurs Docker, ainsi que pour effectuer des opérations courantes telles que la création, la suppression et la surveillance des conteneurs.
Il a pour but de gérer tout le systeme de backup. Et a terme de gérer un déploiement web (api ovh, traeffik, ect...)

## Fonctionnalités

- Déploiement de conteneurs Docker : L'application permet de déployer facilement des conteneurs Docker en spécifiant les images, les ports, les volumes, etc.
- Gestion des conteneurs : Vous pouvez créer, supprimer et surveiller les conteneurs en cours d'exécution.
- Développement en Python : L'application est développée en utilisant le langage de programmation Python, ce qui permet une personnalisation et une extension faciles.

## Prérequis

Avant de commencer, assurez-vous d'avoir les éléments suivants installés :

- Python (version 3.11)
- Docker (version 24.0)

Un volume pour le docker-compose est necessaire il se trouve dans l'image a cet endroit :
/usr/src/app/infradmin/conf/docker/docker-compose.yml

un volume vers le socket docker est aussi necessaire:
/var/run/docker.sock

## Installation

//TO DO
