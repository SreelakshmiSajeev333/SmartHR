from datetime import datetime, timezone
from functools import wraps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from models import db, EmployeeQuery


hr_queries_bp = Blueprint("hr_queries", __name__)


def hr_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))

        if session.get("user_role") != "hr":
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for("home"))

        return function(*args, **kwargs)

    return decorated_function


@hr_queries_bp.route("/hr/queries")
@hr_required
def manage_queries():
    status_filter = request.args.get("status", "").strip()

    query = EmployeeQuery.query

    if status_filter in ["pending", "escalated", "resolved"]:
        query = query.filter_by(status=status_filter)

    all_queries = query.order_by(
        EmployeeQuery.created_at.desc()
    ).all()

    return render_template(
        "hr_queries.html",
        queries=all_queries,
        status_filter=status_filter
    )


@hr_queries_bp.route("/hr/query/<int:query_id>", methods=["GET", "POST"])
@hr_required
def view_query(query_id):
    employee_query = EmployeeQuery.query.get_or_404(query_id)

    if request.method == "POST":
        hr_response = request.form.get("hr_response", "").strip()

        if not hr_response:
            flash("Please enter a response.", "warning")
            return redirect(
                url_for("hr_queries.view_query", query_id=query_id)
            )

        employee_query.hr_response = hr_response
        employee_query.assigned_hr_id = session["user_id"]
        employee_query.status = "resolved"
        employee_query.updated_at = datetime.now(timezone.utc)
        employee_query.resolved_at = datetime.now(timezone.utc)

        db.session.commit()

        flash("Your response has been saved and the query is resolved.", "success")

        return redirect(url_for("hr_queries.manage_queries"))

    return render_template(
        "hr_view_query.html",
        employee_query=employee_query
    )