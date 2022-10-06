from math import floor
from datetime import date
from datetime import timedelta
import pandas as pd
import numpy as np
import datetime, calendar
from dateutil.parser import parse

def test():
    return "Imported DATA Module."

# def read_data()


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

def load_presensi_from_date(conn, start_date, end_date):
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
    
    query = "SELECT * FROM presensi_table WHERE date BETWEEN '" + start_date +"' AND '" + end_date +"'"
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
    result_columns = ['id_leave', 'participant_id', 'leave_kind', 'reason', 'leave_from', 'leave_to', 'status']
    result_df = pd.DataFrame(data=result , columns = result_columns)
    return result_df

def get_leave_data(df_leave, participant_id) :
    df_leave = df_leave[df_leave['status'] == 'Approved']
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
                if pd.Timedelta(presentlist[presentlist["Date"] == day]["firstcheckin"].values[0]).total_seconds()/3600 >= 10 :
                    dict_absen[day].append('T')
                else :
                    dict_absen[day].append('P')
                presentotal += 1

            else :
                dict_absen[day].append('A')
                absentotal += 1

        dict_absen['presensi_total'].append(presentotal)
        dict_absen['absensi_total'].append(absentotal)
        dict_absen['cuti_total'].append(0)
        dict_absen['total_late'].append(total_minutes)
    dict_absen['Total Kehadiran'] = dict_absen['presensi_total']
    del dict_absen['presensi_total']
    dict_absen['Total Absent'] = dict_absen['absensi_total']
    del dict_absen['absensi_total']
    dict_absen['Total Cuti'] = dict_absen['cuti_total']
    del dict_absen['cuti_total']
    dict_absen['Total Telat(Menit)'] = dict_absen['total_late']
    del dict_absen['total_late']

    return pd.DataFrame(dict_absen)

