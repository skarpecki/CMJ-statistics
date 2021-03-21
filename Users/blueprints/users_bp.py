from flask import Blueprint, request, render_template, redirect
from service import users as users_srvc

bp = Blueprint('users', __name__)


@bp.route("/", methods=['GET', 'POST'])
def users():
    if request.method == "POST":
        data = dict(request.form.to_dict())
        users_srvc.insert_athlete(data)
        return redirect("https://athletes-dashboard-306517.ew.r.appspot.com/index")
    else:
        return render_template("add-users.html")
