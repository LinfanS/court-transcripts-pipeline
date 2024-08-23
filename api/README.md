# API Documentation

This folder contains the API implementation and related resources for the court transcript pipeline project.

The API is implemented using the FastAPI framework, using the ORM (object relational mapping) functionality from SQLAlchemy to relate to the data in the database. 

This API provides access to various court case data including courts, judges, lawyers, law firms, participants, tags, verdicts, and court cases (which amalgamates the previous fields together).


## 📚 Folder Contents

- `static/swagger-ui/`: Contains the Swagger UI (API root endpoint) files for API documentation.
  - `swagger-ui.css`: CSS styles for the Swagger UI.
  - `swagger-ui.js`: JavaScript for the Swagger UI.
  
- `api.py`: Implementation of the API using FastAPI framework.
  
- `test_api.py`: Contains the unit tests for the API.
  
- `Dockerfile`: Contains the instructions to build a Docker image for the API.


## API Endpoints

### Root Endpoint
- **Endpoint:** `/`
- **Description:** Root endpoint that redirects to /docs showing API documentation using SwaggerUI

### Courts
- **Endpoint:** `/courts/`
- **Description:** Get court types with optional search and limit parameters.
- **Query Parameters:**
  - `search` (Optional, `str`): Court name to filter by.
  - `limit` (Optional, `int`, default: 100): Limit the number of results, -1 for all results.

### Judges
- **Endpoint:** `/judges/`
- **Description:** Get judge names with optional search and limit parameters.
- **Query Parameters:**
  - `search` (Optional, `str`): Judge name to filter by.
  - `limit` (Optional, `int`, default: 100): Limit the number of results, -1 for all results.

### Lawyers
- **Endpoint:** `/lawyers/`
- **Description:** Get lawyer and law firm names with optional search and limit parameters.
- **Query Parameters:**
  - `lawyer` (Optional, `str`): Lawyer name to filter by.
  - `law_firm` (Optional, `str`): Law firm name to filter by.
  - `limit` (Optional, `int`, default: 100): Limit the number of results, -1 for all results.

### Law Firms
- **Endpoint:** `/law_firms/`
- **Description:** Get law firm names with optional search and limit parameters.
- **Query Parameters:**
  - `search` (Optional, `str`): Law firm name to filter by.
  - `limit` (Optional, `int`, default: 100): Limit the number of results, -1 for all results.

### Participants
- **Endpoint:** `/participants/`
- **Description:** Get participant names with optional search and limit parameters.
- **Query Parameters:**
  - `participant` (Optional, `str`): Participant name to filter by.
  - `lawyer` (Optional, `str`): Lawyer name to filter by.
  - `law_firm` (Optional, `str`): Law firm name to filter by.
  - `limit` (Optional, `int`, default: 100): Limit the number of results, -1 for all results.

### Tags
- **Endpoint:** `/tags/`
- **Description:** Get tag names with optional search and limit parameters.
- **Query Parameters:**
  - `search` (Optional, `str`): Tag name to filter by.
  - `limit` (Optional, `int`, default: 100): Limit the number of results, -1 for all results.

### Verdicts
- **Endpoint:** `/verdicts/`
- **Description:** Get verdict names, cannot be filtered.


### Court Cases
- **Endpoint:** `/court_cases/`
- **Description:** Get court case details with optional search and limit parameters.
- **Query Parameters:**
- `tag` (Optional, str): Tag name to filter by.
- `judge` (Optional, str): Judge name to filter by.
- `participant` (Optional, str): Participant name to filter by.
- `lawyer` (Optional, str): Lawyer name to filter by.
- `law_firm` (Optional, str): Law firm name to filter by.
- `title` (Optional, str): Title of the case to filter by.
- `citation` (Optional, str): Citation ID of the case to filter by.
- `verdict` (Optional, str): Verdict of the case to filter by.
- `court` (Optional, str): Court type to filter by.
- `start_date` (Optional, date): Filter by cases before or on this date.
- `end_date` (Optional, date): Filter by cases on or after this date.
- `limit` (Optional, `int`, default: 100): Limit the number of results, -1 for all results.



## Responses
- **200 OK:** Successful response with the requested data.
- **400 Bad Request:** Invalid query parameters.
- **404 Not Found:** No matching records found.

## Setup Instructions

1. **Install Dependencies**: Make sure you have Python and pip installed and the repository cloned. Run the following command to install the required dependencies:
    ```sh
    cd ~
    cd court-transcripts-pipeline/api
    pip3 install -r requirements.txt
    ```

2. **Environment Variables**: Create a `.env` file in the root of the `api` folder and add the necessary environment variables for the API to contact the database.
   
    - `DB_HOST`: The hostname or IP address of the database server.
    - `DB_PORT`: The port number on which the database server is listening; typically 5432 for PostgreSQL
    - `DB_NAME`: The name of the database to connect to.
    - `DB_USER`: The username to use for authenticating with the database.
    - `DB_PASSWORD`: The password to use for authenticating with the database.


3. **Run the Server**: Start the API server by running:
    ```sh
    fastapi run api.py --port 80
    ```

4. **Access the API**: The API is locally accessible at `http://localhost/` (port 80). You can view the API documentation at on the API root endpoint.


<!-- ## Cloud Deployment 
### Docker Setup Instructions

1. **Build the Docker Image**: Run the following command to build the Docker image:
    ```sh
    docker build -t my-api-image .
    ```

2. **Run the Docker Container**: Start a container from the image:
    ```sh
    docker run -d -p 3000:3000 --env-file .env my-api-image
    ``` -->

## Running Tests

To run the unit tests for the API, use the following command:
```sh
pytest test_api.py