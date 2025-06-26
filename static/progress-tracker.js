/**
 * Progress Tracking Module for Study Guide Generator
 * 
 * This module handles progress tracking, storage, and visualization
 * for the study guide learning journey.
 */

class ProgressTracker {
    constructor() {
        this.storageKey = 'studyGuideProgress';
        this.currentProgress = this.loadProgress();
    }

    /**
     * Initialize progress for a new subject
     */
    initializeSubject(subject, totalSteps = 6) {
        if (!this.currentProgress[subject]) {
            this.currentProgress[subject] = {
                subject: subject,
                totalSteps: totalSteps,
                completedSteps: [],
                startDate: new Date().toISOString(),
                lastAccessed: new Date().toISOString(),
                studyTime: 0, // in minutes
                notes: {},
                checkpoints: {},
                completionPercentage: 0
            };
            this.saveProgress();
        }
        return this.currentProgress[subject];
    }

    /**
     * Mark a step as completed
     */
    markStepCompleted(subject, stepNumber, notes = '') {
        const subjectProgress = this.currentProgress[subject];
        if (!subjectProgress) return;

        if (!subjectProgress.completedSteps.includes(stepNumber)) {
            subjectProgress.completedSteps.push(stepNumber);
            subjectProgress.checkpoints[stepNumber] = {
                completedAt: new Date().toISOString(),
                notes: notes
            };
        }

        subjectProgress.lastAccessed = new Date().toISOString();
        subjectProgress.completionPercentage = 
            (subjectProgress.completedSteps.length / subjectProgress.totalSteps) * 100;

        this.saveProgress();
        this.updateProgressUI(subject);
    }

    /**
     * Add study time
     */
    addStudyTime(subject, minutes) {
        const subjectProgress = this.currentProgress[subject];
        if (!subjectProgress) return;

        subjectProgress.studyTime += minutes;
        subjectProgress.lastAccessed = new Date().toISOString();
        this.saveProgress();
    }

    /**
     * Get progress summary for a subject
     */
    getProgressSummary(subject) {
        const progress = this.currentProgress[subject];
        if (!progress) return null;

        const daysSinceStart = Math.floor(
            (new Date() - new Date(progress.startDate)) / (1000 * 60 * 60 * 24)
        );

        return {
            completionPercentage: progress.completionPercentage,
            completedSteps: progress.completedSteps.length,
            totalSteps: progress.totalSteps,
            studyTime: progress.studyTime,
            daysSinceStart: daysSinceStart,
            currentStreak: this.calculateStreak(subject)
        };
    }

    /**
     * Calculate study streak
     */
    calculateStreak(subject) {
        // Simplified streak calculation
        const progress = this.currentProgress[subject];
        if (!progress) return 0;

        const lastAccessed = new Date(progress.lastAccessed);
        const today = new Date();
        const daysDiff = Math.floor((today - lastAccessed) / (1000 * 60 * 60 * 24));

        return daysDiff <= 1 ? 1 : 0;
    }

    /**
     * Update progress UI
     */
    updateProgressUI(subject) {
        const summary = this.getProgressSummary(subject);
        if (!summary) return;

        // Create or update progress widget
        let progressWidget = document.getElementById('progress-widget');
        if (!progressWidget) {
            progressWidget = this.createProgressWidget();
            document.querySelector('.container').insertBefore(
                progressWidget, 
                document.getElementById('results')
            );
        }

        progressWidget.innerHTML = `
            <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
                <h3 class="text-xl font-semibold mb-4">Your Progress</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div class="text-center">
                        <div class="text-2xl font-bold text-indigo-600">${summary.completionPercentage.toFixed(0)}%</div>
                        <div class="text-sm text-gray-600">Complete</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl font-bold text-green-600">${summary.completedSteps}/${summary.totalSteps}</div>
                        <div class="text-sm text-gray-600">Steps</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl font-bold text-blue-600">${summary.studyTime}</div>
                        <div class="text-sm text-gray-600">Minutes</div>
                    </div>
                    <div class="text-center">
                        <div class="text-2xl font-bold text-purple-600">${summary.daysSinceStart}</div>
                        <div class="text-sm text-gray-600">Days</div>
                    </div>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-4 mb-4">
                    <div class="bg-indigo-600 h-4 rounded-full transition-all duration-500" 
                         style="width: ${summary.completionPercentage}%"></div>
                </div>
                <div class="flex flex-wrap gap-2">
                    ${this.renderStepIndicators(subject)}
                </div>
            </div>
        `;
    }

    /**
     * Render step indicators
     */
    renderStepIndicators(subject) {
        const progress = this.currentProgress[subject];
        if (!progress) return '';

        let indicators = '';
        for (let i = 1; i <= progress.totalSteps; i++) {
            const isCompleted = progress.completedSteps.includes(i);
            indicators += `
                <div class="step-indicator ${isCompleted ? 'completed' : ''}" 
                     title="Step ${i}: ${this.getStepName(i)}">
                    ${i}
                </div>
            `;
        }
        return indicators;
    }

    /**
     * Get step name
     */
    getStepName(step) {
        const stepNames = [
            'Knowledge Assessment',
            'Learning Path Design',
            'Resource Curation',
            'Practice Framework',
            'Progress Tracking',
            'Schedule Generation'
        ];
        return stepNames[step - 1] || `Step ${step}`;
    }

    /**
     * Create progress widget
     */
    createProgressWidget() {
        const widget = document.createElement('div');
        widget.id = 'progress-widget';
        return widget;
    }

    /**
     * Save progress to localStorage
     */
    saveProgress() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.currentProgress));
        } catch (e) {
            console.error('Failed to save progress:', e);
        }
    }

    /**
     * Load progress from localStorage
     */
    loadProgress() {
        try {
            const saved = localStorage.getItem(this.storageKey);
            return saved ? JSON.parse(saved) : {};
        } catch (e) {
            console.error('Failed to load progress:', e);
            return {};
        }
    }

    /**
     * Export progress data
     */
    exportProgress(subject) {
        const progress = this.currentProgress[subject];
        if (!progress) return null;

        const data = {
            ...progress,
            exportDate: new Date().toISOString()
        };

        const blob = new Blob([JSON.stringify(data, null, 2)], 
                             { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `${subject}_progress_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * Get all subjects with progress
     */
    getAllSubjects() {
        return Object.keys(this.currentProgress).map(subject => ({
            subject,
            ...this.getProgressSummary(subject)
        }));
    }
}

// Export for use in main app
window.ProgressTracker = ProgressTracker;