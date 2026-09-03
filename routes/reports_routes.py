from datetime import date, datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import (
    ClassRoom,
    Student,
    Attendance,
    Marks,
    Homework,
    Syllabus,
)


report_bp = Blueprint(
    "reports",
    __name__,
    url_prefix="/api/reports"
)


# ============================================================
# DASHBOARD SUMMARY
# ============================================================

@report_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard_report():

    user_id = int(get_jwt_identity())

    classes = ClassRoom.query.filter_by(
        teacher_id=user_id
    ).all()

    total_students = (
        Student.query
        .join(ClassRoom)
        .filter(
            ClassRoom.teacher_id == user_id
        )
        .count()
    )

    attendance_records = (
        Attendance.query
        .join(
            Student,
            Attendance.student_id == Student.id
        )
        .join(
            ClassRoom,
            Student.class_id == ClassRoom.id
        )
        .filter(
            ClassRoom.teacher_id == user_id
        )
        .all()
    )

    total_attendance = len(
        attendance_records
    )

    present_count = sum(
        1
        for record in attendance_records
        if record.status == "present"
    )

    attendance_percentage = (
        round(
            (present_count / total_attendance) * 100,
            2
        )
        if total_attendance > 0
        else 0
    )

    homework_pending = (
        Homework.query
        .join(ClassRoom)
        .filter(
            ClassRoom.teacher_id == user_id,
            Homework.due_date >= date.today()
        )
        .count()
    )

    return jsonify({
        "success": True,
        "report": {
            "total_classes": len(classes),
            "total_students": total_students,
            "attendance_percentage":
                attendance_percentage,
            "homework_pending":
                homework_pending
        }
    })


# ============================================================
# CLASS REPORT
# ============================================================

@report_bp.route(
    "/class/<int:class_id>",
    methods=["GET"]
)
@jwt_required()
def class_report(class_id):

    user_id = int(get_jwt_identity())

    classroom = ClassRoom.query.filter_by(
        id=class_id,
        teacher_id=user_id
    ).first()

    if not classroom:

        return jsonify({
            "success": False,
            "message": "Class not found"
        }), 404

    total_students = Student.query.filter_by(
        class_id=class_id
    ).count()

    attendance_records = (
        Attendance.query
        .join(
            Student,
            Attendance.student_id == Student.id
        )
        .filter(
            Student.class_id == class_id
        )
        .all()
    )

    total_attendance = len(
        attendance_records
    )

    present_count = sum(
        1
        for record in attendance_records
        if record.status == "present"
    )

    attendance_percentage = (
        round(
            (present_count / total_attendance) * 100,
            2
        )
        if total_attendance > 0
        else 0
    )

    marks_records = (
        Marks.query
        .join(
            Student,
            Marks.student_id == Student.id
        )
        .filter(
            Student.class_id == class_id
        )
        .all()
    )

    average_marks = (
        round(
            sum(
                record.marks_obtained
                for record in marks_records
            )
            / len(marks_records),
            2
        )
        if marks_records
        else 0
    )

    syllabus_records = Syllabus.query.filter_by(
        class_id=class_id
    ).all()

    syllabus_completion = (
        round(
            sum(
                record.completion_percentage
                for record in syllabus_records
            )
            / len(syllabus_records),
            2
        )
        if syllabus_records
        else 0
    )

    return jsonify({
        "success": True,
        "report": {
            "class_id": classroom.id,
            "class_name": classroom.name,
            "section": classroom.section,
            "total_students": total_students,
            "attendance_percentage":
                attendance_percentage,
            "average_marks":
                average_marks,
            "syllabus_completion":
                syllabus_completion
        }
    })


# ============================================================
# STUDENT REPORT
# ============================================================

@report_bp.route(
    "/student/<int:student_id>",
    methods=["GET"]
)
@jwt_required()
def student_report(student_id):

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

    attendance_records = Attendance.query.filter_by(
        student_id=student_id
    ).all()

    total_attendance = len(
        attendance_records
    )

    present_count = sum(
        1
        for record in attendance_records
        if record.status == "present"
    )

    attendance_percentage = (
        round(
            (present_count / total_attendance) * 100,
            2
        )
        if total_attendance > 0
        else 0
    )

    marks_records = Marks.query.filter_by(
        student_id=student_id
    ).all()

    average_marks = (
        round(
            sum(
                record.marks_obtained
                for record in marks_records
            )
            / len(marks_records),
            2
        )
        if marks_records
        else 0
    )

    homework_records = Homework.query.filter_by(
        class_id=student.class_id
    ).all()

    homework_pending = sum(
        1
        for homework in homework_records
        if homework.due_date >= date.today()
    )

    homework_completed = (
        len(homework_records)
        - homework_pending
    )

    syllabus_records = Syllabus.query.filter_by(
        class_id=student.class_id
    ).all()

    syllabus_progress = (
        round(
            sum(
                record.completion_percentage
                for record in syllabus_records
            )
            / len(syllabus_records),
            2
        )
        if syllabus_records
        else 0
    )

    return jsonify({
        "success": True,
        "report": {
            "student_id": student.id,
            "student_name": student.name,
            "attendance_percentage":
                attendance_percentage,
            "average_marks":
                average_marks,
            "homework_completed":
                homework_completed,
            "homework_pending":
                homework_pending,
            "syllabus_progress":
                syllabus_progress
        }
    })


