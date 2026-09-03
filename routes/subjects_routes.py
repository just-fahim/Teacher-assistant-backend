from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import Subject, ClassRoom


subject_bp = Blueprint(
    "subjects",
    __name__,
    url_prefix="/api/subjects"
)


@subject_bp.route("", methods=["POST"])
@jwt_required()
def create_subject():
    data = request.get_json() or {}

    name = data.get("name", "").strip()
    class_id = data.get("class_id")

    if not name or class_id is None:
        return jsonify({
            "success": False,
            "message": "Subject name and class are required"
        }), 400

    try:
        class_id = int(class_id)
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Invalid class ID"
        }), 400

    user_id = int(get_jwt_identity())

    classroom = db.session.get(ClassRoom, class_id)

    if not classroom:
        return jsonify({
            "success": False,
            "message": "Class not found"
        }), 404

    if classroom.teacher_id != user_id:
        return jsonify({
            "success": False,
            "message": "You do not have access to this class"
        }), 403

    subject = Subject(
        name=name,
        class_id=class_id
    )

    db.session.add(subject)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Subject created successfully",
        "subject": {
            "id": subject.id,
            "name": subject.name,
            "class_id": subject.class_id
        }
    }), 201


@subject_bp.route("", methods=["GET"])
@jwt_required()
def get_subjects():
    user_id = int(get_jwt_identity())

    subjects = (
        Subject.query
        .join(ClassRoom)
        .filter(ClassRoom.teacher_id == user_id)
        .all()
    )

    result = []

    for subject in subjects:
        result.append({
            "id": subject.id,
            "name": subject.name,
            "class_id": subject.class_id
        })

    return jsonify({
        "success": True,
        "subjects": result
    })


@subject_bp.route("/<int:subject_id>", methods=["PUT"])
@jwt_required()
def update_subject(subject_id):
    user_id = int(get_jwt_identity())

    subject = (
        Subject.query
        .join(ClassRoom)
        .filter(
            Subject.id == subject_id,
            ClassRoom.teacher_id == user_id
        )
        .first()
    )

    if not subject:
        return jsonify({
            "success": False,
            "message": "Subject not found"
        }), 404

    data = request.get_json() or {}

    if "name" in data:
        name = data["name"].strip()

        if not name:
            return jsonify({
                "success": False,
                "message": "Subject name cannot be empty"
            }), 400

        subject.name = name

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Subject updated successfully"
    })


@subject_bp.route("/<int:subject_id>", methods=["DELETE"])
@jwt_required()
def delete_subject(subject_id):
    user_id = int(get_jwt_identity())

    subject = (
        Subject.query
        .join(ClassRoom)
        .filter(
            Subject.id == subject_id,
            ClassRoom.teacher_id == user_id
        )
        .first()
    )

    if not subject:
        return jsonify({
            "success": False,
            "message": "Subject not found"
        }), 404

    db.session.delete(subject)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Subject deleted successfully"
    })