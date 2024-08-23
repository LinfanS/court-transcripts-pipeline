# Terraform Documentation

## Overview
This is a doc explaining the terraform folder in our project which holds all the terraform files defiing and then creating all the aws cloud solutions we deploy our pipeline through. I will explain how to run these files as well as how they are split, structured and split.

## Structure
The files are split by feature, if you observe our architecture diagram, the features that employ various aws cloud solutions will have their own terraform file including the full configuration of the aws cloud solutions it employs.

## How to run
To run the terraform files in order to build the necessary aws solutions, cd into the terraform directory and run the following commands..

terraform init
terraform plan
terraform apply

This initialises terraform, the plan oversees the changes you want to make and gives an overview before applying them, apply obviously then makes these changes reality.

## Required variables
Create a `terraform.tfvars` file with the following:
    - `ACCESS_KEY_ID` : Your AWS Access Key credentials
    - `SECRET_ACCESS_KEY` : Your AWS Access Key credentials
    - `REGION` : Your AWS region
    - `DB_HOST`: The hostname or IP address of the database server.
    - `DB_PORT`: The port number on which the database server is listening; typically 5432 for PostgreSQL
    - `DB_NAME`: The name of the database to connect to.
    - `DB_USER`: The username to use for authenticating with the database.
    - `DB_PASSWORD`: The password to use for authenticating with the database.
    - `OPENAI_API_KEY`: API key for ChatGPT API.