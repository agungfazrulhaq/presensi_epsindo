from flask import Flask, render_template

app = Flask(__name__)
twelvemonth = ['January','February','March','April','May']

@app.route('/')
def index():
    page_info = {'page':'index', 'months':twelvemonth}
    return render_template('index.html', result = page_info)

@app.route('/monthly/<month>')
def monthly(month='January'):
    page_info = {'page':'monthly', 'month':month}
    return render_template('monthly.html', result = page_info)

@app.route('/importdata')
def import_data():
    page_info = {'page':'importdata', 'months':twelvemonth}
    return render_template('importdata.html', result=page_info)