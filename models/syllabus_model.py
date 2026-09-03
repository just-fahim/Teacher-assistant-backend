from extensions import db


class Syllabus(db.Model):
    __tablename__ = "syllabus"

    id = db.Column(db.Integer, primary_key=True)

    chapter_name = db.Column(
        db.String(200),
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

    target_date = db.Column(
        db.Date,
        nullable=True
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="pending"
    )

    completion_percentage = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    classroom = db.relationship(
        "ClassRoom",
        backref="syllabus_items"
    )

    subject = db.relationship(
        "Subject",
        backref="syllabus_items"
    )