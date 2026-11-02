import time
from functools import wraps

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session, current_app
)

from models import db, EmployeeQuery
from services.document_retriever import retrieve_relevant_chunks
from services.ai_service import generate_hr_response
from services.escalation import check_escalation


employee_bp = Blueprint("employee", __name__)


def employee_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))

        if session.get("user_role") != "employee":
            flash(
                "You do not have permission to access this page.",
                "danger"
            )
            return redirect(url_for("home"))

        return function(*args, **kwargs)

    return decorated_function


@employee_bp.route("/employee/dashboard")
@employee_required
def dashboard():

    recent_queries = (
        EmployeeQuery.query
        .filter_by(employee_id=session["user_id"])
        .order_by(EmployeeQuery.created_at.desc())
        .limit(5)
        .all()
    )

    total_queries = EmployeeQuery.query.filter_by(
        employee_id=session["user_id"]
    ).count()

    return render_template(
        "employee_dashboard.html",
        recent_queries=recent_queries,
        total_queries=total_queries
    )


@employee_bp.route("/employee/ask", methods=["GET", "POST"])
@employee_required
def ask_question():

    if request.method == "POST":

        question = request.form.get("question", "").strip()

        if not question:
            flash("Please enter your question.", "warning")
            return redirect(url_for("employee.ask_question"))

        if len(question) > 3000:
            flash(
                "Your question is too long. Please keep it under 3000 characters.",
                "warning"
            )
            return redirect(url_for("employee.ask_question"))

        total_start = time.perf_counter()

        try:
            retrieval_start = time.perf_counter()
            relevant_chunks = retrieve_relevant_chunks(question)

            retrieval_time = time.perf_counter() - retrieval_start

            current_app.logger.info(
                "[SmartHR] Document retrieval: %.2f seconds | Chunks: %d",
                retrieval_time,
                len(relevant_chunks)
            )

            should_escalate = False
            escalation_reason = None

            if not relevant_chunks:

                ai_response = (
                    "I could not find sufficient information in the "
                    "uploaded HR policies to answer your question. "
                    "Your question has been forwarded to the HR team "
                    "for further assistance."
                )

                should_escalate = True
                escalation_reason = (
                    "No relevant information was found in the uploaded HR policies."
                )

            else:

                ai_start = time.perf_counter()

                try:
                    ai_response = generate_hr_response(
                        question,
                        relevant_chunks
                    )

                    ai_time = time.perf_counter() - ai_start

                    current_app.logger.info(
                        "[SmartHR] Gemini response: %.2f seconds",
                        ai_time
                    )

                except Exception:

                    ai_time = time.perf_counter() - ai_start

                    current_app.logger.exception(
                        "[SmartHR] Gemini failed. "
                        "Saving the question for HR assistance."
                    )

                    ai_response = (
                        "We are currently unable to generate an AI response "
                        "because the AI service is temporarily unavailable. "
                        "Your question has been forwarded to the HR team. "
                        "Please check your query status later for an update."
                    )

                    should_escalate = True
                    escalation_reason = (
                        "AI response could not be generated because "
                        "the Gemini service was unavailable."
                    )

            if not should_escalate:

                escalation_start = time.perf_counter()

                should_escalate, escalation_reason = check_escalation(
                    question
                )

                escalation_time = time.perf_counter() - escalation_start

                current_app.logger.info(
                    "[SmartHR] Escalation check: %.2f seconds",
                    escalation_time
                )

            database_start = time.perf_counter()

            new_query = EmployeeQuery(
                employee_id=session["user_id"],
                question=question,
                ai_response=ai_response,
                status="escalated" if should_escalate else "pending",
                is_escalated=should_escalate,
                escalation_reason=escalation_reason
            )

            db.session.add(new_query)
            db.session.commit()

            database_time = time.perf_counter() - database_start

            current_app.logger.info(
                "[SmartHR] Database save: %.2f seconds",
                database_time
            )

            total_time = time.perf_counter() - total_start

            current_app.logger.info(
                "[SmartHR] TOTAL PROCESSING TIME: %.2f seconds",
                total_time
            )

            return redirect(
                url_for(
                    "employee.view_query",
                    query_id=new_query.id
                )
            )

        except Exception:

            db.session.rollback()

            current_app.logger.exception(
                "[SmartHR] Unable to process employee question."
            )

            flash(
                "We could not process your question right now. "
                "Please try again.",
                "danger"
            )

    return render_template("ask_question.html")


@employee_bp.route("/employee/query/<int:query_id>")
@employee_required
def view_query(query_id):

    employee_query = EmployeeQuery.query.filter_by(
        id=query_id,
        employee_id=session["user_id"]
    ).first_or_404()

    return render_template(
        "view_query.html",
        employee_query=employee_query
    )


@employee_bp.route("/employee/my-queries")
@employee_required
def my_queries():

    queries = (
        EmployeeQuery.query
        .filter_by(employee_id=session["user_id"])
        .order_by(EmployeeQuery.created_at.desc())
        .all()
    )

    return render_template(
        "my_queries.html",
        queries=queries
    )