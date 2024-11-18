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
            0: f"""Create the first part of a study guide for {subject}. Include:
1. A clear introduction to the subject
2. Key foundational concepts that must be understood
3. Common misconceptions to avoid
4. Initial learning objectives""",
            
            1: """Building on the previous content, outline:
1. Intermediate concepts
2. Practical exercises
3. Study techniques
4. Progress tracking methods""",
            
            2: """For the advanced section, provide:
1. Complex topics and their relationships
2. Real-world applications
3. Advanced resources
4. Mastery indicators""",
            
            3: """Create a summary section with:
1. Review of key points
2. Common pitfalls to avoid
3. Next steps for further learning
4. Self-assessment questions""",
        }
        return prompts.get(step, f"Continue the study guide for {subject}, building upon previous content.")

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
        step_prompt = PromptManager.get_step_prompt(step, subject)
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