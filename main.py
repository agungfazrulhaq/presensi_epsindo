from flask import Flask, render_template, redirect, url_for, request, session
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np
import mysql.connector as sqlconnector
import data
import datetime, calendar
import random
import os

app = Flask(__name__)
app.secret_key = 'epsind0'
twelvemonth = ['January','February','March','April','May']
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
host = '192.168.1.73'
database = 'presensi_epsindo'
username = 'root'
password = 'epsindo123'
connection = sqlconnector.connect(host=host,
                           database=database,
                           user=username,
                           password=password)
randomized_filename = "None"

@app.route('/')
def index():
    return redirect(url_for('dashboard', user=0, year=2022))

@app.route('/dashboard/<user>/<year>')
def dashboard(user = 0, year=2022):
    year=int(year)
    connection = sqlconnector.connect(host=host,
                           database=database,
                           user=username,
                           password=password)
    
    df_participant = data.load_participants(connection)
    print("Current user id : ", user)
    df_presensi = data.load_presensi(connection)
    df_leave = data.load_leave(connection)
    df_yearly = data.load_yearly(df_presensi,df_leave, participant_id=int(user), year=year)

    curr_user = df_participant[df_participant['id'] == int(user)].values[0]
    df_participant = df_participant[df_participant['id'] != int(user)]
    df_participant = df_participant.sort_values('name', ascending=True)
    now = datetime.datetime.utcnow()

    page_info = {'page':'index',
                 'year' : year,
                 'now_year' : now.year, 
                 'months':list(monthdict.keys()), 
                 'data_yearly':df_yearly, 
                 'data_participant':df_participant, 
                 'data_current_user':curr_user}

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
    df_leave = data.load_leave(connection)
    df_monthly_data = data.load_monthly_table_data(df_participant, df_presensi, df_leave, month=monthdict[month])

    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    dict_rename = {}
    day_col = 1
    for x in df_monthly_data.columns :
        if isinstance(x, datetime.date) :
            dict_rename[x] = weekdays[x.weekday()] +" "+ str(day_col)
            day_col += 1
    df_monthly_data.rename(columns = dict_rename, inplace=True)
    
    importpres = 'None'
    if session.get('importpresensi_status') == True:
        importpres = str(session['importpresensi_status']) + ' rows inserted.'
        session.pop('importpresensi_status')

    page_info = {'page':'monthly', 'month':month, 'data_monthly':df_monthly_data, 'row_imported':importpres}
    return render_template('monthly.html', result = page_info)

@app.route('/statustable/<start_date>_<end_date>')
def statustable(start_date, end_date):
    stdate = start_date.split('-')
    eddate = end_date.split('-')
    start_date = stdate[2]+"-"+stdate[0]+"-"+stdate[1]
    end_date = eddate[2]+"-"+eddate[0]+"-"+eddate[1]
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

    df_presensi = data.load_presensi_from_date(connection, start_date, end_date)
    df_participant = data.load_participants(connection)
    df_leave = data.load_leave(connection)
    print(start_date)
    print(end_date)
    df_monthly_data = data.load_presensi_table_data(df_participant, df_presensi, df_leave, start_date, end_date)

    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    dict_rename = {}
    day_col = 1
    for x in df_monthly_data.columns :
        if isinstance(x, datetime.date) :
            dict_rename[x] = weekdays[x.weekday()] +" "+ str(x.day)
            day_col += 1
    df_monthly_data.rename(columns = dict_rename, inplace=True)
    
    importpres = 'None'
    if session.get('importpresensi_status') == True:
        importpres = str(session['importpresensi_status']) + ' rows inserted.'
        session.pop('importpresensi_status')

    page_info = {'page':'monthly', 'month':'None', 'data_monthly':df_monthly_data, 'row_imported':importpres}
    return render_template('monthly.html', result = page_info)

@app.route('/tableinputdate/', methods=['GET', 'POST'])
def table_input_date():
    year = 2022
    connection = sqlconnector.connect(host=host,
                           database=database,
                           user=username,
                           password=password)
    
    month = 11

    if request.method == 'POST' :
        start_date = '-'.join(request.form['startdate'].split('/'))
        end_date = '-'.join(request.form['enddate'].split('/'))
    
    else :
        start_date = datetime.date(year, month, 1)
        end_date = datetime.date(year, month, calendar.monthrange(year, month)[1])


    return redirect(url_for('statustable', start_date=start_date, end_date=end_date))

    

