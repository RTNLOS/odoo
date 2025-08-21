$(document).ready(function() {
    const sidebar        = $('#sidebar');
    const mainContent    = $('#mainContent');
    const sidebarToggle  = $('#sidebarToggle');
    const sidebarOverlay = $('#sidebarOverlay');
    
    const SIDEBAR_STATE_KEY  = 'warehouse_sidebar_state';
    const SIDEBAR_MOBILE_KEY = 'warehouse_sidebar_mobile';

    function getSidebarState() {
        try {
            if (typeof(Storage) !== "undefined") {
                return {
                    isCollapsed:  localStorage.getItem(SIDEBAR_STATE_KEY) === 'collapsed',
                    isMobileOpen: localStorage.getItem(SIDEBAR_MOBILE_KEY) === 'open'
                };
            }
        } catch (_) { /* ignore */ }
        try {
            if (typeof(sessionStorage) !== "undefined") {
                return {
                    isCollapsed:  sessionStorage.getItem(SIDEBAR_STATE_KEY) === 'collapsed',
                    isMobileOpen: sessionStorage.getItem(SIDEBAR_MOBILE_KEY) === 'open'
                };
            }
        } catch (_) { /* ignore */ }
        return { isCollapsed: false, isMobileOpen: false };
    }

    function saveSidebarState(isCollapsed, isMobileOpen) {
        try {
            if (typeof(Storage) !== "undefined") {
                localStorage.setItem(SIDEBAR_STATE_KEY,  isCollapsed  ? 'collapsed' : 'expanded');
                localStorage.setItem(SIDEBAR_MOBILE_KEY, isMobileOpen ? 'open'      : 'closed');
                return;
            }
        } catch (_) { /* ignore */ }
        try {
            if (typeof(sessionStorage) !== "undefined") {
                sessionStorage.setItem(SIDEBAR_STATE_KEY,  isCollapsed  ? 'collapsed' : 'expanded');
                sessionStorage.setItem(SIDEBAR_MOBILE_KEY, isMobileOpen ? 'open'      : 'closed');
            }
        } catch (_) { /* ignore */ }
    }

    function initializeSidebarState() {
        const state = getSidebarState();
        if (window.innerWidth <= 768) {
            if (state.isMobileOpen) {
                sidebar.addClass('show');
                sidebarOverlay.addClass('show');
            }
        } else {
            if (state.isCollapsed) {
                sidebar.addClass('collapsed');
                mainContent.addClass('expanded');
            }
        }
    }

    function toggleSidebar() {
        if (window.innerWidth <= 768) {
            const isCurrentlyOpen = sidebar.hasClass('show');
            sidebar.toggleClass('show');
            sidebarOverlay.toggleClass('show');
            saveSidebarState(false, !isCurrentlyOpen);
        } else {
            const isCurrentlyCollapsed = sidebar.hasClass('collapsed');
            sidebar.toggleClass('collapsed');
            mainContent.toggleClass('expanded');
            saveSidebarState(!isCurrentlyCollapsed, false);
        }
    }

    sidebarToggle.on('click', function() {
        toggleSidebar();
    });

    sidebarOverlay.on('click', function() {
        sidebar.removeClass('show');
        sidebarOverlay.removeClass('show');
        saveSidebarState(false, false);
    });

    $(window).on('resize', function() {
        const state = getSidebarState();
        if (window.innerWidth > 768) {
            sidebar.removeClass('show');
            sidebarOverlay.removeClass('show');
            if (state.isCollapsed) {
                sidebar.addClass('collapsed');
                mainContent.addClass('expanded');
            }
        } else {
            sidebar.removeClass('collapsed');
            mainContent.removeClass('expanded');
        }
    });

    // Fallback function to set active menu item based on path
    function fallbackSetActiveByPath() {
        $('.nav-link').removeClass('active');
        const current = window.location.pathname;
        $('.nav-link').each(function() {
            const href = $(this).attr('href');
            if ((current === '/warehouse' || current === '/warehouse/') && href === '/warehouse/dashboard') {
                $(this).addClass('active');
                return;
            }
            if (current === href || (href !== '/warehouse' && href !== '/' && current.startsWith(href))) {
                $(this).addClass('active');
            }
        });
    }

    // Smooth scrolling for anchor links
    $('a[href^="#"]').on('click', function(e) {
        e.preventDefault();
        const target = $(this.getAttribute('href'));
        if (target.length) {
            $('html, body').stop().animate({
                scrollTop: target.offset().top
            }, 1000);
        }
    });
    
    // Close sidebar on Escape key
    $(document).on('keydown', function(e) {
        if (e.key === 'Escape' && window.innerWidth <= 768) {
            sidebar.removeClass('show');
            sidebarOverlay.removeClass('show');
            saveSidebarState(false, false);
        }
    });

    // Handle brand click navigation
    $('.sidebar-brand').on('click', function(e) {
        e.preventDefault();
        window.location.href = '/warehouse/dashboard';
    });

    // Initialize everything
    initializeSidebarState();
    fallbackSetActiveByPath();
});