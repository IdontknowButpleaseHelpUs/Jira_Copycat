





import sys
from pathlib import Path

                           
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Course, CourseEnrollment, User, Team, TeamMember, CourseType
from app.tokens import hash_password as get_password_hash


def seed_courses_and_enrollments():
    db: Session = SessionLocal()
    try:
                                                 
        courses_data = [
                              
            {"code": "CS101", "name": "Introduction to Computer Science", "description": "Fundamentals of computing, algorithms, and programming basics.", "course_type": CourseType.academic},
            {"code": "CS202", "name": "Data Structures and Algorithms", "description": "Advanced data structures, algorithm analysis, and optimization.", "course_type": CourseType.academic},
            {"code": "MATH201", "name": "Discrete Mathematics", "description": "Logic, set theory, combinatorics, and graph theory.", "course_type": CourseType.academic},
                             
            {"code": "PRJ301", "name": "Software Engineering Project", "description": "Team-based software development project with agile methodologies.", "course_type": CourseType.project},
            {"code": "PRJ401", "name": "Capstone Project", "description": "Final year project demonstrating comprehensive engineering skills.", "course_type": CourseType.project},
        ]

        created_courses = {}
        for data in courses_data:
            existing = db.query(Course).filter(Course.code == data["code"]).first()
            if not existing:
                course = Course(**data)
                db.add(course)
                db.flush()
                created_courses[data["code"]] = course
                print(f"Created course: {data['code']} - {data['name']}")
            else:
                created_courses[data["code"]] = existing
                print(f"Course exists: {data['code']}")

                                 
        demo_users = [
            {"handle": "user1", "name": "Name Surname1", "email": "email1@uni.edu", "password": "password123"},
            {"handle": "user2", "name": "Name Surname2", "email": "email2@uni.edu", "password": "password123"},
            {"handle": "user3", "name": "Name Surname3", "password": "password123"},
        ]

        created_users = {}
        for data in demo_users:
            existing = db.query(User).filter(User.handle == data["handle"]).first()
            if not existing:
                email = data.get("email")
                user = User(
                    handle=data["handle"],
                    name=data["name"],
                    email=email if email else None,
                    password_hash=get_password_hash(data["password"]),
                )
                db.add(user)
                db.flush()
                created_users[data["handle"]] = user
                print(f"Created user: {data['handle']}")
            else:
                created_users[data["handle"]] = existing
                print(f"User exists: {data['handle']}")

                                              
        for user in created_users.values():
            for course in created_courses.values():
                existing = (
                    db.query(CourseEnrollment)
                    .filter(
                        CourseEnrollment.course_id == course.id,
                        CourseEnrollment.user_id == user.id,
                    )
                    .first()
                )
                if not existing:
                    enrollment = CourseEnrollment(course_id=course.id, user_id=user.id)
                    db.add(enrollment)
                    print(f"Enrolled {user.handle} in {course.code}")

                                               
        project_courses = [c for c in created_courses.values() if c.course_type == CourseType.project]
        team_counter = 1

        for course in project_courses:
                                                          
            existing_teams = db.query(Team).filter(Team.course_id == course.id).all()
            if existing_teams:
                print(f"Teams already exist for {course.code}")
                continue

                                               
            for team_num in range(1, 3):
                team_name = f"{course.code} Team {team_num}"
                join_code = f"{course.code.lower()}-team{team_num}"

                team = Team(
                    course_id=course.id,
                    name=team_name,
                    description=f"Demo team for {course.name}",
                    join_code=join_code,
                )
                db.add(team)
                db.flush()

                                                                 
                for i, user in enumerate(created_users.values()):
                    role = "supervisor" if i == 0 else "member"
                    member = TeamMember(
                        team_id=team.id,
                        display_name=user.name,
                        handle=user.handle,
                        role_name=role,
                        is_active=True,
                    )
                    db.add(member)

                print(f"Created team: {team_name} in {course.code}")

        db.commit()
        print("\n✅ Seed completed successfully!")
        print(f"Courses: {len(created_courses)}")
        print(f"Users: {len(created_users)}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_courses_and_enrollments()
