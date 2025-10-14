// Büfé App JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease-out';
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);
    });
    
    // Form submission button state
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const originalText = {};
        
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitButton && !submitButton.disabled) {
                originalText[form.id] = submitButton.textContent || submitButton.value;
                submitButton.disabled = true;
                if (submitButton.tagName === 'BUTTON') {
                    submitButton.textContent = 'Küldés...';
                } else {
                    submitButton.value = 'Küldés...';
                }
                
                // Re-enable after 3 seconds in case of validation failure
                setTimeout(() => {
                    submitButton.disabled = false;
                    if (submitButton.tagName === 'BUTTON') {
                        submitButton.textContent = originalText[form.id] || 'Küldés';
                    } else {
                        submitButton.value = originalText[form.id] || 'Küldés';
                    }
                }, 3000);
            }
        });
    });
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
});
