# dhruv-email-integration
multi-tenant email read/send app

### Run app
1. Install Python
2. Install Poetry (package manager for python)
3. Clone this repo (`git clone git@github.com:jetoslabs/dhruv-email-integration.git`)
4. Copy the Configuration folder in top app folder
5. Init poetry virtual env, run cmd `poetry shell`
6. Activate the shell (this step is usually included as part of `poetry shell` cmd)
7. Install dependencies, run cmd `poetry update`
8. Start application, run cmd `uvicorn app.main:app --workers 2 --port 9999`
9. Check the app is running, by going to `http://127.0.0.1:9999/docs`

### Functionality
1. Read
   1. list emails for a user between 2 dates
      - a. recevied - return ‘from email’, subject line’, ‘immutable_id’
      - b. sent
   2. save email in correspondence table
      - columns - immutable id, bkg no, quote no, account code (which is client id), body, attachment
2. Send
   1. Send email in behalf of a user

# Developer Notes
1. Have to manually match columns in `models` and `schema` package. 

# Identity
#### client secret variation 
- Reference repo: https://github.com/Azure-Samples/ms-identity-python-daemon/tree/master/1-Call-MsGraph-WithSecret#register-the-client-app-daemon-console
- reference repo : https://docs.microsoft.com/en-us/graph/auth-v2-service
- ![Client level secret](https://github.com/Azure-Samples/ms-identity-python-daemon/blob/master/1-Call-MsGraph-WithSecret/ReadmeFiles/topology.svg)

# Database
#### SqlAlchemy
- ![sqlalchemy-orm-tutorial-for-python-developers](https://auth0.com/blog/sqlalchemy-orm-tutorial-for-python-developers/)
- ![Use SQLAlchemy as Dependency vs. Middleware vs. scoped_session](https://github.com/tiangolo/fastapi/issues/726#issuecomment-557687526)