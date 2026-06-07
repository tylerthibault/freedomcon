"""Quick script to create/reset the admin user."""
from run import create_app

app = create_app()
with app.app_context():
    from src.models.main import AdminUser, db
    user = db.session.execute(
        db.select(AdminUser).where(AdminUser.username == "admin")
    ).scalar_one_or_none()
    if not user:
        user = AdminUser(username="admin")
        db.session.add(user)
    user.set_password("admin")
    db.session.commit()
    print("Admin user ready — username: admin  password: admin")
    print("Change the password after first login via flask create-admin")
