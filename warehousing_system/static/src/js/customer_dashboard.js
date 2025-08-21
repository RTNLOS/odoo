/** @odoo-module **/

(function() {
    'use strict';

    class WarehouseDashboardController {
        constructor() {
            this.state = {
                filters: { 
                    vessel: '',
                    location_id: null
                },
                isLoading: false,
                hasError: false,
                dashboardData: {}
            };
            this.elements = {};
            this.searchTimeout = null;
            this.imageRetryCount = new Map();
        }

        async init() {
            this.cacheElementReferences();
            this.setupImageErrorHandling();
            this.setupEventListeners();
            await this.fetchDashboardData();
            setTimeout(() => this.fixBrokenImages(), 500);
        }

        cacheElementReferences() {
            this.elements = {
                vesselFilter: document.getElementById('vessel-filter'),
                warehouseSelect: document.getElementById('warehouseSelect'),
                cardsContainer: document.getElementById('cards-container'),
            };
            
            [   'totalInStock', 'expectedToday', 'expectedTomorrow', 'pendingAllocation','labelsToBePrinted',
                'dispatchedToday', 'dispatchedTomorrow', 'longerThan90Days', 'criticalStockItems', 'dangerousGoods', 'temperatureSensitive',
                'openOSDInventory', 'mainWarehouseUtilization', 'bondedWarehouseUtilization', 'coveredStackingUtilization', 'openStackingUtilization'
            ].forEach(cat => {
                this.elements[`count-${cat}`] = document.getElementById(`count-${cat}`);
            });
        }

        setupImageErrorHandling() {
            const images = document.querySelectorAll('.card-icon img[data-icon-type="png"]');
            images.forEach(img => {
                img.addEventListener('error', () => this.handleImageError(img));
                img.addEventListener('load', () => this.handleImageLoad(img));
            });
        }

        handleImageError(img) {
            const retryKey = img.src.split('?')[0];
            const currentRetries = this.imageRetryCount.get(retryKey) || 0;
            
            if (currentRetries < 3) {
                console.log(`Retrying image load (attempt ${currentRetries + 1}):`, retryKey);
                this.imageRetryCount.set(retryKey, currentRetries + 1);
                const baseSrc = img.dataset.fallbackSrc || retryKey;
                img.src = `${baseSrc}?v=${Date.now()}&retry=${currentRetries + 1}`;
            } else {
                console.error('Failed to load image after 3 retries:', retryKey);
                img.style.display = 'none';
                const placeholder = document.createElement('div');
                placeholder.innerHTML = '⚠️';
                placeholder.style.cssText = 'font-size: 1.5rem; color: #c02c2c; text-align: center;';
                img.parentNode.appendChild(placeholder);
            }
        }

        handleImageLoad(img) {
            const retryKey = img.src.split('?')[0];
            this.imageRetryCount.delete(retryKey);
            img.style.display = 'block';
        }

        fixBrokenImages() {
            const images = document.querySelectorAll('.card-icon img[data-icon-type="png"]');
            images.forEach(img => {
                if (img.complete && (img.naturalWidth === 0 || img.naturalHeight === 0)) {
                    console.log('Detected broken image, reloading:', img.src);
                    const baseSrc = img.dataset.fallbackSrc || img.src.split('?')[0];
                    img.src = `${baseSrc}?v=${Date.now()}&reload=1`;
                }
            });
        }

        setupEventListeners() {
            if (this.elements.vesselFilter) {
                this.elements.vesselFilter.addEventListener('input',
                    this.debounce(ev => this.onFilterChange(ev, 'vessel'), 300)
                );
            }
            
            if (this.elements.warehouseSelect) {
                this.elements.warehouseSelect.addEventListener('change', 
                    () => this.fetchDashboardData()
                );
            }

            document.querySelectorAll('.warehouse-card').forEach(card => {
                card.addEventListener('click', () => {
                    this.onCardClick(card.dataset.category, card.dataset.title);
                });
            });

            document.addEventListener('visibilitychange', () => {
                if (!document.hidden) {
                    setTimeout(() => this.fixBrokenImages(), 100);
                }
            });

            window.addEventListener('pageshow', (event) => {
                if (event.persisted) {
                    setTimeout(() => this.fixBrokenImages(), 100);
                }
            });
        }

        onFilterChange(ev, field) {
            this.state.filters[field] = ev.target.value;
            this.fetchDashboardData();
        }

        updateLoadingState(isLoading) {
            this.state.isLoading = isLoading;
            if (this.elements.loadingState) {
                this.elements.loadingState.style.display = isLoading ? 'block' : 'none';
            }
            if (this.elements.cardsContainer) {
                this.elements.cardsContainer.style.opacity = isLoading ? '0.6' : '1';
                this.elements.cardsContainer.style.pointerEvents = isLoading ? 'none' : 'auto';
            }
        }

        updateErrorState(hasError, msg='') {
            this.state.hasError = hasError;
            if (this.elements.errorState) {
                this.elements.errorState.style.display = hasError ? 'block' : 'none';
            }
            if (this.elements.errorMessage) {
                this.elements.errorMessage.textContent = msg;
            }
            if (hasError) {
                console.error('Dashboard error:', msg);
            }
        }

        updateCardCounts(data) {
           Object.entries(data).forEach(([key, value]) => {
                const el = this.elements[`count-${key}`];
                if (el) {
                    el.style.transition = 'color 0.3s ease';
                    el.style.color = '#28a745';
                    el.textContent = value || 0;
                    setTimeout(() => {
                        el.style.color = '';
                    }, 300);
                }
           });
        }

        async fetchDashboardData() {
            const selectedLocationId = this.elements.warehouseSelect ? this.elements.warehouseSelect.value : null;
            this.state.filters.location_id = selectedLocationId;

            this.updateLoadingState(true);
            this.updateErrorState(false);
            
            try {
                const res = await fetch('/warehouse/customer/dashboard/data', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Cache-Control': 'no-cache'
                    },
                    body: JSON.stringify({
                        jsonrpc: '2.0', 
                        method: 'call',
                        params: { filters: this.state.filters },
                        id: Math.random() * 1e6 | 0
                    })
                });
                
                if (!res.ok) {
                    throw new Error(`HTTP error! status: ${res.status}`);
                }
                
                const payload = await res.json();
                
                if (payload.error) {
                    throw new Error(payload.error.data?.message || payload.error.message);
                }
                
                this.state.dashboardData = payload.result || {};
                this.updateCardCounts(this.state.dashboardData);
                
                setTimeout(() => this.fixBrokenImages(), 100);
                
            } catch (e) {
                console.error('Failed to fetch dashboard data:', e);
                this.updateErrorState(true, 'Failed to load dashboard data. Please try again.');
            } finally {
                this.updateLoadingState(false);
            }
        }

        async onCardClick(cardId, title) {
            if (this.state.isLoading) return;
            
            const { vessel, location_id } = this.state.filters;
            
            const params = new URLSearchParams({
                cardSelected: cardId,
                title: title,
                vessel: vessel || '',
                location_id: location_id || ''
            });
            
            this.updateLoadingState(true);
            window.location.href = `/warehouse/customer/dashboard/list?${params.toString()}`;
        }

        debounce(fn, wait = 300) {
            return (...args) => {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => fn.apply(this, args), wait);
            };
        }

        // Public method to manually refresh images (can be called from console if needed)
        refreshImages() {
            console.log('Manually refreshing all images...');
            const images = document.querySelectorAll('.card-icon img[data-icon-type="png"]');
            images.forEach(img => {
                const baseSrc = img.dataset.fallbackSrc || img.src.split('?')[0];
                img.src = `${baseSrc}?v=${Date.now()}&manual=1`;
            });
        }

        destroy() {
            clearTimeout(this.searchTimeout);
            this.imageRetryCount.clear();
        }
    }

    window.warehouseDashboard = null;

    document.addEventListener('DOMContentLoaded', () => {
        window.warehouseDashboard = new WarehouseDashboardController();
        window.warehouseDashboard.init();
    });

    window.addEventListener('beforeunload', () => {
        if (window.warehouseDashboard) {
            window.warehouseDashboard.destroy();
        }
    });

})();