from flask import render_template, jsonify, Blueprint, redirect, url_for, request, session
from sqlalchemy.sql.expression import union_all

from CTFd.utils import unix_time, authed, get_config
from CTFd.models import db, Students, Solves, Awards, Challenges, Teams

scoreboard = Blueprint('scoreboard', __name__)


def get_standings(admin=False, count=None):
    user = Students.query.filter_by(id=session['id']).first()

    score = db.func.sum(Challenges.value).label('score')
    date = db.func.max(Solves.date).label('date')
    scores = db.session.query(Solves.studentid.label('studentid'), score, date).join(Challenges).group_by(Solves.studentid)
    awards = db.session.query(Awards.studentid.label('studentid'), db.func.sum(Awards.value).label('score'), db.func.max(Awards.date).label('date')) \
        .group_by(Awards.studentid)
    results = union_all(scores, awards).alias('results')
    sum = db.session.query(results.columns.studentid, db.func.sum(results.columns.score).label('score'), db.func.max(results.columns.date).label('date')) \
        .group_by(results.columns.studentid).subquery()
    sumscores = db.session.query(Teams.id.label('teamid'), Teams.name.label('name'),
                             db.func.sum(sum.columns.score).label('score'),
                             db.func.max(sum.columns.date).label('date')).join(Students) \
        .filter(Students.id == sum.columns.studentid, Students.teamid == Teams.id, Students.sectionid == user.sectionid) \
        .group_by(Teams.id).subquery()
    if admin:
        standings_query = db.session.query(Teams.id.label('teamid'), Teams.name.label('name'), sumscores.columns.score) \
                                    .join(sumscores, Teams.id == sumscores.columns.teamid) \
                                    .order_by(sumscores.columns.score.desc(), sumscores.columns.date)
    else:
        standings_query = db.session.query(Teams.id.label('teamid'), Teams.name.label('name'), sumscores.columns.score) \
                                    .join(sumscores, Teams.id == sumscores.columns.teamid) \
                                    .order_by(sumscores.columns.score.desc(), sumscores.columns.date)
    if count is None:
        standings = standings_query.all()
    else:
        standings = standings_query.limit(count).all()
    db.session.close()
    return standings


@scoreboard.route('/scoreboard')
def scoreboard_view():
    if get_config('view_scoreboard_if_authed') and not authed():
        return redirect(url_for('auth.login', next=request.path))
    standings = get_standings()
    return render_template('scoreboard.html', teams=standings)


@scoreboard.route('/scores')
def scores():
    if get_config('view_scoreboard_if_authed') and not authed():
        return redirect(url_for('auth.login', next=request.path))
    standings = get_standings()
    json = {'standings': []}
    for i, x in enumerate(standings):
        json['standings'].append({'pos': i + 1, 'id': x.studentid, 'team': x.name, 'score': int(x.score)})
    return jsonify(json)


@scoreboard.route('/top/<int:count>')
def topteams(count):
    if get_config('view_scoreboard_if_authed') and not authed():
        return redirect(url_for('auth.login', next=request.path))
    try:
        count = int(count)
    except ValueError:
        count = 10
    if count > 20 or count < 0:
        count = 10

    user = Students.query.filter_by(id=session['id']).first()

    json = {'scores': {}}
    standings = get_standings(count=count)

    for team in standings:
        solves = db.session.query(Solves).join(Students).filter(Students.teamid == team.teamid, Students.sectionid == user.sectionid).all()
        awards = db.session.query(Awards).join(Students).filter(Students.teamid == team.teamid, Students.sectionid == user.sectionid).all()
        json['scores'][team.name] = []
        for x in solves:
            json['scores'][team.name].append({
                'chal': x.chalid,
                'student.id': x.studentid,
                'value': x.chal.value,
                'time': unix_time(x.date)
            })
        for award in awards:
            json['scores'][team.name].append({
                'chal': None,
                'student.id': award.studentid,
                'value': award.value,
                'time': unix_time(award.date)
            })
        json['scores'][team.name] = sorted(json['scores'][team.name], key=lambda k: k['time'])
    return jsonify(json)
