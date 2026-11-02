from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


def current_time():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="employee")
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=current_time)

    policies = db.relationship(
        "HRPolicy",
        back_populates="uploader",
        lazy=True
    )

    employee_queries = db.relationship(
        "EmployeeQuery",
        foreign_keys="EmployeeQuery.employee_id",
        back_populates="employee",
        lazy=True
    )

    assigned_queries = db.relationship(
        "EmployeeQuery",
        foreign_keys="EmployeeQuery.assigned_hr_id",
        back_populates="assigned_hr",
        lazy=True
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class HRPolicy(db.Model):
    __tablename__ = "hr_policies"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    extracted_text = db.Column(db.Text, nullable=False)

    uploaded_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    uploaded_at = db.Column(db.DateTime(timezone=True), default=current_time)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    uploader = db.relationship(
        "User",
        back_populates="policies"
    )

    chunks = db.relationship(
        "DocumentChunk",
        back_populates="policy",
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        return f"<HRPolicy {self.title}>"


class DocumentChunk(db.Model):
    __tablename__ = "document_chunks"

    id = db.Column(db.Integer, primary_key=True)

    policy_id = db.Column(
        db.Integer,
        db.ForeignKey("hr_policies.id"),
        nullable=False
    )

    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=current_time)

    policy = db.relationship(
        "HRPolicy",
        back_populates="chunks"
    )

    def __repr__(self):
        return f"<DocumentChunk {self.id}>"


class EmployeeQuery(db.Model):
    __tablename__ = "employee_queries"

    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    question = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=True)

    status = db.Column(
        db.String(30),
        nullable=False,
        default="pending"
    )

    is_escalated = db.Column(db.Boolean, default=False, nullable=False)
    escalation_reason = db.Column(db.Text, nullable=True)

    assigned_hr_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    hr_response = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), default=current_time)

    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=current_time,
        onupdate=current_time
    )

    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)

    employee = db.relationship(
        "User",
        foreign_keys=[employee_id],
        back_populates="employee_queries"
    )

    assigned_hr = db.relationship(
        "User",
        foreign_keys=[assigned_hr_id],
        back_populates="assigned_queries"
    )

    def __repr__(self):
        return f"<EmployeeQuery {self.id}>"