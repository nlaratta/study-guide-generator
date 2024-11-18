/**
 * Study Guide Generator Frontend
 * 
 * This module handles the frontend functionality for the study guide generator,
 * including form submission, API interactions, and UI updates.
 */

// Constants
const API_ENDPOINTS = {
    GENERATE: '/generate',
    COMPONENT_DETAILS: '/get_component_details'
};

// UI State Management
class UIState {
    constructor() {
        this.isModalLoading = false;
        this.previousResponses = [];
        this.floatingButton = null;
        this.currentSelection = '';
    }

    setModalLoading(loading) {
        this.isModalLoading = loading;
        if (loading) {
            modal.classList.add('loading');
        } else {
            modal.classList.remove('loading');
        }
    }

    createFloatingButton() {
        if (this.floatingButton) {
            return this.floatingButton;
        }

        this.floatingButton = document.createElement('button');
        this.floatingButton.className = 'floating-button';
        this.floatingButton.textContent = 'Explain This';
        this.floatingButton.style.position = 'absolute';
        this.floatingButton.style.display = 'none';
        this.floatingButton.style.zIndex = '1000';
        document.body.appendChild(this.floatingButton);
        return this.floatingButton;
    }

    removeFloatingButton() {
        if (this.floatingButton) {
            document.body.removeChild(this.floatingButton);
            this.floatingButton = null;
        }
    }
}

// UI Components Handler
class UIComponents {
    constructor() {
        this.studyForm = document.getElementById('studyForm');
        this.resultsDiv = document.getElementById('results');
        this.timeAvailable = document.getElementById('timeAvailable');
        this.timeDisplay = document.getElementById('timeDisplay');
        this.modal = document.getElementById('modal');
        this.modalTitle = document.getElementById('modalTitle');
        this.modalContent = document.getElementById('modalContent');
        this.closeModal = document.getElementById('closeModal');
        this.maxSteps = document.getElementById('maxSteps')?.value || 1;

        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Time slider update
        this.timeAvailable.addEventListener('input', (e) => {
            this.timeDisplay.textContent = `${e.target.value} hours per week`;
        });

        // Modal close handlers
        this.closeModal.addEventListener('click', () => this.modal.classList.add('hidden'));
        window.addEventListener('click', (e) => {
            if (e.target === this.modal) this.modal.classList.add('hidden');
        });
    }

    createStepCard(stepNumber) {
        const card = document.createElement('div');
        card.className = 'step-card';
        card.setAttribute('data-step', stepNumber);
        card.innerHTML = `
            <div class="step-header">
                <div class="step-number">${stepNumber}</div>
                <h2 class="text-xl font-semibold">Step ${stepNumber}</h2>
            </div>
            <div class="loading-bar">
                <div class="loading-bar-progress"></div>
            </div>
            <div class="loading-text">Processing...</div>
            <div class="step-content markdown-content mt-4"></div>
        `;
        return card;
    }

    updateStepCard(card, content, stepNumber) {
        card.querySelector('.loading-bar').remove();
        card.querySelector('.loading-text').remove();
        card.querySelector('.step-content').innerHTML = marked.parse(content);
    }

    showError(stepCard, error) {
        stepCard.querySelector('.step-content').innerHTML = `
            <div class="text-red-600">Error generating content: ${error}</div>
        `;
    }
}

// Selection Handler
class SelectionHandler {
    constructor(ui, state) {
        this.ui = ui;
        this.state = state;
        this.currentSubject = '';
        this.setupSelectionHandling();
        console.log('SelectionHandler initialized');
    }

    setCurrentSubject(subject) {
        console.log('Setting current subject:', subject);
        this.currentSubject = subject;
    }

    setupSelectionHandling() {
        // Handle text selection
        document.addEventListener('selectionchange', () => {
            this.handleSelectionChange();
        });

        // Handle mouse up for button positioning
        document.addEventListener('mouseup', (e) => {
            // Ignore if clicking the floating button
            if (this.state.floatingButton && this.state.floatingButton.contains(e.target)) {
                return;
            }

            const selection = window.getSelection();
            if (selection.toString().trim()) {
                this.updateFloatingButtonPosition(e);
            }
        });

        // Handle clicks outside selection
        document.addEventListener('mousedown', (e) => {
            // Ignore if clicking the floating button
            if (this.state.floatingButton && this.state.floatingButton.contains(e.target)) {
                return;
            }
            this.state.removeFloatingButton();
        });

        // Hide button when clicking outside
        document.addEventListener('mousedown', (e) => {
            if (this.state.floatingButton && !this.state.floatingButton.contains(e.target)) {
                this.state.removeFloatingButton();
            }
        });
    }

    findStepCard(node) {
        // Handle text nodes by getting their parent
        let element = node.nodeType === Node.TEXT_NODE ? node.parentElement : node;
        
        // Traverse up until we find a step card or reach the document root
        while (element && !element.classList?.contains('step-card')) {
            element = element.parentElement;
        }
        
        return element;
    }

    handleSelectionChange() {
        const selection = window.getSelection();
        const selectedText = selection.toString().trim();
        
        if (!selectedText) {
            this.state.removeFloatingButton();
            return;
        }

        // Check if selection is within a step card
        if (!selection.rangeCount) return;
        
        const range = selection.getRangeAt(0);
        const stepCard = this.findStepCard(range.commonAncestorContainer);

        if (!stepCard) {
            this.state.removeFloatingButton();
            return;
        }

        console.log('Valid selection in step card:', selectedText);
        this.state.currentSelection = selectedText;
    }