def load_presensi_table_data(df_participant, df_presensi, df_leave, start_date, end_date) :
    sdate = parse(start_date)
    edate = parse(end_date)
    # sdate.tz_localize(None)
    # edate.tz_localize(None)

    list_date = pd.date_range(start_date,end_date,freq='d')

    days = []
    for x in list_date :
        days.append(x.date())
    days

    # days = []
    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    print(days)

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
                # print(presentlist[presentlist["Date"] == day]["firstcheckin"].values[0].total_seconds()/3600)
                if pd.Timedelta(presentlist[presentlist["Date"] == day]["firstcheckin"].values[0]).total_seconds()/3600 >= 10 :
                    dict_absen[day].append('T')
                else :
                    dict_absen[day].append('P')
                presentotal += 1

            else :
                dict_absen[day].append('A')
                absentotal += 1

        dict_absen['presensi_total'].append(presentotal)
        dict_absen['absensi_total'].append(absentotal)
        dict_absen['cuti_total'].append(0)
        dict_absen['total_late'].append(total_minutes)
        
    dict_absen['Total Kehadiran'] = dict_absen['presensi_total']
    del dict_absen['presensi_total']
    dict_absen['Total Absent'] = dict_absen['absensi_total']
    del dict_absen['absensi_total']
    dict_absen['Total Cuti'] = dict_absen['cuti_total']
    del dict_absen['cuti_total']
    dict_absen['Total Telat(Menit)'] = dict_absen['total_late']
    del dict_absen['total_late']

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
        latetotal = 0
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
                    if pd.Timedelta(presentlist[presentlist["Date"] == day]["firstcheckin"].values[0]).total_seconds()/3600 >= 10 :
                        latetotal += 1
                    # dict_absen[day].append('P')
                    else :
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
        totaldata = presentotal + absentotal + nodata + leavetotal + latetotal
        monthly_['total_present'] = presentotal
        monthly_['present_pct'] = round((presentotal/totaldata)*100)
        monthly_['total_late'] = latetotal
        monthly_['late_pct'] = round((latetotal/totaldata)*100)
        monthly_['total_absent'] = absentotal
        monthly_['absent_pct'] = round((absentotal/totaldata)*100)
        monthly_['nodata'] = nodata
        monthly_['nodata_pct'] = round((nodata/totaldata)*100)
        monthly_['total_leave'] = leavetotal
        monthly_['leave_pct'] = round((leavetotal/totaldata)*100)
        allmonth[str(imonth+1)] = monthly_
    dict_analysis['monthly'] = allmonth
    
    totalpresent = 0
    totallate = 0
    totalabsent = 0
    totalnodata = 0
    totalleave = 0
    for i in range(12) :
        totalpresent += dict_analysis['monthly'][str(i+1)]['total_present']
        totallate += dict_analysis['monthly'][str(i+1)]['total_late']
        totalabsent += dict_analysis['monthly'][str(i+1)]['total_absent']
        totalnodata += dict_analysis['monthly'][str(i+1)]['nodata']
        totalleave += dict_analysis['monthly'][str(i+1)]['total_leave']
    
    totaldata = totalabsent + totalpresent + totalleave + totallate
    dict_analysis['yearly'] = { 'total_present': totalpresent,
                                'total_absent': totalabsent,
                                'total_late' : totallate,
                                'total_nodata': totalnodata,
                                'total_leave' : totalleave,
                                'presentpct': round((totalpresent/totaldata)*100),
                                'latepct': round((totallate/totaldata)*100),
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
    print(dict_analysis)
    return dict_analysis

def load_yearly_all(df_presensi, df_leave, df_participants, year=2022) :
    arr_participant = df_participants['id'].values
    list_of_d = []
    for x in arr_participant :
        list_of_d.append(load_yearly(df_presensi, df_leave, x, year))
    
    dict_new = {}
    dict_new['monthly'] = {}
    for i in range(12) :
        dict_new['monthly'][str(i+1)] = {}
    for i in range(12) :
        total_present = 0
        total_late = 0
        total_leave = 0
        total_absent = 0
        total_nodata = 0
        for x in list_of_d :
            total_present += x['monthly'][str(i+1)]['total_present']
            total_late += x['monthly'][str(i+1)]['total_late']
            total_leave += x['monthly'][str(i+1)]['total_leave']
            total_absent += x['monthly'][str(i+1)]['total_absent']
            total_nodata += x['monthly'][str(i+1)]['nodata']
        totaldata = total_present + total_late + total_leave + total_absent + total_nodata
        dict_new['monthly'][str(i+1)]['total_present'] = total_present
        dict_new['monthly'][str(i+1)]['total_late'] = total_late
        dict_new['monthly'][str(i+1)]['total_leave'] = total_leave
        dict_new['monthly'][str(i+1)]['total_absent'] = total_absent
        dict_new['monthly'][str(i+1)]['nodata'] = total_nodata
        dict_new['monthly'][str(i+1)]['present_pct'] = round((total_present/totaldata)*100)
        dict_new['monthly'][str(i+1)]['late_pct'] = round((total_late/totaldata)*100)
        dict_new['monthly'][str(i+1)]['leave_pct'] = round((total_leave/totaldata)*100)
        dict_new['monthly'][str(i+1)]['absent_pct'] = round((total_absent/totaldata)*100)
        dict_new['monthly'][str(i+1)]['nodata_pct'] = round((total_nodata/totaldata)*100)
    
    totalpresent = 0
    totallate = 0
    totalabsent = 0
    totalnodata = 0
    totalleave = 0
    for i in range(12) :
        totalpresent += dict_new['monthly'][str(i+1)]['total_present']
        totallate += dict_new['monthly'][str(i+1)]['total_late']
        totalabsent += dict_new['monthly'][str(i+1)]['total_absent']
        totalnodata += dict_new['monthly'][str(i+1)]['nodata']
        totalleave += dict_new['monthly'][str(i+1)]['total_leave']
    
    totaldata = totalabsent + totalpresent + totalleave + totallate
    dict_new['yearly'] = { 'total_present': totalpresent,
                                'total_absent': totalabsent,
                                'total_late' : totallate,
                                'total_nodata': totalnodata,
                                'total_leave' : totalleave,
                                'presentpct': round((totalpresent/totaldata)*100),
                                'latepct': round((totallate/totaldata)*100),
                                'absentpct': round((totalabsent/totaldata)*100),
                                'leavepct': round((totalleave/totaldata)*100),
                                'nodatapct': round((totalnodata/totaldata)*100)
                            }
    
    return dict_new
        
 
def check_xls_file(columns) :
    arr_validation = ['Date', 'ID', 'Name', 'Status', 'First Check In', 'Last Check Out',
                      'Duration (Hour)', 'Break (Hour)', 'Actual (Hour)', 'Overtime (Hour)',
                      'Remark', 'Department', 'Branch']

    flag = True
    for i in range(len(arr_validation)) :
        if columns[i] != arr_validation[i] :
            flag = False

    return flag

def read_presensi_file(conn, filename) :
    df = pd.read_excel(filename)

    df.columns = df.iloc[6].values

    if check_xls_file(df.columns) == False :
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    # print(df.columns)
    df = df[7:]
    department_name = df['Department'].unique()
    id_dep = []
    for x in range(len(department_name)):
        id_dep.append(x)
        if pd.isna(department_name[x]) :
            department_name[x] = 'Other'
    data_department = {'id':id_dep, 'name':department_name}
    df_department = pd.DataFrame(data_department)

    participant_name = df['Name'].unique()
    id_participant = [i for i in range(len(participant_name))]
    id_department = ['non' for i in range(len(participant_name))]
    email = ['None' for i in range(len(participant_name))]
    # iter_d = 0
    for ind,val in df.iterrows() :
        if id_department[np.where(participant_name == val['Name'])[0][0]] == 'non' :
            if pd.isna(val['Department']) == False :
                id_department[np.where(participant_name == val['Name'])[0][0]] = id_dep[np.where(department_name == val['Department'])[0][0]]
            else :
                id_department[np.where(participant_name == val['Name'])[0][0]] = id_dep[np.where(department_name == 'Other')[0][0]]
            # iter_d += 1

    dict_participant = {'id_p':id_participant, 'Name':participant_name, 'dep_id':id_department, 'email':email}
    df_participant = pd.DataFrame(dict_participant)
    df_participant = load_participants(conn)

    partid_df = []
    for ind, val in df.iterrows():
        partid_df.append(df_participant[df_participant['name'] == val['Name']]['id'].values[0])

    df['Participant_id'] = partid_df
    df_presensi = df[['Date','Name', 'Participant_id', 'Status', 'First Check In', 'Last Check Out']]
    df_presensi.columns = ['Date', 'Name', 'Participant_id', 'status', 'firstcheckin', 'lastcheckout']

    return df_participant, df_department, df_presensi

def check_duplicate_data(df, source, subset_) :
    df_ = df[subset_]
    df_['Date'] = df_['Date'].astype(str)
    source_ = source[subset_]
    source_['Date'] = source_['Date'].astype(str)
    print(df_.describe())
    print(source_.dtypes)
    print(len(source_)," ", len(df_))
    arr_ = []
    for ind,val in df_.iterrows() :
        flag = False
        for comp_val in source_.values :
            inside_flag = True
            for i in range(len(val.values)) :
                if comp_val[i] != val.values[i] :
                    inside_flag = False
            if inside_flag :
                flag = True
                break
        arr_.append(flag)
    
    # print(df_.duplicated(keep=False).values)
    
    return arr_

def check_duplicate_data_leave(df, source, subset_) :
    df_ = df[subset_]
    df_['leave_from'] = df_['leave_from'].astype(str)
    df_['leave_to'] = df_['leave_to'].astype(str)
    source_ = source[subset_]
    source_['leave_from'] = source_['leave_from'].astype(str)
    source_['leave_to'] = source_['leave_to'].astype(str)
    print(df_.describe())
    print(source_.dtypes)
    print(len(source_)," ", len(df_))
    arr_ = []
    for ind,val in df_.iterrows() :
        flag = False
        for comp_val in source_.values :
            inside_flag = True
            for i in range(len(val.values)) :
                if comp_val[i] != val.values[i] :
                    inside_flag = False
            if inside_flag :
                flag = True
                break
        arr_.append(flag)
    
    # print(df_.duplicated(keep=False).values)
    
    return arr_

def import_presensi(conn, df, dup_action='replace') :
    if dup_action == 'replace' :
        cur = conn.cursor()
        cutted_df = df[df['duplicated']]
        for ind,val in cutted_df.iterrows():
            query = 'DELETE FROM presensi_table WHERE date="' + str(val['Date']) + '" AND participant_id=' + str(val['Participant_id']) + ' AND status="' + str(val['status'])+'"'
            cur.execute(query)
        conn.commit()
        print(cur.rowcount, "rows executed.")

        df['firstcheckin'] = pd.to_datetime(df['firstcheckin'], format='%I:%M %p').dt.strftime('%H:%M:%S')
        df['lastcheckout'] = pd.to_datetime(df['lastcheckout'], format='%I:%M %p').dt.strftime('%H:%M:%S')
        df = df.fillna(np.nan).replace([np.nan], [None])
        df = df[['Date','Participant_id','status','firstcheckin', 'lastcheckout']]
        
        sql = "INSERT INTO presensi_table (date, participant_id, status, firstcheckin, lastcheckout)  VALUES (%s, %s, %s, %s, %s)"
        values = []
        for ind,val in df.iterrows() :
            # print(val.values)
            values = tuple(val.values)
            cur.execute(sql, values)
        conn.commit()
        print(cur.rowcount, "rows executed.")

        return cur.rowcount
    else :
        cur = conn.cursor()
        df = df[~df['duplicated']]
        df['firstcheckin'] = pd.to_datetime(df['firstcheckin'], format='%I:%M %p').dt.strftime('%H:%M:%S')
        df['lastcheckout'] = pd.to_datetime(df['lastcheckout'], format='%I:%M %p').dt.strftime('%H:%M:%S')
        df = df[['Date','Participant_id','status','firstcheckin', 'lastcheckout']]
        df = df.fillna(np.nan).replace([np.nan], [None])
        print(df)
        
        sql = "INSERT INTO presensi_table (date, participant_id, status, firstcheckin, lastcheckout)  VALUES (%s, %s, %s, %s, %s)"
        values = []
        for ind,val in df.iterrows() :
            # print(val.values)
            values = tuple(val.values)
            cur.execute(sql, values)
        conn.commit()
        print(cur.rowcount, "rows executed.")

        return cur.rowcount

def check_xls_leave_file(columns):
    arr_validation = ['ID', 'Name', 'Applied At', 'Leave', 'From', 'To', 'For', 'Session',
       'Status', 'Emergency', 'Reason', 'Remark', 'Department', 'Branch',
       'Attachment']

    flag = True
    for i in range(len(arr_validation)) :
        if columns[i] != arr_validation[i] :
            flag = False

    return flag

def read_leave(filename, df_participant) :
    df = pd.read_excel(filename)

    df.columns = df.iloc[6].values
    
    df = df[7:]
    
    if check_xls_leave_file(df.columns) == False :
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    # print(df.columns)
    participant_id = []
    for ind,val in df.iterrows() :
        participant_id.append(df_participant[df_participant['name'] == val['Name']]['id'].values[0])
    # leave_id = [i for i in range(len(df_leave))]

    df_leave_tb = pd.DataFrame({'participant_id':participant_id, 
                                'leave_kind':df['Leave'].values,
                                'reason':df['Reason'].values,
                                'leave_from':df['From'].values,
                                'leave_to':df['To'].values,
                                'status':df['Status'].values})

    return df_leave_tb

def import_leave(conn, df, dup_action='replace') :
    cur = conn.cursor()
    if dup_action == 'replace' :
        cur = conn.cursor()
        cutted_df = df[df['duplicated']]
        for ind,val in cutted_df.iterrows():
            query = 'DELETE FROM leave_table WHERE participant_id=' + str(val['participant_id']) + ' AND reason="' + str(val['reason']) + '" AND leave_from="' + str(val['leave_from']) + '" AND leave_to="' + str(val['leave_to']) + '" AND status="' + str(val['status'])+'"'
            cur.execute(query)
        conn.commit()
        print(cur.rowcount, " rows executed.")

        df = df[['participant_id','leave_kind','reason','leave_from', 'leave_to','status']]
        leave_values = []
        for ind, val in df.iterrows():
            leave_values.append(tuple(val.values))
        
        sql = "INSERT INTO leave_table (participant_id, leave_kind, reason, leave_from, leave_to, status)  VALUES (%s, %s, %s, %s, %s, %s)"
        cur.executemany(sql, leave_values)
        conn.commit()
        print(cur.rowcount, "rows executed.")

        return cur.rowcount
    else :
        cur = conn.cursor()
        df = df[~df['duplicated']]
        df = df[['participant_id','leave_kind','reason','leave_from', 'leave_to','status']]
        leave_values = []
        for ind, val in df.iterrows():
            leave_values.append(tuple(val.values))
        
        sql = "INSERT INTO leave_table (participant_id, leave_kind, reason, leave_from, leave_to, status)  VALUES (%s, %s, %s, %s, %s, %s)"
        cur.executemany(sql, leave_values)
        conn.commit()
        print(cur.rowcount, "rows executed.")

        return cur.rowcount


def add_holiday(conn, dict_) :
    cur = conn.cursor()
    sql = "INSERT INTO tabel_libur (date, deskripsi) VALUES (%s, %s)"
    libur_values = (dict_['date'], dict_['description'])
    cur.execute(sql, libur_values)
    conn.commit()

    return cur.rowcount

def get_holidays(conn) :
    cur=conn.cursor()
    sql = "SELECT * FROM tabel_libur"
    cur.execute(sql)

    result = cur.fetchall()

    return pd.DataFrame(data=result, columns=['id', 'date', 'description'])

def delete_holiday(conn, id) :
    cur=conn.cursor()
    sql = "DELETE FROM tabel_libur WHERE id=" + str(id)

    cur.execute(sql)
    conn.commit()

    return cur.rowcount

