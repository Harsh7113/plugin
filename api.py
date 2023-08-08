import mysql.connector
from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel
import uvicorn

class Database:
    def __init__(self, host, port, username, password, database):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.connect()
        

    def connect(self):
        self.connection = mysql.connector.connect(
            host=self.host,
            port=self.port,
            user=self.username,
            password=self.password,
            database=self.database
        )
        self.cursor = self.connection.cursor()


    def query_data(self, table_name: str):
        query = f"SELECT * FROM {table_name};"
        self.cursor.execute(query)
        result = self.cursor.fetchall()
        return result

    def upsert_data(self, data, table_name):
        # will be implementing upsert logic here
        pass

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

class UpsertRequest(BaseModel):
    data: dict
    table_name: str
#enter your database info here
db = Database(
    host="here",
    port="here",
    username="here",
    password="here",
    database="here"
)

@app.get("/query")
def query_data(table_name: str):  
    try:
        result = db.query_data(table_name)  
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upsert")
def upsert_data(request: UpsertRequest):
    try:
        data = request.data
        table_name = data.get("table_name")
        
        # extracts relevant fields from user request data and perform the update logic
        if table_name in db.connection.table_names():
            
            # get the list of columns in the table
            db.cursor.execute(f"DESCRIBE {table_name};")
            columns = []
            for column in db.cursor.fetchall():
                columns.append(column[0])

            # filter the input data to only include valid columns
            filtered_data = {k: v for k, v in data.items() if k in columns}

            # checks if the filtered data is not empty
            if filtered_data:
                
                #constructs the SQL query dynamically based on the filtered data
                placeholders = ', '.join(['%s'] * len(filtered_data))
                columns_query = ', '.join(filtered_data.keys())
                values = tuple(filtered_data.values())

                #performs the INSERT or UPDATE query based on the table and existing records
                db.cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
                existing_record = db.cursor.fetchone()

                if existing_record:
                    set_query = ', '.join([f"{column} = %s" for column in filtered_data.keys()])
                    db.cursor.execute(f"UPDATE {table_name} SET {set_query};", values + values)
                else:
                    db.cursor.execute(f"INSERT INTO {table_name} ({columns_query}) VALUES ({placeholders});", values)

                #makes the changes to the database
                db.connection.commit()

        return {"message": "Successfully updated data into the database"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
