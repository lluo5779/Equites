# Machine Learning Regime Switching Robo Advisor - WIP

Hi Giorgio!

## Requirements
1. Please run the following to install packages:
```pip3 install -r requirements.txt ```

2. Please run the following to populate the database (with PostgreSQL running):
```python3 update_databases.py```
    - Note only Tiingo data currently populates. The factor models are yet to be implemented.

Also, **Make sure your PostgreSQL server is running**. I am currently using PostgreSQL 11.5. For where to install, go here for installation exe: 

https://www.enterprisedb.com/downloads/postgres-postgresql-downloads

## Quickstart
Run the following command at the project root directory. Exposes app on port 5000.

```python3 app.py``` 

## Routing
See "./server/swagger.yaml" for routing details and currently available routes.

## Front-end
Please dump your templates in ./server/templates and organize as you see fit.

## Business Logic
We will need to talk about what needs to go where and how to hook up :)

## Back-end
Major updates since last time:

- code was refactored to be more organized
- one can now register and login via

```{localhost:5000 or alike}/auth/login and {localhost:5000 or alike}/auth/register```
- See config files in various folders for, \*well\*, configuration XD
