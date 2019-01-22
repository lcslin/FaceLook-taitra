from flask import Flask
import pandas as pd
import requests
import bs4 as bs
from bs4 import BeautifulSoup as soup
from flask import jsonify
from flask import request
import pymssql  


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


@app.route('/emp/<query_text>')
def query_emp(query_text):
    if query_text == '':
        return 'Try something, please'
    if '@' in query_text:
        query_text = query_text.split('@')[0]
   
    parser = 'html5lib'
    payload_emp = {}
    result_emp = ''

    # for the drop down queries
    department = {}
    title = {}
    gender = {}

    with requests.session() as emp:

        url = "http://mail.taitra.org.tw/EmployeeQuery"
        try:
            r = emp.get(url)
        except requests.exceptions.ConnectionError:
            r.status_code = 'Connection refused'

        soup = bs.BeautifulSoup(r.content, parser)
        input_form = {}
        all_input = soup.find_all('input')
        input_form['__VIEWSTATE'] = all_input[0]['value']
        input_form['__VIEWSTATEGENERATOR'] = all_input[1]['value']
        for i in soup.find_all('select'):
            #職級
            if i['id'] == 'ctl00_ContentPlaceHolder1_drpJobLevel': 
                for j in i.find_all('option'):
                    title[j.text] = j['value']
            #部門 onkeyup="dept2Changed(this)
            if i['id'] == 'ctl00_ContentPlaceHolder1_drpDept1':
                for j in i.find_all('option'):
                    department[j.text] = j['value']
            #性別
            if i['id'] == 'ctl00_ContentPlaceHolder1_drpGender':
                for j in i.find_all('option'):
                    gender[j['value']] = j.text

        payload_emp[0] = {
            '__ASYNCPOST'	:	'TRUE'	,
            '__EVENTARGUMENT'	:	''	,
            '__EVENTTARGET'	:	'ctl00$ContentPlaceHolder1$UpdatePanel1'	,
            '__VIEWSTATE'	:	'',
            '__VIEWSTATEGENERATOR'	:	all_input[1]['value'],
            'ctl00$ContentPlaceHolder1$drpDept1'	:''	,
            'ctl00$ContentPlaceHolder1$drpDept2'	:'全部'	,
            'ctl00$ContentPlaceHolder1$drpGender'	:'不拘'	,
            'ctl00$ContentPlaceHolder1$drpJobLevel'	:'全部'
        }

        payload_emp[1] = dict(payload_emp[0])
        payload_emp[2] = dict(payload_emp[0])
        payload_emp[3] = dict(payload_emp[0])
        payload_emp[4] = dict(payload_emp[0])


        payload_emp[0]['ctl00$ContentPlaceHolder1$tboEMPName'] = query_text        
        payload_emp[1]['ctl00$ContentPlaceHolder1$tboExtNo'] = query_text
        payload_emp[2]['ctl00$ContentPlaceHolder1$tboEmail'] = query_text
        payload_emp[3]['ctl00$ContentPlaceHolder1$tboEMPNO'] = query_text

        query_result = {}
	
        if ('台貿' == query_text) or ('台貿中心' == query_text) or ('台灣貿易中心' == query_text) or ('辦事處' == query_text) or ('代表處' == query_text):
            query_fdept_1 = '台貿'
            query_fdept_2 = '台灣貿易'
            query_fdept_3 = '代表'
        else:
            query_fdept_1 = 'xxxxxxxxxxxxx'
            query_fdept_2 = 'xxxxxxxxxxxxx'
            query_fdept_3 = 'xxxxxxxxxxxxx'
 
        for k,v in department.items():    
            if query_text in k or query_fdept_1 in k or query_fdept_2 in k or query_fdept_3 in k:
                payload_emp[4]['ctl00$ContentPlaceHolder1$drpDept1'] = department[k]
                result_emp = emp.post(url, data=payload_emp[4])
                result_emp = bs.BeautifulSoup(result_emp.content, parser)

                for j in result_emp.find_all('tr')[2:]:
                    tmp = []
                    try:
                        dept, team = j.find_all('td')[0].contents[0], j.find_all('td')[0].contents[2] 
                    except Exception:
                        dept, team = j.find_all('td')[0].contents[0], '' 
                    tmp.append(dept)
                    tmp.append(team)
                    for k in j.find_all('td')[1:]:
                        tmp.append(k.text)
                    query_result[j.find_all('td')[4].text] = tmp

        for i in range(4):
            result_emp = emp.post(url, data=payload_emp[i])
            result_emp = bs.BeautifulSoup(result_emp.content, parser)

            for j in result_emp.find_all('tr')[2:]:
                tmp = []
                try:
                    dept, team = j.find_all('td')[0].contents[0], j.find_all('td')[0].contents[2] 
                except Exception:
                    dept, team = j.find_all('td')[0].contents[0], '' 
                tmp.append(dept)
                tmp.append(team)
                for k in j.find_all('td')[1:]:
                    tmp.append(k.text)
                query_result[j.find_all('td')[4].text] = tmp

        df_result = pd.DataFrame(query_result, index = \
                  ['dept','team','name','title','gender','id','email','ext']) 

        df_result_t = pd.merge(df_result.T, df_workPlace, how='left', left_on='email', right_on='email').T
        df_result_t.columns = df_result_t.loc['id']
        return df_result_t.to_json(force_ascii=False)
    
#         return pd.DataFrame(query_result, index = ['dept','team','name','title','gender','id','email','ext']).to_json(force_ascii=False)
        

