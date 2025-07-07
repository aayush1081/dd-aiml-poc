import numpy as np
#!pip install sqlparse
import sqlparse
## !pip install openai
from openai import AzureOpenAI
from utils import *


def response_generator(user_query):
    

    ## Set parameters
    ## Key Variables
    db_path = 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:dbserver-aditaas-us-nonprd-eastus.database.windows.net,1433;Database=digitaldesk_rms_qa;UID=digitaldesk_rms_qa;PWD=DigiR$#24dskQa;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
    tbl_nm = 'view_aiml_inc_all' ## only incident data in this version
    
    # Connection definition
    endpoint = "https://chatbouthub4961306707.openai.azure.com/"
    model_name = "gpt-4o-mini"
    deployment = "gpt-4o-mini"
    subscription_key = "6i2vrxk6aBZgAJ84cMn7OrziaHMRopuLctHkGzu18tZYyCBoIbLmJQQJ99BDACHYHv6XJ3w3AAAAACOGLF9D"
    api_version = "2024-12-01-preview"
    
    # Model usage parameters
    stream=False
    max_tokens=4096
    temperature=1.0
    top_p=1.0
    model=deployment
    
    ## Common columns on which filters are expected
    column_description = '''Type -	Unique values Incident, Service Request or Change Request
    Ticket_ID -	Unique identifier for the table
    Customer_Name - 	Name of customer that is facing the issue
    Account_Manager - 	Account manager for client where the issue is happening
    Site_Name - 	Location name of customer where issue happened
    Short_Description -	Description of issue / ticket
    Status - 	Unique values: AUTOMATED RESOLUTION REPORTED, CLOSED, IN APPROVAL, IN PROGRESS , OPEN, PEND 3RD PARTY, PEND CLIENT, PEND PARTNER, PROGRESSING, REJECTED, REJECTED-CLOSED, RESOLVED, SCHEDULED TASK, UNDER OBSERVATION
    Priority - 	Unique values: P1, P2, P3, P4, P5
    Impact - 	Unique values: LOW, MEDIUM, HIGH. Can be Null
    Urgency - 	Unique values: LOW, MEDIUM, HIGH. Can be Null
    Channel - 	Channel through which ticket was created. Unique values : CHAT, EMAIL, EVENT,  MANAGE ENGINE, MOBILE APP, OTHERS, PHONE, PRTG, SELF SERVICE, SERVICE NOW
    Asset_Name - 	Device where issue happened. Can be device name or IP address
    Creation_Date - 	Date on which ticket was created
    Assigned Group - 	Resolver group
    Assign_To - 	First resolver name. Name of person ticket is assigned to
    Resolved_Date_and_Time -  time at which ticket was resolved. Resolution time = Resolved_Date_and_Time - Creation_Date
    Resolved_By - 	Name of resolver
    Resolution_Method - 	Unique values: , 3RD PARTY, CUSTOMER, EMAIL, NO ACTION REQUIRED, NOT RESOLVED, PHONE, REMOTE CONTROL/TOOLS, RESOLVED BY IBM SNOW, SITE VISIT
    Hypercare_Assistance - 	Whether the ticket needed domain specialists assitance to resolve. Will be Null or empty space (' ') when no assitance was required
    Response_SLA_Violated - 	Unique Values: Yes, No
    Resolution_SLA_Violated - 	Unique Values: Yes, No
    '''
    
    
    schema = load_db_schema(db_path,tbl_nm)
    messages = prompt_for_qry(schema,user_query, column_description)
    client = generate_azure_connection(api_version,endpoint,subscription_key)
    qry = generate_sql(client, model_name,deployment,stream,max_tokens,temperature,top_p,messages)
    val_qry = validate_sql(qry)
    print(qry)
    
    if val_qry:
        chk,results = execute_test_query(qry, db_path)
        if chk:
            print(results)
        else:
            print("results are incorrect, running correction")
            messages = prompt_for_correction(schema,qry, results)
            qry = generate_sql(client, model_name,deployment,stream,max_tokens,temperature,top_p,messages)
            print("corrected query ",  qry)
            chk,results = execute_test_query(qry, db_path)
    else:
        print("syntax is incorrect, running correction")
        messages = prompt_for_correction(schema,qry, results)
        qry = generate_sql(client, model_name,deployment,stream,max_tokens,temperature,top_p,messages)
        print("corrected query ",  qry)
        chk,results = execute_test_query(qry, db_path)
    
    
    client.close()

    return results
    
    ## results will have the final data that we want to show on chat output