@app.route('/importdata/<part>/preview=<filename>')
def import_data(part = 'presensi', filename='None'):
    connection = sqlconnector.connect(host=host,
                           database=database,
                           user=username,
                           password=password)
    

    if part == 'presensi' :
        if filename=='None' :
            page_info = {'page':'importdata', 'months':twelvemonth, 'part':part, 'filename':filename}
        else :
            df_part, df_dep, df_presensi = data.read_presensi_file(connection,filename)
            if len(df_presensi.columns) == 0:
                page_info = {'page':'importdata', 
                        'months':twelvemonth, 
                        'part':part, 
                        'filename':'error', 
                        'data_presensi':'error'}
            
            else :
                df_presensi['duplicated'] = data.check_duplicate_data(df_presensi, 
                                                                    data.load_presensi(connection), 
                                                                    subset_=['Date', 
                                                                            'Participant_id', 
                                                                            'status'])
                if True in df_presensi['duplicated'].values :
                    duplicate_data = True
                else :
                    duplicate_data = False
                # if randomized_filename == "None" :
                    # randomized_namefile = str(random.randint(100000,999999)) + ".csv"
                # print(session["name"])

                # df_presensi.to_csv(randomized_namefile, index=False)
                page_info = {'page':'importdata', 
                        'months':twelvemonth, 
                        'part':part, 
                        'filename':filename,
                        'duplicated':duplicate_data, 
                        'data_presensi':df_presensi}
                presensi_dict = df_presensi.to_dict('list')
                session["data"] = presensi_dict
    else :
        if filename=='None' :
            page_info = {'page':'importdata', 'months':twelvemonth, 'part':part, 'filename':filename}
        else :
            df_participant = data.load_participants(connection)
            df_leave = data.read_leave(filename, df_participant)
            if len(df_leave.columns) == 0:
                page_info = {'page':'importdata', 
                        'months':twelvemonth, 
                        'part':part, 
                        'filename':'error', 
                        'data_presensi':'error'}
            
            else :
                df_leave['duplicated'] = data.check_duplicate_data_leave(df_leave, 
                                                                    data.load_leave(connection), 
                                                                    subset_=['participant_id',
                                                                             'reason', 
                                                                             'leave_from', 
                                                                             'leave_to',
                                                                             'status'])
                if True in df_leave['duplicated'].values :
                    duplicate_data = True
                else :
                    duplicate_data = False
                # if randomized_filename == "None" :
                    # randomized_namefile = str(random.randint(100000,999999)) + ".csv"
                # print(session["name"])

                # df_presensi.to_csv(randomized_namefile, index=False)
                page_info = {'page':'importdata', 
                        'months':twelvemonth, 
                        'part':part, 
                        'filename':filename,
                        'duplicated':duplicate_data, 
                        'data_presensi':df_leave}
                leave_dict = df_leave.to_dict('list')
                session["data"] = leave_dict

    return render_template('importdata.html', result=page_info)

@app.route('/importpresensi', methods= ['GET','POST'])
def preimporter():
    # page_info = {'page':'presensi', 'months':twelvemonth}
    if request.method == 'POST':
        f = request.files['file']
        print(f.filename)
        f.save(secure_filename(f.filename))
        return redirect(url_for('import_data', part='presensi', filename=f.filename.replace(" ", "_")))

@app.route('/importpresensi/insertdb/<dup_action>')
def importpresensidb(dup_action) :
    connection = sqlconnector.connect(host=host,
                           database=database,
                           user=username,
                           password=password)
    pres_dict = session["data"]
    df_pres = pd.DataFrame(pres_dict)
    firstrow = df_pres['Date'].iloc[0]
    rowcount_imported = data.import_presensi(connection, df_pres, dup_action=dup_action)

    session.pop('data', None)
    session['importpresensi_status'] = rowcount_imported

    return redirect(url_for('monthly', month=list(monthdict.keys())[list(monthdict.values()).index(int(firstrow[5:7]))]))

@app.route('/importleave/insertdb/<dup_action>')
def importleavedb(dup_action) :
    connection = sqlconnector.connect(host=host,
                           database=database,
                           user=username,
                           password=password)
    leave_dict = session["data"]
    df_leave = pd.DataFrame(leave_dict)
    firstrow = df_leave['leave_from'].iloc[0]
    rowcount_imported = data.import_leave(connection, df_leave, dup_action=dup_action)

    session.pop('data', None)
    session['importpresensi_status'] = rowcount_imported

    return redirect(url_for('monthly', month=list(monthdict.keys())[list(monthdict.values()).index(int(firstrow[5:7]))]))


@app.route('/importleave', methods=['GET', 'POST'])
def leimporter():
    if request.method == 'POST':
        f = request.files['file']
        print(f.filename)
        f.save(secure_filename(f.filename))
        return redirect(url_for('import_data', part='leave', filename=f.filename.replace(" ", "_")))

@app.route('/participants')
def participant_list():
    connection = sqlconnector.connect(host=host,
                           database=database,
                           user=username,
                           password=password)
    # df_participant = data.load_participants(connection)
    cursor = connection.cursor()

    sql = "SELECT * FROM participant LEFT JOIN department ON participant.department_id=department.department_id;"
    cursor.execute(sql)

    hasil = cursor.fetchall()
    df_participant = pd.DataFrame(hasil, columns=['Participant ID', 'Name', 'Department ID', 'e-mail', 'Department ID', 'Department'])


    page_info = {'page':'participantlist', 
                        'months':twelvemonth,
                        'data_participant':df_participant
                        }
    return render_template('participants.html', result=page_info)

if __name__ == '__main__' :
    app.run(host='0.0.0.0', debug=True)