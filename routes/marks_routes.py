from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import Marks, Student, ClassRoom, Subject, Exam


marks_bp = Blueprint(
    "marks",
    __name__,
    url_prefix="/api/marks"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_teacher_id():
    return int(get_jwt_identity())


def get_teacher_student(student_id, user_id):
    return (
        Student.query
        .join(ClassRoom)
        .filter(
            Student.id == student_id,
            ClassRoom.teacher_id == user_id
        )
        .first()
    )


def calculate_grade(percentage):
    if percentage >= 90:
        return "A+"
    elif percentage >= 80:
        return "A"
    elif percentage >= 70:
        return "B"
    elif percentage >= 60:
        return "C"
    elif percentage >= 50:
        return "D"
    else:
        return "F"


# ============================================================
# ENTER / UPDATE SINGLE MARK
# ============================================================

@marks_bp.route("", methods=["POST"])
@jwt_required()
def enter_marks():
    data = request.get_json() or {}

    student_id = data.get("student_id")
    subject_id = data.get("subject_id")
    exam_id = data.get("exam_id")
    marks_obtained = data.get("marks_obtained")

    if (
        student_id is None
        or subject_id is None
        or exam_id is None
        or marks_obtained is None
    ):
        return jsonify({
            "success": False,
            "message": "Student, subject, exam and marks are required"
        }), 400

    try:
        student_id = int(student_id)
        subject_id = int(subject_id)
        exam_id = int(exam_id)
        marks_obtained = float(marks_obtained)
        user_id = get_teacher_id()

    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Invalid marks data"
        }), 400

    student = db.session.get(Student, student_id)
    subject = db.session.get(Subject, subject_id)
    exam = db.session.get(Exam, exam_id)

    if not student:
        return jsonify({
            "success": False,
            "message": "Student not found"
        }), 404

    if not subject:
        return jsonify({
            "success": False,
            "message": "Subject not found"
        }), 404

    if not exam:
        return jsonify({
            "success": False,
            "message": "Exam not found"
        }), 404

    classroom = db.session.get(
        ClassRoom,
        student.class_id
    )

    if not classroom or classroom.teacher_id != user_id:
        return jsonify({
            "success": False,
            "message": "You do not have access to this student"
        }), 403

    if subject.class_id != student.class_id:
        return jsonify({
            "success": False,
            "message": "Subject does not belong to student's class"
        }), 400

    if exam.class_id != student.class_id:
        return jsonify({
            "success": False,
            "message": "Exam does not belong to student's class"
        }), 400

    if exam.subject_id != subject_id:
        return jsonify({
            "success": False,
            "message": "Exam does not belong to this subject"
        }), 400

    if marks_obtained < 0:
        return jsonify({
            "success": False,
            "message": "Marks cannot be negative"
        }), 400

    if marks_obtained > exam.max_marks:
        return jsonify({
            "success": False,
            "message": f"Marks cannot be greater than {exam.max_marks}"
        }), 400

    existing = Marks.query.filter_by(
        student_id=student_id,
        subject_id=subject_id,
        exam_id=exam_id
    ).first()

    if existing:
        existing.marks_obtained = marks_obtained
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Marks updated successfully",
            "marks": {
                "id": existing.id,
                "student_id": existing.student_id,
                "subject_id": existing.subject_id,
                "exam_id": existing.exam_id,
                "marks_obtained": existing.marks_obtained
            }
        })

    marks = Marks(
        student_id=student_id,
        subject_id=subject_id,
        exam_id=exam_id,
        marks_obtained=marks_obtained
    )

    db.session.add(marks)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Marks entered successfully",
        "marks": {
            "id": marks.id,
            "student_id": marks.student_id,
            "subject_id": marks.subject_id,
            "exam_id": marks.exam_id,
            "marks_obtained": marks.marks_obtained
        }
    }), 201


# ============================================================
# BULK MARKS - SAVE COMPLETE CLASS REGISTER
# ============================================================

