document.addEventListener('DOMContentLoaded', () => {
    const themeDropdownItems = document.querySelectorAll('.theme-dropdown-item');
    
    // Apply the saved theme on page load
    const savedTheme = localStorage.getItem('theme') || localStorage.getItem('dashboardTheme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    localStorage.setItem('theme', savedTheme);
    localStorage.setItem('dashboardTheme', savedTheme);

    // Add click event listeners to dropdown items
    themeDropdownItems.forEach(item => {
        item.addEventListener('click', () => {
            const selectedTheme = item.getAttribute('data-theme');
            if (!selectedTheme) return;
            document.documentElement.setAttribute('data-theme', selectedTheme);
            localStorage.setItem('theme', selectedTheme);
            localStorage.setItem('dashboardTheme', selectedTheme);
            window.dispatchEvent(new Event('themechange'));
        });
    });
});