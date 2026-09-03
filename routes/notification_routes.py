from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import Notification


notification_bp = Blueprint(
    "notifications",
    __name__,
    url_prefix="/api/notifications"
)


# CREATE NOTIFICATION
@notification_bp.route("", methods=["POST"])
@jwt_required()
def create_notification():
    data = request.get_json() or {}

    title = data.get("title", "").strip()
    message = data.get("message", "").strip()
    notification_type = data.get("type", "general").strip()

    if not title or not message:
        return jsonify({
            "success": False,
            "message": "Title and message are required"
        }), 400

    if not notification_type:
        notification_type = "general"

    notification = Notification(
        title=title,
        message=message,
        notification_type=notification_type,
        is_read=False
    )

    db.session.add(notification)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Notification created successfully",
        "notification": {
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "type": notification.notification_type,
            "is_read": notification.is_read,
            "created_at": (
                notification.created_at.isoformat()
                if notification.created_at
                else None
            )
        }
    }), 201


# GET NOTIFICATIONS
@notification_bp.route("", methods=["GET"])
@jwt_required()
def get_notifications():
    notifications = (
        Notification.query
        .order_by(Notification.created_at.desc())
        .all()
    )

    result = []

    for notification in notifications:
        result.append({
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "type": notification.notification_type,
            "is_read": notification.is_read,
            "created_at": (
                notification.created_at.isoformat()
                if notification.created_at
                else None
            )
        })

    return jsonify({
        "success": True,
        "notifications": result
    })


# GET SINGLE NOTIFICATION
@notification_bp.route("/<int:notification_id>", methods=["GET"])
@jwt_required()
def get_notification(notification_id):
    notification = db.session.get(
        Notification,
        notification_id
    )

    if not notification:
        return jsonify({
            "success": False,
            "message": "Notification not found"
        }), 404

    return jsonify({
        "success": True,
        "notification": {
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "type": notification.notification_type,
            "is_read": notification.is_read,
            "created_at": (
                notification.created_at.isoformat()
                if notification.created_at
                else None
            )
        }
    })


# MARK NOTIFICATION AS READ
@notification_bp.route(
    "/<int:notification_id>/read",
    methods=["PUT"]
)
@jwt_required()
def mark_as_read(notification_id):
    notification = db.session.get(
        Notification,
        notification_id
    )

    if not notification:
        return jsonify({
            "success": False,
            "message": "Notification not found"
        }), 404

    notification.is_read = True

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Notification marked as read"
    })


# MARK NOTIFICATION AS UNREAD
@notification_bp.route(
    "/<int:notification_id>/unread",
    methods=["PUT"]
)
@jwt_required()
def mark_as_unread(notification_id):
    notification = db.session.get(
        Notification,
        notification_id
    )

    if not notification:
        return jsonify({
            "success": False,
            "message": "Notification not found"
        }), 404

    notification.is_read = False

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Notification marked as unread"
    })


# DELETE NOTIFICATION
@notification_bp.route(
    "/<int:notification_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_notification(notification_id):
    notification = db.session.get(
        Notification,
        notification_id
    )

    if not notification:
        return jsonify({
            "success": False,
            "message": "Notification not found"
        }), 404

    db.session.delete(notification)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Notification deleted successfully"
    })