// Main application JavaScript
class PesaPalApp {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.updateLiveData();
    }
    
    setupEventListeners() {
        // Form validation
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', this.handleFormSubmit.bind(this));
        });
        
        // Real-time data updates
        document.addEventListener('focus', this.updateLiveData.bind(this));
    }
    
    handleFormSubmit(event) {
        const form = event.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        
        // Show loading state
        if (submitBtn) {
            submitBtn.classList.add('loading');
            submitBtn.disabled = true;
        }
    }
    
    async updateLiveData() {
        try {
            const response = await fetch('/api/dashboard/stats/');
            if (response.ok) {
                const data = await response.json();
                this.updateStats(data);
            }
        } catch (error) {
            console.log('Could not update live data:', error);
        }
    }
    
    updateStats(data) {
        // Update dashboard stats
        document.querySelectorAll('[data-stat]').forEach(element => {
            const statName = element.dataset.stat;
            if (data[statName]) {
                element.textContent = data[statName];
            }
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.pesaPalApp = new PesaPalApp();
});