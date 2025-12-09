"""
Review Queue API Routes — Phase 9

REST endpoints for operators to:
- View review queue
- Approve/reject tasks
- Provide custom input
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aicmo.cam.engine.review_queue import (
    get_review_queue,
    approve_review_task,
    reject_review_task,
    flag_lead_for_review,
)
from aicmo.cam.db_models import Base

bp = Blueprint("review_queue", __name__, url_prefix="/api/v1/review-queue")


def get_db_session():
    """Factory for database sessions."""
    engine = create_engine("sqlite:///./cam.db")
    Session = sessionmaker(bind=engine)
    return Session()


@bp.route("/tasks", methods=["GET"])
@login_required
def list_review_tasks():
    """
    Get all review tasks.
    
    Query params:
    - campaign_id: Optional filter
    - review_type: Optional filter (MESSAGE, PROPOSAL, etc.)
    
    Returns:
        {
            "total": int,
            "tasks": [ReviewTask dicts],
            "summary": {
                "MESSAGE": count,
                "PROPOSAL": count,
                ...
            }
        }
    """
    try:
        campaign_id = request.args.get("campaign_id", type=int)
        review_type_filter = request.args.get("review_type", type=str)
        
        db_session = get_db_session()
        tasks = get_review_queue(db_session, campaign_id=campaign_id)
        
        # Optional filter by review_type
        if review_type_filter:
            tasks = [t for t in tasks if t.review_type == review_type_filter]
        
        # Build summary
        summary = {}
        for task in tasks:
            summary[task.review_type] = summary.get(task.review_type, 0) + 1
        
        response = {
            "total": len(tasks),
            "tasks": [t.to_dict() for t in tasks],
            "summary": summary,
        }
        
        db_session.close()
        return jsonify(response), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/tasks/<int:lead_id>/approve", methods=["POST"])
@login_required
def approve_task(lead_id):
    """
    Approve a review task.
    
    Body:
    {
        "action": "approve" | "skip",
        "custom_message": "optional override"
    }
    """
    try:
        data = request.get_json()
        action = data.get("action", "approve")
        custom_message = data.get("custom_message")
        
        db_session = get_db_session()
        success = approve_review_task(
            lead_id,
            db_session,
            action=action,
            custom_message=custom_message,
        )
        db_session.close()
        
        if success:
            return jsonify({"status": "approved", "lead_id": lead_id}), 200
        else:
            return jsonify({"error": "Could not approve task"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/tasks/<int:lead_id>/reject", methods=["POST"])
@login_required
def reject_task(lead_id):
    """
    Reject a review task.
    
    Body:
    {
        "reason": "Why rejecting"
    }
    """
    try:
        data = request.get_json()
        reason = data.get("reason", "Operator rejection")
        
        db_session = get_db_session()
        success = reject_review_task(lead_id, db_session, reason=reason)
        db_session.close()
        
        if success:
            return jsonify({"status": "rejected", "lead_id": lead_id}), 200
        else:
            return jsonify({"error": "Could not reject task"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/tasks/<int:lead_id>/flag", methods=["POST"])
@login_required
def flag_task(lead_id):
    """
    Flag a lead for human review (pause automated actions).
    
    Body:
    {
        "review_type": "MESSAGE" | "PROPOSAL" | etc.,
        "reason": "Why flagging"
    }
    """
    try:
        data = request.get_json()
        review_type = data.get("review_type", "MESSAGE")
        reason = data.get("reason", "Flagged for human review")
        
        db_session = get_db_session()
        success = flag_lead_for_review(
            lead_id,
            db_session,
            review_type=review_type,
            reason=reason,
        )
        db_session.close()
        
        if success:
            return jsonify({"status": "flagged", "lead_id": lead_id}), 200
        else:
            return jsonify({"error": "Could not flag lead"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/stats", methods=["GET"])
@login_required
def queue_stats():
    """
    Get review queue statistics.
    
    Returns:
        {
            "total_pending": int,
            "by_type": {"MESSAGE": count, ...},
            "by_campaign": {"Campaign Name": count, ...},
            "oldest_task_created_at": ISO datetime
        }
    """
    try:
        db_session = get_db_session()
        tasks = get_review_queue(db_session)
        
        by_type = {}
        by_campaign = {}
        oldest_created = None
        
        for task in tasks:
            by_type[task.review_type] = by_type.get(task.review_type, 0) + 1
            
            if oldest_created is None or task.created_at < oldest_created:
                oldest_created = task.created_at
        
        response = {
            "total_pending": len(tasks),
            "by_type": by_type,
            "oldest_task_created_at": oldest_created.isoformat() if oldest_created else None,
        }
        
        db_session.close()
        return jsonify(response), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
