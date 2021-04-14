from lorem_text import lorem

EXERCISES_USER_1 = [
    {
        "name": "push ups",
        "kind": "rep",
        "instructions": "Remember about hollow body position.",
        "tags": ["easy", "popular"],
        "tutorials": [10],
        "muscles": ["pec", "tri"],
    },
    {
        "name": "pull ups",
        "kind": "rep",
        "instructions": "Tense your core during movement.",
        "tags": ["medium", "popular"],
        "tutorials": [20],
        "muscles": ["lat", "bic", "sca"],
    },
    {
        "name": "bulgarian split squat",
        "kind": "rep",
        "instructions": lorem.words(10),
        "tags": ["legs"],
        "tutorials": [21, 22, 23],
        "muscles": ["qua", "glu"],
    },
    {
        "name": "romanian single leg deadlift",
        "kind": "rep",
        "instructions": lorem.words(20),
        "tags": ["legs"],
        "muscles": ["ham", "lob"],
    },
    {
        "name": "pistol squat",
        "kind": "rep",
        "instructions": lorem.words(30),
        "forks_count": 12,
        "tags": ["legs", "hard", "mobility"],
        "muscles": ["qua", "glu"],
    },
    {
        "name": "sumo walk",
        "kind": "rew",
        "instructions": lorem.words(100),
        "forks_count": 8,
        "tags": ["legs"],
        "muscles": ["qua"],
    },
    {
        "name": "calf raises",
        "kind": "rep",
        "instructions": "To increase difficulty you can stand on the step.",
        "tags": ["legs"],
        "muscles": ["cal"],
    },
    {
        "name": "squat",
        "kind": "rew",
        "instructions": "Keep your back straight, maintain external knee rotation.",
        "tags": ["legs", "strength"],
        "muscles": ["glu", "qua"],
        "tutorials": [50, 51, 52],
    },
    {
        "name": "jogging",
        "kind": "dis",
        "instructions": "Jogging at low pace.",
        "tags": ["endurance"],
        "muscles": ["qua", "glu", "ham"],
        "forks_count": 2,
    },
    {
        "name": "lunges",
        "kind": "rep",
        "tags": ["legs"],
        "muscles": ["glu", "qua", "ham"],
    },
    {
        "name": "step ups",
        "kind": "rep",
        "tags": ["legs"],
        "muscles": ["glu"],
    },
    {
        "name": "box jumps",
        "kind": "rep",
        "tags": ["legs"],
        "muscles": ["glu"],
    },
    {
        "name": "bridge",
        "kind": "tim",
        "tags": ["mobility"],
        "muscles": ["lob"],
    },
    {
        "name": "dance",
        "kind": "tim",
        "tags": ["popular"],
    },
    {
        "name": "intervals run",
        "kind": "tim",
    },
    {
        "name": "hip thrust",
        "kind": "rew",
        "tutorials": [17, 29, 41],
        "instructions": "Good for your muchacha`s.",
    },
]

EXERCISES_USER_2 = [
    {"name": "bench press", "kind": "rew"},
    {"name": "planche", "kind": "tim"},
    {"name": "diamond push ups", "kind": "rep"},
    {"name": "pike push ups", "kind": "rep"},
    {"name": "archer push ups", "kind": "rep"},
    {"name": "sphinx push ups", "kind": "rep"},
    {"name": "hindu push ups", "kind": "rep"},
    {"name": "one arm push ups", "kind": "rep"},
    {"name": "push ups", "kind": "rep"},
    {"name": "pull ups", "kind": "rep"},
    {
        "name": "plank",
        "kind": "tim",
        "instructions": "Arms should be straight.",
        "tutorials": [60, 61],
        "muscles": ["abs"],
    },
]

