from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import Exam, ClassRoom, Subject


exam_bp = Blueprint(
    "exams",
    __name__,
    url_prefix="/api/exams"
)


# CREATE EXAM
@exam_bp.route("", methods=["POST"])
@jwt_required()
def create_exam():
    data = request.get_json() or {}

    name = data.get("name", "").strip()
    exam_type = data.get("exam_type", "").strip()
    exam_date = data.get("exam_date")
    class_id = data.get("class_id")
    subject_id = data.get("subject_id")
    max_marks = data.get("max_marks")

    if (
        not name
        or not exam_type
        or not exam_date
        or class_id is None
        or subject_id is None
        or max_marks is None
    ):
        return jsonify({
            "success": False,
            "message": "All exam fields are required"
        }), 400

    try:
        class_id = int(class_id)
        subject_id = int(subject_id)
        max_marks = float(max_marks)
        user_id = int(get_jwt_identity())

        exam_date = datetime.strptime(
            exam_date,
            "%Y-%m-%d"
        ).date()

    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Invalid class, subject, marks or date. Date must be YYYY-MM-DD"
        }), 400

    if max_marks <= 0:
        return jsonify({
            "success": False,
            "message": "Maximum marks must be greater than zero"
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

    exam = Exam(
        name=name,
        exam_type=exam_type,
        exam_date=exam_date,
        class_id=class_id,
        subject_id=subject_id,
        max_marks=max_marks
    )

    db.session.add(exam)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Exam created successfully",
        "exam": {
            "id": exam.id,
            "name": exam.name,
            "exam_type": exam.exam_type,
            "exam_date": exam.exam_date.isoformat(),
            "class_id": exam.class_id,
            "subject_id": exam.subject_id,
            "max_marks": exam.max_marks
        }
    }), 201


# GET ALL EXAMS
@exam_bp.route("", methods=["GET"])
@jwt_required()
def get_exams():
    user_id = int(get_jwt_identity())

    exams = (
        Exam.query
        .join(ClassRoom)
        .filter(ClassRoom.teacher_id == user_id)
        .order_by(Exam.exam_date.asc())
        .all()
    )

    result = []

    for exam in exams:
        result.append({
            "id": exam.id,
            "name": exam.name,
            "exam_type": exam.exam_type,
            "exam_date": exam.exam_date.isoformat(),
            "class_id": exam.class_id,
            "subject_id": exam.subject_id,
            "max_marks": exam.max_marks
        })

    return jsonify({
        "success": True,
        "exams": result
    })


# GET SINGLE EXAM
@exam_bp.route("/<int:exam_id>", methods=["GET"])
@jwt_required()
def get_single_exam(exam_id):
    user_id = int(get_jwt_identity())

    exam = (
        Exam.query
        .join(ClassRoom)
        .filter(
            Exam.id == exam_id,
            ClassRoom.teacher_id == user_id
        )
        .first()
    )

    if not exam:
        return jsonify({
            "success": False,
            "message": "Exam not found"
        }), 404

    return jsonify({
        "success": True,
        "exam": {
            "id": exam.id,
            "name": exam.name,
            "exam_type": exam.exam_type,
            "exam_date": exam.exam_date.isoformat(),
            "class_id": exam.class_id,
            "subject_id": exam.subject_id,
            "max_marks": exam.max_marks
        }
    })


# UPDATE EXAM
@exam_bp.route("/<int:exam_id>", methods=["PUT"])
@jwt_required()
def update_exam(exam_id):
    user_id = int(get_jwt_identity())

    exam = (
        Exam.query
        .join(ClassRoom)
        .filter(
            Exam.id == exam_id,
            ClassRoom.teacher_id == user_id
        )
        .first()
    )

    if not exam:
        return jsonify({
            "success": False,
            "message": "Exam not found"
        }), 404

    data = request.get_json() or {}

    if "name" in data:
        name = data["name"].strip()

        if not name:
            return jsonify({
                "success": False,
                "message": "Exam name cannot be empty"
            }), 400

        exam.name = name

    if "exam_type" in data:
        exam_type = data["exam_type"].strip()

        if not exam_type:
            return jsonify({
                "success": False,
                "message": "Exam type cannot be empty"
            }), 400

        exam.exam_type = exam_type

    if "exam_date" in data:
        try:
            exam.exam_date = datetime.strptime(
                data["exam_date"],
                "%Y-%m-%d"
            ).date()
        except ValueError:
            return jsonify({
                "success": False,
                "message": "Date must be YYYY-MM-DD"
            }), 400

    if "max_marks" in data:
        try:
            max_marks = float(data["max_marks"])
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "message": "Maximum marks must be a number"
            }), 400

        if max_marks <= 0:
            return jsonify({
                "success": False,
                "message": "Maximum marks must be greater than zero"
            }), 400

        exam.max_marks = max_marks

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Exam updated successfully"
    })


# DELETE EXAM
@exam_bp.route("/<int:exam_id>", methods=["DELETE"])
@jwt_required()
def delete_exam(exam_id):
    user_id = int(get_jwt_identity())

    exam = (
        Exam.query
        .join(ClassRoom)
        .filter(
            Exam.id == exam_id,
            ClassRoom.teacher_id == user_id
        )
        .first()
    )

    if not exam:
        return jsonify({
            "success": False,
            "message": "Exam not found"
        }), 404

    db.session.delete(exam)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Exam deleted successfully"
    })