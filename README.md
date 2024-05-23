FastAPI workflow for data-ingestor dockerized.
It must be run together with data-annotation and data-catalogue modules.

To run the data-ingestor workflow, make the following steps:

0. Create the network
   > docker network create mynetwork
2. Build the Dockerfile in src/Dockerfile:
   > docker build -t data-ingestor-image
3. Run the image:
   > docker run --network mynetowrk --name data-ingestor-container-name -p 8002:8002 data-ingestor-image
4. Go to http://localhost:8002/docs in your browser and upload the AML_DATA_ES.csv in Example_data (after uploading a valid schema).