ROUTINES_USER_1 = [
    {
        "name": "Leg workout A",
        "kind": "sta",
        "instructions": "This is the first leg workout.",
        "forks_count": 5,
        "exercises": [
            {"name": "bulgarian split squat", "sets": 3},
            {"name": "romanian single leg deadlift", "sets": 3},
            {"name": "pistol squat", "sets": 3},
            {"name": "lunges", "sets": 3},
            {"name": "box jumps", "sets": 3},
        ],
    },
    {
        "name": "Leg workout B",
        "kind": "cir",
        "instructions": "My favourite leg workout.",
        "exercises": [
            {"name": "bridge", "sets": 3, "instructions": lorem.words(5)},
            {"name": "hip thrust", "sets": 3, "instructions": lorem.words(10)},
            {"name": "step ups", "sets": 5, "instructions": lorem.words(20)},
            {"name": "jogging", "sets": 5, "instructions": lorem.words(40)},
        ],
    },
    {"name": "Push A", "kind": "sta", "forks_count": 11},
    {"name": "Push B", "kind": "sta"},
    {"name": "Push C", "kind": "sta"},
    {"name": "Push D", "kind": "sta"},
    {"name": "Pull A", "kind": "sta", "forks_count": 3},
    {"name": "Pull B", "kind": "sta", "forks_count": 2},
    {"name": "Pull C", "kind": "sta"},
    {"name": "Pull D", "kind": "sta"},
    {"name": "FBW A", "kind": "sta", "forks_count": 1},
    {"name": "FBW B", "kind": "sta"},
    {"name": "FBW C", "kind": "sta"},
    {"name": "FBW D", "kind": "sta"},
]

for i in range(30):
    ROUTINES_USER_1.append({"name": f"Routine {i}", "kind": "sta"})

ROUTINES_USER_2 = [
    {"name": "Chest, triceps and shoulders", "kind": "sta"},
    {"name": "Arms", "kind": "cir"},
    {"name": "Upper body (bodyweight)", "kind": "sta"},
    {"name": "Upper body (weights)", "kind": "sta"},
    {"name": "Powerlifting", "kind": "sta", "forks_count": 3},
    {"name": "Begginers", "kind": "sta", "forks_count": 2},
    {"name": "Advanced abs", "kind": "sta"},
    {"name": "Quads, hamstrings", "kind": "sta"},
    {"name": "Endurance", "kind": "sta", "forks_count": 1},
    {"name": "Full body", "kind": "cir"},
    {"name": "Strenght", "kind": "sta"},
    {"name": "Hypertrophy", "kind": "sta"},
]

WORKOUTS_USER_1 = [
    {
        "date": "2020-12-01",
        "completed": True,
        "exercises": [
            {"exercise": "push ups", "set_number": 1, "reps": 10},
            {"exercise": "push ups", "set_number": 2, "reps": 10},
            {"exercise": "push ups", "set_number": 3, "reps": 10},
            {"exercise": "pull ups", "set_number": 1, "reps": 15},
            {"exercise": "pull ups", "set_number": 2, "reps": 10},
            {"exercise": "pull ups", "set_number": 3, "reps": 5},
            {"exercise": "intervals run", "set_number": 1, "time": 3600},
        ],
    },
    {
        "date": "2020-12-08",
        "completed": True,
        "routine": "Leg workout A",
        "exercises": [
            {"exercise": "bulgarian split squat", "set_number": 1, "reps": 8},
            {"exercise": "bulgarian split squat", "set_number": 2, "reps": 8},
            {"exercise": "bulgarian split squat", "set_number": 3, "reps": 8},
            {"exercise": "romanian single leg deadlift", "set_number": 1, "reps": 8},
            {"exercise": "romanian single leg deadlift", "set_number": 2, "reps": 8},
            {"exercise": "romanian single leg deadlift", "set_number": 3, "reps": 8},
            {"exercise": "pistol squat", "set_number": 1, "reps": 8},
            {"exercise": "pistol squat", "set_number": 2, "reps": 8},
            {"exercise": "pistol squat", "set_number": 3, "reps": 8},
            {"exercise": "lunges", "set_number": 1, "reps": 8},
            {"exercise": "lunges", "set_number": 2, "reps": 8},
            {"exercise": "lunges", "set_number": 3, "reps": 8},
            {"exercise": "box jumps", "set_number": 1, "reps": 8},
            {"exercise": "box jumps", "set_number": 2, "reps": 8},
            {"exercise": "box jumps", "set_number": 3, "reps": 8},
        ],
    },
]

WORKOUTS_USER_2 = []