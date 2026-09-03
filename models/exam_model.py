from extensions import db


class Exam(db.Model):
    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        nullable=False
    )

    exam_type = db.Column(
        db.String(50),
        nullable=False
    )

    exam_date = db.Column(
        db.Date,
        nullable=False
    )

    class_id = db.Column(
        db.Integer,
        db.ForeignKey("classes.id"),
        nullable=False
    )

    subject_id = db.Column(
        db.Integer,
        db.ForeignKey("subjects.id"),
        nullable=False
    )

    max_marks = db.Column(
        db.Float,
        nullable=False
    )

    classroom = db.relationship(
        "ClassRoom",
        backref="exams"
    )

    subject = db.relationship(
        "Subject",
        backref="exams"
    )