"""Coding problems for Code Solver Environment with procedural generation"""

import random
import string
from typing import Dict, Any, List, Tuple


# ============================================================================
# CANONICAL PROBLEMS (9 hand-curated)
# ============================================================================

CANONICAL_PROBLEMS = [
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
        "solution_template": "def two_sum(nums, target):\n    # Your solution here\n    pass",
        "source": "canonical"
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
        "solution_template": "def is_palindrome(s):\n    # Your solution here\n    pass",
        "source": "canonical"
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
        "solution_template": "def fizz_buzz(n):\n    # Your solution here\n    pass",
        "source": "canonical"
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
        "solution_template": "def length_of_longest_substring(s):\n    # Your solution here\n    pass",
        "source": "canonical"
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
            {"input": {"s": "()[]{}"}, "expected": True},
            {"input": {"s": "(]"}, "expected": False},
            {"input": {"s": "([)]"}, "expected": False},
            {"input": {"s": "{[]}"}, "expected": True},
        ],
        "solution_template": "def is_valid(s):\n    # Your solution here\n    pass",
        "source": "canonical"
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
        "solution_template": "def max_sub_array(nums):\n    # Your solution here (Kadane's algorithm)\n    pass",
        "source": "canonical"
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
        "solution_template": "def merge_k_lists(lists):\n    # Your solution here\n    pass",
        "source": "canonical"
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
        "solution_template": "def trap_water(height):\n    # Your solution here\n    pass",
        "source": "canonical"
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
        "solution_template": "def word_break(s, word_dict):\n    # Your solution here (dynamic programming recommended)\n    pass",
        "source": "canonical"
    }
]

# Keep reference for backward compatibility
PROBLEMS = CANONICAL_PROBLEMS


# ============================================================================
# PROCEDURAL PROBLEM GENERATOR
# ============================================================================

