FastAPI workflow for data-ingestor dockerized.
It must be run together with data-annotation and data-catalogue modules.

To run the data-ingestor workflow, make the following steps:

0. Create the network
   > docker network create _mynetwork_
2. Build the Dockerfile in src/Dockerfile:
   > docker build -t _data-ingestor-image_
3. Run the image:
   > docker run --network _mynetowrk_ --name _data-ingestor-container-name_ -p 8002:8002 _data-ingestor-image_
4. Go to http://localhost:8002/docs in your browser and upload the AML_DATA_ES.csv in Example_data (after uploading a valid schema).

N.B. Remember to put _data-annotation-container-name_ and _data-catalogue-container-name_ in ANNOTATION_ENDPOINT and CATALOGUE_ENDPOINT respectively in main.py
