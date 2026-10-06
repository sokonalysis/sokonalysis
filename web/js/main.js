document.addEventListener('DOMContentLoaded', function() {
    const path = window.location.pathname;
    const isRoot = !path.includes('/pages/');
    const basePath = isRoot ? '' : '../';
    
    // Initialize theme
    initTheme();
    
    // Load components
    loadHeader(basePath);
    loadFooter(basePath);
});

function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        updateThemeIcon(themeToggle, savedTheme);
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(themeToggle, newTheme);
        });
    }
}

function updateThemeIcon(toggle, theme) {
    const icon = toggle.querySelector('i');
    if (icon) {
        icon.className = theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
    }
}

function loadHeader(basePath) {
    const headerPlaceholder = document.getElementById('header-placeholder');
    if (!headerPlaceholder) return;
    
    fetch(basePath + 'components/header.html')
        .then(response => response.text())
        .then(data => {
            headerPlaceholder.innerHTML = data;
            initMobileMenu();
            setActiveLink();
            initTheme(); // Re-init theme after header load
        })
        .catch(() => {
            headerPlaceholder.innerHTML = `
                <header class="site-header">
                    <div class="header-container">
                        <a href="${basePath}index.html" class="logo-link">
                            <img src="${basePath}assets/images/logo.png" alt="sokonalysis" class="logo-img">
                            <span class="logo-text">sokonalysis</span>
                        </a>
                        <button class="mobile-toggle" id="mobileToggle">
                            <span></span><span></span><span></span>
                        </button>
                        <nav class="main-nav" id="mainNav">
                            <ul>
                                <li><a href="${basePath}index.html" class="nav-link"><img src="${basePath}assets/images/home.png" class="nav-icon">Home</a></li>
                                <li><a href="${basePath}pages/downloads.html" class="nav-link"><img src="${basePath}assets/images/download.png" class="nav-icon">Downloads</a></li>
                            </ul>
                            <button class="theme-toggle" id="themeToggle">
                                <i class="fas fa-moon"></i>
                            </button>
                        </nav>
                    </div>
                </header>
            `;
            initMobileMenu();
            setActiveLink();
            initTheme();
        });
}

function loadFooter(basePath) {
    const footerPlaceholder = document.getElementById('footer-placeholder');
    if (!footerPlaceholder) return;
    
    fetch(basePath + 'components/footer.html')
        .then(response => response.text())
        .then(data => {
            footerPlaceholder.innerHTML = data;
        })
        .catch(() => {
            footerPlaceholder.innerHTML = `
                <footer class="site-footer">
                    <div class="footer-container">
                        <a href="https://github.com/sokonalysis/sokonalysis" class="footer-github-link" target="_blank">
                            <svg height="16" width="16" viewBox="0 0 16 16" fill="currentColor">
                                <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
                            </svg>
                            <span>github.com/sokonalysis/sokonalysis</span>
                        </a>
                    </div>
                </footer>
            `;
        });
}

function initMobileMenu() {
    const toggle = document.getElementById('mobileToggle');
    const nav = document.getElementById('mainNav');
    
    if (toggle && nav) {
        toggle.addEventListener('click', function() {
            nav.classList.toggle('active');
        });
    }
}

function setActiveLink() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    
    document.querySelectorAll('.nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href && href.endsWith(currentPage)) {
            link.classList.add('active');
        }
    });
}

// Copy to clipboard
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('copy-btn')) {
        const codeBlock = e.target.closest('.code-block');
        if (codeBlock) {
            const code = codeBlock.querySelector('code').textContent;
            navigator.clipboard.writeText(code).then(() => {
                e.target.textContent = 'Copied!';
                e.target.classList.add('copied');
                setTimeout(() => {
                    e.target.textContent = 'Copy';
                    e.target.classList.remove('copied');
                }, 2000);
            });
        }
    }
});

// Tab functionality
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('tab-btn')) {
        const tabGroup = e.target.closest('.tabs');
        const tabButtons = tabGroup.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');
        
        tabButtons.forEach(btn => btn.classList.remove('active'));
        e.target.classList.add('active');
        
        const tabId = e.target.getAttribute('data-tab');
        tabContents.forEach(content => {
            content.classList.remove('active');
            if (content.id === tabId) {
                content.classList.add('active');
            }
        });
    }
});