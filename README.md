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

0. Create the network
   > docker network create _mynetwork_
2. Build the Dockerfile in src/Dockerfile:
   > docker build -t _data-ingestor-image_
3. Run the image:
   > docker run --network _mynetowrk_ --name _data-ingestor-container-name_ -p 8002:8002 _data-ingestor-image_
4. Go to http://localhost:8002/docs in your browser and upload the AML_DATA_ES.csv in Example_data (after uploading a valid schema).

N.B. Remember to put _data-annotation-container-name_ and _data-catalogue-container-name_ in ANNOTATION_ENDPOINT and CATALOGUE_ENDPOINT respectively in main.py

## License

This project is licensed under the [MIT License](LICENSE).

This project extends and uses the following Open Softwares, which are compliant with MIT License:

* FastAPI: MIT License
* Pandas: BSD License
* psycopg2-binary: PostgreSQL License
* Uvicorn: BSD License
* python-multipart: MIT License
* python-jose: MIT License
* passlib: BSD License
* pytest: MIT License
* jsonschema: MIT License
* sqlalchemy: MIT License
* sqlmodel: MIT License
* requests: Apache 2.0 License
