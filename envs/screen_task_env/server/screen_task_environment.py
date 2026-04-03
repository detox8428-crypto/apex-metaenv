"""Screen Task Environment Implementation"""

import subprocess
import time
import base64
import io
import random
import pyautogui
import mss
import pyperclip
from PIL import Image
from typing import Tuple
from ..models import ScreenAction, ScreenObservation, ScreenState
from .tasks import TASKS, get_task_by_id


class ScreenTaskEnvironment:
    """GUI interaction environment where an agent learns to control Notepad"""

    def __init__(self):
        """Initialize the environment"""
        self.current_task = None
        self.notepad_process = None
        self.state = ScreenState()
        self.step_count = 0
        self.max_steps = 50
        self.sct = mss.mss()
        
        # Disable pyautogui safety features for faster automation
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.05

    def reset(self) -> ScreenObservation:
        """Reset environment: close any existing Notepad, pick random task, launch Notepad, take screenshot"""
        # Close any existing Notepad
        self._close_notepad()
        time.sleep(0.5)
        
        # Pick a random task
        self.current_task = random.choice(TASKS)
        self.state.task_id = self.current_task["task_id"]
        self.state.task_description = self.current_task["description"]
        self.step_count = 0
        
        # Launch Notepad
        try:
            self.notepad_process = subprocess.Popen(["notepad.exe"])
            self.state.app_handle = self.notepad_process.pid
            self.state.is_running = True
        except Exception as e:
            raise RuntimeError(f"Failed to launch Notepad: {e}")
        
        # Wait for Notepad to fully load
        time.sleep(1.5)
        
        # Take initial screenshot
        screenshot_b64 = self._capture_screenshot()
        
        observation = ScreenObservation(
            screenshot_b64=screenshot_b64,
            task=self.current_task["description"],
            last_action_result="Episode started",
            step_num=self.step_count
        )
        
        return observation

    def step(self, action: ScreenAction) -> Tuple[ScreenObservation, float, bool]:
        """
        Execute an action and return observation, reward, and done flag
        
        Args:
            action: ScreenAction with action_type, coordinates, text, or keys
            
        Returns:
            (observation, reward, done): Tuple of observation, reward (0.0 or 1.0), and episode end flag
        """
        self.step_count += 1
        action_result = ""
        
        try:
            # Execute the action
            if action.action_type == "click":
                pyautogui.click(action.x, action.y)
                action_result = f"Clicked at ({action.x}, {action.y})"
                
            elif action.action_type == "type":
                pyautogui.typewrite(action.text, interval=0.01)
                action_result = f"Typed: {action.text}"
                
            elif action.action_type == "hotkey":
                # Parse hotkey string like "ctrl+a" or "ctrl+c"
                keys = action.keys.lower().split("+")
                pyautogui.hotkey(*keys)
                action_result = f"Hotkey pressed: {action.keys}"
                
            elif action.action_type == "submit":
                action_result = "Task completed (submit action)"
                
            else:
                action_result = f"Unknown action type: {action.action_type}"
            
            # Small delay for action to take effect
            time.sleep(0.3)
            
        except Exception as e:
            action_result = f"Action failed: {str(e)}"
        
        # Take screenshot after action
        screenshot_b64 = self._capture_screenshot()
        
        # Check if task is completed
        success = self._check_success()
        reward = 1.0 if success else 0.0
        done = success or self.step_count >= self.max_steps
        
        observation = ScreenObservation(
            screenshot_b64=screenshot_b64,
            task=self.current_task["description"],
            last_action_result=action_result,
            step_num=self.step_count
        )
        
        return observation, reward, done

    def _capture_screenshot(self) -> str:
        """Capture current screen and encode to base64"""
        try:
            monitor = self.sct.monitors[1]  # Primary monitor
            screenshot = self.sct.grab(monitor)
            
            # Convert to PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
            # Encode to base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            return img_b64
            
        except Exception as e:
            raise RuntimeError(f"Screenshot capture failed: {e}")

    def _check_success(self) -> bool:
        """Check if current task is completed based on success_check condition"""
        if not self.current_task:
            return False
        
        success_check = self.current_task.get("success_check", "")
        
        if not success_check or ":" not in success_check:
            return False
        
        check_type, check_value = success_check.split(":", 1)
        
        if check_type == "notepad_text_contains":
            try:
                # Select all text in Notepad
                pyautogui.hotkey("ctrl", "a")
                time.sleep(0.1)
                
                # Copy to clipboard
                pyautogui.hotkey("ctrl", "c")
                time.sleep(0.1)
                
                # Get clipboard content
                content = pyperclip.paste()
                
                # Deselect (click somewhere in Notepad)
                pyautogui.click(400, 300)
                
                # Check if required text is in content
                return check_value in content
                
            except Exception as e:
                return False
        
        return False

    def _close_notepad(self):
        """Close the Notepad process"""
        if self.notepad_process:
            try:
                self.notepad_process.terminate()
                self.notepad_process.wait(timeout=2)
            except:
                try:
                    self.notepad_process.kill()
                except:
                    pass
            self.notepad_process = None

    @property
    def state_property(self) -> ScreenState:
        """Get current environment state"""
        return self.state

    def close(self):
        """Clean up resources"""
        self._close_notepad()
        if self.sct:
            self.sct.close()
