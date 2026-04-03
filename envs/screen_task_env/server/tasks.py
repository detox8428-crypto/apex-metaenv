"""Task definitions for Screen Task Environment"""

TASKS = [
    {
        "task_id": "task_001",
        "description": "Open Notepad and type the word 'Python'",
        "app": "Notepad",
        "success_check": "notepad_text_contains:Python",
        "difficulty": "easy"
    },
    {
        "task_id": "task_002",
        "description": "Type 'Hello World' in Notepad",
        "app": "Notepad",
        "success_check": "notepad_text_contains:Hello World",
        "difficulty": "easy"
    },
    {
        "task_id": "task_003",
        "description": "Type the numbers 1 through 10 in Notepad, each on a new line",
        "app": "Notepad",
        "success_check": "notepad_text_contains:10",
        "difficulty": "medium"
    },
    {
        "task_id": "task_004",
        "description": "Type a haiku about programming in Notepad (5-7-5 syllable structure)",
        "app": "Notepad",
        "success_check": "notepad_text_contains:code",
        "difficulty": "medium"
    },
    {
        "task_id": "task_005",
        "description": "Type 'OpenEnv Challenge' in Notepad",
        "app": "Notepad",
        "success_check": "notepad_text_contains:OpenEnv Challenge",
        "difficulty": "easy"
    },
    {
        "task_id": "task_006",
        "description": "Type your name and today's date in Notepad (format: Name - YYYY-MM-DD)",
        "app": "Notepad",
        "success_check": "notepad_text_contains:-",
        "difficulty": "medium"
    },
    {
        "task_id": "task_007",
        "description": "Type a list of 5 programming languages in Notepad",
        "app": "Notepad",
        "success_check": "notepad_text_contains:Python",
        "difficulty": "medium"
    },
    {
        "task_id": "task_008",
        "description": "Type 'AI Agent Learning' in Notepad and make sure text is saved",
        "app": "Notepad",
        "success_check": "notepad_text_contains:AI Agent Learning",
        "difficulty": "medium"
    },
    {
        "task_id": "task_009",
        "description": "Type 'RL Environment' in Notepad",
        "app": "Notepad",
        "success_check": "notepad_text_contains:RL Environment",
        "difficulty": "easy"
    },
    {
        "task_id": "task_010",
        "description": "Type 'Hackathon 2026' in Notepad",
        "app": "Notepad",
        "success_check": "notepad_text_contains:Hackathon 2026",
        "difficulty": "easy"
    }
]


def get_task_by_id(task_id: str):
    """Get a task by its ID"""
    for task in TASKS:
        if task["task_id"] == task_id:
            return task
    return None
