"""
Prompt Templates for VLM Service
==================================

Templates for generating prompts for SmolVLM to answer contextual questions
about the scene in Turkish language.
"""

from typing import Dict, List, Optional


class PromptTemplates:
    """Prompt templates for VLM contextual assistance."""
    
    # System prompt for SmolVLM - SIMPLE AND DIRECT
    SYSTEM_PROMPT = """You are a visual assistant. Answer in English only.

Look at the image and answer the question directly. NO explanations, NO prefixes, just the answer."""

    # Common preset questions in ENGLISH
    PRESET_QUESTIONS = {
        "whats_ahead": "What is ahead of me?",
        "safe_to_cross": "Is it safe to cross the street?",
        "nearest_obstacle": "Where is the nearest obstacle?",
        "stairs_present": "Are there stairs ahead?",
        "people_around": "Are there people around me?",
        "traffic_status": "What is the traffic situation?",
        "obstacles_left": "Are there any obstacles to my left?",
        "obstacles_right": "Are there any obstacles to my right?",
        "nearest_path": "Which way is the safest path?",
        "collision_risk": "Is there any collision risk ahead?",
    }
    
    @staticmethod
    def format_detected_objects(detections: List[Dict]) -> str:
        """
        Format YOLO detections into a readable context string.
        
        Args:
            detections: List of detected objects with class, distance, confidence
            
        Returns:
            Formatted string describing detected objects
        """
        if not detections:
            return "No objects detected."
        
        lines = []
        for det in detections:
            # Handle both old format (class/class_name) and new format (name/name_tr)
            class_name = det.get('name_tr') or det.get('class_name') or det.get('class', 'unknown')
            distance = det.get('distance', 'unknown')
            confidence = det.get('confidence', 0.0)
            region = det.get('region', det.get('direction', ''))
            
            # Format distance
            if isinstance(distance, (int, float)):
                dist_str = f"{distance:.1f}m" if distance > 0 else "unknown distance"
            else:
                dist_str = str(distance)
            
            # Build description
            desc = f"- {class_name}"
            if region:
                desc += f" ({region})"
            desc += f" at {dist_str}, confidence {confidence:.2f}"
            
            lines.append(desc)
        
        return "\n".join(lines)
    
    @staticmethod
    def build_prompt(
        question: str,
        detections: Optional[List[Dict]] = None,
        additional_context: Optional[str] = None
    ) -> str:
        """
        Build complete prompt for VLM.
        
        Args:
            question: User's question in Turkish
            detections: YOLO detection results
            additional_context: Any additional context to include
            
        Returns:
            Complete formatted prompt
        """
        prompt_parts = [PromptTemplates.SYSTEM_PROMPT]
        
        # Add detected objects FIRST - this constrains the answer
        if detections:
            objects_list = ", ".join([d.get('name_tr') or d.get('class_name') or d.get('class', 'object') for d in detections])
            prompt_parts.append(f"\nScene contains: {objects_list}")
        
        # Then add the question 
        prompt_parts.append(f"\nQuestion: {question}\n")
        
        return "\n".join(prompt_parts)
    
    @staticmethod
    def get_preset_question(preset_key: str) -> Optional[str]:
        """Get a preset question by key."""
        return PromptTemplates.PRESET_QUESTIONS.get(preset_key)
    
    @staticmethod
    def get_all_preset_questions() -> Dict[str, str]:
        """Get all preset questions."""
        return PromptTemplates.PRESET_QUESTIONS.copy()


# Example usage
if __name__ == "__main__":
    # Example detections from YOLO
    sample_detections = [
        {
            "class": "person",
            "distance": 2.5,
            "confidence": 0.95,
            "direction": "left"
        },
        {
            "class": "car",
            "distance": 8.0,
            "confidence": 0.87,
            "direction": "right"
        },
        {
            "class": "stairs",
            "distance": 1.2,
            "confidence": 0.92,
            "direction": "ahead"
        }
    ]
    
    question = "What is ahead of me?"
    prompt = PromptTemplates.build_prompt(question, sample_detections)
    
    print("=" * 70)
    print("EXAMPLE PROMPT:")
    print("=" * 70)
    print(prompt)
    print("=" * 70)
