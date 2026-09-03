from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import Syllabus, ClassRoom, Subject


syllabus_bp = Blueprint(
    "syllabus",
    __name__,
    url_prefix="/api/syllabus"
)


# CREATE SYLLABUS CHAPTER
@syllabus_bp.route("", methods=["POST"])
@jwt_required()
def create_syllabus():
    data = request.get_json() or {}

    chapter_name = data.get("chapter_name", "").strip()
    class_id = data.get("class_id")
    subject_id = data.get("subject_id")
    target_date = data.get("target_date")

    if not chapter_name or class_id is None or subject_id is None:
        return jsonify({
            "success": False,
            "message": "Chapter name, class and subject are required"
        }), 400

    try:
        class_id = int(class_id)
        subject_id = int(subject_id)
        user_id = int(get_jwt_identity())

        if target_date:
            target_date = datetime.strptime(
                target_date,
                "%Y-%m-%d"
            ).date()

    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Invalid class, subject or date. Date must be YYYY-MM-DD"
        }), 400

    classroom = db.session.get(ClassRoom, class_id)
    subject = db.session.get(Subject, subject_id)

    if not classroom:
        return jsonify({
            "success": False,
            "message": "Class not found"
        }), 404

    if not subject:
        return jsonify({
            "success": False,
            "message": "Subject not found"
        }), 404

    if classroom.teacher_id != user_id:
        return jsonify({
            "success": False,
            "message": "You do not have access to this class"
        }), 403

    if subject.class_id != class_id:
        return jsonify({
            "success": False,
            "message": "Subject does not belong to this class"
        }), 400

    syllabus = Syllabus(
        chapter_name=chapter_name,
        class_id=class_id,
        subject_id=subject_id,
        target_date=target_date,
        status="pending",
        completion_percentage=0
    )

    db.session.add(syllabus)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Syllabus chapter created successfully",
        "syllabus": {
            "id": syllabus.id,
            "chapter_name": syllabus.chapter_name,
            "class_id": syllabus.class_id,
            "subject_id": syllabus.subject_id,
            "target_date": (
                syllabus.target_date.isoformat()
                if syllabus.target_date
                else None
            ),
            "status": syllabus.status,
            "completion_percentage": syllabus.completion_percentage
        }
    }), 201


# GET SYLLABUS
@syllabus_bp.route("", methods=["GET"])
@jwt_required()
def get_syllabus():
    user_id = int(get_jwt_identity())

    records = (
        Syllabus.query
        .join(ClassRoom)
        .filter(ClassRoom.teacher_id == user_id)
        .order_by(Syllabus.target_date.asc())
        .all()
    )

    result = []

    for syllabus in records:
        result.append({
            "id": syllabus.id,
            "chapter_name": syllabus.chapter_name,
            "class_id": syllabus.class_id,
            "subject_id": syllabus.subject_id,
            "target_date": (
                syllabus.target_date.isoformat()
                if syllabus.target_date
                else None
            ),
            "status": syllabus.status,
            "completion_percentage": syllabus.completion_percentage
        })

    return jsonify({
        "success": True,
        "syllabus": result
    })


# GET SINGLE SYLLABUS
@syllabus_bp.route("/<int:syllabus_id>", methods=["GET"])
@jwt_required()
def get_single_syllabus(syllabus_id):
    user_id = int(get_jwt_identity())

    syllabus = (
        Syllabus.query
        .join(ClassRoom)
        .filter(
            Syllabus.id == syllabus_id,
            ClassRoom.teacher_id == user_id
        )
        .first()
    )

    if not syllabus:
        return jsonify({
            "success": False,
            "message": "Syllabus chapter not found"
        }), 404

    return jsonify({
        "success": True,
        "syllabus": {
            "id": syllabus.id,
            "chapter_name": syllabus.chapter_name,
            "class_id": syllabus.class_id,
            "subject_id": syllabus.subject_id,
            "target_date": (
                syllabus.target_date.isoformat()
                if syllabus.target_date
                else None
            ),
            "status": syllabus.status,
            "completion_percentage": syllabus.completion_percentage
        }
    })


# UPDATE SYLLABUS
@syllabus_bp.route("/<int:syllabus_id>", methods=["PUT"])
@jwt_required()
def update_syllabus(syllabus_id):
    user_id = int(get_jwt_identity())

    syllabus = (
        Syllabus.query
        .join(ClassRoom)
        .filter(
            Syllabus.id == syllabus_id,
            ClassRoom.teacher_id == user_id
        )
        .first()
    )

    if not syllabus:
        return jsonify({
            "success": False,
            "message": "Syllabus chapter not found"
        }), 404

    data = request.get_json() or {}

    if "chapter_name" in data:
        chapter_name = data["chapter_name"].strip()

        if not chapter_name:
            return jsonify({
                "success": False,
                "message": "Chapter name cannot be empty"
            }), 400

        syllabus.chapter_name = chapter_name

    if "target_date" in data:
        if data["target_date"]:
            try:
                syllabus.target_date = datetime.strptime(
                    data["target_date"],
                    "%Y-%m-%d"
                ).date()
            except ValueError:
                return jsonify({
                    "success": False,
                    "message": "Date must be YYYY-MM-DD"
                }), 400
        else:
            syllabus.target_date = None

    if "completion_percentage" in data:
        try:
            percentage = float(data["completion_percentage"])
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "message": "Invalid completion percentage"
            }), 400

        if not 0 <= percentage <= 100:
            return jsonify({
                "success": False,
                "message": "Completion must be between 0 and 100"
            }), 400

        syllabus.completion_percentage = percentage

        if percentage == 100:
            syllabus.status = "completed"
        elif percentage > 0:
            syllabus.status = "in_progress"
        else:
            syllabus.status = "pending"

    if "status" in data:
        status = data["status"]

        if status not in [
            "pending",
            "in_progress",
            "completed"
        ]:
            return jsonify({
                "success": False,
                "message": "Invalid syllabus status"
            }), 400

        syllabus.status = status

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Syllabus updated successfully"
    })


# DELETE SYLLABUS
@syllabus_bp.route("/<int:syllabus_id>", methods=["DELETE"])
@jwt_required()
def delete_syllabus(syllabus_id):
    user_id = int(get_jwt_identity())

    syllabus = (
        Syllabus.query
        .join(ClassRoom)
        .filter(
            Syllabus.id == syllabus_id,
            ClassRoom.teacher_id == user_id
        )
        .first()
    )

    if not syllabus:
        return jsonify({
            "success": False,
            "message": "Syllabus chapter not found"
        }), 404

    db.session.delete(syllabus)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Syllabus deleted successfully"
    })