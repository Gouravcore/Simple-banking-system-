/**
 * KUBERA BANK – Main JavaScript
 * Handles: Navbar, hamburger, scroll effects,
 *          scroll animations, chatbot, counter animations.
 */

// ==========================================
// NAVBAR – scroll effect & hamburger
// ==========================================
const mainNav   = document.getElementById('mainNav');
const hamburger = document.getElementById('hamburger');
const navLinks  = document.getElementById('navLinks');

// Add "scrolled" class when user scrolls down
window.addEventListener('scroll', () => {
    if (window.scrollY > 60) {
        mainNav?.classList.add('scrolled');
    } else {
        mainNav?.classList.remove('scrolled');
    }
});

// Hamburger menu toggle (mobile)
hamburger?.addEventListener('click', () => {
    navLinks?.classList.toggle('open');
    // Animate hamburger lines
    const spans = hamburger.querySelectorAll('span');
    if (navLinks?.classList.contains('open')) {
        spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
        spans[1].style.opacity   = '0';
        spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
    } else {
        spans[0].style.transform = '';
        spans[1].style.opacity   = '';
        spans[2].style.transform = '';
    }
});

// Close nav when clicking a link (mobile)
navLinks?.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
        navLinks.classList.remove('open');
    });
});

// ==========================================
// SCROLL REVEAL ANIMATION
// (Elements with data-animate attribute)
// ==========================================
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -40px 0px'
};

const scrollObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const delay = entry.target.dataset.delay || 0;
            setTimeout(() => {
                entry.target.classList.add('animated');
            }, parseInt(delay));
            scrollObserver.unobserve(entry.target);
        }
    });
}, observerOptions);

// Observe all elements with data-animate attribute
document.querySelectorAll('[data-animate]').forEach(el => {
    scrollObserver.observe(el);
});

// ==========================================
// COUNTER ANIMATION
// (data-count attribute)
// ==========================================
function animateCounter(element, target, duration = 1500) {
    let start     = 0;
    const step    = target / (duration / 16); // 60fps
    const timer   = setInterval(() => {
        start += step;
        if (start >= target) {
            start = target;
            clearInterval(timer);
        }
        // Format large numbers
        element.textContent = target >= 1000
            ? Math.floor(start).toLocaleString('en-IN')
            : Math.floor(start);
    }, 16);
}

const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const count = parseInt(entry.target.dataset.count || '0');
            animateCounter(entry.target, count);
            counterObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });

document.querySelectorAll('[data-count]').forEach(el => {
    counterObserver.observe(el);
});

// ==========================================
// CHATBOT
// ==========================================
const chatbotTrigger = document.getElementById('chatbotTrigger');
const chatbotWindow  = document.getElementById('chatbotWindow');
const chatbotClose   = document.getElementById('chatbotClose');
const chatInput      = document.getElementById('chatInput');
const chatSend       = document.getElementById('chatSend');
const chatMessages   = document.getElementById('chatMessages');

// Toggle chatbot
chatbotTrigger?.addEventListener('click', () => {
    chatbotWindow?.classList.toggle('active');
    // Remove badge when opened
    const badge = chatbotTrigger.querySelector('.kb-chatbot-badge');
    if (badge) badge.remove();
});

chatbotClose?.addEventListener('click', () => {
    chatbotWindow?.classList.remove('active');
});

// Send message
function sendChatMessage() {
    const message = chatInput?.value.trim();
    if (!message) return;

    // Add user message to chat
    addChatMessage(message, 'user');
    chatInput.value = '';

    // Show typing indicator
    const typingId = addChatMessage('...', 'bot', true);

    // Call the chatbot API
    fetch('/api/chatbot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
    })
    .then(response => response.json())
    .then(data => {
        // Remove typing indicator and add real reply
        removeMessage(typingId);
        addChatMessage(data.reply, 'bot');
    })
    .catch(() => {
        removeMessage(typingId);
        addChatMessage('Sorry, I could not connect. Please try again.', 'bot');
    });
}

function addChatMessage(text, sender, isTyping = false) {
    const msgId = 'msg-' + Date.now();
    const div   = document.createElement('div');
    div.className = `kb-chat-msg kb-chat-${sender}`;
    div.id = msgId;
    div.innerHTML = `<div class="kb-chat-bubble">${isTyping ? '<i class="fas fa-spinner fa-spin"></i>' : text}</div>`;
    chatMessages?.appendChild(div);
    // Scroll to bottom
    if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
    return msgId;
}

function removeMessage(id) {
    document.getElementById(id)?.remove();
}

chatSend?.addEventListener('click', sendChatMessage);
chatInput?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendChatMessage();
});

// ==========================================
// AUTO-DISMISS FLASH MESSAGES
// ==========================================
setTimeout(() => {
    document.querySelectorAll('.kb-alert').forEach(alert => {
        alert.style.transition = 'opacity 0.5s ease';
        alert.style.opacity    = '0';
        setTimeout(() => alert.remove(), 500);
    });
}, 5000);

// ==========================================
// SIDEBAR TOGGLE (Dashboard)
// ==========================================
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar       = document.getElementById('sidebar');

sidebarToggle?.addEventListener('click', () => {
    sidebar?.classList.toggle('open');
});

// Close sidebar when clicking outside on mobile
document.addEventListener('click', (e) => {
    if (sidebar?.classList.contains('open') &&
        !sidebar.contains(e.target) &&
        !sidebarToggle?.contains(e.target)) {
        sidebar.classList.remove('open');
    }
});

// ==========================================
// ACTIVE NAV LINK HIGHLIGHT
// ==========================================
const currentPath = window.location.pathname;
document.querySelectorAll('.kb-sidebar-link').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
        link.classList.add('active');
    }
});
