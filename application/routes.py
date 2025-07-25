"""Flask routes for invoice web interface."""

import sqlite3

from flask import Blueprint, jsonify, render_template

from . import db
from .models import Invoice

bp = Blueprint("main", __name__)


@bp.route("/")
def dashboard():
    """Render dashboard with 3 most recent invoices."""
    try:
        recent_invoices = Invoice.get_recent(3)
        return render_template("dashboard.html", recent_invoices=recent_invoices)
    except sqlite3.Error:
        # Display friendly error message if database unavailable
        return render_template(
            "dashboard.html",
            recent_invoices=[],
            error="Unable to load invoices. Please try again later.",
        )


@bp.route("/status")
def status():
    """Health check endpoint with database connectivity test."""
    try:
        # Test database connectivity by executing SELECT COUNT(*) FROM invoices
        connection = db.get_db_connection()
        cursor = connection.execute("SELECT COUNT(*) FROM invoices")
        total_invoices = cursor.fetchone()[0]

        return jsonify(
            {
                "status": "healthy",
                "database": "connected",
                "total_invoices": total_invoices,
            }
        ), 200
    except sqlite3.Error as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503
