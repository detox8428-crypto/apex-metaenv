"""
Code Generator & AI Assistant Module
=====================================
Generates code, fixes bugs, refactors, explains code using OpenAI

Features:
- Code generation from natural language
- Bug fixing and debugging
- Code refactoring
- Code explanation
- Multiple language support
- Syntax checking
- Test generation
"""

import os
import re
import logging
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

# Try importing OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not available")


class CodeTask(Enum):
    """Code task types"""
    GENERATE = "generate"  # Generate code from description
    FIX = "fix"  # Fix bugs in code
    REFACTOR = "refactor"  # Improve code quality
    EXPLAIN = "explain"  # Explain what code does
    OPTIMIZE = "optimize"  # Optimize for performance
    TEST = "test"  # Generate tests
    DOCUMENT = "document"  # Add documentation


class CodeGenerator:
    """AI-powered code generation and analysis"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.enabled = False
        self.total_tokens = 0
        self.total_cost = 0.0
        
        self.pricing = {
            "gpt-4": {"input": 0.03 / 1000, "output": 0.06 / 1000},
            "gpt-3.5-turbo": {"input": 0.0005 / 1000, "output": 0.0015 / 1000}
        }
        
        if OPENAI_AVAILABLE and self.api_key:
            openai.api_key = self.api_key
            self.enabled = True
            logger.info("✅ Code Generator (OpenAI) enabled")
        else:
            logger.warning("⚠️ Code Generator disabled")
    
    def _extract_code_blocks(self, response: str) -> List[str]:
        """Extract code blocks from response"""
        
        # Find markdown code blocks
        pattern = r'```[\w]*\n(.*?)\n```'
        blocks = re.findall(pattern, response, re.DOTALL)
        
        if blocks:
            return blocks
        
        # If no markdown blocks, try to find code-like content
        if any(kw in response for kw in ["def ", "class ", "function ", "import ", "async "]):
            return [response]
        
        return []
    
    def generate(self, description: str, language: str = "python",
                context: Optional[str] = None, model: str = "gpt-3.5-turbo") -> Dict:
        """
        Generate code from description
        
        Args:
            description: What code should do
            language: Programming language (python, javascript, java, etc.)
            context: Additional context/requirements
            model: OpenAI model
        
        Returns:
            {"success": bool, "code": str, "explanation": str, ...}
        """
        
        if not self.enabled:
            return {"success": False, "error": "Code Generator not configured"}
        
        try:
            prompt = f"""You are an expert {language} programmer. 

Generate clean, well-documented {language} code that does the following:
{description}

{f'Additional context: {context}' if context else ''}

Requirements:
- Include comments explaining key parts
- Use best practices and conventions for {language}
- Make it production-ready
- Include error handling where appropriate

Respond with only the code in a markdown code block."""
            
            logger.info(f"Generating {language} code: {description[:50]}...")
            
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": f"You are an expert {language} programmer. Generate clean, well-documented code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            code = response.choices[0].message.content.strip()
            code_blocks = self._extract_code_blocks(code)
            
            if code_blocks:
                generated_code = code_blocks[0]
            else:
                generated_code = code
            
            tokens = response.usage.total_tokens
            cost = (response.usage.prompt_tokens * self.pricing[model]["input"] +
                   response.usage.completion_tokens * self.pricing[model]["output"])
            
            self.total_tokens += tokens
            self.total_cost += cost
            
            return {
                "success": True,
                "code": generated_code,
                "language": language,
                "description": description,
                "model": model,
                "tokens": tokens,
                "cost": round(cost, 6),
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Code generation error: {e}")
            return {"success": False, "error": str(e)}
    
    def fix_bug(self, code: str, issue: str, language: str = "python",
               model: str = "gpt-3.5-turbo") -> Dict:
        """
        Fix bug in code
        
        Args:
            code: Code with bug
            issue: Description of the bug
            language: Programming language
            model: OpenAI model
        
        Returns:
            {"success": bool, "fixed_code": str, "explanation": str, ...}
        """
        
        if not self.enabled:
            return {"success": False, "error": "Code Generator not configured"}
        
        try:
            prompt = f"""You are an expert {language} programmer and debugger.

