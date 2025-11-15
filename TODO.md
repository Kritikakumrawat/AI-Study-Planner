# TODO: Add Login/Sign-in Page for Users

- [x] Add login and logout views in planner/views.py
- [x] Add login and logout URL patterns in planner/urls.py
- [x] Update planner/templates/planner/base.html to conditionally show login/logout links
- [x] Create planner/templates/planner/login.html template
- [x] Test the login functionality (server running, test user created)

# TODO: Add Signup Page and Update Home Page

- [x] Add signup view in planner/views.py
- [x] Add signup URL pattern in planner/urls.py
- [x] Create planner/templates/planner/signup.html template
- [x] Update planner/templates/planner/base.html to include signup link
- [x] Update planner/templates/planner/login.html to link to signup
- [x] Update planner/templates/planner/signup.html to link to login
- [x] Update studyplanner/settings.py with authentication settings
- [x] Update planner/templates/planner/home.html to show login/signup buttons for unauthenticated users and personalized content for authenticated users

# TODO: Add User Profile with Phone and Email

- [x] Add UserProfile model with phone_number and email in planner/models.py
- [x] Update signup to collect phone and email
- [x] Update login to allow login with username, email, or phone
- [x] Run migrations for UserProfile