@marks_bp.route("/bulk", methods=["POST"])
@jwt_required()
def bulk_enter_marks():
    data = request.get_json() or {}

    exam_id = data.get("exam_id")
    marks_list = data.get("marks")

    if exam_id is None or not isinstance(marks_list, list):
        return jsonify({
            "success": False,
            "message": "Exam ID and marks list are required"
        }), 400

    try:
        exam_id = int(exam_id)
        user_id = get_teacher_id()
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Invalid exam ID"
        }), 400

    exam = db.session.get(Exam, exam_id)

    if not exam:
        return jsonify({
            "success": False,
            "message": "Exam not found"
        }), 404

    classroom = db.session.get(
        ClassRoom,
        exam.class_id
    )

    if not classroom or classroom.teacher_id != user_id:
        return jsonify({
            "success": False,
            "message": "You do not have access to this exam"
        }), 403

    subject = db.session.get(
        Subject,
        exam.subject_id
    )

    if not subject:
        return jsonify({
            "success": False,
            "message": "Exam subject not found"
        }), 404

    updated_count = 0
    created_count = 0
    skipped_count = 0

    for item in marks_list:
        if not isinstance(item, dict):
            skipped_count += 1
            continue

        student_id = item.get("student_id")
        marks_obtained = item.get("marks_obtained")

        if student_id is None or marks_obtained is None:
            skipped_count += 1
            continue

        try:
            student_id = int(student_id)
            marks_obtained = float(marks_obtained)
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "message": "Invalid student ID or marks"
            }), 400

        student = get_teacher_student(
            student_id,
            user_id
        )

        if not student:
            return jsonify({
                "success": False,
                "message": (
                    f"Student {student_id} not found "
                    "or access denied"
                )
            }), 403

        if student.class_id != exam.class_id:
            return jsonify({
                "success": False,
                "message": (
                    f"Student {student.name} does not "
                    "belong to this exam's class"
                )
            }), 400

        if marks_obtained < 0:
            return jsonify({
                "success": False,
                "message": (
                    f"Marks cannot be negative "
                    f"for {student.name}"
                )
            }), 400

        if marks_obtained > exam.max_marks:
            return jsonify({
                "success": False,
                "message": (
                    f"Marks for {student.name} cannot "
                    f"be greater than {exam.max_marks}"
                )
            }), 400

        existing = Marks.query.filter_by(
            student_id=student_id,
            subject_id=exam.subject_id,
            exam_id=exam_id
        ).first()

        if existing:
            existing.marks_obtained = marks_obtained
            updated_count += 1
        else:
            new_marks = Marks(
                student_id=student_id,
                subject_id=exam.subject_id,
                exam_id=exam_id,
                marks_obtained=marks_obtained
            )

            db.session.add(new_marks)
            created_count += 1

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Class marks saved successfully",
        "created": created_count,
        "updated": updated_count,
        "skipped": skipped_count
    })


# ============================================================
# GET ALL MARKS
# ============================================================

@marks_bp.route("", methods=["GET"])
@jwt_required()
def get_marks():
    user_id = get_teacher_id()

    records = (
        Marks.query
        .join(Student, Marks.student_id == Student.id)
        .join(ClassRoom, Student.class_id == ClassRoom.id)
        .filter(ClassRoom.teacher_id == user_id)
        .all()
    )

    result = []

    for record in records:
        result.append({
            "id": record.id,
            "student_id": record.student_id,
            "subject_id": record.subject_id,
            "exam_id": record.exam_id,
            "marks_obtained": record.marks_obtained
        })

    return jsonify({
        "success": True,
        "marks": result
    })


# ============================================================
# GET EXAM-WISE CLASS REGISTER
# ============================================================

