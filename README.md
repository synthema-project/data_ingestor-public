FastAPI workflow for data ingestion

Example_data: here we can find an example of dataset to upload (.csv file) and an example of a schema for AML (.json)

fastapi: source code to run the FastAPI ingestion workflow
          - data_ingestion_utils.py: here the basic functions to connect fastapi and postgres database are defined
          - main.py: here the CRUD functions for both schemas and datasets are defined. 

To run the data ingestion workflow, make the following steps:
1) create the conda environment from the environment.yaml file and activate it
     > conda env create -f environment.yaml
     > conda activate fastapi
2) run the main.py function
     > python main.py
3) open your browser and go to "http://127.0.0.1:8001/docs" (or change 8001 to the port you indicate in the main.py)
