
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect
from plotters import disputesGraph, stakesJurorsGraph, disputesbyCourtGraph
from bin.KlerosDB import Visitor, Court, Config, Juror, Dispute, Vote
from bin.Kleros import StakesKleros
from bin import db
from datetime import datetime
import logging

# Elastic Beanstalk initalization
application = Flask(__name__)
application.config.from_object('config')
application.debug=True
db.init_app(application)
logger = logging.getLogger()

@application.route('/')
def index():
    Visitor().addVisit('dashboard')
    startTime = datetime.now()
    pnkStaked = Court(id=0).juror_stats()['total']
    tokenSupply =  float(Config().get('token_supply'))
    activeJurors = len(Juror.stakedJurors());
    drawnJurors = len(Juror.list())
    retention =  Juror.retention() / drawnJurors
    adoption = len(Juror.adoption())
    ruledCases = Dispute().ruledCases
    openCases = Dispute().openCases
    mostActiveCourt = Court.query.filter(Court.id==list(Dispute.mostActiveCourt().keys())[0]).first().name,
    pnkPrice = float(Config.get('PNKprice'))
    courtTable = StakesKleros.getCourtInfoTable()
    for c in courtTable.keys():
        courtTable[c]['Min Stake in USD'] = courtTable[c]['Min Stake']*pnkPrice
    logger.info(f"Load all the data from the DB takes: {(datetime.now()-startTime).seconds} seconds.")
    return render_template('main.html',
                           last_update= Config.get('updated'),
                           disputes= Dispute.query.order_by(Dispute.id.desc()).first().id,
                           activeJurors= activeJurors,
                           jurorsdrawn = drawnJurors,
                           retention= retention,
                           adoption= adoption,
                           most_active_court = mostActiveCourt[0],
                           cases_closed = ruledCases,
                           cases_rulling = openCases,
                           tokenSupply= tokenSupply,
                           pnkStaked= pnkStaked,
                           pnkStakedPercent= pnkStaked/tokenSupply,
                           ethPrice= float(Config.get('ETHprice')),
                           pnkPrice= pnkPrice,
                           pnkPctChange = float(Config.get('PNKpctchange24h'))/100,
                           pnkVol24= float(Config.get('PNKvolume24h')),
                           pnkCircSupply= float(Config.get('PNKcirculating_supply')),
                           courtTable = courtTable
                           )


@application.route('/support/')
def support():
    Visitor().addVisit('support')
    return render_template('support.html',
                           last_update= Config.get('updated'))

@application.route('/odds/', methods=['GET','POST'])
def odds():
    Visitor().addVisit('odds')
    pnkStaked = 100000
    if request.method == 'POST':
        # Form being submitted; grab data from form.
        try:
            pnkStaked = int(request.form['pnkStaked'])
        except:
            pnkStaked = 100000

    return render_template('odds.html',
                           last_update= Config.get('updated'),
                           pnkStaked= pnkStaked,
                           courtChances= StakesKleros.getAllCourtChances(pnkStaked))

@application.route('/kleros-map/')
def maps():
    Visitor().addVisit('map')
    return render_template('kleros-map.html',
                            last_update= Config.get('updated')
                            )

@application.route('/visitorMetrics/')
def visitorMetrics():
    visitors = Visitor()
    return render_template('visitors.html',
                           home=visitors.dashboard,
                           odds=visitors.odds,
                           map=visitors.map,
                           support=visitors.support,
                           last_update= Config.get('updated'),
                           )


@application.route('/dispute/', methods=['POST','GET'])
def dispute():
    try:
        id = request.form['disputeID']
    except:
        id = Dispute.query.order_by(Dispute.id.desc()).first().id
    vote_count = {}
    dispute = Dispute.query.get(id)
    dispute.rounds = dispute.rounds()
    for r in dispute.rounds:
        vote_count[r.id] = {'Yes':0,'No':0,'Refuse':0,'Pending':0}
        r.votes = r.votes()
        for v in r.votes:
            if v.vote == 1:
                if v.choice == 1:
                    v.vote_str = 'Yes'
                    vote_count[r.id]['Yes'] +=1
                elif v.choice == 2:
                    v.vote_str = 'No'
                    vote_count[r.id]['No'] +=1
                elif v.choice == 0:
                    v.vote_str = 'Refuse'
                    vote_count[r.id]['Refuse'] +=1
            else: 
                v.vote_str = 'Pending'
                vote_count[r.id]['Pending'] +=1
    return render_template('dispute.html',
                           dispute=dispute,
                           vote_count=vote_count,
                           last_update= Config.get('updated'),
                           )


@application.route('/updateDB/', methods=['POST','GET'])
def updateDB():
    from bin.dbModule import fillDB
    fillDB()
    return render_template("404.html")

@application.errorhandler(404)
def not_found(e):
    Visitor().addVisit('unknown')
    return render_template("404.html")


if __name__ == "__main__":
    application.run(debug=True)