from flask import Flask, render_template
import pandas as pd
import numpy as np
import mysql.connector as sqlconnector
import data
import datetime, calendar

app = Flask(__name__)
twelvemonth = ['January','February','March','April','May']
host = '192.168.1.73'
database = 'presensi_epsindo'
username = 'root'
password = 'epsindo123'
connection = sqlconnector.connect(host=host,
                           database=database,
                           user=username,
                           password=password)

@app.route('/')
def index():
    page_info = {'page':'index', 'months':twelvemonth}
    return render_template('index.html', result = page_info)

@app.route('/monthly/<month>')
def monthly(month='January'):
    connection = sqlconnector.connect(host=host,
                           database=database,
                           user=username,
                           password=password)
    monthdict = { 'January' : 1 ,
                  'February' : 2,
                  'March' : 3,
                  'April' : 4,
                  'May' : 5,
                  'June' : 6,
                  'July' : 7,
                  'August' : 8,
                  'September' : 9,
                  'October' : 10,
                  'November' : 11,
                  'December' : 12}

    df_presensi = data.load_presensi(connection, month=month)
    df_participant = data.load_participants(connection)
    df_monthly_data = data.load_monthly_table_data(df_participant, df_presensi, month=monthdict[month])
    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    dict_rename = {}
    day_col = 1
    for x in df_monthly_data.columns :
        if isinstance(x, datetime.date) :
            dict_rename[x] = weekdays[x.weekday()] +" "+ str(day_col)
            day_col += 1
    df_monthly_data.rename(columns = dict_rename, inplace=True)


    page_info = {'page':'monthly', 'month':month, 'data_monthly':df_monthly_data}
    return render_template('monthly.html', result = page_info)

@app.route('/importdata')
def import_data():

    page_info = {'page':'importdata', 'months':twelvemonth}
    return render_template('importdata.html', result=page_info)

if __name__ == '__main__' :
    app.run(host='0.0.0.0', debug=True)