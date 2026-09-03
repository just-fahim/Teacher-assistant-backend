from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import Homework, ClassRoom, Subject


homework_bp = Blueprint(
    "homework",
    __name__,
    url_prefix="/api/homework"
)


# CREATE HOMEWORK
@homework_bp.route("", methods=["POST"])
@jwt_required()
def create_homework():
    data = request.get_json() or {}

    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    class_id = data.get("class_id")
    subject_id = data.get("subject_id")
    due_date = data.get("due_date")

    if not title or class_id is None or subject_id is None or not due_date:
        return jsonify({
            "success": False,
            "message": "Title, class, subject and due date are required"
        }), 400

    try:
        class_id = int(class_id)
        subject_id = int(subject_id)
        user_id = int(get_jwt_identity())
        homework_date = datetime.strptime(
            due_date, "%Y-%m-%d"
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

    homework = Homework(
        title=title,
        description=description,
        class_id=class_id,
        subject_id=subject_id,
        due_date=homework_date
    )

    db.session.add(homework)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Homework created successfully",
        "homework": {
            "id": homework.id,
            "title": homework.title,
            "description": homework.description,
            "class_id": homework.class_id,
            "subject_id": homework.subject_id,
            "due_date": homework.due_date.isoformat()
        }
    }), 201


# GET ALL HOMEWORK
@homework_bp.route("", methods=["GET"])
@jwt_required()
def get_homework():
    user_id = int(get_jwt_identity())

    homework_records = (
        Homework.query
        .join(ClassRoom)
        .filter(ClassRoom.teacher_id == user_id)
        .order_by(Homework.due_date.asc())
        .all()
    )

    result = []

    for homework in homework_records:
        result.append({
            "id": homework.id,
            "title": homework.title,
            "description": homework.description,
            "class_id": homework.class_id,
            "subject_id": homework.subject_id,
            "due_date": homework.due_date.isoformat()
        })

    return jsonify({
        "success": True,
        "homework": result
    })


# GET SINGLE HOMEWORK
@homework_bp.route("/<int:homework_id>", methods=["GET"])
@jwt_required()
def get_single_homework(homework_id):
    user_id = int(get_jwt_identity())

    homework = (
        Homework.query
        .join(ClassRoom)
        .filter(
            Homework.id == homework_id,
            ClassRoom.teacher_id == user_id
        )
        .first()
    )

    if not homework:
        return jsonify({
            "success": False,
            "message": "Homework not found"
        }), 404

    return jsonify({
        "success": True,
        "homework": {
            "id": homework.id,
            "title": homework.title,
            "description": homework.description,
            "class_id": homework.class_id,
            "subject_id": homework.subject_id,
            "due_date": homework.due_date.isoformat()
        }
    })


# UPDATE HOMEWORK
@homework_bp.route("/<int:homework_id>", methods=["PUT"])
@jwt_required()
def update_homework(homework_id):
    user_id = int(get_jwt_identity())

    homework = (
        Homework.query
        .join(ClassRoom)
        .filter(
            Homework.id == homework_id,
            ClassRoom.teacher_id == user_id
        )
        .first()
    )

    if not homework:
        return jsonify({
            "success": False,
            "message": "Homework not found"
        }), 404

    data = request.get_json() or {}

    if "title" in data:
        title = data["title"].strip()

        if not title:
            return jsonify({
                "success": False,
                "message": "Title cannot be empty"
            }), 400

        homework.title = title

    if "description" in data:
        homework.description = data["description"].strip()

    if "due_date" in data:
        try:
            homework.due_date = datetime.strptime(
                data["due_date"],
                "%Y-%m-%d"
            ).date()
        except ValueError:
            return jsonify({
                "success": False,
                "message": "Date must be YYYY-MM-DD"
            }), 400

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Homework updated successfully"
    })


# DELETE HOMEWORK
@homework_bp.route("/<int:homework_id>", methods=["DELETE"])
@jwt_required()
def delete_homework(homework_id):
    user_id = int(get_jwt_identity())

    homework = (
        Homework.query
        .join(ClassRoom)
        .filter(
            Homework.id == homework_id,
            ClassRoom.teacher_id == user_id
        )
        .first()
    )

    if not homework:
        return jsonify({
            "success": False,
            "message": "Homework not found"
        }), 404

    db.session.delete(homework)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Homework deleted successfully"
    })