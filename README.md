# dhruv-email-integration
manages interaction with o365

#### 1. give me list of email for a user between 2 dates
- a. recevied - return ‘from email’, subject line’, ‘immutable_id’
- b. sent
#### 2. save email in correspondence table
- columns - immutable id, bkg no, quote no, account code (which is client id), body, attachment


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