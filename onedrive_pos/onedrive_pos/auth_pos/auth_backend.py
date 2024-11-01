from django.contrib.auth.backends import ModelBackend
from auth_pos.models import User
from django.contrib.sessions.models import Session
from datetime import datetime, timedelta

class RememberMeAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None):
        if request is None or not hasattr(request, 'COOKIES'):
            return None

        try:
            print(f"Authenticating user: {username}")
            user = User.objects.get(username=username)
            print(f"User object retrieved: {user}")
            if user.check_password(password):
                print("Password is valid")
                # Check if the user has a valid session
                session_key = request.COOKIES.get('sessionid')
                if session_key:
                    session = Session.objects.get(session_key=session_key)
                    if session.expire_date > datetime.now():
                        # The user has a valid session, so we can log them in
                        print("User has a valid session")
                        return user
                else:
                    # The user doesn't have a valid session
                    print("User doesn't have a valid session")
                    return "SESSION_EXPIRED"
            else:
                print("Password is invalid")
        except User.DoesNotExist:
            print("User does not exist")
            return None