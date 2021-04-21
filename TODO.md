# [!] Workout API

Workout validation:

- if Routine is specified make sure that all exercise belongs to that routine, and all routine exercises are part of workout
- if Routine is specified make sure that user is Routine owner

WorkoutLogEntry validation:

- make sure that additional values are compatible with exercise type
- make sure that user is an owner of the exercise

# Important improvements

- handle fetch more wisely (reuse logic, create function)
- fix infinite forking bug (only backend involved)
- switch JWT from local storage to cookie (remember about HTTP flag?)

# Exercise tab refactoring:

- add can_be_edited property to exercise
- disable access to edit not your exercise page
- fix no feedback on trying to edit exercise name that already exist
- rewrite exercise table using library (fix responsiveness)
- add tutorials carousele to exercise detail

# Routine tab refactoring:

- fix object mutation in exercise table properties

# Before deploy:

- different handling of static / media files
- stronger password validation (more than 4 characters)

# Keep in mind

- Object.freeze for form data

* [ctrl + left arrow] collapse explorer