@app.route('/dept/', defaults={'query_text': ''})
@app.route('/dept/<query_text>')
def query_dept(query_text):
    parser = 'html5lib'
    try:
        query_text
    except:
        return False
    payload_emp = {}
    result_emp = {}
    department = {}

    with requests.session() as emp:

        url = "http://mail.taitra.org.tw/EmployeeQuery"
        r = emp.get(url)

        soup = bs.BeautifulSoup(r.content, parser)
        input_form = {}
        all_input = soup.find_all('input')
        input_form['__VIEWSTATE'] = all_input[0]['value']
        input_form['__VIEWSTATEGENERATOR'] = all_input[1]['value']

        for i in soup.find_all('select'):
            #部門 onkeyup="dept2Changed(this)
            if i['id'] == 'ctl00_ContentPlaceHolder1_drpDept1':
                for j in i.find_all('option'):
                    department[j.text] = j['value']
        payload_emp = {
            '__ASYNCPOST'	:	'TRUE'	,
            '__EVENTARGUMENT'	:	''	,
            '__EVENTTARGET'	:	'ctl00$ContentPlaceHolder1$UpdatePanel1'	,
            '__VIEWSTATE'	:	'',
            '__VIEWSTATEGENERATOR'	:	all_input[1]['value'],
            'ctl00$ContentPlaceHolder1$drpDept1'	:	''	,
            'ctl00$ContentPlaceHolder1$drpDept2'	:	'全部'	,
            'ctl00$ContentPlaceHolder1$drpGender'	:	'不拘'	,
            'ctl00$ContentPlaceHolder1$drpJobLevel'	:	'全部'	,
            'ctl00$ContentPlaceHolder1$tboEMPNO'	:	query_text
        }
        result_emp = emp.post(url, data=payload_emp)
        result_emp = bs.BeautifulSoup(result_emp.content, parser)

    query_result = {}
    for j in result_emp.find_all('tr')[2:]:
        tmp = []
        try:
            dept, team = j.find_all('td')[0].contents[0], j.find_all('td')[0].contents[2] 
        except Exception:
            dept, team = j.find_all('td')[0].contents[0], '' 
        tmp.append(dept)
        tmp.append(team)
        for k in j.find_all('td')[1:]:
            tmp.append(k.text)
        query_result[j.find_all('td')[4].text] = tmp

    query_dept = list(query_result.values())[0][0]
    query_team = list(query_result.values())[0][1]

    dict_team = {}

    #pd.DataFrame(department.items())

    url_team = 'http://mail.taitra.org.tw/subDept'
    if dept in department:
        pay_load = {'deptName' : department[dept]}
    else:
        department[dept] = ''
        pay_load = {'deptName' : ''}
        
    r = requests.session()
    rs = r.post(url_team, pay_load)

    #無組者未處理

    list_team = rs.content.decode('utf-8').split()[1:]
    for i in range(0, len(list_team),2):
        dict_team[list_team[i+1]] = list_team[i]
    with requests.session() as emp:
        url = "http://mail.taitra.org.tw/EmployeeQuery"
        r = emp.get(url)

        soup = bs.BeautifulSoup(r.content, parser)
        input_form = {}
        all_input = soup.find_all('input')
        input_form['__VIEWSTATE'] = all_input[0]['value']
        input_form['__VIEWSTATEGENERATOR'] = all_input[1]['value']

        # 0 名字

        payload_emp = {
            '__ASYNCPOST'	:	'TRUE'	,
            '__EVENTARGUMENT'	:	''	,
            '__EVENTTARGET'	:	'ctl00$ContentPlaceHolder1$UpdatePanel1'	,
            '__VIEWSTATE'	:	'',
            '__VIEWSTATEGENERATOR'	:	all_input[1]['value'],
            'ctl00$ContentPlaceHolder1$drpDept1'	:	''	,
            'ctl00$ContentPlaceHolder1$drpDept2'	:	'全部'	,
            'ctl00$ContentPlaceHolder1$drpGender'	:	'不拘'	,
            'ctl00$ContentPlaceHolder1$drpJobLevel'	:	'全部'
        }
        payload_emp['ctl00$ContentPlaceHolder1$drpDept1'] = department[dept]
        try:
            payload_emp['ctl00$ContentPlaceHolder1$drpDept2'] = dict_team[team]
            payload_emp['ctl00$ContentPlaceHolder1$hidDept2Value'] = dict_team[team]
        except:
            payload_emp['ctl00$ContentPlaceHolder1$drpDept2'] = ''
            payload_emp['ctl00$ContentPlaceHolder1$hidDept2Value'] = ''
        result_emp = emp.post(url, data=payload_emp)
        result_emp = bs.BeautifulSoup(result_emp.content, parser)

    query_result = {}
    #for i in range(3,5):

    for j in result_emp.find_all('tr')[2:]:
        tmp = []
        try:
            dept, team = j.find_all('td')[0].contents[0], j.find_all('td')[0].contents[2] 
        except Exception:
            dept, team = j.find_all('td')[0].contents[0], '' 
        tmp.append(dept)
        tmp.append(team)
        for k in j.find_all('td')[1:]:
            tmp.append(k.text)
        query_result[j.find_all('td')[4].text] = tmp
        
    df_result = pd.DataFrame(query_result, index = \
              ['dept','team','name','title','gender','id','email','ext']) 

    df_result_t = pd.merge(df_result.T, df_workPlace, how='left', left_on='email', right_on='email').T
    df_result_t.columns = df_result_t.loc['id']
    return df_result_t.to_json(force_ascii=False)
        
        
#     return pd.DataFrame(query_result, index = \
#             ['dept','team','name','title','gender','id','email','ext']).to_json(force_ascii=False)
