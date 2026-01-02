import threading
import numpy as np
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AppState:
    """
    Global application state to store latest processed frames.
    Used for the debug dashboard to show real-time limits without affecting performance.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(AppState, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.last_frame: Optional[np.ndarray] = None
        self.last_depth: Optional[np.ndarray] = None
        self.last_analysis: Dict[str, Any] = {}
        self.frame_lock = threading.Lock()
        
    def update_state(self, original_frame: np.ndarray, depth_map: Optional[np.ndarray] = None, analysis_result: Dict[str, Any] = None):
        """
        Update the current state with new frame data.
        This operation is lightweight (reference copy only).
        """
        try:
            with self.frame_lock:
                # Store references only (fast)
                self.last_frame = original_frame
                if depth_map is not None:
                    self.last_depth = depth_map
                if analysis_result is not None:
                    self.last_analysis = analysis_result
        except Exception as e:
            logger.error(f"Failed to update app state: {e}")

    def get_snapshot(self):
        """Get a thread-safe snapshot of the current state"""
        with self.frame_lock:
            return {
                'frame': self.last_frame,
                'depth': self.last_depth,
                'analysis': self.last_analysis
            }

# Global instance
app_state = AppState()
