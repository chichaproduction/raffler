from datetime import date
from flask import Flask, make_response, request, render_template, jsonify
from flask_bootstrap import Bootstrap
import numpy as np
import pandas as pd
import mysql.connector
from mysql.connector import errorcode

try:
    connection = mysql.connector.connect(host='localhost',
                                        database='raffler',
                                        user='root',
                                        password='')
    if connection.is_connected():
        db_Info = connection.get_server_info()
        print("Connected to MySQL Server version ", db_Info)
        cursor = connection.cursor()
        cursor.execute("select database();")
        record = cursor.fetchone()
        print("You're connected to database: ", record)
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)


app = Flask(__name__)
Bootstrap(app)

@app.route('/')
def index():
    return render_template('title.html')

@app.route('/raffler', methods=["GET"])
def raffler():
    if request.method == 'GET':

        select_cursor_participants = connection.cursor(dictionary=True)
        select_cursor_participants.execute("SELECT * FROM participants WHERE is_active = 1 AND selected = 0")
        selected_participants = select_cursor_participants.fetchall()
        connection.commit()

        select_cursor_participants.close()

        select_cursor_prizes = connection.cursor(dictionary=True)
        select_cursor_prizes.execute("SELECT * FROM prizes WHERE is_active = 1 AND selected = 0")
        selected_prizes = select_cursor_prizes.fetchall()
        connection.commit()

        select_cursor_prizes.close()

        print(selected_participants)
        print(selected_prizes)


        return render_template('raffler_frame.html', participants = selected_participants, prizes = selected_prizes)


@app.route('/participant_upload', methods=["POST"])
def participant_upload():
    if request.method == 'POST':
        participants_data = request.files['participants']
        
        # Check IF There is a File or Not
        if not participants_data:
            print("NO PARTICIPANTS SUBMITTED")
            return render_template('title.html', postres = False)
        
        print("HAS FILES")

        #Get All Data of Participants
        participants_data_encoded = pd.read_csv(participants_data, encoding = "ISO-8859-1")
        participants_data_encoded = participants_data_encoded.replace(to_replace = np.nan, value = " ")
        participants_data_record = participants_data_encoded.to_dict('records')


        #Insert All Participants

        table = "participants"
        columns = [ 'f_name', 'l_name', 'm_name', 'is_active', 'created_at']
        id_list = []

        query = Queries(table, columns)
        for participant in participants_data_record:
            # print("name: ", participant['First Name'], " ",  participant['Middle Name'], " ", participant['Last Name'])

            today = date.today()

             # #Input Values
            input_values = {
                "f_name"     : participant['First Name'],
                "m_name"     : participant['Middle Name'],
                "l_name"     : participant['Last Name'],
                "is_active"  : 1,
                "created_at" : today.strftime("%b-%d-%Y"),
            }
            last_insert_id = query.insert(input_values)
            id_list.append(last_insert_id)

        return render_template('title.html')
    
@app.route('/prize_upload', methods=["POST"])
def prize_upload():
    if request.method == 'POST':
        prizes_data = request.files['prizes']

        # Check IF There is a File or Not
        if not prizes_data:
            print("NO PRIZES SUBMITTED")
            return render_template('title.html', postres = False)
        
        print("HAS FILES")

          #Get All Data of Participants
        prizes_data_encoded = pd.read_csv(prizes_data, encoding = "ISO-8859-1")
        prizes_data_encoded = prizes_data_encoded.replace(to_replace = np.nan, value = " ")
        prizes_data_record = prizes_data_encoded.to_dict('records')

        print(len(prizes_data_record))
        #Insert All Participants

        table = "prizes"
        columns = [ 'code', 'name', 'quantity', 'is_active', 'created_at']
        id_list = []

        query = Queries(table, columns)
        for prize in prizes_data_record:

            today = date.today()

             # #Input Values
            input_values = {
                "code"       : prize['code'],
                "name"       : prize['name'],
                "quantity"   : prize['quantity'],
                "is_active"  : 1,
                "created_at" : today.strftime("%b-%d-%Y"),
            }
            last_insert_id = query.insert(input_values)
            id_list.append(last_insert_id)

 
        return render_template('title.html')




# ================ QUERIES =================== #
class Queries():
    def __init__(self, table, columns):
        self.table = table
        self.columns = columns

    def insert(self, values):
        print(connection.cursor())

        try:
            insert_cursor = connection.cursor()
            mode = "INSERT INTO "
            insert_table = self.table
            insert_columns = self.columns
            columnstring = ' ('
            valuestring = ' VALUES ('
            # for x in values:

            for index, vvalue in enumerate(insert_columns, start=1):
                if index == len(insert_columns):
                    # valuestring = valuestring + '%' + 's'
                    columnstring = columnstring + vvalue +  ')'
                    valuestring = valuestring + '%(' + vvalue +  ')s '
                else:
                    columnstring = columnstring + vvalue +  ', '
                    valuestring = valuestring + '%(' + vvalue +  ')s, '
                    # valuestring = valuestring + '%' + 's, '
            valuestring = valuestring + ')'

            insert_query = mode + insert_table + columnstring + valuestring

            insert_cursor.execute(insert_query, values)
            connection.commit()

            insert_cursor.close()

            lastid = insert_cursor.lastrowid

            return lastid


        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)

    def select(self, values):
        def query_states(col, value, querymode):
            returnquery = ''            
            if(querymode == 'where'):
                returnquery = returnquery + " WHERE " + col + " = " + str(value)
            if(querymode == 'andwhere'):
                returnquery + " AND WHERE " + col + " = " + str(value)
            if(querymode == 'andwherelike'):
                returnquery + " AND WHERE " + col + " LIKE %" + str(value) + "%"
            if(querymode == 'orwhere'):
                returnquery + " OR WHERE " + col + " = " + str(value)
            if(querymode == 'orwherelike'):
                returnquery + " OR WHERE " + col + " LIKE %" + str(value) + "%"

            return returnquery

        try:
            select_cursor = connection.cursor(dictionary=True)
            mode = "SELECT "
            select_table = self.table
            select_columns = self.columns
            columnstring = ' '
            conditionstring = ' '

            select_columns.insert(0, "id")

            # for x in values:
            for index, vvalue in enumerate(select_columns, start=1):
                if index == len(select_columns):
                    columnstring = columnstring + vvalue +  ' '
                else:
                    columnstring = columnstring + vvalue +  ', '

            for key, value in values.items():
                conditionstring = conditionstring + query_states(key, value['value'], value['type'])


            select_query = mode + columnstring + "FROM " + select_table + conditionstring

            select_cursor.execute(select_query)
            selected_user = select_cursor.fetchall()
            connection.commit()

            select_cursor.close()

            return selected_user

        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)


if __name__ == '__main__':
    app.run(debug=True)