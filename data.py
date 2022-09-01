from math import floor
from datetime import date
import pandas as pd
import numpy as np
import datetime, calendar

def test():
    return "Imported DATA Module."

def format_timedelta(td):
    if pd.isnull(td) :
        return None
    else :
        minutes, seconds = divmod(td.seconds + td.days * 86400, 60)
        hours, minutes = divmod(minutes, 60)
        return '{:d}:{:02d}:{:02d}'.format(hours, minutes, seconds)

def total_late(fi) :
    if fi.total_seconds()/3600 >= 10:
        tolate = (fi.total_seconds() - (3600*10))/60
        return tolate
    else :
        return 0

def load_presensi(conn, month='all', year=date.today().year):
    cursor = conn.cursor()
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
    if month=='all' :
        query = "SELECT * FROM presensi_table"
    else :
        query = "SELECT * FROM presensi_table WHERE MONTH(date)=" + str(monthdict[month]) +" AND YEAR(date)=" + str(year)
    cursor.execute(query)

    result = cursor.fetchall()
    df_presensi = pd.DataFrame(data=result, columns=['id','Date', 'Participant_id','status','firstcheckin', 'lastcheckout'])
    df_presensi['firstcheckinstr'] = df_presensi['firstcheckin'].apply(lambda x : format_timedelta(x))
    df_presensi['lastcheckoutstr'] = df_presensi['lastcheckout'].apply(lambda x : format_timedelta(x))
    df_presensi['total_late'] = df_presensi['firstcheckin'].apply(lambda x: total_late(x))
    return df_presensi

def load_participants(conn, department=-1):
    cursor = conn.cursor()

    if department < 0 :
        cursor.execute("SELECT * FROM participant")
    else :
        cursor.execute("SELECT * FROM participant WHERE department_id="+str(department))
    
    result = cursor.fetchall()
    
    name = [result[i][1] for i in range(len(result))]
    ids = [result[i][0] for i in range(len(result))]
    dep_ids = [result[i][2] for i in range(len(result))]
    emails = [result[i][3] for i in range(len(result))]

    participant_df = pd.DataFrame({'id':ids, 'name':name, 'dep_id':dep_ids, 'email':emails})
    return participant_df

def load_leave(conn) :
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leave_table")
    result = cursor.fetchall()
    result_columns = ['id_leave', 'participant_id', 'leave_kind', 'reason', 'leave_from', 'leave_to']
    result_df = pd.DataFrame(data=result , columns = result_columns)
    return result_df

def get_leave_data(df_leave, participant_id) :
    leave_data = df_leave[df_leave['participant_id'] == participant_id]
    # print(leave_data)
    leave_list = []
    for ind, val in leave_data.iterrows() :
        current_date = val['leave_from']
        # print(val['leave_from'] - val['leave_to'])
        for x in range((val['leave_to'] - val['leave_from']).days + 1) :
            # print(x)
            if current_date in leave_list :
                pass
            else :
                leave_list.append(current_date)
            current_date = current_date + datetime.timedelta(days=1)
    return leave_list

def load_monthly_table_data(df_participant, df_presensi, df_leave, month=1, year=2022) :
    days = [datetime.date(year, month, d+1) for d in range(calendar.monthrange(year,month)[1])]
    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    # df_presensi['datetimedate'] = df_presensi["Date"].apply(lambda x : datetime.datetime.strptime(x, "%Y-%m-%d").date())
    dict_absen = {'Name':[]}

    dates = 0
    for day in days :
        wkday = weekdays[day.weekday()]
        dict_absen[day] = []
        dates += 1
    dict_absen['presensi_total'] = []
    dict_absen['absensi_total'] = []
    dict_absen['cuti_total'] = []
    dict_absen['total_late'] = []
    if len(df_presensi['Date'].values) > 0 :
        mindate = min(df_presensi['Date'].values)
        maxdate = max(df_presensi['Date'].values)
    print(df_presensi)
    # dict_absen
    for ind,val in df_participant.iterrows() :
        dict_absen['Name'].append(val['name'])
        presentlist = df_presensi[df_presensi["Participant_id"] == val["id"]]
        daysindata = presentlist['Date'].values
        leave_data = get_leave_data(df_leave, val["id"])
        total_minutes = 0
        for x in presentlist['total_late'].values :
            total_minutes += x
        # total_late_seconds = 0
        # for ind, val in presentlist.iterrows():
        #     if np.isnat(val['firstcheckin']) == False :
        #         if val['firstcheckin'].total_seconds() > 36000 :
        #             total_late_seconds = val['firstcheckin'].total_seconds() - 36000

        presentotal = 0
        absentotal = 0
        for day in days:
            if day.weekday() == 5 or day.weekday() == 6 :
                dict_absen[day].append('L')

            elif len(df_presensi['Date'].values) == 0 :
                dict_absen[day].append('N')

            elif day < mindate or day > maxdate :
                dict_absen[day].append('N')

            elif day in leave_data :
                dict_absen[day].append('C')

            elif day in daysindata :
                dict_absen[day].append('P')
                presentotal += 1

            else :
                dict_absen[day].append('A')
                absentotal += 1

        dict_absen['presensi_total'].append(presentotal)
        dict_absen['absensi_total'].append(absentotal)
        dict_absen['cuti_total'].append(0)
        dict_absen['total_late'].append(total_minutes)

    return pd.DataFrame(dict_absen)

