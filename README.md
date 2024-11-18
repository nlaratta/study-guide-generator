# Study Guide Generator

An intelligent web application that generates personalized study guides for any subject using AI. The application creates comprehensive learning paths tailored to your current knowledge level, available time, and preferred learning style.

## Features

- Personalized study guide generation based on:
  - Subject/topic
  - Current knowledge level
  - Weekly time availability
  - Preferred learning style
  - Specific learning goals
- Six-step comprehensive learning plan:
  1. Knowledge Assessment
  2. Learning Path Design
  3. Resource Curation
  4. Practice Framework
  5. Progress Tracking System
  6. Study Schedule Generation
- Interactive components with detailed explanations
- Real-time progress tracking
- Responsive design for all devices

## Setup

1. Clone the repository:
```bash
git clone [repository-url]
cd studier
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

5. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

1. Fill out the study guide form with your:
   - Subject or skill to learn
   - Current knowledge level
   - Weekly hours available
   - Preferred learning style
   - Specific learning goal

2. Click "Generate Study Guide" to create your personalized learning plan

3. Review each section of your study guide:
   - Click on core components in Step 1 for detailed explanations
   - Follow the structured learning path
   - Use the curated resources
   - Follow the practice framework
   - Track your progress
   - Adhere to the generated schedule

## Technology Stack

- Backend: Flask (Python)
- Frontend: HTML, CSS, JavaScript
- UI Framework: TailwindCSS
- AI: OpenAI GPT-4
- Markdown Processing: marked.js

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