I have a bug in my {language} code:
{issue}

Here's the code:
```{language}
{code}
```

Please:
1. Identify the bug(s)
2. Provide the fixed code
3. Explain what was wrong and how you fixed it

Format your response as:
BUGS FOUND:
- [list bugs]

FIXED CODE:
[code in markdown]

EXPLANATION:
[explanation]"""
            
            logger.info(f"Fixing {language} code bug: {issue[:50]}...")
            
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": f"You are an expert {language} debugger. Find and fix bugs precisely."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            analysis = response.choices[0].message.content.strip()
            code_blocks = self._extract_code_blocks(analysis)
            
            fixed_code = code_blocks[0] if code_blocks else code
            
            tokens = response.usage.total_tokens
            cost = (response.usage.prompt_tokens * self.pricing[model]["input"] +
                   response.usage.completion_tokens * self.pricing[model]["output"])
            
            self.total_tokens += tokens
            self.total_cost += cost
            
            return {
                "success": True,
                "original_code": code,
                "fixed_code": fixed_code,
                "analysis": analysis,
                "language": language,
                "issue": issue,
                "tokens": tokens,
                "cost": round(cost, 6),
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Bug fix error: {e}")
            return {"success": False, "error": str(e)}
    
    def refactor(self, code: str, language: str = "python",
                goals: Optional[str] = None, model: str = "gpt-3.5-turbo") -> Dict:
        """
        Refactor code for quality
        
        Args:
            code: Code to refactor
            language: Programming language
            goals: Refactoring goals (readability, performance, simplicity, etc.)
            model: OpenAI model
        
        Returns:
            {"success": bool, "refactored_code": str, "improvements": list, ...}
        """
        
        if not self.enabled:
            return {"success": False, "error": "Code Generator not configured"}
        
        try:
            goals_text = f"Focus on: {goals}" if goals else "Focus on: readability, maintainability, and performance"
            
            prompt = f"""You are an expert code reviewer.

Refactor this {language} code for better quality:
```{language}
{code}
```

{goals_text}

Please:
1. Provide the refactored code
2. List the improvements made
3. Explain why these changes are beneficial

Format:
REFACTORED CODE:
[code]

IMPROVEMENTS:
- [improvement 1]
- [improvement 2]
...

RATIONALE:
[explanation]"""
            
            logger.info(f"Refactoring {language} code...")
            
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": f"You are an expert code reviewer. Refactor code following best practices."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            analysis = response.choices[0].message.content.strip()
            code_blocks = self._extract_code_blocks(analysis)
            
            refactored_code = code_blocks[0] if code_blocks else code
            
            tokens = response.usage.total_tokens
            cost = (response.usage.prompt_tokens * self.pricing[model]["input"] +
                   response.usage.completion_tokens * self.pricing[model]["output"])
            
            self.total_tokens += tokens
            self.total_cost += cost
            
            return {
                "success": True,
                "original_code": code,
                "refactored_code": refactored_code,
                "analysis": analysis,
                "language": language,
                "goals": goals or "general improvement",
                "tokens": tokens,
                "cost": round(cost, 6),
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Refactoring error: {e}")
            return {"success": False, "error": str(e)}
    
    def explain(self, code: str, language: str = "python",
               model: str = "gpt-3.5-turbo") -> Dict:
        """Explain what code does"""
        
        if not self.enabled:
            return {"success": False, "error": "Code Generator not configured"}
        
        try:
            prompt = f"""Explain this {language} code:
```{language}
{code}
```

