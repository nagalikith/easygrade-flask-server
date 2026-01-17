Currently you are in the project directory

make directories assignments and submissions
mkdir assignments
mkdir submissions

also make a directory for the venv-python
mkdir .venv

make the venv in .venv folder
python3 -m venv .venv

activate the virtual environment
source .venv/bin/activate

now install the required libraries to run the app
pip install -r requirement.txt

create a .env file using .env.example

AWS setup
Create an S3 bucket, in the region of your liking
Make a group that has only access to this bucket and operations putObject, getObject and deleteObject
Create a user for the group, and generate its CLI credentials
Make changes in your .env file changing the values for AWS_CRED and AWS_BUCKET

Database Setup
Download postgresql (v15: recommended).
Set the configs such that remote access is possible
Make a user and set its password
Make a database and give all permission for that database to the user made
Make changes to .env file in the DB_INFO

run the app
uvicorn app.main:app --reload --host 0.0.0.0 --port 5050
