from flask import Blueprint, render_template

bp = Blueprint("dashboard", __name__)


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/meetings")
def meetings():
    return render_template("meetings.html")


@bp.get("/clients")
def clients():
    return render_template("clients.html")


@bp.get("/matters")
def matters():
    return render_template("matters.html")


@bp.get("/personal")
def personal():
    return render_template("personal.html")
