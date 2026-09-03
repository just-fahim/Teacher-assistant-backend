from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from extensions import db, migrate, jwt


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Models
    from models import (
    User,
    ClassRoom,
    Student,
    Subject,
    Attendance,
    Homework,
    Exam,
    Marks,
    Syllabus,
    Notification
)

    # Authentication routes
    from routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp)

    # Class routes
    from routes.class_routes import class_bp
    app.register_blueprint(class_bp)

    # Student routes
    from routes.students_routes import student_bp
    app.register_blueprint(student_bp)

    # Subject routes
    from routes.subjects_routes import subject_bp
    app.register_blueprint(subject_bp)

    # Attendance routes
    from routes.attendance_routes import attendance_bp
    app.register_blueprint(attendance_bp)

    # Homework routes
    from routes.homework_routes import homework_bp
    app.register_blueprint(homework_bp)

    # Exam routes
    from routes.exam_routes import exam_bp
    app.register_blueprint(exam_bp)

    # Marks routes
    from routes.marks_routes import marks_bp
    app.register_blueprint(marks_bp)

    # Syllabus routes
    from routes.syllabus_routes import syllabus_bp
    app.register_blueprint(syllabus_bp)

    # Report routes
    from routes.reports_routes import report_bp
    app.register_blueprint(report_bp)

    # Notification routes
    from routes.notification_routes import notification_bp
    app.register_blueprint(notification_bp)

    # User routes
    from routes.user_routes import user_bp
    app.register_blueprint(user_bp)

    @app.route("/")
    def home():
        return jsonify({
            "success": True,
            "message": "Teacher Assistant API is running"
        })

    @app.route("/api/health")
    def health():
        try:
            with db.engine.connect() as connection:
                connection.execute(db.text("SELECT 1"))

            return jsonify({
                "success": True,
                "database": "connected"
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "database": "connection failed",
                "error": str(e)
            }), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)