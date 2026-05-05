// static/js/ajax-cart.js

document.addEventListener('DOMContentLoaded', function() {
    // Handle all add-to-cart forms
    const addToCartForms = document.querySelectorAll('form[action*="/cart/add/"]');
    
    addToCartForms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault(); // Stop page from reloading
            
            const url = this.action;
            const formData = new FormData(this);
            
            try {
                const response = await fetch(url, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showNotification(data.message, 'success');
                    updateCartCount(data.cart_count);
                    animateCartIcon();
                    
                    // Optional: Change button text temporarily
                    const submitBtn = this.querySelector('button[type="submit"], input[type="submit"]');
                    if (submitBtn) {
                        const originalText = submitBtn.innerHTML;
                        submitBtn.innerHTML = '<i class="fas fa-check"></i> Added!';
                        submitBtn.disabled = true;
                        setTimeout(() => {
                            submitBtn.innerHTML = originalText;
                            submitBtn.disabled = false;
                        }, 2000);
                    }
                } else {
                    showNotification(data.error || 'Error adding to cart', 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                showNotification('Failed to add item to cart', 'error');
            }
        });
    });
    
    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Show notification
    function showNotification(message, type = 'success') {
        // Remove existing notification
        const existingNotif = document.querySelector('.ajax-notification');
        if (existingNotif) existingNotif.remove();
        
        const notification = document.createElement('div');
        notification.className = `ajax-notification ${type}`;
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}" style="font-size: 20px;"></i>
                <span style="flex: 1;">${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: white; cursor: pointer; font-size: 18px;">&times;</button>
            </div>
        `;
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 15px 20px;
            background: ${type === 'success' ? '#10b981' : '#ef4444'};
            color: white;
            border-radius: 12px;
            z-index: 10000;
            animation: slideInRight 0.3s ease-out;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            min-width: 280px;
            max-width: 400px;
        `;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification) {
                notification.style.animation = 'slideOutRight 0.3s ease-out';
                setTimeout(() => notification.remove(), 300);
            }
        }, 3000);
    }
    
    // Update cart count in navbar
    function updateCartCount(count) {
        const cartCountElements = document.querySelectorAll('.cart-count, #cart-count, .cart-badge, .cart-item-count');
        cartCountElements.forEach(el => {
            el.textContent = count;
            if (count === 0) {
                el.style.display = 'none';
            } else {
                el.style.display = 'inline-block';
            }
        });
    }
    
    // Animate cart icon
    function animateCartIcon() {
        const cartIcon = document.querySelector('.cart-icon, .fa-shopping-cart, .cart-link, .cart-btn');
        if (cartIcon) {
            cartIcon.style.transform = 'scale(1.2)';
            cartIcon.style.transition = 'transform 0.2s';
            setTimeout(() => {
                cartIcon.style.transform = 'scale(1)';
            }, 200);
        }
    }
    
    // Add CSS animations if not already added
    if (!document.querySelector('#ajax-cart-styles')) {
        const style = document.createElement('style');
        style.id = 'ajax-cart-styles';
        style.textContent = `
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes slideOutRight {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
});