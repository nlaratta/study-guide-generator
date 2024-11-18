"""
Study Guide Generator Backend

This module provides the backend functionality for generating personalized study guides
using OpenAI's GPT model. It handles user input processing, AI interactions, and
response management.
"""

import os
import json
import logging
from typing import Dict, List, Optional, TypedDict
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import openai

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    """Application configuration settings."""
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    DEFAULT_STEPS: int = int(os.getenv('DEFAULT_STEPS', '1'))
    RESPONSES_FILE: str = 'saved_responses.json'
    MODEL: str = "gpt-4o"

config = Config()
openai.api_key = config.OPENAI_API_KEY

# Type definitions
class StudyGuideRequest(TypedDict):
    subject: str
    currentLevel: str
    timeAvailable: str
    learningStyle: str
    goal: str
    step: int
    previousResponses: List[str]

class ResponseManager:
    """Manages saving and loading of responses."""
    
    @staticmethod
    def save_response(subject: str, step: int, response: str) -> None:
        """Save a response to the JSON file."""
        try:
            # Load existing responses
            responses = ResponseManager.load_responses()
            
            # Create entry for this subject if it doesn't exist
            if subject not in responses:
                responses[subject] = {}
            
            # Save response with timestamp
            responses[subject][str(step)] = {
                'response': response,
                'timestamp': datetime.now().isoformat()
            }
            
            # Write back to file
            with open(config.RESPONSES_FILE, 'w', encoding='utf-8') as f:
                json.dump(responses, f, indent=2)
                
            logger.info(f"Saved response for {subject} step {step}")
        except Exception as e:
            logger.error(f"Error saving response: {e}")

    @staticmethod
    def load_responses() -> Dict:
        """Load all saved responses from the JSON file."""
        try:
            if os.path.exists(config.RESPONSES_FILE):
                with open(config.RESPONSES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading responses: {e}")
            return {}

    @staticmethod
    def get_response(subject: str, step: int) -> Optional[str]:
        """Get a saved response for a specific subject and step."""
        try:
            responses = ResponseManager.load_responses()
            if subject in responses and str(step) in responses[subject]:
                return responses[subject][str(step)]['response']
            return None
        except Exception as e:
            logger.error(f"Error getting response: {e}")
            return None

class PromptManager:
    """Manages prompt generation and formatting."""
    
    @staticmethod
    def get_system_prompt(data: StudyGuideRequest) -> str:
        """Returns the system prompt with context about the student."""
        return f"""You are world class educator, professor, and expert in {data.get('subject')} who is creating a personalized study guide for a student with the following context:
- Subject: {data.get('subject')}
- Current Level: {data.get('currentLevel')}
- Available Time: {data.get('timeAvailable')} hours/week
- Learning Style: {data.get('learningStyle')}
- Learning Goal: {data.get('goal')}

Please respond to all requests in a Markdown format. Include links to relevant resources for each step.
Maintain this context for all responses and ensure each step builds upon previous steps."""

    @staticmethod
    def get_step_prompt(step: int, data: StudyGuideRequest) -> str:
        """Returns the prompt for a specific step in the study guide generation process."""
        time_per_week = data.get('timeAvailable')
        learning_style = data.get('learningStyle')
        current_level = data.get('currentLevel')
        goal = data.get('goal')
        subject = data.get('subject')

        prompts = {
            0: f"""Create the first part of a study guide for {subject}, considering the student is at a {current_level} level and has {time_per_week} hours/week to study. Include:
1. A clear introduction to {subject} aligned with the goal: {goal}
2. Key foundational concepts that must be understood at {current_level} level
3. Common misconceptions to avoid for {current_level} learners
4. Initial learning objectives that can be achieved within {time_per_week} hours/week
5. Learning resources that match {learning_style} learning style""",
            
            1: f"""Building on the previous content, outline for a {learning_style} learner:
1. Intermediate concepts that build towards {goal}
2. Practical exercises tailored to {time_per_week} hours/week availability
3. Study techniques optimized for {learning_style} learning style
4. Progress tracking methods to measure advancement from {current_level} level
5. Time management suggestions for {time_per_week} hours/week study schedule""",
            
            2: f"""For the advanced section, provide content suitable for progression from {current_level} level:
1. Complex topics and their relationships, presented in a {learning_style}-friendly way
2. Real-world applications related to {goal}
3. Advanced resources that match {learning_style} learning style
4. Mastery indicators aligned with {goal}
5. Advanced exercises designed for {time_per_week} hours/week commitment""",
            
            3: f"""Create a summary section with:
1. Review of key points aligned with {goal}
2. Common pitfalls for {current_level} level students to avoid
3. Next steps for further learning beyond {current_level} level
4. Self-assessment questions tailored to {learning_style} learning style
5. Long-term study plan suggestion for {time_per_week} hours/week""",
        }
        return prompts.get(step, f"Continue the study guide for {subject}, building upon previous content while considering the student's {learning_style} learning style, {current_level} level, and {time_per_week} hours/week availability.")

class OpenAIService:
    """Handles interactions with OpenAI API."""
    
    @staticmethod
    async def generate_response(system_prompt: str, user_prompt: str, previous_responses: List[str]) -> str:
        """Generate a response using OpenAI's API."""
        try:
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add previous responses as context
            for prev_response in previous_responses:
                messages.append({"role": "assistant", "content": prev_response})
            
            # Add current prompt
            messages.append({"role": "user", "content": user_prompt})
            
            response = await openai.ChatCompletion.acreate(
                model=config.MODEL,
                messages=messages,
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

@app.route('/')
def home():
    """Renders the home page."""
    return render_template('index.html', default_steps=config.DEFAULT_STEPS)

@app.route('/generate', methods=['POST'])
async def generate_study_guide():
    """Generate a step of the study guide."""
    try:
        data = request.json
        subject = data.get('subject', '')
        step = data.get('step', 0)
        
        # Check for saved response first
        saved_response = ResponseManager.get_response(subject, step)
        if saved_response:
            logger.info(f"Using saved response for {subject} step {step}")
            return jsonify({"response": saved_response})
        
        # Generate new response
        system_prompt = PromptManager.get_system_prompt(data)
        step_prompt = PromptManager.get_step_prompt(step, data)
        previous_responses = data.get('previousResponses', [])
        
        response = await OpenAIService.generate_response(
            system_prompt,
            step_prompt,
            previous_responses
        )
        
        # Save the response
        ResponseManager.save_response(subject, step, response)
        
        return jsonify({"response": response})
    
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_component_details', methods=['POST'])
async def get_component_details():
    """Get detailed explanation of a specific component."""
    try:
        data = request.json
        component = data.get('component')
        subject = data.get('subject')
        
        if not component or not subject:
            return jsonify({"error": "Missing required parameters"}), 400
        
        prompt = f"""Descriptively explain the following component of {subject} in detail: {component}
Include:
1. Definition and core concepts
2. Importance and applications
3. Common challenges and solutions
4. Learning resources and tips"""
        
        system_message = f"You are a fun loving, world-class expert, professor, and educator in {subject}"
        response = await OpenAIService.generate_response(system_message, prompt, [])
        
        return jsonify({"response": response})
    
    except Exception as e:
        logger.error(f"Error getting component details: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)