    updateFloatingButtonPosition(e) {
        if (!this.state.currentSelection) {
            console.log('No current selection');
            return;
        }

        const selection = window.getSelection();
        if (!selection.rangeCount) {
            console.log('No selection range');
            return;
        }

        const range = selection.getRangeAt(0);
        const stepCard = this.findStepCard(range.commonAncestorContainer);

        if (!stepCard) {
            console.log('Selection not in step card');
            this.state.removeFloatingButton();
            return;
        }

        const rect = range.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) {
            console.log('Invalid selection rectangle');
            return;
        }

        console.log('Positioning floating button');
        const button = this.state.createFloatingButton();
        
        // Remove any existing click handlers
        button.replaceWith(button.cloneNode(true));
        this.state.floatingButton = button;
        document.body.appendChild(button);

        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        button.style.top = `${rect.top + scrollTop - 40}px`; // 40px above selection
        button.style.left = `${rect.left + (rect.width / 2) - (button.offsetWidth / 2)}px`;
        button.style.display = 'block';

        // Add click handler to the new button
        button.addEventListener('click', async (e) => {
            console.log('Explain button clicked');
            e.preventDefault();
            e.stopPropagation();
            await this.handleExplanationRequest();
        }, { once: true }); // Only trigger once
    }

    async handleExplanationRequest() {
        console.log('Starting explanation request');
        console.log('Current subject:', this.currentSubject);
        console.log('Current selection:', this.state.currentSelection);

        if (!this.currentSubject || !this.state.currentSelection) {
            console.error('Missing required data:', {
                subject: this.currentSubject,
                selection: this.state.currentSelection
            });
            return;
        }

        if (this.state.isModalLoading) {
            console.log('Modal is already loading, ignoring request');
            return;
        }

        const selectedText = this.state.currentSelection;
        console.log(`Requesting explanation for: ${selectedText} in subject: ${this.currentSubject}`);

        this.ui.modalTitle.textContent = selectedText;
        this.ui.modalContent.innerHTML = '<div class="loading-text">Loading detailed explanation...</div>';
        this.state.setModalLoading(true);
        this.ui.modal.classList.remove('hidden');

        try {
            console.log('Sending fetch request');
            const response = await fetch('/get_component_details', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    component: selectedText,
                    subject: this.currentSubject
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Received explanation:', data);
            this.ui.modalContent.innerHTML = marked.parse(data.response);
        } catch (error) {
            console.error('Error loading explanation:', error);
            this.ui.modalContent.innerHTML = `
                <div class="text-red-600">Error loading content: ${error.message}</div>
            `;
        } finally {
            this.state.setModalLoading(false);
            this.state.removeFloatingButton();
        }
    }
}

// API Service
class APIService {
    static async generateStep(formData, step, previousResponses) {
        try {
            console.log('Making API request with data:', { formData, step, previousResponses });
            const response = await fetch(API_ENDPOINTS.GENERATE, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...formData, step, previousResponses })
            });

            const data = await response.json();
            console.log('API response:', data);

            if (!response.ok) {
                throw new Error(data.error || 'Network response was not ok');
            }

            return data;
        } catch (error) {
            console.error('API error:', error);
            throw error;
        }
    }

    static async getComponentDetails(component, subject) {
        try {
            console.log('Requesting component details:', { component, subject });
            const response = await fetch(API_ENDPOINTS.COMPONENT_DETAILS, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ component, subject })
            });

            const data = await response.json();
            console.log('Component details response:', data);

            if (!response.ok) {
                throw new Error(data.error || 'Network response was not ok');
            }

            return data;
        } catch (error) {
            console.error('API error:', error);
            throw error;
        }
    }
}

// Study Guide Generator
class StudyGuideGenerator {
    constructor() {
        this.ui = new UIComponents();
        this.state = new UIState();
        this.selectionHandler = new SelectionHandler(this.ui, this.state);
        
        // Bind form submission
        this.ui.studyForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
    }

    async handleFormSubmit(e) {
        e.preventDefault();
        console.log('Form submitted - starting study guide generation');
        
        const formData = {
            subject: document.getElementById('subject').value,
            currentLevel: document.getElementById('currentLevel').value,
            timeAvailable: document.getElementById('timeAvailable').value,
            learningStyle: document.getElementById('learningStyle').value,
            goal: document.getElementById('goal').value,
            maxSteps: this.ui.maxSteps
        };

        // Update current subject for the selection handler
        this.selectionHandler.setCurrentSubject(formData.subject);
        
        console.log('Form data:', formData);
        this.ui.resultsDiv.innerHTML = '';
        this.state.previousResponses = [];

        try {
            for (let step = 0; step < formData.maxSteps; step++) {
                console.log(`Processing step ${step + 1} of ${formData.maxSteps}`);
                const stepCard = this.ui.createStepCard(step + 1);
                this.ui.resultsDiv.appendChild(stepCard);

                try {
                    console.log(`Sending request for step ${step + 1} with previous responses:`, this.state.previousResponses);
                    const data = await APIService.generateStep(formData, step, this.state.previousResponses);
                    console.log(`Received data for step ${step + 1}:`, data);
                    
                    this.ui.updateStepCard(stepCard, data.response, step + 1);
                    this.state.previousResponses.push(data.response);
                } catch (error) {
                    console.error(`Error in step ${step + 1}:`, error);
                    this.ui.showError(stepCard, error.message);
                    break;
                }
            }
        } catch (error) {
            console.error('Error in form submission:', error);
            this.ui.resultsDiv.innerHTML = `
                <div class="text-red-600">Error: ${error.message}</div>
            `;
        }
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Study Guide Generator');
    const app = new StudyGuideGenerator();
});

// Add marked.js for Markdown parsing
const script = document.createElement('script');
script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
document.head.appendChild(script);
