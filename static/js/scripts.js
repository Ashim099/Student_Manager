// D:\StudentManager\static\js\scripts.js
<script src="{% static 'js/scripts.js' %}"></script>
document.addEventListener('DOMContentLoaded', function () {
    console.log('Student Manager WebApp loaded successfully!');

    // === Feature 1: Smooth Scroll for Navigation ===
    function initSmoothScroll() {
        const links = document.querySelectorAll('a[href*="#"]');
        links.forEach(link => {
            link.addEventListener('click', function (e) {
                e.preventDefault();
                const targetId = this.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                if (targetElement) {
                    window.scrollTo({
                        top: targetElement.offsetTop - 70, // Adjust for navbar height
                        behavior: 'smooth'
                    });
                }
            });
        });
    }

    // === Feature 2: Dynamic Navbar Effect on Scroll ===
    function initNavbarScrollEffect() {
        const navbar = document.querySelector('.navbar');
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbar.style.padding = '0.5rem 0';
                navbar.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.5)';
                navbar.style.background = 'linear-gradient(135deg, #0A1A2F, #1B263B)';
            } else {
                navbar.style.padding = '1rem 0';
                navbar.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
                navbar.style.background = 'linear-gradient(135deg, #0A1A2F, #1B263B)';
            }
        });
    }

    // === Feature 3: Preloader Animation ===
    function initPreloader() {
        // Create preloader HTML dynamically
        const preloader = document.createElement('div');
        preloader.id = 'preloader';
        preloader.innerHTML = `
            <div class="preloader-spinner">
                <i class="fas fa-graduation-cap fa-spin"></i>
            </div>
        `;
        document.body.appendChild(preloader);

        // Fade out preloader when the page is fully loaded
        window.addEventListener('load', () => {
            setTimeout(() => {
                preloader.style.opacity = '0';
                preloader.style.visibility = 'hidden';
            }, 1000); // Delay for a luxurious feel
        });
    }

    // === Feature 4: Hover Animations for Buttons and Cards ===
    function initHoverAnimations() {
        // Buttons
        const buttons = document.querySelectorAll('.btn-primary');
        buttons.forEach(button => {
            button.addEventListener('mouseenter', () => {
                button.style.boxShadow = '0 0 20px rgba(212, 175, 55, 0.5)';
                button.style.transform = 'translateY(-3px) scale(1.05)';
            });
            button.addEventListener('mouseleave', () => {
                button.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.2)';
                button.style.transform = 'translateY(0) scale(1)';
            });
        });

        // Cards
        const cards = document.querySelectorAll('.feature-card, .dashboard-card');
        cards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.boxShadow = '0 12px 40px rgba(0, 0, 0, 0.6)';
                card.style.transform = 'translateY(-10px)';
            });
            card.addEventListener('mouseleave', () => {
                card.style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.3)';
                card.style.transform = 'translateY(0)';
            });
        });
    }

    // === Feature 5: Pomodoro Timer Enhancements ===
    function initPomodoroEnhancements() {
        const timerDisplay = document.getElementById('timer');
        const startBtn = document.getElementById('startBtn');
        const pauseBtn = document.getElementById('pauseBtn');
        const resetBtn = document.getElementById('resetBtn');

        if (timerDisplay && startBtn && pauseBtn && resetBtn) {
            let time = 25 * 60;
            let timerInterval;
            let isWorkSession = true;

            // Create audio for notification
            const notificationSound = new Audio('https://www.soundjay.com/buttons/beep-01a.mp3');

            function updateTimer() {
                const minutes = Math.floor(time / 60);
                const seconds = time % 60;
                timerDisplay.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
                if (time <= 0) {
                    clearInterval(timerInterval);
                    notificationSound.play();
                    timerDisplay.classList.add('animate__animated', 'animate__pulse');
                    timerDisplay.textContent = isWorkSession ? 'Break Time!' : 'Work Time!';
                    startBtn.disabled = false;
                    pauseBtn.disabled = true;
                    setTimeout(() => {
                        time = isWorkSession ? 5 * 60 : 25 * 60; // 5-minute break or 25-minute work
                        isWorkSession = !isWorkSession;
                        updateTimer();
                    }, 2000);
                }
            }

            function startTimer() {
                timerInterval = setInterval(() => {
                    time--;
                    updateTimer();
                }, 1000);
                startBtn.disabled = true;
                pauseBtn.disabled = false;
            }

            startBtn.addEventListener('click', startTimer);
            pauseBtn.addEventListener('click', () => {
                clearInterval(timerInterval);
                startBtn.disabled = false;
                pauseBtn.disabled = true;
            });
            resetBtn.addEventListener('click', () => {
                clearInterval(timerInterval);
                time = 25 * 60;
                isWorkSession = true;
                updateTimer();
                startBtn.disabled = false;
                pauseBtn.disabled = true;
            });

            updateTimer();
        }
    }

    // === Feature 6: Dynamic Theme Toggle (Optional) ===
    function initThemeToggle() {
        const themeToggleBtn = document.createElement('button');
        themeToggleBtn.id = 'theme-toggle';
        themeToggleBtn.innerHTML = '<i class="fas fa-moon"></i>';
        themeToggleBtn.style.position = 'fixed';
        themeToggleBtn.style.bottom = '20px';
        themeToggleBtn.style.right = '20px';
        themeToggleBtn.style.background = 'var(--luxury-gold)';
        themeToggleBtn.style.color = 'var(--dark-blue)';
        themeToggleBtn.style.border = 'none';
        themeToggleBtn.style.borderRadius = '50%';
        themeToggleBtn.style.width = '50px';
        themeToggleBtn.style.height = '50px';
        themeToggleBtn.style.display = 'flex';
        themeToggleBtn.style.alignItems = 'center';
        themeToggleBtn.style.justifyContent = 'center';
        themeToggleBtn.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.2)';
        themeToggleBtn.style.cursor = 'pointer';
        themeToggleBtn.style.zIndex = '1000';
        document.body.appendChild(themeToggleBtn);

        // Check for saved theme in localStorage
        const savedTheme = localStorage.getItem('theme') || 'dark';
        applyTheme(savedTheme);

        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
            localStorage.setItem('theme', newTheme);
            themeToggleBtn.innerHTML = newTheme === 'dark' ? '<i class="fas fa-moon"></i>' : '<i class="fas fa-sun"></i>';
        });

        function applyTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            if (theme === 'light') {
                document.documentElement.style.setProperty('--dark-blue', '#E6F0FA');
                document.documentElement.style.setProperty('--navy-blue', '#B0C4DE');
                document.documentElement.style.setProperty('--luxury-gold', '#FFD700');
                document.documentElement.style.setProperty('--light-blue', '#4682B4');
                document.documentElement.style.setProperty('--background-gradient', 'linear-gradient(135deg, #E6F0FA, #B0C4DE)');
                document.documentElement.style.setProperty('--text-primary', '#1B263B');
                document.documentElement.style.setProperty('--text-secondary', '#4A4A4A');
                document.documentElement.style.setProperty('--glass-bg', 'rgba(0, 0, 0, 0.1)');
            } else {
                document.documentElement.style.setProperty('--dark-blue', '#0A1A2F');
                document.documentElement.style.setProperty('--navy-blue', '#1B263B');
                document.documentElement.style.setProperty('--luxury-gold', '#D4AF37');
                document.documentElement.style.setProperty('--light-blue', '#4A6FA5');
                document.documentElement.style.setProperty('--background-gradient', 'linear-gradient(135deg, #0A1A2F, #1B263B)');
                document.documentElement.style.setProperty('--text-primary', '#FFFFFF');
                document.documentElement.style.setProperty('--text-secondary', '#B0C4DE');
                document.documentElement.style.setProperty('--glass-bg', 'rgba(255, 255, 255, 0.1)');
            }
        }
    }

    // Initialize all features
    initSmoothScroll();
    initNavbarScrollEffect();
    initPreloader();
    initHoverAnimations();
    initPomodoroEnhancements();
    initThemeToggle();
});