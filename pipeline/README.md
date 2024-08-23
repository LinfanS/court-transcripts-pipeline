# Pipeline Documentation

This folder contains the scripts and resources for the court transcript data pipelines. The pipeline is responsible for extracting, transforming, and loading court case data into the database. 

The overall pipeline, is divided into two constituent parts, a live pipeline intended to be deployed on the cloud using an AWS Lambda function to listen for and add new court cases and a batch pipeline intended to add past court cases which is run once locally.

## 📚 Folder Contents

- `batch_pipeline.log`: Log file from running the batch pipeline.

- `batch_pipeline.py`: Python script to run the batch pipeline locally to insert past court cases to the database and cache GPT data in Redis.

- `calculate_gpt_cost.py`: Script to calculate the cost of using GPT for data processing from batch pipeline log.

- `court_transcript_batch_backup.sql`: SQL backup of court transcripts processed in batch pipeline.

- `Dockerfile`: Dockerfile to create a Docker image for the live pipeline.

- `extract.py`: Contains functions to extract data from the National Archives website from html tags.

- `initialise_json.py`: Script to initialise a JSON file and send it to an S3 bucket.

- `invalid_gpt_responses.txt`: Log of invalid GPT responses generated from batch pipeline.

- `judge_matching.py`: Script for matching judges names to similar names e.g. with and without titles.

- `live_pipeline.py`: Python script to run the live pipeline on AWS Lambda to add new court cases to the database.

- `load.py`: Contains functions to load data into the database.

- `nltk_setup.py`: Script to set up NLTK resources for a Docker image.

- `prompts.py`: Contains system and user prompts used for GPT data processing.

- `README.md`: This file, documentation for the pipeline folder.

- `requirements.txt`: List of dependencies required for the pipeline.

- `reset.sh`: Shell script to reset the database and rerun the schema.

- `transform.py`: Script to transform the data extracted from the National Archives website through ChatGPT into a format that can be loaded into a database.




## 🛠️ Batch Pipeline Setup Instructions

0. **Prerequisite**: You must have a database setup first, see database folder for setup instructions.
1. **Setup local Redis cache**: 
    In order to run the batch pipeline , you need to have Redis installed on your local machine. You can do this with the following command using Homebrew.

    ```sh
    brew install redis

    #Enabling persistence through generating an appendonly file
    redis-cli CONFIG SET appendonly yes

    #To run the redis server as a background task
    nohup redis-server &
    ```

    The following utility commands may also be helpful:

    ```sh
    ps aux | grep redis-server #check that the redis-server is running in the background
    redis-cli flushalll #empty the redis cache of existing keys and values
    ```


2. **Install Dependencies**: 
   
   Make sure you have Python and pip installed and the repository cloned. Run the following command to install the required dependencies:
    ```sh
    cd ~
    cd court-transcripts-pipeline/pipeline
    pip3 install -r requirements.txt
    ```


3. **Environment Variables**: 
   
   Create a `.env` file in the root of the `pipeline` folder and add the necessary environment variables for the batch pipeline to contact the database and the ChatGPT API.
   
    - `DB_HOST`: The hostname or IP address of the database server.
    - `DB_PORT`: The port number on which the database server is listening; typically 5432 for PostgreSQL
    - `DB_NAME`: The name of the database to connect to.
    - `DB_USER`: The username to use for authenticating with the database.
    - `DB_PASSWORD`: The password to use for authenticating with the database.
    - `OPENAI_API_KEY`: API key for ChatGPT API.

4. **Run Batch Pipeline**: 
   
   Once the setup steps are complete, the batch pipeline can now be run using the following command.
   ```sh
    python3 batch_pipeline.py
    ```


## 🛠️ Live Pipeline Setup Instructions
0. **Install Dependencies**: 
   Make sure you have Python and pip installed and the repository cloned. Run the following command to install the required dependencies:
    ```sh
    cd ~
    cd court-transcripts-pipeline/pipeline
    pip3 install -r requirements.txt
    ```

1. **Environment Variables**:
    Add the following AWS credentials to your `.env` file created above:
   
    - `ACCESS_KEY_ID`
    - `SECRET_ACCESS_KEY`

2. **Run the terraform files to create all the resources needed.**
    This can be done by navigating to the terraform directory with the following commands:
    ```sh
    cd ..
    cd terraform/live_pipeline_tf
    ```
    Then individually run the following commands
    
    NOTE - these will require environment variables - see the README.md in the `/terraform` for more details:
    ```sh
    terraform init
    terraform plan #if you want to double-check what resources are being created
    terraform apply #then 'yes' when prompted
    ```
    This will set up the required resources, including: s3 bucket, lambda (see the README.md in the `/terraform` for more details)

3. **Create log file**
    Once the resources are ready, you should initialise the file that will work like a cache by saving a list of all the citation ids of the files that have already been uploaded to the dashboard.
    ```sh
    cd ..
    python3 initialise_json.py
    ```

4. **Run Batch Pipeline**: 
   Once the setup steps are complete, the batch pipeline can now be run using the following command.
   ```sh
    python3 live_pipeline.py
    ```

## Running Tests

To run the unit tests for the pipeline, use the following command:
```sh
pytest
```
Or to run individual ones, 
```sh
pytest <test_filename>
```

