# pylint: disable=no-member
import flask
import json
import time
from collections import Counter
from flask import request, abort
from flask_cors import CORS

import sheets
import database

app = flask.Flask(__name__)
app.config["DEBUG"] = True
CORS(app)

creds = sheets.load_credentials()
sheets_api = sheets.get_sheets_api(creds)

conn = database.connect_db()
cursor = conn.cursor()

LEADERBOARD = None
count = 0
LOAD_TIME = time.time()

SPREADSHEETS = {
    '1SWRQGdd5ImD4kHmEgwX1O0wo2Nfhmb5a4YSRi2M15TY': 10,
    '1gO-4hcAuuZxTkgjQKqiRTOx3wQPGp-ArsVYoSNRE5tA': 5,
    '1UCnwrYmtv4GlrTkRxrIgSbkPJJLDkcUdhChj701LY3k': 7,
    '1AR7xNmKaNqaH7mQSGsZB4GzbNPiEd6E5Ms2zLAxLk8Y': 5
}

def exists(query):
    return query.fetchone()[0]

@app.route('/add', methods=['GET'])
def add_new_user():
    required_args = ('firstname', 'lastname', 'college', 'year', 'branch', 'phone')
    values = request.args
    for arg in required_args:
        if arg not in values:
            return json.dumps({
                'success': False,
                'message': "Invalid request."
            })

    query = cursor.execute(
        """
        select count(*) from User
        where phone = ?;
        """,
        (values['phone'],)    
    )
    if exists(query):
        return json.dumps({
            'success': False,
            'message': "A user with this phone number already exists."
        })

    initials = values['firstname'][0] + values['lastname'][0]
    counter = 1
    while True:
        referral = f"{initials}{counter:0>2}"
        query = cursor.execute(
            """
            select count(*) from User
            where referral = ?;
            """,
            (referral,)    
        )
        if exists(query):
            counter += 1
        else:
            break

    cursor.execute(
        """
        insert into User values
        (?, ?, ?, ?, ?, ?, ?);
        """,
        (
            values['phone'],
            referral,
            values['firstname'],
            values['lastname'],
            values['college'],
            values['year'],
            values['branch'],
        )
    )

    conn.commit()

    return json.dumps({
        'success': True,
        'message': "Referral Generated!\nReferral code: {}".format(referral)
    })

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    global LEADERBOARD
    global LOAD_TIME

    if LEADERBOARD and time.time()-LOAD_TIME < 60:
        return LEADERBOARD

    LOAD_TIME = time.time()
    global count
    count += 1
    referrals = {}
    for spreadsheet_id, col in SPREADSHEETS.items():
        result_body = (sheets_api
                       .spreadsheets()
                       .values()
                       .get(spreadsheetId=spreadsheet_id, range='A:T')
                       .execute())

        data = result_body.get('values', [])
        for row in data:
            if len(row) > col:
                phone = str(row[3]).strip('+').lstrip('0')
                if len(phone) > 10:
                    if phone.find('91') == 0:
                        phone = phone[2:]
                    phone = phone[:10]

                referral = str(row[col]).strip()
                if referral[:2].isalpha() and referral[2:].isdigit():
                    referrals.update({phone: referral.upper()})
    
    leaderboard = sorted([list(i) for i in Counter(referrals.values()).items()],
                         key=lambda x: x[1],
                         reverse=True)

    for index, user in enumerate(leaderboard):
        referral = user[0]
        query = cursor.execute(
            """
            select count(*) from User
            where referral = ?;
            """,
            (referral,)
        )
        if exists(query):
            query = cursor.execute(
                """
                select *
                from User
                where referral = ?;
                """,
                (referral,)
            )
            res = query.fetchone()[2:]
            name = f"{res[0].title()} {res[1].title()}"
            college = res[2]
            branch = f"{res[4]} branch"
            year_number = int(res[3])
            if year_number == 1:
                year = '1st year'
            elif year_number == 2:
                year = '2nd year'
            elif year_number == 3:
                year = '3rd year'
            else:
                year = f'{year_number}th year'
        else:
            name = college = year = branch = ''
        
        for info in (name, college, year, branch):
            leaderboard[index].append(info)

    
    LEADERBOARD = json.dumps({
        'referrals': referrals,
        'leaderboard': leaderboard,
        'count': count
    })
    return LEADERBOARD