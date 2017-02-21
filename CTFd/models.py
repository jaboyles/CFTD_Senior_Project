import datetime
import hashlib
import json
from socket import inet_aton, inet_ntoa
from struct import unpack, pack, error as struct_error

from flask_sqlalchemy import SQLAlchemy
from passlib.hash import bcrypt_sha256
from sqlalchemy.exc import DatabaseError


def sha512(string):
    return hashlib.sha512(string).hexdigest()


def ip2long(ip):
    return unpack('!i', inet_aton(ip))[0]


def long2ip(ip_int):
    try:
        return inet_ntoa(pack('!i', ip_int))
    except struct_error:
        # Backwards compatibility with old CTFd databases
        return inet_ntoa(pack('!I', ip_int))


db = SQLAlchemy()


class Pages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    route = db.Column(db.String(80), unique=True)
    html = db.Column(db.Text)

    def __init__(self, route, html):
        self.route = route
        self.html = html

    def __repr__(self):
        return "<Pages {0} for challenge {1}>".format(self.tag, self.chal)


class Containers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    buildfile = db.Column(db.Text)

    def __init__(self, name, buildfile):
        self.name = name
        self.buildfile = buildfile

    def __repr__(self):
        return "<Container ID:(0) {1}>".format(self.id, self.name)


class Challenges(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    description = db.Column(db.Text)
    value = db.Column(db.Integer)
    category = db.Column(db.String(80))
    flags = db.Column(db.Text)
    hidden = db.Column(db.Boolean)

    def __init__(self, name, description, value, category, flags):
        self.name = name
        self.description = description
        self.value = value
        self.category = category
        self.flags = json.dumps(flags)

    def __repr__(self):
        return '<chal %r>' % self.name


class Awards(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    studentid = db.Column(db.Integer, db.ForeignKey('students.id'))
    name = db.Column(db.String(80))
    description = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    value = db.Column(db.Integer)
    category = db.Column(db.String(80))
    icon = db.Column(db.Text)

    def __init__(self, studentid, name, value):
        self.studentid = studentid
        self.name = name
        self.value = value

    def __repr__(self):
        return '<award %r>' % self.name


class Tags(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chal = db.Column(db.Integer, db.ForeignKey('challenges.id'))
    tag = db.Column(db.String(80))

    def __init__(self, chal, tag):
        self.chal = chal
        self.tag = tag

    def __repr__(self):
        return "<Tag {0} for challenge {1}>".format(self.tag, self.chal)


class Files(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chal = db.Column(db.Integer, db.ForeignKey('challenges.id'))
    location = db.Column(db.Text)

    def __init__(self, chal, location):
        self.chal = chal
        self.location = location

    def __repr__(self):
        return "<File {0} for challenge {1}>".format(self.location, self.chal)


class Keys(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chal = db.Column(db.Integer, db.ForeignKey('challenges.id'))
    key_type = db.Column(db.Integer)
    flag = db.Column(db.Text)

    def __init__(self, chal, flag, key_type):
        self.chal = chal
        self.flag = flag
        self.key_type = key_type

    def __repr__(self):
        return self.flag


class Sections(db.Model):
    sectionNumber = db.Column(db.Integer, primary_key=True)
    courseNumber = db.Column(db.Integer)

    def __init__(self, sectionNumber, courseNumber):
        self.sectionNumber = sectionNumber
        self.courseNumber = courseNumber


class Teams(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    sectionNumber = db.Column(db.Integer, db.ForeignKey('sections.sectionNumber'))

    def __init__(self, name, sectionid):
        self.name = name
        self.sectionNumber = sectionid

    def score(self):
        students = Students.objects.filter(teamid=self.id)
        sum = 0
        for student in students:
            sum += student.score

        return sum

    def num_students(self):
        return Students.objects.filter(teamid=self.id)

class Students(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    email = db.Column(db.String(128), unique=True)
    teamid = db.Column(db.Integer, db.ForeignKey('teams.id'))
    password = db.Column(db.String(128))
    bracket = db.Column(db.String(32))
    banned = db.Column(db.Boolean, default=False)
    verified = db.Column(db.Boolean, default=False)
    admin = db.Column(db.Boolean, default=False)
    joined = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, name, email, password, teamid):
        self.name = name
        self.email = email
        self.password = bcrypt_sha256.encrypt(str(password))
        self.teamid = teamid

    def __repr__(self):
        return '<student %r>' % self.name

    def score(self):
        score = db.func.sum(Challenges.value).label('score')
        student = db.session.query(Solves.studentid, score).join(Students).join(Challenges).filter(Students.banned == False, Students.id == self.id).group_by(Solves.studentid).first()
        award_score = db.func.sum(Awards.value).label('award_score')
        award = db.session.query(award_score).filter_by(studentid=self.id).first()
        if student:
            return int(student.score or 0) + int(award.award_score or 0)
        else:
            return 0

    def place(self):
        score = db.func.sum(Challenges.value).label('score')
        quickest = db.func.max(Solves.date).label('quickest')
        students = db.session.query(Solves.studentid).join(Students).join(Challenges).filter(Students.banned == False).group_by(Solves.studentid).order_by(score.desc(), quickest).all()
        # http://codegolf.stackexchange.com/a/4712
        try:
            i = students.index((self.id,)) + 1
            k = i % 10
            return "%d%s" % (i, "tsnrhtdd"[(i / 10 % 10 != 1) * (k < 4) * k::4])
        except ValueError:
            return 0


class Solves(db.Model):
    __table_args__ = (db.UniqueConstraint('chalid', 'studentid'), {})
    id = db.Column(db.Integer, primary_key=True)
    chalid = db.Column(db.Integer, db.ForeignKey('challenges.id'))
    studentid = db.Column(db.Integer, db.ForeignKey('students.id'))
    ip = db.Column(db.Integer)
    flag = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    student = db.relationship('Students', foreign_keys="Solves.studentid", lazy='joined')
    chal = db.relationship('Challenges', foreign_keys="Solves.chalid", lazy='joined')
    # value = db.Column(db.Integer)

    def __init__(self, chalid, studentid, ip, flag):
        self.ip = ip2long(ip)
        self.chalid = chalid
        self.studentid = studentid
        self.flag = flag
        # self.value = value

    def __repr__(self):
        return '<solves %r>' % self.chal


class WrongKeys(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chalid = db.Column(db.Integer, db.ForeignKey('challenges.id'))
    studentid = db.Column(db.Integer, db.ForeignKey('students.id'))
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    flag = db.Column(db.Text)
    chal = db.relationship('Challenges', foreign_keys="WrongKeys.chalid", lazy='joined')

    def __init__(self, studentid, chalid, flag):
        self.studentid = studentid
        self.chalid = chalid
        self.flag = flag

    def __repr__(self):
        return '<wrong %r>' % self.flag


class Tracking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.BigInteger)
    student = db.Column(db.Integer, db.ForeignKey('students.id'))
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, ip, student):
        self.ip = ip2long(ip)
        self.student = student

    def __repr__(self):
        return '<ip %r>' % self.student


class Config(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.Text)
    value = db.Column(db.Text)

    def __init__(self, key, value):
        self.key = key
        self.value = value
