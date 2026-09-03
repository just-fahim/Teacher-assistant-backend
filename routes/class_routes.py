from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import ClassRoom, User


class_bp = Blueprint(
    "classes",
    __name__,
    url_prefix="/api/classes"
)


# CREATE CLASS
@class_bp.route("", methods=["POST"])
@jwt_required()
def create_class():
    data = request.get_json() or {}

    name = data.get("name", "").strip()
    section = data.get("section", "").strip()
    academic_year = data.get("academic_year", "").strip()

    if not name or not section or not academic_year:
        return jsonify({
            "success": False,
            "message": "Name, section and academic year are required"
        }), 400

    try:
        user_id = int(get_jwt_identity())
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Invalid user token"
        }), 401

    user = db.session.get(User, user_id)

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404

    new_class = ClassRoom(
        name=name,
        section=section,
        academic_year=academic_year,
        teacher_id=user.id
    )

    db.session.add(new_class)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Class created successfully",
        "class": {
            "id": new_class.id,
            "name": new_class.name,
            "section": new_class.section,
            "academic_year": new_class.academic_year,
            "teacher_id": new_class.teacher_id
        }
    }), 201


# GET ALL CLASSES
@class_bp.route("", methods=["GET"])
@jwt_required()
def get_classes():
    try:
        user_id = int(get_jwt_identity())
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Invalid user token"
        }), 401

    classes = ClassRoom.query.filter_by(
        teacher_id=user_id
    ).all()

    result = []

    for classroom in classes:
        result.append({
            "id": classroom.id,
            "name": classroom.name,
            "section": classroom.section,
            "academic_year": classroom.academic_year,
            "teacher_id": classroom.teacher_id
        })

    return jsonify({
        "success": True,
        "classes": result
    })


# UPDATE CLASS
@class_bp.route("/<int:class_id>", methods=["PUT"])
@jwt_required()
def update_class(class_id):
    try:
        user_id = int(get_jwt_identity())
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Invalid user token"
        }), 401

    classroom = ClassRoom.query.filter_by(
        id=class_id,
        teacher_id=user_id
    ).first()

    if not classroom:
        return jsonify({
            "success": False,
            "message": "Class not found"
        }), 404

    data = request.get_json() or {}

    if "name" in data:
        classroom.name = data["name"].strip()

    if "section" in data:
        classroom.section = data["section"].strip()

    if "academic_year" in data:
        classroom.academic_year = data["academic_year"].strip()

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Class updated successfully"
    })


# DELETE CLASS
@class_bp.route("/<int:class_id>", methods=["DELETE"])
@jwt_required()
def delete_class(class_id):
    try:
        user_id = int(get_jwt_identity())
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Invalid user token"
        }), 401

    classroom = ClassRoom.query.filter_by(
        id=class_id,
        teacher_id=user_id
    ).first()

    if not classroom:
        return jsonify({
            "success": False,
            "message": "Class not found"
        }), 404

    db.session.delete(classroom)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Class deleted successfully"
    })