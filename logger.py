#!/usr/bin/python3

"""
Logger module for Blues Goal Horn application.
Handles all logging functionality including activity tracking and error logging.
"""

import json
import os
from datetime import datetime
from config import LOG_DIR, HISTORY_FILE, ERROR_LOG_FILE, LOG_DATE_FORMAT

def ensure_log_files():
    """Ensure log directory and files exist."""
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Create history file if it doesn't exist
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w') as f:
            f.write('')
    
    # Create error log if it doesn't exist
    if not os.path.exists(ERROR_LOG_FILE):
        with open(ERROR_LOG_FILE, 'w') as f:
            f.write('')

def log_activity(action, message='', user_agent=''):
    """
    Log an activity (button press, sound played, etc).
    
    Args:
        action (str): The action name (e.g., 'powerplay', 'stop', 'volume_up')
        message (str): Optional message describing the action
        user_agent (str): Optional user agent or source
    """
    try:
        ensure_log_files()
        
        entry = {
            'timestamp': datetime.now().strftime(LOG_DATE_FORMAT),
            'action': action,
            'message': message,
            'source': user_agent or 'web_ui'
        }
        
        with open(HISTORY_FILE, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    except Exception as e:
        log_error(f'Failed to log activity: {action}', str(e))

def log_error(context, error_message):
    """
    Log an error message.
    
    Args:
        context (str): Context or description of where error occurred
        error_message (str): The error message
    """
    try:
        ensure_log_files()
        
        entry = {
            'timestamp': datetime.now().strftime(LOG_DATE_FORMAT),
            'context': context,
            'error': error_message
        }
        
        with open(ERROR_LOG_FILE, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    except Exception as e:
        print(f"CRITICAL: Failed to log error: {e}")

def get_recent_history(count=10):
    """
    Get the most recent activities.
    
    Args:
        count (int): Number of recent activities to retrieve
    
    Returns:
        list: List of activity dictionaries
    """
    try:
        if not os.path.exists(HISTORY_FILE):
            return []
        
        activities = []
        with open(HISTORY_FILE, 'r') as f:
            lines = f.readlines()
        
        # Get the last 'count' lines
        for line in lines[-count:]:
            try:
                activities.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
        
        return activities
    
    except Exception as e:
        log_error('get_recent_history', str(e))
        return []

def get_activity_summary():
    """
    Get a summary of all activities (count by action type).
    
    Returns:
        dict: Dictionary with action names as keys and counts as values
    """
    try:
        if not os.path.exists(HISTORY_FILE):
            return {}
        
        summary = {}
        with open(HISTORY_FILE, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    action = entry.get('action', 'unknown')
                    summary[action] = summary.get(action, 0) + 1
                except json.JSONDecodeError:
                    continue
        
        return summary
    
    except Exception as e:
        log_error('get_activity_summary', str(e))
        return {}

def get_stats():
    """
    Get comprehensive statistics about the application.
    
    Returns:
        dict: Dictionary with various statistics
    """
    try:
        summary = get_activity_summary()
        recent = get_recent_history(10)
        
        total_actions = sum(summary.values())
        
        return {
            'total_actions': total_actions,
            'summary': summary,
            'recent_actions': recent
        }
    
    except Exception as e:
        log_error('get_stats', str(e))
        return {
            'total_actions': 0,
            'summary': {},
            'recent_actions': []
        }

def clear_history():
    """Clear all activity history."""
    try:
        ensure_log_files()
        with open(HISTORY_FILE, 'w') as f:
            f.write('')
        return True
    except Exception as e:
        log_error('clear_history', str(e))
        return False

def get_history_file_size():
    """Get the size of the history file in MB."""
    try:
        if os.path.exists(HISTORY_FILE):
            size = os.path.getsize(HISTORY_FILE) / (1024 * 1024)  # Convert to MB
            return round(size, 2)
        return 0
    except Exception as e:
        log_error('get_history_file_size', str(e))
        return 0