@marks_bp.route(
    "/exam/<int:exam_id>",
    methods=["GET"]
)
@jwt_required()
def get_exam_register(exam_id):
    user_id = get_teacher_id()

    exam = db.session.get(
        Exam,
        exam_id
    )

    if not exam:
        return jsonify({
            "success": False,
            "message": "Exam not found"
        }), 404

    classroom = db.session.get(
        ClassRoom,
        exam.class_id
    )

    if not classroom or classroom.teacher_id != user_id:
        return jsonify({
            "success": False,
            "message": "You do not have access to this exam"
        }), 403

    subject = db.session.get(
        Subject,
        exam.subject_id
    )

    students = (
        Student.query
        .filter(
            Student.class_id == exam.class_id,
            Student.status == "active"
        )
        .order_by(Student.roll_number.asc())
        .all()
    )

    result = []

    for student in students:
        existing = Marks.query.filter_by(
            student_id=student.id,
            subject_id=exam.subject_id,
            exam_id=exam.id
        ).first()

        result.append({
            "student_id": student.id,
            "student_name": student.name,
            "roll_number": student.roll_number,
            "marks_id": existing.id if existing else None,
            "marks_obtained": (
                existing.marks_obtained
                if existing
                else None
            )
        })

    return jsonify({
        "success": True,
        "exam": {
            "id": exam.id,
            "name": exam.name,
            "exam_type": exam.exam_type,
            "exam_date": exam.exam_date.isoformat(),
            "class_id": exam.class_id,
            "subject_id": exam.subject_id,
            "subject_name": (
                subject.name
                if subject
                else None
            ),
            "max_marks": exam.max_marks
        },
        "students": result
    })


# ============================================================
# EXAM RESULT + TOP 3
# ============================================================

@marks_bp.route(
    "/exam/<int:exam_id>/result",
    methods=["GET"]
)
@jwt_required()
def get_exam_result(exam_id):
    user_id = get_teacher_id()

    exam = db.session.get(
        Exam,
        exam_id
    )

    if not exam:
        return jsonify({
            "success": False,
            "message": "Exam not found"
        }), 404

    classroom = db.session.get(
        ClassRoom,
        exam.class_id
    )

    if not classroom or classroom.teacher_id != user_id:
        return jsonify({
            "success": False,
            "message": "You do not have access to this exam"
        }), 403

    students = (
        Student.query
        .filter(
            Student.class_id == exam.class_id,
            Student.status == "active"
        )
        .order_by(Student.roll_number.asc())
        .all()
    )

    result = []

    for student in students:
        record = Marks.query.filter_by(
            student_id=student.id,
            subject_id=exam.subject_id,
            exam_id=exam.id
        ).first()

        obtained = (
            record.marks_obtained
            if record
            else None
        )

        percentage = (
            round(
                (obtained / exam.max_marks) * 100,
                2
            )
            if obtained is not None
            and exam.max_marks > 0
            else 0
        )

        result.append({
            "student_id": student.id,
            "student_name": student.name,
            "roll_number": student.roll_number,
            "marks_obtained": obtained,
            "max_marks": exam.max_marks,
            "percentage": percentage,
            "grade": (
                calculate_grade(percentage)
                if obtained is not None
                else None
            )
        })

    ranked = [
        item for item in result
        if item["marks_obtained"] is not None
    ]

    ranked.sort(
        key=lambda item: item["marks_obtained"],
        reverse=True
    )

    for index, item in enumerate(ranked):
        item["rank"] = index + 1

    top_three = ranked[:3]

    return jsonify({
        "success": True,
        "exam": {
            "id": exam.id,
            "name": exam.name,
            "exam_type": exam.exam_type,
            "max_marks": exam.max_marks
        },
        "students": result,
        "top_3": top_three
    })


# ============================================================
# GET STUDENT FINAL RESULT
# ============================================================

