from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import Student, ClassRoom


student_bp = Blueprint(
    "students",
    __name__,
    url_prefix="/api/students"
)


# ============================================================
# CREATE STUDENT
# ============================================================

@student_bp.route("", methods=["POST"])
@jwt_required()
def create_student():

    data = request.get_json() or {}

    name = data.get("name", "").strip()
    roll_number = data.get("roll_number")
    parent_name = data.get("parent_name", "").strip()
    parent_phone = data.get("parent_phone", "").strip()
    class_id = data.get("class_id")

    if not name or roll_number is None or class_id is None:
        return jsonify({
            "success": False,
            "message": "Name, roll number and class are required"
        }), 400

    try:
        roll_number = int(roll_number)
        class_id = int(class_id)
        user_id = int(get_jwt_identity())

    except (ValueError, TypeError):

        return jsonify({
            "success": False,
            "message": "Roll number and class ID must be valid numbers"
        }), 400

    classroom = db.session.get(
        ClassRoom,
        class_id
    )

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

    student = Student(
        name=name,
        roll_number=roll_number,
        parent_name=parent_name or None,
        parent_phone=parent_phone or None,
        class_id=class_id,
        status="active"
    )

    db.session.add(student)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Student created successfully",
        "student": {
            "id": student.id,
            "name": student.name,
            "roll_number": student.roll_number,
            "parent_name": student.parent_name,
            "parent_phone": student.parent_phone,
            "class_id": student.class_id,
            "status": student.status
        }
    }), 201


# ============================================================
# GET STUDENTS
# ============================================================

@student_bp.route("", methods=["GET"])
@jwt_required()
def get_students():

    user_id = int(get_jwt_identity())

    # --------------------------------------------------------
    # OPTIONAL CLASS FILTER
    # --------------------------------------------------------

    class_id = request.args.get("class_id")

    query = (
        Student.query
        .join(ClassRoom)
        .filter(
            ClassRoom.teacher_id == user_id
        )
    )

    if class_id is not None:

        try:
            class_id = int(class_id)

        except (ValueError, TypeError):

            return jsonify({
                "success": False,
                "message": "Invalid class ID"
            }), 400

        query = query.filter(
            Student.class_id == class_id
        )

    students = query.order_by(
        Student.roll_number.asc()
    ).all()

    result = []

    for student in students:

        result.append({
            "id": student.id,
            "name": student.name,
            "roll_number": student.roll_number,
            "parent_name": student.parent_name,
            "parent_phone": student.parent_phone,
            "class_id": student.class_id,
            "status": student.status
        })

    return jsonify({
        "success": True,
        "students": result
    })


# ============================================================
# GET SINGLE STUDENT
# ============================================================

@student_bp.route(
    "/<int:student_id>",
    methods=["GET"]
)
@jwt_required()
def get_student(student_id):

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

    return jsonify({
        "success": True,
        "student": {
            "id": student.id,
            "name": student.name,
            "roll_number": student.roll_number,
            "parent_name": student.parent_name,
            "parent_phone": student.parent_phone,
            "class_id": student.class_id,
            "status": student.status
        }
    })


# ============================================================
# UPDATE STUDENT
# ============================================================

@student_bp.route(
    "/<int:student_id>",
    methods=["PUT"]
)
@jwt_required()
def update_student(student_id):

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

    data = request.get_json() or {}

    # --------------------------------------------------------
    # NAME
    # --------------------------------------------------------

    if "name" in data:

        name = data["name"].strip()

        if not name:

            return jsonify({
                "success": False,
                "message": "Name cannot be empty"
            }), 400

        student.name = name

    # --------------------------------------------------------
    # ROLL NUMBER
    # --------------------------------------------------------

    if "roll_number" in data:

        try:
            student.roll_number = int(
                data["roll_number"]
            )

        except (ValueError, TypeError):

            return jsonify({
                "success": False,
                "message": "Roll number must be a valid number"
            }), 400

    # --------------------------------------------------------
    # PARENT NAME
    # --------------------------------------------------------

    if "parent_name" in data:

        student.parent_name = (
            data["parent_name"].strip()
            or None
        )

    # --------------------------------------------------------
    # PARENT PHONE
    # --------------------------------------------------------

    if "parent_phone" in data:

        student.parent_phone = (
            data["parent_phone"].strip()
            or None
        )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    if "status" in data:

        if data["status"] not in [
            "active",
            "inactive"
        ]:

            return jsonify({
                "success": False,
                "message": "Invalid student status"
            }), 400

        student.status = data["status"]

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Student updated successfully"
    })


# ============================================================
# DELETE STUDENT
# ============================================================

@student_bp.route(
    "/<int:student_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_student(student_id):

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

    db.session.delete(student)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Student deleted successfully"
    })