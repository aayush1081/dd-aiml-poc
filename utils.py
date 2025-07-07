import pandas as pd 
import numpy as np
import pyodbc
import sqlparse

from openai import AzureOpenAI

## Get schema details
def load_db_schema(db_path, tbl_nm):
    conn = pyodbc.connect(db_path)
    cursor = conn.cursor()
    qry = f'''SELECT distinct COLUMN_NAME FROM
        INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{tbl_nm}' '''
    cursor.execute(qry)
    schema = ", ".join(row[0] for row in cursor.fetchall() if row[0])
    schema = schema + f''' . The table name is {tbl_nm} . Use this table name in your queries.'''  
    
    conn.close()
    return schema


# Formatting the user prompt
def prompt_for_qry(db_schema,nlp_query, column_description):
    system_prompt = f"""
    You are an assistant which takes an input a query written in natural language
    and converts this into a well structured SQL query.
    The schema of the database is: {db_schema}
    Only use column names present in the schema. 
    Refer column description {column_description} if required, especially to decide filters in the query.
    Do not provide any explaination  for the query, just the query. 
    Just generate a valid syntactically correct SQL qry. 
    Do not use \n or any comments. 
    Do not use ```
    Convert columns and filter string to lower case.
    Use MSSQL syntax.
    """
    user_prompt = f"Convert the following request into an SQL query: {nlp_query}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    return messages

# Formatting the correcting errors in SQL
def prompt_for_correction(db_schema,incorrect_qry, error_msg):
    system_prompt = f"""
    You are an assistant which takes an input an incorrect query written in SQL with the error message
    and corrects the SQL query.
    The schema of the database is: {db_schema}
    Only use column names present in the schema. 
    Do not provide any explaination  for the query, just the query. 
    Just generate a valid syntactically correct SQL qry. Do not use \n or any comments. 
    Convert columns and filter string to lower case.
    Use MSSQL syntax.
    """
    incorrect_qry = f"Incorrect SQL Qry: {incorrect_qry} with error message {error_msg}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": incorrect_qry}
    ]
    return messages

def generate_azure_connection(api_version,endpoint,subscription_key):
    
    client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
    )

    return client


def generate_sql(client, model_name,deployment,stream,max_tokens,temperature,top_p,messages):
    
    response = client.chat.completions.create(
        stream=stream,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        model=deployment,
    )
    
    return response.choices[0].message.content

## Validate SQL queries
def validate_sql(query):
    try:
        parsed = sqlparse.parse(query)
        if not parsed:
            return False, "Invalid SQL syntax."
        return True, "SQL is valid"
    except Exception as e:
        return False, str(e)

##Execute SQL queries
def execute_test_query(query, db_path):
    
    try:
        conn = pyodbc.connect(db_path)
        #cursor = conn.cursor()
        df = pd.read_sql(query, conn)
        conn.close()
        return True, df
    except Exception as e:
        return False, str(e)