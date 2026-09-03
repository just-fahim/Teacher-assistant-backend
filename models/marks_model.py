from extensions import db


class Marks(db.Model):
    __tablename__ = "marks"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id"),
        nullable=False
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subjects.id"),
        nullable=False
    )

    exam_id = db.Column(
        db.Integer,
        db.ForeignKey("exams.id"),
        nullable=False
    )

    marks_obtained = db.Column(
        db.Float,
        nullable=False
    )

    student = db.relationship(
        "Student",
        backref="marks_records"
    )

    subject = db.relationship(
        "Subject",
        backref="marks_records"
    )

    exam = db.relationship(
        "Exam",
        backref="marks_records"
    )