# ============================================================
# ATTENDANCE PERIOD REPORT
#
# Supports:
# Monthly
# Quarterly
# Yearly
#
# Required:
# start_date=YYYY-MM-DD
# end_date=YYYY-MM-DD
#
# Optional:
# class_id
# ============================================================

@report_bp.route(
    "/attendance",
    methods=["GET"]
)
@jwt_required()
def attendance_period_report():

    user_id = int(get_jwt_identity())

    start_date = request.args.get(
        "start_date"
    )

    end_date = request.args.get(
        "end_date"
    )

    class_id = request.args.get(
        "class_id"
    )

    # --------------------------------------------------------
    # REQUIRED DATES
    # --------------------------------------------------------

    if not start_date or not end_date:

        return jsonify({
            "success": False,
            "message":
                "start_date and end_date are required"
        }), 400

    # --------------------------------------------------------
    # DATE VALIDATION
    # --------------------------------------------------------

    try:

        start = datetime.strptime(
            start_date,
            "%Y-%m-%d"
        ).date()

        end = datetime.strptime(
            end_date,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        return jsonify({
            "success": False,
            "message":
                "Dates must be in YYYY-MM-DD format"
        }), 400

    if start > end:

        return jsonify({
            "success": False,
            "message":
                "start_date cannot be after end_date"
        }), 400

    # --------------------------------------------------------
    # OPTIONAL CLASS
    # --------------------------------------------------------

    selected_class_id = None

    if class_id:

        try:
            selected_class_id = int(class_id)

        except (ValueError, TypeError):

            return jsonify({
                "success": False,
                "message": "Invalid class_id"
            }), 400

        classroom = ClassRoom.query.filter_by(
            id=selected_class_id,
            teacher_id=user_id
        ).first()

        if not classroom:

            return jsonify({
                "success": False,
                "message": "Class not found"
            }), 404

    # --------------------------------------------------------
    # GET TEACHER STUDENTS
    # --------------------------------------------------------

    students_query = (
        Student.query
        .join(ClassRoom)
        .filter(
            ClassRoom.teacher_id == user_id
        )
    )

    if selected_class_id is not None:

        students_query = students_query.filter(
            Student.class_id == selected_class_id
        )

    students = (
        students_query
        .order_by(
            Student.class_id.asc(),
            Student.roll_number.asc(),
            Student.name.asc()
        )
        .all()
    )

    # --------------------------------------------------------
    # GET ATTENDANCE RECORDS
    # --------------------------------------------------------

    attendance_query = (
        Attendance.query
        .join(
            Student,
            Attendance.student_id == Student.id
        )
        .join(
            ClassRoom,
            Student.class_id == ClassRoom.id
        )
        .filter(
            ClassRoom.teacher_id == user_id,
            Attendance.date >= start,
            Attendance.date <= end
        )
    )

    if selected_class_id is not None:

        attendance_query = attendance_query.filter(
            Student.class_id == selected_class_id
        )

    attendance_records = (
        attendance_query
        .order_by(
            Attendance.date.asc()
        )
        .all()
    )

    # --------------------------------------------------------
    # GROUP ATTENDANCE BY STUDENT
    # --------------------------------------------------------

    attendance_by_student = {}

    for record in attendance_records:

        if record.student_id not in attendance_by_student:

            attendance_by_student[
                record.student_id
            ] = {
                "present": 0,
                "absent": 0,
                "total": 0
            }

        student_data = attendance_by_student[
            record.student_id
        ]

        student_data["total"] += 1

        if record.status == "present":
            student_data["present"] += 1

        elif record.status == "absent":
            student_data["absent"] += 1

    # --------------------------------------------------------
    # BUILD REPORT
    # --------------------------------------------------------

    result = []

    total_records = 0
    total_present = 0
    total_absent = 0

    for student in students:

        data = attendance_by_student.get(
            student.id,
            {
                "present": 0,
                "absent": 0,
                "total": 0
            }
        )

        total = data["total"]
        present = data["present"]
        absent = data["absent"]

        percentage = (
            round(
                (present / total) * 100,
                2
            )
            if total > 0
            else 0
        )

        classroom = db.session.get(
            ClassRoom,
            student.class_id
        )

        result.append({
            "student_id": student.id,
            "student_name": student.name,
            "roll_number": student.roll_number,
            "class_id": student.class_id,
            "class_name":
                classroom.name
                if classroom
                else "",
            "section":
                classroom.section
                if classroom
                else "",
            "present": present,
            "absent": absent,
            "total_days": total,
            "attendance_percentage":
                percentage
        })

        total_records += total
        total_present += present
        total_absent += absent

    overall_percentage = (
        round(
            (total_present / total_records) * 100,
            2
        )
        if total_records > 0
        else 0
    )

    return jsonify({
        "success": True,
        "report": {
            "start_date": start_date,
            "end_date": end_date,
            "class_id": selected_class_id,
            "students": result,
            "summary": {
                "total_students":
                    len(result),
                "total_records":
                    total_records,
                "present":
                    total_present,
                "absent":
                    total_absent,
                "attendance_percentage":
                    overall_percentage
            }
        }
    })