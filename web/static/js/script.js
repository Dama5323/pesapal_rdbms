// Simple script for interactivity
document.addEventListener('DOMContentLoaded', function() {
    // Add active class to current page in sidebar
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('aside a');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('bg-blue-50', 'text-blue-600');
        }
    });
    
    // Simple toast notification
    window.showToast = function(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg text-white ${
            type === 'success' ? 'bg-green-500' : 
            type === 'error' ? 'bg-red-500' : 
            'bg-blue-500'
        }`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    };
});