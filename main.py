from flask import Flask, render_template
import pandas as pd
import numpy as np
import mysql.connector as sqlconnector
import data

app = Flask(__name__)
twelvemonth = ['January','February','March','April','May']
connection = sqlconnector.connect(host='192.168.1.73',
                           database='presensi_epsindo',
                           user='root',
                           password='epsindo123')

@app.route('/')
def index():
    page_info = {'page':'index', 'months':twelvemonth}
    return render_template('index.html', result = page_info)

@app.route('/monthly/<month>')
def monthly(month='January'):
    df_presensi = data.load_presensi(connection, month=month)
    df_participant = data.load_participant(connection)
    

    page_info = {'page':'monthly', 'month':month}
    return render_template('monthly.html', result = page_info)

@app.route('/importdata')
def import_data():
    page_info = {'page':'importdata', 'months':twelvemonth}
    return render_template('importdata.html', result=page_info)