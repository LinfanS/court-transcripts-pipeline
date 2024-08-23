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