"""Coding problems for Code Solver Environment"""

PROBLEMS = [
    # ==================== EASY ====================
    {
        "problem_id": "p001",
        "title": "Two Sum",
        "difficulty": "easy",
        "description": "Given an array of integers nums and an integer target, return the indices of the two numbers that add up to target. You may assume each input has exactly one solution. You may not use the same element twice.",
        "function_signature": "def two_sum(nums, target):",
        "examples": "Example 1:\nInput: nums = [2, 7, 11, 15], target = 9\nOutput: [0, 1]\nExplanation: nums[0] + nums[1] = 2 + 7 = 9\n\nExample 2:\nInput: nums = [3, 2, 4], target = 6\nOutput: [1, 2]\nExplanation: nums[1] + nums[2] = 2 + 4 = 6",
        "constraints": "2 <= len(nums) <= 10^4, -10^9 <= nums[i] <= 10^9, -10^9 <= target <= 10^9",
        "test_cases": [
            {"input": {"nums": [2, 7, 11, 15], "target": 9}, "expected": [0, 1]},
            {"input": {"nums": [3, 2, 4], "target": 6}, "expected": [1, 2]},
            {"input": {"nums": [3, 3], "target": 6}, "expected": [0, 1]},
            {"input": {"nums": [1, 2, 3, 4, 5], "target": 9}, "expected": [3, 4]},
            {"input": {"nums": [-1, -2, -3, 5, 10], "target": 7}, "expected": [3, 4]},
        ],
        "solution_template": "def two_sum(nums, target):\n    # Your solution here\n    pass"
    },
    {
        "problem_id": "p002",
        "title": "Palindrome Check",
        "difficulty": "easy",
        "description": "Given a string s, determine if it is a palindrome, considering only alphanumeric characters and ignoring cases. Return True if it is, False otherwise.",
        "function_signature": "def is_palindrome(s):",
        "examples": "Example 1:\nInput: s = \"A man, a plan, a canal: Panama\"\nOutput: True\n\nExample 2:\nInput: s = \"race a car\"\nOutput: False",
        "constraints": "1 <= len(s) <= 2*10^5, s consists of ASCII characters",
        "test_cases": [
            {"input": {"s": "A man, a plan, a canal: Panama"}, "expected": True},
            {"input": {"s": "race a car"}, "expected": False},
            {"input": {"s": "0P"}, "expected": False},
            {"input": {"s": "a"}, "expected": True},
            {"input": {"s": "aba"}, "expected": True},
        ],
        "solution_template": "def is_palindrome(s):\n    # Your solution here\n    pass"
    },
    {
        "problem_id": "p003",
        "title": "FizzBuzz",
        "difficulty": "easy",
        "description": "Given an integer n, return a list of strings representing numbers from 1 to n. For multiples of 3, return 'Fizz', for multiples of 5 return 'Buzz', for multiples of both return 'FizzBuzz'.",
        "function_signature": "def fizz_buzz(n):",
        "examples": "Example 1:\nInput: n = 3\nOutput: [\"1\", \"2\", \"Fizz\"]\n\nExample 2:\nInput: n = 5\nOutput: [\"1\", \"2\", \"Fizz\", \"4\", \"Buzz\"]",
        "constraints": "1 <= n <= 10^4",
        "test_cases": [
            {"input": {"n": 3}, "expected": ["1", "2", "Fizz"]},
            {"input": {"n": 5}, "expected": ["1", "2", "Fizz", "4", "Buzz"]},
            {"input": {"n": 15}, "expected": ["1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz", "11", "Fizz", "13", "14", "FizzBuzz"]},
            {"input": {"n": 1}, "expected": ["1"]},
            {"input": {"n": 6}, "expected": ["1", "2", "Fizz", "4", "Buzz", "Fizz"]},
        ],
        "solution_template": "def fizz_buzz(n):\n    # Your solution here\n    pass"
    },
    # ==================== MEDIUM ====================
    {
        "problem_id": "p004",
        "title": "Longest Substring Without Repeating Characters",
        "difficulty": "medium",
        "description": "Given a string s, find the length of the longest substring without repeating characters.",
        "function_signature": "def length_of_longest_substring(s):",
        "examples": "Example 1:\nInput: s = \"abcabcbb\"\nOutput: 3\nExplanation: \"abc\" has length 3\n\nExample 2:\nInput: s = \"bbbbb\"\nOutput: 1\nExplanation: \"b\" has length 1",
        "constraints": "0 <= len(s) <= 5*10^4, s consists of ASCII characters",
        "test_cases": [
            {"input": {"s": "abcabcbb"}, "expected": 3},
            {"input": {"s": "bbbbb"}, "expected": 1},
            {"input": {"s": "pwwkew"}, "expected": 3},
            {"input": {"s": ""}, "expected": 0},
            {"input": {"s": "au"}, "expected": 2},
        ],
        "solution_template": "def length_of_longest_substring(s):\n    # Your solution here\n    pass"
    },
    {
        "problem_id": "p005",
        "title": "Valid Parentheses",
        "difficulty": "medium",
        "description": "Given a string s containing '(', ')', '{', '}', '[', ']', determine if it is valid. A valid string has properly matched and ordered brackets.",
        "function_signature": "def is_valid(s):",
        "examples": "Example 1:\nInput: s = \"()\"\nOutput: True\n\nExample 2:\nInput: s = \"()[]{}\"\nOutput: True\n\nExample 3:\nInput: s = \"(]\"\nOutput: False",
        "constraints": "1 <= len(s) <= 10^4, s contains only brackets",
        "test_cases": [
            {"input": {"s": "()"}, "expected": True},
            {"input": {"s": "()[]{}"},"expected": True},
            {"input": {"s": "(]"}, "expected": False},
            {"input": {"s": "([)]"}, "expected": False},
            {"input": {"s": "{[]}"}, "expected": True},
        ],
        "solution_template": "def is_valid(s):\n    # Your solution here\n    pass"
    },
    {
        "problem_id": "p006",
        "title": "Maximum Subarray",
        "difficulty": "medium",
        "description": "Given an integer array nums, find the contiguous subarray with the largest sum and return that sum. Use Kadane's algorithm.",
        "function_signature": "def max_sub_array(nums):",
        "examples": "Example 1:\nInput: nums = [-2, 1, -3, 4, -1, 2, 1, -5, 4]\nOutput: 6\nExplanation: [4, -1, 2, 1] has maximum sum 6\n\nExample 2:\nInput: nums = [5, 4, -1, 7, 8]\nOutput: 23",
        "constraints": "1 <= len(nums) <= 10^5, -10^4 <= nums[i] <= 10^4",
        "test_cases": [
            {"input": {"nums": [-2, 1, -3, 4, -1, 2, 1, -5, 4]}, "expected": 6},
            {"input": {"nums": [5, 4, -1, 7, 8]}, "expected": 23},
            {"input": {"nums": [-1]}, "expected": -1},
            {"input": {"nums": [1, 2, 3, 4, 5]}, "expected": 15},
            {"input": {"nums": [-2, -1, -3]}, "expected": -1},
        ],
        "solution_template": "def max_sub_array(nums):\n    # Your solution here (Kadane's algorithm)\n    pass"
    },
    # ==================== HARD ====================
    {
        "problem_id": "p007",
        "title": "Merge K Sorted Lists",
        "difficulty": "hard",
        "description": "Given k sorted lists (represented as lists of integers), merge them into one sorted list.",
        "function_signature": "def merge_k_lists(lists):",
        "examples": "Example 1:\nInput: lists = [[1, 4, 5], [1, 3, 4], [2, 6]]\nOutput: [1, 1, 2, 3, 4, 4, 5, 6]\n\nExample 2:\nInput: lists = []\nOutput: []",
        "constraints": "k == len(lists), 0 <= k <= 10^4, each list is sorted in ascending order",
        "test_cases": [
            {"input": {"lists": [[1, 4, 5], [1, 3, 4], [2, 6]]}, "expected": [1, 1, 2, 3, 4, 4, 5, 6]},
            {"input": {"lists": []}, "expected": []},
            {"input": {"lists": [[]]}, "expected": []},
            {"input": {"lists": [[1], [2], [3]]}, "expected": [1, 2, 3]},
            {"input": {"lists": [[1, 2, 3], [4, 5, 6]]}, "expected": [1, 2, 3, 4, 5, 6]},
        ],
        "solution_template": "def merge_k_lists(lists):\n    # Your solution here\n    pass"
    },
    {
        "problem_id": "p008",
        "title": "Trapping Rain Water",
        "difficulty": "hard",
        "description": "Given n non-negative integers representing elevation map where width of bar is 1, compute how much water it can trap after raining.",
        "function_signature": "def trap_water(height):",
        "examples": "Example 1:\nInput: height = [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]\nOutput: 6\n\nExample 2:\nInput: height = [4, 2, 0, 3, 2, 5]\nOutput: 9",
        "constraints": "n == len(height), 0 <= height[i] <= 10^4",
        "test_cases": [
            {"input": {"height": [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]}, "expected": 6},
            {"input": {"height": [4, 2, 0, 3, 2, 5]}, "expected": 9},
            {"input": {"height": [2, 0, 2]}, "expected": 2},
            {"input": {"height": []}, "expected": 0},
            {"input": {"height": [3]}, "expected": 0},
        ],
        "solution_template": "def trap_water(height):\n    # Your solution here\n    pass"
    },
    {
        "problem_id": "p009",
        "title": "Word Break",
        "difficulty": "hard",
        "description": "Given a string s and a list of words word_dict, return True if s can be segmented into words from the dictionary. Words can be reused.",
        "function_signature": "def word_break(s, word_dict):",
        "examples": "Example 1:\nInput: s = \"leetcode\", word_dict = [\"leet\", \"code\"]\nOutput: True\n\nExample 2:\nInput: s = \"applepenapple\", word_dict = [\"apple\", \"pen\"]\nOutput: True",
        "constraints": "1 <= len(s) <= 300, 1 <= len(word_dict) <= 1000, words may repeat",
        "test_cases": [
            {"input": {"s": "leetcode", "word_dict": ["leet", "code"]}, "expected": True},
            {"input": {"s": "applepenapple", "word_dict": ["apple", "pen"]}, "expected": True},
            {"input": {"s": "catsandog", "word_dict": ["cat", "cats", "and", "sand", "dog"]}, "expected": False},
            {"input": {"s": "a", "word_dict": ["a"]}, "expected": True},
            {"input": {"s": "ab", "word_dict": ["a"]}, "expected": False},
        ],
        "solution_template": "def word_break(s, word_dict):\n    # Your solution here (dynamic programming recommended)\n    pass"
    }
]


def get_problem_by_id(problem_id: str):
    """Get a problem by its ID"""
    for problem in PROBLEMS:
        if problem["problem_id"] == problem_id:
            return problem
    return None


def get_problems_by_difficulty(difficulty: str):
    """Get all problems of a given difficulty"""
    return [p for p in PROBLEMS if p["difficulty"] == difficulty]
