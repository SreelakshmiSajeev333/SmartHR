import os
import uuid
from functools import wraps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    current_app
)
from werkzeug.utils import secure_filename

from models import db, HRPolicy, DocumentChunk, EmployeeQuery
from services.pdf_processor import (
    extract_text_from_pdf,
    split_text_into_chunks
)


hr_bp = Blueprint("hr", __name__)

ALLOWED_EXTENSIONS = {"pdf"}


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


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@hr_bp.route("/hr/dashboard")
@hr_required
def dashboard():
    total_employees = EmployeeQuery.query.with_entities(
        EmployeeQuery.employee_id
    ).distinct().count()

    total_queries = EmployeeQuery.query.count()

    escalated_queries = EmployeeQuery.query.filter_by(
        is_escalated=True
    ).count()

    pending_queries = EmployeeQuery.query.filter_by(
        status="pending"
    ).count()

    recent_queries = (
        EmployeeQuery.query
        .order_by(EmployeeQuery.created_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "hr_dashboard.html",
        total_employees=total_employees,
        total_queries=total_queries,
        escalated_queries=escalated_queries,
        pending_queries=pending_queries,
        recent_queries=recent_queries
    )


@hr_bp.route("/hr/policies")
@hr_required
def policies():
    all_policies = (
        HRPolicy.query
        .filter_by(is_active=True)
        .order_by(HRPolicy.uploaded_at.desc())
        .all()
    )

    return render_template(
        "hr_policies.html",
        policies=all_policies
    )


@hr_bp.route("/hr/upload-policy", methods=["GET", "POST"])
@hr_required
def upload_policy():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        uploaded_file = request.files.get("policy_file")

        if not title or not uploaded_file or not uploaded_file.filename:
            flash("Please provide a policy title and PDF file.", "warning")
            return redirect(url_for("hr.upload_policy"))

        if not allowed_file(uploaded_file.filename):
            flash("Only PDF files are allowed.", "danger")
            return redirect(url_for("hr.upload_policy"))

        original_filename = secure_filename(uploaded_file.filename)

        if not original_filename:
            flash("Invalid file name.", "danger")
            return redirect(url_for("hr.upload_policy"))

        stored_filename = f"{uuid.uuid4().hex}.pdf"
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        file_path = os.path.join(upload_folder, stored_filename)

        try:
            uploaded_file.save(file_path)

            extracted_text = extract_text_from_pdf(file_path)
            chunks = split_text_into_chunks(extracted_text)

            if not chunks:
                raise ValueError("No readable text was found in this PDF.")

            policy = HRPolicy(
                title=title,
                original_filename=original_filename,
                stored_filename=stored_filename,
                extracted_text=extracted_text,
                uploaded_by=session["user_id"]
            )

            db.session.add(policy)
            db.session.flush()

            for index, chunk_content in enumerate(chunks):
                document_chunk = DocumentChunk(
                    policy_id=policy.id,
                    chunk_index=index,
                    content=chunk_content
                )
                db.session.add(document_chunk)

            db.session.commit()

            flash("HR policy uploaded and processed successfully.", "success")
            return redirect(url_for("hr.policies"))

        except Exception as error:
            db.session.rollback()

            if os.path.exists(file_path):
                os.remove(file_path)

            current_app.logger.exception("Policy upload failed.")
            flash(f"Policy upload failed: {error}", "danger")

    return render_template("upload_policy.html")