class ProceduralProblemGenerator:
    """Generate randomized problem variants from templates"""

    def __init__(self, seed: int = None):
        """
        Initialize the generator with a seed.
        
        Args:
            seed: Random seed for deterministic generation. If None, use random seed.
        """
        if seed is None:
            seed = random.randint(0, 2**31 - 1)
        self.seed = seed
        random.seed(seed)

    def generate(self, problem_type: str, difficulty: str) -> Dict[str, Any]:
        """
        Generate a procedural problem.
        
        Args:
            problem_type: Type of problem (two_sum, palindrome, sorting, string_search, math, tree, dp)
            difficulty: Difficulty level (easy, medium, hard)
            
        Returns:
            Problem dictionary with problem_id, title, description, test_cases, etc.
        """
        generators = {
            "two_sum": self._generate_two_sum,
            "palindrome": self._generate_palindrome,
            "sorting": self._generate_sorting,
            "string_search": self._generate_string_search,
            "math": self._generate_math,
            "tree": self._generate_tree,
            "dp": self._generate_dp,
        }

        if problem_type not in generators:
            raise ValueError(f"Unknown problem type: {problem_type}")

        return generators[problem_type](difficulty)

    def _generate_two_sum(self, difficulty: str) -> Dict[str, Any]:
        """Generate Two Sum variant"""
        # Randomize parameters
        size = random.randint(10, 1000) if difficulty == "easy" else random.randint(100, 5000)
        min_val = random.randint(-1000, -100)
        max_val = random.randint(100, 1000)
        allow_duplicates = random.choice([True, False])

        # Generate array
        if allow_duplicates:
            arr = [random.randint(min_val, max_val) for _ in range(size)]
        else:
            arr = random.sample(range(min_val, max_val), min(size, max_val - min_val + 1))

        # Pick valid pair
        i, j = random.sample(range(len(arr)), 2)
        target = arr[i] + arr[j]

        # Test cases (10-20)
        test_cases = [
            {"input": {"nums": arr, "target": target}, "expected": sorted([i, j])}
        ]

        # Add edge cases
        test_cases.extend(self._generate_two_sum_edge_cases(arr[:10], target))

        problem_id = f"two_sum_v{self.seed}"
        return {
            "problem_id": problem_id,
            "title": f"Two Sum (Random v{self.seed})",
            "difficulty": difficulty,
            "description": f"Find two numbers in array of {len(arr)} elements that sum to {target}. Array values range from {min_val} to {max_val}. Duplicates {'allowed' if allow_duplicates else 'not allowed'}.",
            "function_signature": "def two_sum(nums, target):",
            "examples": f"Example:\nInput: nums = {arr[:5]}..., target = {target}\nOutput: [{i}, {j}]",
            "constraints": f"{len(arr)} numbers, target = {target}, range [{min_val}, {max_val}]",
            "test_cases": test_cases[:20],  # Cap at 20
            "solution_template": "def two_sum(nums, target):\n    # Your solution here\n    pass",
            "source": "procedural"
        }

    def _generate_two_sum_edge_cases(self, sample_arr: List[int], target: int) -> List[Dict]:
        """Generate edge case test cases for two_sum"""
        cases = []
        for i in range(min(5, len(sample_arr))):
            for j in range(i + 1, min(5, len(sample_arr))):
                if sample_arr[i] + sample_arr[j] == target:
                    cases.append({
                        "input": {"nums": sample_arr, "target": target},
                        "expected": sorted([i, j])
                    })
        return cases

    def _generate_palindrome(self, difficulty: str) -> Dict[str, Any]:
        """Generate Palindrome variant"""
        length = random.randint(10, 100) if difficulty == "easy" else random.randint(100, 500)
        
        # Determine character set
        if difficulty == "easy":
            charset = string.ascii_letters + " "
        else:
            charset = string.ascii_letters + string.digits + " .,!?"

        # Generate non-palindrome
        front = ''.join(random.choices(charset, k=length // 2))
        s = front + ''.join(random.choices(charset, k=length % 2)) + front[::-1]

        # Optionally make it a palindrome
        if random.choice([True, False]):
            is_pal = True
        else:
            is_pal = False
            s = front + random.choice(charset) + front

        test_cases = [
            {"input": {"s": s}, "expected": is_pal}
        ]

        # Add edge cases
        test_cases.append({"input": {"s": "a"}, "expected": True})
        test_cases.append({"input": {"s": "ab"}, "expected": False})
        test_cases.append({"input": {"s": "aba"}, "expected": True})
        test_cases.append({"input": {"s": "A man, a plan, a canal: Panama"}, "expected": True})

        problem_id = f"palindrome_v{self.seed}"
        return {
            "problem_id": problem_id,
            "title": f"Palindrome Check (Random v{self.seed})",
            "difficulty": difficulty,
            "description": f"Check if string is palindrome (ignore spaces/punctuation, case-insensitive). Length ~{length}.",
            "function_signature": "def is_palindrome(s):",
            "examples": f"Example:\nInput: s = \"{s[:30]}...\"\nOutput: {is_pal}",
            "constraints": f"String length ~{length}, characters: {charset[:10]}...",
            "test_cases": test_cases[:20],
            "solution_template": "def is_palindrome(s):\n    # Your solution here\n    pass",
            "source": "procedural"
        }

    def _generate_sorting(self, difficulty: str) -> Dict[str, Any]:
        """Generate Sorting variant"""
        size = random.randint(10, 100) if difficulty == "easy" else random.randint(100, 1000)
        min_val = random.randint(-1000, -100)
        max_val = random.randint(100, 1000)
        reverse = random.choice([True, False])

        arr = [random.randint(min_val, max_val) for _ in range(size)]
        expected = sorted(arr, reverse=reverse)

        test_cases = [
            {"input": {"nums": arr}, "expected": expected}
        ]

        # Edge cases
        test_cases.extend([
            {"input": {"nums": [1]}, "expected": [1]},
            {"input": {"nums": [3, 1, 2]}, "expected": [1, 2, 3] if not reverse else [3, 2, 1]},
            {"input": {"nums": []}, "expected": []},
        ])

        problem_id = f"sorting_v{self.seed}"
        direction = "descending" if reverse else "ascending"
        return {
            "problem_id": problem_id,
            "title": f"Sort Array ({direction.capitalize()}) v{self.seed}",
            "difficulty": difficulty,
            "description": f"Sort array of {len(arr)} numbers in {direction} order.",
            "function_signature": "def sort_array(nums):",
            "examples": f"Example:\nInput: {arr[:5]}...\nOutput: {expected[:5]}...",
            "constraints": f"Array size: {len(arr)}, range: [{min_val}, {max_val}], order: {direction}",
            "test_cases": test_cases[:20],
            "solution_template": "def sort_array(nums):\n    # Your solution here\n    pass",
            "source": "procedural"
        }

    def _generate_string_search(self, difficulty: str) -> Dict[str, Any]:
        """Generate String Search variant"""
        text_len = random.randint(100, 500) if difficulty == "easy" else random.randint(500, 5000)
        pattern_len = random.randint(3, 20)
        
        text = ''.join(random.choices(string.ascii_lowercase, k=text_len))
        pattern = ''.join(random.choices(string.ascii_lowercase, k=pattern_len))

        # Sometimes add pattern to text
        if random.choice([True, True, False]):  # 67% chance
            idx = random.randint(0, len(text) - pattern_len)
            text = text[:idx] + pattern + text[idx + pattern_len:]
            expected_count = text.count(pattern)
        else:
            expected_count = 0

        test_cases = [
            {"input": {"text": text, "pattern": pattern}, "expected": expected_count}
        ]

        # Edge cases
        test_cases.extend([
            {"input": {"text": "aaaa", "pattern": "aa"}, "expected": 3},
            {"input": {"text": "abc", "pattern": "xyz"}, "expected": 0},
        ])

        problem_id = f"string_search_v{self.seed}"
        return {
            "problem_id": problem_id,
            "title": f"String Search v{self.seed}",
            "difficulty": difficulty,
            "description": f"Find number of non-overlapping occurrences of pattern in text.",
            "function_signature": "def count_pattern(text, pattern):",
            "examples": f"Example:\nInput: text = \"{text[:30]}...\", pattern = \"{pattern}\"\nOutput: {expected_count}",
            "constraints": f"Text length: {text_len}, pattern length: {pattern_len}",
            "test_cases": test_cases[:20],
            "solution_template": "def count_pattern(text, pattern):\n    # Your solution here\n    pass",
            "source": "procedural"
        }

    def _generate_math(self, difficulty: str) -> Dict[str, Any]:
        """Generate Math/Sequence variant"""
        if difficulty == "easy":
            # Fibonacci
            n = random.randint(5, 20)
            
            def fib(x):
                if x <= 1:
                    return x
                a, b = 0, 1
                for _ in range(x - 1):
                    a, b = b, a + b
                return b

            expected = fib(n)
            test_cases = [
                {"input": {"n": n}, "expected": expected},
                {"input": {"n": 0}, "expected": 0},
                {"input": {"n": 1}, "expected": 1},
                {"input": {"n": 5}, "expected": 5},
            ]
            func_name = "fibonacci"
        else:
            # Primes
            limit = random.randint(100, 500)

            def count_primes(x):
                if x < 2:
                    return 0
                sieve = [True] * x
                sieve[0] = sieve[1] = False
                for i in range(2, int(x**0.5) + 1):
                    if sieve[i]:
                        for j in range(i*i, x, i):
                            sieve[j] = False
                return sum(sieve)

            expected = count_primes(limit)
            test_cases = [
                {"input": {"n": limit}, "expected": expected},
                {"input": {"n": 10}, "expected": 4},  # 2, 3, 5, 7
                {"input": {"n": 0}, "expected": 0},
            ]
            func_name = "count_primes"

        problem_id = f"math_v{self.seed}"
        return {
            "problem_id": problem_id,
            "title": f"{func_name.replace('_', ' ').title()} v{self.seed}",
            "difficulty": difficulty,
            "description": f"Compute {func_name} for given input.",
            "function_signature": f"def {func_name}(n):",
            "examples": f"Example:\nInput: n = {n if difficulty == 'easy' else limit}\nOutput: {expected}",
            "constraints": f"Input range varies by problem type",
            "test_cases": test_cases[:20],
            "solution_template": f"def {func_name}(n):\n    # Your solution here\n    pass",
            "source": "procedural"
        }

    def _generate_tree(self, difficulty: str) -> Dict[str, Any]:
        """Generate Tree variant (medium/hard)"""
        height = random.randint(2, 5) if difficulty == "medium" else random.randint(3, 6)

        def make_tree(h):
            if h == 0:
                return None
            return {
                "val": random.randint(1, 100),
                "left": make_tree(h - 1),
                "right": make_tree(h - 1)
            }

        tree = make_tree(height)

        def tree_height(node):
            if node is None:
                return -1
            return 1 + max(tree_height(node.get("left")), tree_height(node.get("right")))

        expected = tree_height(tree)

        test_cases = [
            {"input": {"root": tree}, "expected": expected},
            {"input": {"root": None}, "expected": -1},
            {"input": {"root": {"val": 1, "left": None, "right": None}}, "expected": 0},
        ]

        problem_id = f"tree_v{self.seed}"
        return {
            "problem_id": problem_id,
            "title": f"Tree Height v{self.seed}",
            "difficulty": difficulty,
            "description": f"Find height of binary tree (height = max edge count from root to leaf).",
            "function_signature": "def tree_height(root):",
            "examples": "Example:\nInput: tree with height 3\nOutput: 3",
            "constraints": f"Tree height up to {height}",
            "test_cases": test_cases[:20],
            "solution_template": "def tree_height(root):\n    # Your solution here\n    pass",
            "source": "procedural"
        }

    def _generate_dp(self, difficulty: str) -> Dict[str, Any]:
        """Generate Dynamic Programming variant (hard)"""
        # Coin Change
        coins = sorted(random.sample(range(1, 20), random.randint(2, 5)))
        amount = random.randint(10, 100)

        def coin_change(coins_list, amt):
            dp = [float('inf')] * (amt + 1)
            dp[0] = 0
            for coin in coins_list:
                for i in range(coin, amt + 1):
                    dp[i] = min(dp[i], dp[i - coin] + 1)
            return dp[amt] if dp[amt] != float('inf') else -1

        expected = coin_change(coins, amount)

        test_cases = [
            {"input": {"coins": coins, "amount": amount}, "expected": expected},
            {"input": {"coins": [1], "amount": 0}, "expected": 0},
            {"input": {"coins": [2], "amount": 3}, "expected": -1},
        ]

        problem_id = f"dp_v{self.seed}"
        return {
            "problem_id": problem_id,
            "title": f"Coin Change v{self.seed}",
            "difficulty": difficulty,
            "description": f"Find minimum coins needed to make amount {amount} using coins {coins}.",
            "function_signature": "def coin_change(coins, amount):",
            "examples": f"Example:\nInput: coins = {coins}, amount = {amount}\nOutput: {expected}",
            "constraints": f"Coins: {coins}, amount: {amount}",
            "test_cases": test_cases[:20],
            "solution_template": "def coin_change(coins, amount):\n    # Your solution here (DP recommended)\n    pass",
            "source": "procedural"
        }


def get_canonical_problem(problem_id: str) -> Dict[str, Any]:
    """Get a canonical problem by ID"""
    for problem in CANONICAL_PROBLEMS:
        if problem["problem_id"] == problem_id:
            return problem
    return None


def get_problem_by_id(problem_id: str) -> Dict[str, Any]:
    """Get a problem by ID (canonical or procedural)"""
    # First try canonical
    for problem in CANONICAL_PROBLEMS:
        if problem["problem_id"] == problem_id:
            return problem
    
    # If not found and ID looks procedural, try to regenerate it
    if "_v" in problem_id:
        base_name, seed_str = problem_id.rsplit("_v", 1)
        try:
            seed = int(seed_str)
            gen = ProceduralProblemGenerator(seed=seed)
            return gen.generate(base_name, "easy")  # Default to easy
        except (ValueError, KeyError):
            pass

    return None


def get_problems_by_difficulty(difficulty: str) -> List[Dict[str, Any]]:
    """Get all canonical problems of a given difficulty"""
    return [p for p in CANONICAL_PROBLEMS if p["difficulty"] == difficulty]


def get_random_canonical_problem(difficulty: str = None) -> Dict[str, Any]:
    """Get a random canonical problem, optionally filtered by difficulty"""
    if difficulty:
        problems = get_problems_by_difficulty(difficulty)
    else:
        problems = CANONICAL_PROBLEMS
    
    return random.choice(problems) if problems else None

