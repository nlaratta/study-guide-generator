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
    DEFAULT_STEPS: int = int(os.getenv('DEFAULT_STEPS', '6'))
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
        return f"""You are creating a personalized study guide for a student with the following context:
- Subject: {data.get('subject')}
- Current Level: {data.get('currentLevel')}
- Available Time: {data.get('timeAvailable')} hours/week
- Learning Style: {data.get('learningStyle')}
- Learning Goal: {data.get('goal')}

Please respond to all requests in a Markdown format. Include links to relevant resources for each step.
Maintain this context for all responses and ensure each step builds upon previous steps."""

    @staticmethod
    def get_step_prompt(step: int, subject: str) -> str:
        """Returns the prompt for a specific step in the study guide generation process."""
        prompts = {
            0: f"""**Step 1: Knowledge Assessment**
Create a comprehensive knowledge assessment for {subject}. Include:
1. Pre-assessment questions to gauge current understanding
2. Key prerequisite knowledge needed
3. Common misconceptions and knowledge gaps
4. Self-evaluation checklist with skill levels (beginner/intermediate/advanced)
5. Recommended starting points based on different knowledge levels""",
            
            1: f"""**Step 2: Learning Path Design**
Design a structured learning path for {subject}. Include:
1. Clear learning objectives and milestones
2. Topic progression from foundational to advanced
3. Estimated time for each topic/module
4. Alternative paths for different learning styles
5. Key concepts and their relationships (concept map)""",
            
            2: f"""**Step 3: Resource Curation**
Curate comprehensive learning resources for {subject}. Include:
1. Essential textbooks and reading materials
2. Online courses and video tutorials (with links)
3. Interactive tools and simulations
4. Practice websites and platforms
5. Community forums and study groups
6. Free vs paid resource recommendations""",
            
            3: f"""**Step 4: Practice Framework**
Create a hands-on practice framework for {subject}. Include:
1. Beginner exercises with solutions
2. Intermediate challenges and projects
3. Advanced real-world applications
4. Common mistakes and how to avoid them
5. Self-check rubrics for each practice level
6. Recommended practice schedule""",
            
            4: f"""**Step 5: Progress Tracking**
Design a progress tracking system for {subject}. Include:
1. Key performance indicators (KPIs) for learning
2. Weekly/monthly assessment templates
3. Progress visualization methods
4. Milestone celebrations and rewards
5. Adjustment strategies when falling behind
6. Portfolio building suggestions""",
            
            5: f"""**Step 6: Schedule Generation**
Generate a personalized study schedule for {subject}. Include:
1. Weekly study plan based on available hours
2. Daily learning activities breakdown
3. Spaced repetition schedule for retention
4. Buffer time for review and catch-up
5. Integration with work/life commitments
6. Flexibility guidelines for schedule adjustments""",
        }
        return prompts.get(step, f"Continue the study guide for {subject}, building upon previous content.")

class OpenAIService:
    """Handles interactions with OpenAI API."""
    
    @staticmethod
    def generate_response(system_prompt: str, user_prompt: str, previous_responses: List[str]) -> str:
        """Generate a response using OpenAI's API."""
        try:
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add previous responses as context
            for prev_response in previous_responses:
                messages.append({"role": "assistant", "content": prev_response})
            
            # Add current prompt
            messages.append({"role": "user", "content": user_prompt})
            
            response = openai.ChatCompletion.create(
                model=config.MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                n=1,
                stop=None,
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
def generate_study_guide():
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
        step_prompt = PromptManager.get_step_prompt(step, subject)
        previous_responses = data.get('previousResponses', [])
        
        response = OpenAIService.generate_response(
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
def get_component_details():
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
        response = OpenAIService.generate_response(system_message, prompt, [])
        
        return jsonify({"response": response})
    
    except Exception as e:
        logger.error(f"Error getting component details: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)