Provide:
1. High-level summary
2. What each section does
3. Key functions/methods explained
4. Input/output explanation
5. Any important details to know"""
            
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Explain code clearly and thoroughly"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            explanation = response.choices[0].message.content.strip()
            
            tokens = response.usage.total_tokens
            cost = (response.usage.prompt_tokens * self.pricing[model]["input"] +
                   response.usage.completion_tokens * self.pricing[model]["output"])
            
            self.total_tokens += tokens
            self.total_cost += cost
            
            return {
                "success": True,
                "explanation": explanation,
                "language": language,
                "tokens": tokens,
                "cost": round(cost, 6),
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Explanation error: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_tests(self, code: str, language: str = "python",
                      test_framework: Optional[str] = None,
                      model: str = "gpt-3.5-turbo") -> Dict:
        """Generate unit tests for code"""
        
        if not self.enabled:
            return {"success": False, "error": "Code Generator not configured"}
        
        try:
            framework = test_framework or ("pytest" if language == "python" else "jest")
            
            prompt = f"""Generate comprehensive unit tests for this {language} code using {framework}:
```{language}
{code}
```

Create:
1. Tests for normal cases
2. Edge case tests
3. Error/exception tests
4. At least 5-10 test cases

Format the tests in a markdown code block."""
            
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": f"Generate high-quality {language} unit tests"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1200
            )
            
            analysis = response.choices[0].message.content.strip()
            code_blocks = self._extract_code_blocks(analysis)
            
            tests = code_blocks[0] if code_blocks else analysis
            
            tokens = response.usage.total_tokens
            cost = (response.usage.prompt_tokens * self.pricing[model]["input"] +
                   response.usage.completion_tokens * self.pricing[model]["output"])
            
            self.total_tokens += tokens
            self.total_cost += cost
            
            return {
                "success": True,
                "tests": tests,
                "language": language,
                "framework": framework,
                "tokens": tokens,
                "cost": round(cost, 6),
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Test generation error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_stats(self) -> Dict:
        """Get usage stats"""
        return {
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 6),
            "currency": "USD",
            "status": "✅ Active" if self.enabled else "⚠️ Disabled"
        }


class CodeGeneratorManager:
    """Manages code generation"""
    
    def __init__(self):
        self.generator = CodeGenerator()
        self.enabled = self.generator.enabled
    
    def generate(self, description: str, language: str = "python",
                context: Optional[str] = None) -> Dict:
        """Generate code"""
        return self.generator.generate(description, language, context)
    
    def fix_bug(self, code: str, issue: str, language: str = "python") -> Dict:
        """Fix bug"""
        return self.generator.fix_bug(code, issue, language)
    
    def refactor(self, code: str, language: str = "python",
                goals: Optional[str] = None) -> Dict:
        """Refactor code"""
        return self.generator.refactor(code, language, goals)
    
    def explain(self, code: str, language: str = "python") -> Dict:
        """Explain code"""
        return self.generator.explain(code, language)
    
    def generate_tests(self, code: str, language: str = "python",
                      test_framework: Optional[str] = None) -> Dict:
        """Generate tests"""
        return self.generator.generate_tests(code, language, test_framework)
    
    def get_status(self) -> Dict:
        """Get status"""
        stats = self.generator.get_stats()
        stats["provider"] = "OpenAI"
        stats["supported_languages"] = ["python", "javascript", "java", "cpp", "go", "rust", "sql"]
        return stats


# Global manager instance
code_generator_manager = CodeGeneratorManager()


if __name__ == "__main__":
    # Demo
    print("Code Generator Module")
    print("=" * 50)
    print(code_generator_manager.get_status())
    print("\nUsage:")
    print("1. Generate code: code_generator_manager.generate('description')")
    print("2. Fix bugs: code_generator_manager.fix_bug(code, issue)")
    print("3. Refactor: code_generator_manager.refactor(code)")
    print("4. Explain: code_generator_manager.explain(code)")
    print("5. Generate tests: code_generator_manager.generate_tests(code)")
