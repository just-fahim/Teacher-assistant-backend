from extensions import db


class ClassRoom(db.Model):
    __tablename__ = "classes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(10), nullable=False)
    academic_year = db.Column(db.String(20), nullable=False)

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    students = db.relationship(
        "Student",
        backref="classroom",
        lazy=True
    )

    subjects = db.relationship(
        "Subject",
        backref="classroom",
        lazy=True
    )