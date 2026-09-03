from extensions import db


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)

    roll_number = db.Column(
        db.Integer,
        nullable=False
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    parent_name = db.Column(
        db.String(100),
        nullable=True
    )

    parent_phone = db.Column(
        db.String(20),
        nullable=True
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="active"
    )

    class_id = db.Column(
        db.Integer,
        db.ForeignKey("classes.id"),
        nullable=False
    )