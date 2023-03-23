# easygrade-flask-server

To run the app type 

flask --app easygrade-flask-server

### API

### /api/v1.0/assignments

This endpoint returns all assignments in the database. The endpoint takes the following optional query parameters:

* `user_id` - The id of the user to filter by
* `course_id` - The id of the course to filter by

### /api/v1.0/assignments/<int:assignment_id>

This endpoint returns a single assignment with the given id.

### /api/v1.0/assignments/<int:assignment_id>/submissions

This endpoint returns all submissions for a given assignment. The endpoint takes the following optional query parameters:

* `user_id` - The id of the user to filter by

### /api/v1.0/assignments/<int:assignment_id>/submissions/<int:submission_id>

This endpoint returns a single submission for a given assignment.

### /api/v1.0/assignments/<int:assignment_id>/submissions/<int:submission_id>/results

This endpoint returns the result for a given submission.

### /api/v1.0/courses

This endpoint returns all courses in the database. The endpoint takes the following optional query parameters:

* `user_id` - The id of the user to filter by

### /api/v1.0/courses/<int:course_id>

This endpoint returns a single course with the given id.

### /api/v1.0/courses/<int:course_id>/assignments

This endpoint returns all assignments for a given course.

### /api/v1.0/courses/<int:course_id>/users

This endpoint returns all users for a given course.

### /api/v1.0/users

This endpoint returns all users in the database. The endpoint takes the following optional query parameters:

* `course_id` - The id of the course to filter by

### /api/v1.0/users/<int:user_id>

This endpoint returns a single user with the given id.

### /api/v1.0/users/<int:user_id>/courses

This endpoint returns all courses for a given user.

### /api/v1.0/users/<int:user_id>/assignments

This endpoint returns all assignments for a given user