def load_yearly(df_presensi, df_leave, participant_id=0, year=2022) :
    days = []
    for i in range(12) :
        days.append([datetime.date(year, i+1, d+1) for d in range(calendar.monthrange(year,i+1)[1])])

    # weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    dict_analysis = {}
    leave_data = get_leave_data(df_leave, participant_id)
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
    
    allmonth = {}
    for imonth in range(12) :
        monthly_ = {}
        if imonth == 11 :
            presentlist = df_presensi[  (df_presensi['Participant_id'] == participant_id) & 
                                    (df_presensi['Date'] >= datetime.date(year,imonth+1,1)) & 
                                    (df_presensi['Date'] <= datetime.date(year,imonth+1,31))]
        else :
            presentlist = df_presensi[  (df_presensi['Participant_id'] == participant_id) & 
                                    (df_presensi['Date'] >= datetime.date(year,imonth+1,1)) & 
                                    (df_presensi['Date'] < datetime.date(year,imonth+2,1))]
         
        # print(len(presentlist))
        daysindata = presentlist['Date'].values
        presentotal = 0
        absentotal = 0
        nodata = 0
        leavetotal = 0
        if len(df_presensi['Date'].values) > 0 :
            mindate = min(df_presensi['Date'].values)
            maxdate = max(df_presensi['Date'].values)
            for day in days[imonth]:
                if day.weekday() == 5 or day.weekday() == 6 :
                    pass
            
                elif day < mindate or day > maxdate :
                    nodata += 1
                
                elif day in leave_data :
                    leavetotal += 1

                elif day in daysindata :
                    # dict_absen[day].append('P')
                    presentotal += 1

                else :
                    # dict_absen[day].append('A')
                    absentotal += 1
        else :
            for day in days[imonth]:
                if day.weekday() == 5 or day.weekday() == 6 :
                    pass
            
                else :
                    nodata += 1
        totaldata = presentotal + absentotal + nodata + leavetotal
        monthly_['total_present'] = presentotal
        monthly_['present_pct'] = round((presentotal/totaldata)*100)
        monthly_['total_absent'] = absentotal
        monthly_['absent_pct'] = round((absentotal/totaldata)*100)
        monthly_['nodata'] = nodata
        monthly_['nodata_pct'] = round((nodata/totaldata)*100)
        monthly_['total_leave'] = leavetotal
        monthly_['leave_pct'] = round((leavetotal/totaldata)*100)
        allmonth[str(imonth+1)] = monthly_
    dict_analysis['monthly'] = allmonth
    
    totalpresent = 0
    totalabsent = 0
    totalnodata = 0
    totalleave = 0
    for i in range(12) :
        totalpresent += dict_analysis['monthly'][str(i+1)]['total_present']
        totalabsent += dict_analysis['monthly'][str(i+1)]['total_absent']
        totalnodata += dict_analysis['monthly'][str(i+1)]['nodata']
        totalleave += dict_analysis['monthly'][str(i+1)]['total_leave']
    
    totaldata = totalabsent + totalpresent + totalleave
    dict_analysis['yearly'] = { 'total_present': totalpresent,
                                'total_absent': totalabsent,
                                'total_nodata': totalnodata,
                                'total_leave' : totalleave,
                                'presentpct': round((totalpresent/totaldata)*100),
                                'absentpct': round((totalabsent/totaldata)*100),
                                'leavepct': round((totalleave/totaldata)*100),
                                'nodatapct': round((totalnodata/totaldata)*100)
                            }
    # print(totalpresent)
    # for y in range(12) :
    #     monthly_ = {}
    #     monthly_['total_present'] = 
    # dates = 0
    # for day in days :
    #     wkday = weekdays[day.weekday()]
    #     dict_absen[day] = []
    #     dates += 1
    
    # print(max(df_presensi['Date'].values))
    # # dict_absen
    
    #     dict_absen['presensi_total'].append(presentotal)
    #     dict_absen['absensi_total'].append(absentotal)
    #     dict_absen['cuti_total'].append(0)

    return dict_analysis

