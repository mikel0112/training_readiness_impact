import mysql.connector as connector
from mysql.connector import Error
import pandas as pd
import json
import os
import datetime as dt

class Database:
    def __init__(self, user, password, db_name):
        self.user = user
        self.password = password
        self.db_name = db_name

    def connect_to_db(self):
        try:
            connection = connector.connect(host="localhost", user=self.user, password=self.password)
            if connection.is_connected():
                db_Info = connection.get_server_info()
                print("Connected to MySQL Server version ", db_Info)
                cursor = connection.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_name};")
                cursor.execute(f"USE {self.db_name};")
                print("You're connected to database: ", connection.database)
                return connection, cursor
        except Error as e:
            print("Error while connecting to MySQL", e)
    
    def close_connection(self, connection, cursor):
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")
        else:
            print("MySQL connection is already closed")

    def execute_query(self, connection, cursor, query):
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    
    def execute_query_with_params(self, connection, cursor, query, params):
        cursor.execute(query, params)
        result = cursor.fetchall()
        return result
    
    def extract_dataframe_columns(self, df):
        columns_list = df.columns.tolist()
        return columns_list

if __name__ == "__main__":
    user = input("Enter username: ")
    password = input("Enter password: ")
    db_name = input("Enter database name: ")
    db = Database(user, password, db_name)
    connection, cursor = db.connect_to_db()
    
    db.close_connection(connection, cursor)