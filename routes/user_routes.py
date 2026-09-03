from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from models import User


user_bp = Blueprint(
    "users",
    __name__,
    url_prefix="/api/users"
)


# GET CURRENT USER PROFILE
@user_bp.route("/me", methods=["GET"])
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity())

    user = db.session.get(User, user_id)

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404

    return jsonify({
        "success": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "created_at": (
                user.created_at.isoformat()
                if user.created_at
                else None
            )
        }
    })


# UPDATE CURRENT USER PROFILE
@user_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())

    user = db.session.get(User, user_id)

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404

    data = request.get_json() or {}

    if "name" in data:
        name = str(data["name"]).strip()

        if not name:
            return jsonify({
                "success": False,
                "message": "Name cannot be empty"
            }), 400

        user.name = name

    if "email" in data:
        email = str(data["email"]).strip().lower()

        if not email:
            return jsonify({
                "success": False,
                "message": "Email cannot be empty"
            }), 400

        existing_user = User.query.filter(
            User.email == email,
            User.id != user.id
        ).first()

        if existing_user:
            return jsonify({
                "success": False,
                "message": "Email is already in use"
            }), 409

        user.email = email

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Profile updated successfully"
    })


# CHANGE PASSWORD
@user_bp.route("/change-password", methods=["PUT"])
@jwt_required()
def change_password():
    user_id = int(get_jwt_identity())

    user = db.session.get(User, user_id)

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404

    data = request.get_json() or {}

    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if not current_password or not new_password:
        return jsonify({
            "success": False,
            "message": "Current password and new password are required"
        }), 400

    if not check_password_hash(
        user.password_hash,
        current_password
    ):
        return jsonify({
            "success": False,
            "message": "Current password is incorrect"
        }), 401

    if len(new_password) < 8:
        return jsonify({
            "success": False,
            "message": "New password must be at least 8 characters"
        }), 400

    user.password_hash = generate_password_hash(
        new_password
    )

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Password changed successfully"
    })