@marks_bp.route(
    "/final/<int:student_id>",
    methods=["GET"]
)
@jwt_required()
def get_final_result(student_id):
    user_id = get_teacher_id()

    student = get_teacher_student(
        student_id,
        user_id
    )

    if not student:
        return jsonify({
            "success": False,
            "message": "Student not found"
        }), 404

    exams = (
        Exam.query
        .filter(
            Exam.class_id == student.class_id
        )
        .order_by(
            Exam.exam_date.asc(),
            Exam.id.asc()
        )
        .all()
    )

    if not exams:
        return jsonify({
            "success": True,
            "unlocked": False,
            "message": "No exams found for this class"
        })

    exam_results = []
    total_marks = 0
    maximum_marks = 0

    completed_exams = 0

    for exam in exams:
        record = Marks.query.filter_by(
            student_id=student.id,
            subject_id=exam.subject_id,
            exam_id=exam.id
        ).first()

        if record:
            completed_exams += 1

            total_marks += record.marks_obtained
            maximum_marks += exam.max_marks

            exam_results.append({
                "exam_id": exam.id,
                "exam_name": exam.name,
                "exam_type": exam.exam_type,
                "subject_id": exam.subject_id,
                "marks_obtained": record.marks_obtained,
                "max_marks": exam.max_marks
            })
        else:
            exam_results.append({
                "exam_id": exam.id,
                "exam_name": exam.name,
                "exam_type": exam.exam_type,
                "subject_id": exam.subject_id,
                "marks_obtained": None,
                "max_marks": exam.max_marks
            })

    active_students = (
        Student.query
        .filter(
            Student.class_id == student.class_id,
            Student.status == "active"
        )
        .all()
    )

    all_complete = True

    for exam in exams:
        for class_student in active_students:
            record = Marks.query.filter_by(
                student_id=class_student.id,
                subject_id=exam.subject_id,
                exam_id=exam.id
            ).first()

            if not record:
                all_complete = False
                break

        if not all_complete:
            break

    if not all_complete:
        return jsonify({
            "success": True,
            "unlocked": False,
            "student": {
                "id": student.id,
                "name": student.name,
                "roll_number": student.roll_number
            },
            "completed_exams": completed_exams,
            "total_exams": len(exams),
            "message": (
                "Final result is locked until all "
                "class exams are completed"
            )
        })

    percentage = (
        round(
            (total_marks / maximum_marks) * 100,
            2
        )
        if maximum_marks > 0
        else 0
    )

    grade = calculate_grade(
        percentage
    )

    return jsonify({
        "success": True,
        "unlocked": True,
        "student": {
            "id": student.id,
            "name": student.name,
            "roll_number": student.roll_number
        },
        "result": {
            "total_marks": total_marks,
            "maximum_marks": maximum_marks,
            "percentage": percentage,
            "grade": grade,
            "completed_exams": completed_exams,
            "total_exams": len(exams),
            "exams": exam_results
        }
    })


# ============================================================
# FINAL CLASS RESULT + TOP 3
# ============================================================

@marks_bp.route(
    "/final/class/<int:class_id>",
    methods=["GET"]
)
@jwt_required()
def get_final_class_result(class_id):
    user_id = get_teacher_id()

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

    exams = (
        Exam.query
        .filter(
            Exam.class_id == class_id
        )
        .order_by(
            Exam.exam_date.asc(),
            Exam.id.asc()
        )
        .all()
    )

    students = (
        Student.query
        .filter(
            Student.class_id == class_id,
            Student.status == "active"
        )
        .order_by(
            Student.roll_number.asc()
        )
        .all()
    )

    if not exams:
        return jsonify({
            "success": True,
            "unlocked": False,
            "message": "No exams found for this class"
        })

    all_complete = True

    for exam in exams:
        for student in students:
            record = Marks.query.filter_by(
                student_id=student.id,
                subject_id=exam.subject_id,
                exam_id=exam.id
            ).first()

            if not record:
                all_complete = False
                break

        if not all_complete:
            break

    if not all_complete:
        return jsonify({
            "success": True,
            "unlocked": False,
            "message": (
                "Final result is locked until all "
                "class exams are completed"
            )
        })

    final_results = []

    for student in students:
        total_marks = 0
        maximum_marks = 0

        for exam in exams:
            record = Marks.query.filter_by(
                student_id=student.id,
                subject_id=exam.subject_id,
                exam_id=exam.id
            ).first()

            if record:
                total_marks += record.marks_obtained
                maximum_marks += exam.max_marks

        percentage = (
            round(
                (total_marks / maximum_marks) * 100,
                2
            )
            if maximum_marks > 0
            else 0
        )

        final_results.append({
            "student_id": student.id,
            "student_name": student.name,
            "roll_number": student.roll_number,
            "total_marks": total_marks,
            "maximum_marks": maximum_marks,
            "percentage": percentage,
            "grade": calculate_grade(percentage)
        })

    final_results.sort(
        key=lambda item: item["percentage"],
        reverse=True
    )

    for index, item in enumerate(final_results):
        item["rank"] = index + 1

    return jsonify({
        "success": True,
        "unlocked": True,
        "class_id": class_id,
        "total_exams": len(exams),
        "students": final_results,
        "top_3": final_results[:3]
    })


