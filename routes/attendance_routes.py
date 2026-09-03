from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import Attendance, Student, ClassRoom


attendance_bp = Blueprint(
    "attendance",
    __name__,
    url_prefix="/api/attendance"
)


# ============================================================
# CREATE / UPDATE ATTENDANCE
# ============================================================

@attendance_bp.route("", methods=["POST"])
@jwt_required()
def create_attendance():

    data = request.get_json() or {}

    student_id = data.get("student_id")
    date = data.get("date")
    status = data.get("status")

    if (
        student_id is None
        or not date
        or not status
    ):
        return jsonify({
            "success": False,
            "message": "Student, date and status are required"
        }), 400

    try:
        student_id = int(student_id)
        user_id = int(get_jwt_identity())

    except (ValueError, TypeError):

        return jsonify({
            "success": False,
            "message": "Invalid student ID or token"
        }), 400

    try:
        attendance_date = datetime.strptime(
            date,
            "%Y-%m-%d"
        ).date()

    except (ValueError, TypeError):

        return jsonify({
            "success": False,
            "message": "Date must be in YYYY-MM-DD format"
        }), 400

    status = str(status).strip().lower()

    if status not in ["present", "absent"]:

        return jsonify({
            "success": False,
            "message": "Status must be present or absent"
        }), 400

    student = db.session.get(
        Student,
        student_id
    )

    if not student:

        return jsonify({
            "success": False,
            "message": "Student not found"
        }), 404

    classroom = db.session.get(
        ClassRoom,
        student.class_id
    )

    if not classroom:

        return jsonify({
            "success": False,
            "message": "Student's class not found"
        }), 404

    if classroom.teacher_id != user_id:

        return jsonify({
            "success": False,
            "message": "You do not have access to this student"
        }), 403

    existing = Attendance.query.filter_by(
        student_id=student_id,
        date=attendance_date
    ).first()

    if existing:

        existing.status = status

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Attendance updated successfully",
            "attendance": {
                "id": existing.id,
                "student_id": existing.student_id,
                "date": str(existing.date),
                "status": existing.status
            }
        }), 200

    new_attendance = Attendance(
        student_id=student_id,
        date=attendance_date,
        status=status
    )

    db.session.add(new_attendance)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Attendance saved successfully",
        "attendance": {
            "id": new_attendance.id,
            "student_id": new_attendance.student_id,
            "date": str(new_attendance.date),
            "status": new_attendance.status
        }
    }), 201


# ============================================================
# GET ALL ATTENDANCE
# ============================================================

@attendance_bp.route("", methods=["GET"])
@jwt_required()
def get_attendance():

    user_id = int(get_jwt_identity())

    records = (
        Attendance.query
        .join(Student)
        .join(ClassRoom)
        .filter(
            ClassRoom.teacher_id == user_id
        )
        .order_by(
            Attendance.date.desc()
        )
        .all()
    )

    result = []

    for record in records:

        result.append({
            "id": record.id,
            "student_id": record.student_id,
            "date": str(record.date),
            "status": record.status
        })

    return jsonify({
        "success": True,
        "attendance": result
    })


# ============================================================
# GET ATTENDANCE FOR DATE
# ============================================================

@attendance_bp.route(
    "/date/<string:date>",
    methods=["GET"]
)
@jwt_required()
def get_attendance_by_date(date):

    user_id = int(get_jwt_identity())

    try:
        attendance_date = datetime.strptime(
            date,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        return jsonify({
            "success": False,
            "message": "Date must be in YYYY-MM-DD format"
        }), 400

    records = (
        Attendance.query
        .join(Student)
        .join(ClassRoom)
        .filter(
            ClassRoom.teacher_id == user_id,
            Attendance.date == attendance_date
        )
        .order_by(
            Attendance.student_id.asc()
        )
        .all()
    )

    result = []

    for record in records:

        result.append({
            "id": record.id,
            "student_id": record.student_id,
            "date": str(record.date),
            "status": record.status
        })

    return jsonify({
        "success": True,
        "date": date,
        "attendance": result
    })


# ============================================================
# GET ATTENDANCE FOR SPECIFIC STUDENT
# ============================================================

@attendance_bp.route(
    "/student/<int:student_id>",
    methods=["GET"]
)
@jwt_required()
def get_student_attendance(student_id):

    user_id = int(get_jwt_identity())

    student = (
        Student.query
        .join(ClassRoom)
        .filter(
            Student.id == student_id,
            ClassRoom.teacher_id == user_id
        )
        .first()
    )

    if not student:

        return jsonify({
            "success": False,
            "message": "Student not found"
        }), 404

    records = (
        Attendance.query
        .filter_by(
            student_id=student_id
        )
        .order_by(
            Attendance.date.desc()
        )
        .all()
    )

    result = []

    for record in records:

        result.append({
            "id": record.id,
            "student_id": record.student_id,
            "date": str(record.date),
            "status": record.status
        })

    return jsonify({
        "success": True,
        "student_id": student_id,
        "attendance": result
    })


# ============================================================
# GET SINGLE ATTENDANCE
# ============================================================

@attendance_bp.route(
    "/<int:attendance_id>",
    methods=["GET"]
)
@jwt_required()
def get_single_attendance(attendance_id):

    user_id = int(get_jwt_identity())

    record = (
        Attendance.query
        .join(Student)
        .join(ClassRoom)
        .filter(
            Attendance.id == attendance_id,
            ClassRoom.teacher_id == user_id
        )
        .first()
    )

    if not record:

        return jsonify({
            "success": False,
            "message": "Attendance record not found"
        }), 404

    return jsonify({
        "success": True,
        "attendance": {
            "id": record.id,
            "student_id": record.student_id,
            "date": str(record.date),
            "status": record.status
        }
    })


# ============================================================
# DELETE ATTENDANCE
# ============================================================

@attendance_bp.route(
    "/<int:attendance_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_attendance(attendance_id):

    user_id = int(get_jwt_identity())

    record = (
        Attendance.query
        .join(Student)
        .join(ClassRoom)
        .filter(
            Attendance.id == attendance_id,
            ClassRoom.teacher_id == user_id
        )
        .first()
    )

    if not record:

        return jsonify({
            "success": False,
            "message": "Attendance record not found"
        }), 404

    db.session.delete(record)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Attendance deleted successfully"
    })