# Data ingestor module

## Description

This project hosts the code for the data ingestor module of real data management workflow in Synthema.
Data ingestor component is responsible for:

* Ingesting a new dataset to the local filesystem
* Deleting an existing dataset from the local filesystem

### Structure

The data-ingestor module is structured in the following folders:

* The folder *src* provides utilities, datasets, models, fastapi, requirements and Dockerfile
* The folder *k8s* includes kubernetes manifests
* The folder *jenkins* contains the Jenkinsfile to run unit and functional tests. 

## Data-ingestor deployment