# ============================================================
# STUDENT RESULT - OLD ENDPOINT PRESERVED
# ============================================================

@marks_bp.route(
    "/student/<int:student_id>",
    methods=["GET"]
)
@jwt_required()
def get_student_result(student_id):
    user_id = get_teacher_id()

    student = get_teacher_student(
        student_id,
        user_id
    )

    if not student:
        return jsonify({
            "success": False,
            "message": "Student not found"
        }), 404

    records = Marks.query.filter_by(
        student_id=student_id
    ).all()

    total_marks = sum(
        record.marks_obtained
        for record in records
    )

    max_marks = 0

    for record in records:
        exam = db.session.get(
            Exam,
            record.exam_id
        )

        if exam:
            max_marks += exam.max_marks

    percentage = (
        round(
            (total_marks / max_marks) * 100,
            2
        )
        if max_marks > 0
        else 0
    )

    grade = calculate_grade(
        percentage
    )

    return jsonify({
        "success": True,
        "student": {
            "id": student.id,
            "name": student.name
        },
        "result": {
            "total_marks": total_marks,
            "maximum_marks": max_marks,
            "percentage": percentage,
            "grade": grade
        }
    })


# ============================================================
# UPDATE MARKS
# ============================================================

@marks_bp.route(
    "/<int:marks_id>",
    methods=["PUT"]
)
@jwt_required()
def update_marks(marks_id):
    user_id = get_teacher_id()

    marks = (
        Marks.query
        .join(
            Student,
            Marks.student_id == Student.id
        )
        .join(
            ClassRoom,
            Student.class_id == ClassRoom.id
        )
        .filter(
            Marks.id == marks_id,
            ClassRoom.teacher_id == user_id
        )
        .first()
    )

    if not marks:
        return jsonify({
            "success": False,
            "message": "Marks record not found"
        }), 404

    data = request.get_json() or {}

    if "marks_obtained" not in data:
        return jsonify({
            "success": False,
            "message": "marks_obtained is required"
        }), 400

    try:
        new_marks = float(
            data["marks_obtained"]
        )
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Marks must be a number"
        }), 400

    exam = db.session.get(
        Exam,
        marks.exam_id
    )

    if new_marks < 0:
        return jsonify({
            "success": False,
            "message": "Marks cannot be negative"
        }), 400

    if exam and new_marks > exam.max_marks:
        return jsonify({
            "success": False,
            "message": (
                f"Marks cannot be greater than "
                f"{exam.max_marks}"
            )
        }), 400

    marks.marks_obtained = new_marks

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Marks updated successfully"
    })


# ============================================================
# DELETE MARKS
# ============================================================

@marks_bp.route(
    "/<int:marks_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_marks(marks_id):
    user_id = get_teacher_id()

    marks = (
        Marks.query
        .join(
            Student,
            Marks.student_id == Student.id
        )
        .join(
            ClassRoom,
            Student.class_id == ClassRoom.id
        )
        .filter(
            Marks.id == marks_id,
            ClassRoom.teacher_id == user_id
        )
        .first()
    )

    if not marks:
        return jsonify({
            "success": False,
            "message": "Marks record not found"
        }), 404

    db.session.delete(marks)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Marks deleted successfully"
    })