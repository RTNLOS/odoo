/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState, onMounted } from "@odoo/owl";

class WarehouseDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.menuService = useService("menu");
        this.rpc = useService("rpc");
        this.notificationService = useService("notification");
        this.user = useService("user");

        this.state = useState({
            sidebarOpen: false,
            warehouseSetupExpanded: false,
            companyLogo: null,
            filters: {
                client: '',
                vessel: '',
            },
            stats: {
                totalInventoryItem: 0,
                expectedTomorrow: 0,
                expectedToday: 0,
                toBePutInStock: 0,
                withoutAllocatedStorage: 0,
                labelsToBePrinted: 0,
                longerThan90Days: 0,
                openOSDInventory: 0,
                criticalStockItems: 0,
                dangerousGoods: 0,
                temperatureSensitive: 0,
                PendingdispatchedItems: 0,
                mainWarehouseUtilization: "0",
                bondedWarehouseUtilization: "0",
                coveredStackingUtilization: "0",
                openStackingUtilization: "0"
            }
        });
        
        onWillStart(async () => {
            // 3. Fetch the company logo URL using the third method (search for companies)
            try {
                const companies = await this.orm.searchRead('res.company', [], ['id', 'name'], { limit: 1 });
                if (companies && companies.length > 0) {
                    const companyId = companies[0].id;
                    this.state.companyLogo = `/web/image/res.company/${companyId}/logo`;
                }
            } catch (error) {
                console.error("Failed to fetch company logo:", error);
            }
            
            // Fetch the rest of the dashboard data
            await this.fetchDashboardData();
        });
        
        onMounted(() => {
            const savedSidebarState = localStorage.getItem('warehouse_sidebar_open');
            if (savedSidebarState !== null) {
                this.state.sidebarOpen = JSON.parse(savedSidebarState);
            }
        });
    }
    
    async fetchDashboardData() {
        try {
            const filterData = {
                client: this.state.filters.client,
                vessel: this.state.filters.vessel,
            };
            
            const stats = await this.orm.call(
                'stock.picking',
                'get_warehouse_dashboard_data',
                [filterData]
            );

            this.state.stats = stats || {
                totalInventoryItem: 0,
                expectedTomorrow: 0,
                expectedToday: 0,
                toBePutInStock: 0,
                withoutAllocatedStorage: 0,
                labelsToBePrinted: 0,
                longerThan90Days: 0,
                openOSDInventory: 0,
                criticalStockItems: 0,
                dangerousGoods: 0,
                temperatureSensitive: 0,
                PendingdispatchedItems: 0,
                mainWarehouseUtilization: "0",
                bondedWarehouseUtilization: "0",
                coveredStackingUtilization: "0",
                openStackingUtilization: "0"
            };
            
        } catch (error) {
            console.error("Failed to fetch dashboard data:", error);
            this.notificationService.add(
                "Failed to fetch dashboard data. Please try again.",
                {
                    type: "warning",
                    title: "Dashboard Error",
                }
            );
        }
    }
    
    async openAppDrawer() {
        try {
            await this.actionService.doAction({
                type: 'ir.actions.client',
                tag: 'menu',
                target: 'current'
            });
        } catch (error) {
            console.error("Failed to open app drawer using action service:", error);
            
            try {
                if (this.menuService && this.menuService.toggle) {
                    this.menuService.toggle();
                } else {
                    await this.actionService.doAction('base.open_menu');
                }
            } catch (fallbackError) {
                console.error("Failed to open app drawer:", fallbackError);
                
                try {
                    await this.actionService.doAction({
                        type: 'ir.actions.client',
                        tag: 'home',
                        target: 'current'
                    });
                } catch (homeError) {
                    console.error("All methods failed to open app drawer:", homeError);
                    this.notificationService.add(
                        "Unable to open app drawer. Please refresh the page.",
                        {
                            type: "warning",
                            title: "Navigation Error",
                        }
                    );
                }
            }
        }
    }
    
    toggleSidebar() {
        this.state.sidebarOpen = !this.state.sidebarOpen;
        
        // Save sidebar state to localStorage
        localStorage.setItem('warehouse_sidebar_open', JSON.stringify(this.state.sidebarOpen));
        
        // Toggle classes for hamburger icon
        const openBtn = document.getElementById('opennavbtn');
        const closeBtn = document.getElementById('closenavbtn');
        
        if (this.state.sidebarOpen) {
            openBtn.classList.add('d-none');
            closeBtn.classList.remove('d-none');
        } else {
            openBtn.classList.remove('d-none');
            closeBtn.classList.add('d-none');
        }
    }

    toggleWarehouseSetup() {
        this.state.warehouseSetupExpanded = !this.state.warehouseSetupExpanded;
    }
    
    handleDashboardClick() {
        // Stay on current dashboard view
        console.log("Dashboard clicked");
    }
    
    handleReceiptsClick() {
        this.navigateToWarehouseReceipts();
    }
    
    handleDispatchClick() {
        this.navigateToWarehouseDispatch();
    }
    
    handleReportingClick() {
        this.navigateToStockReporting();
    }
    
    async navigateToWarehouseReceipts() {
        try {
            await this.actionService.doAction('warehousing_system.action_warehouse_inventory_receipts');
        } catch (error) {
            console.error("Failed to navigate to warehouse receipts:", error);
        }
    }
    
    async navigateToWarehouseDispatch() {
        try {
            await this.actionService.doAction('warehousing_system.action_warehouse_dispatch_inventory');
        } catch (error) {
            console.error("Failed to navigate to warehouse dispatch:", error);
        }
    }
    
    async navigateToStockReporting() {
        try {
            await this.actionService.doAction('stock.dashboard_open_quants');
        } catch (error) {
            console.error("Failed to navigate to stock reporting:", error);
        }
    }
    
    async navigateToWarehouseSetup() {
        try {
            await this.doAction('stock.action_picking_type_list');
        } catch (error) {
            console.error("Failed to navigate to warehouse setup:", error);
        }
    }
    
    async navigateToWarehouses() {
        try {
            await this.actionService.doAction('stock.action_warehouse_form');
        } catch (error) {
            console.error("Failed to navigate to warehouses:", error);
        }
    }
    
    async navigateToLocations() {
        try {
            await this.actionService.doAction('stock.action_location_form');
        } catch (error) {
            console.error("Failed to navigate to storage locations:", error);
        }
    }
    
    async navigateToOperationalTypes() {
        try {
            await this.actionService.doAction('stock.action_picking_type_list');
        } catch (error) {
            console.error("Failed to navigate to operational types:", error);
        }
    }

    
    onFilterChange(event, filterName) {
        this.state.filters[filterName] = event.target.value;
        this.fetchDashboardData();
    }

    onClientInputChange(event, filterName) {
        this.state.filters[filterName] = event.target.value;
        this._debouncedFetch();
    }

    _debouncedFetch() {
        if (this._searchTimeout) {
            clearTimeout(this._searchTimeout);
        }
        this._searchTimeout = setTimeout(() => {
            this.fetchDashboardData();
        }, 500);
    }

    async onCardClick(actionName, cardSelected, title) {
        try {
            const filterData = {
                client: this.state.filters.client,
                vessel: this.state.filters.vessel,
            };
            
            const actionData = {
                title: title,
                cardSelected: cardSelected || {},
                filterData
            };

            const result = await this.orm.call(
                'stock.picking',
                'get_action',
                [actionData]
            );

            if (result && result.action) {
                await this.actionService.doAction(result.action);
            }
        } catch (error) {
            console.error("Failed to execute action:", error);
            this.notificationService.add(
                "Failed to open view. Please try again.",
                {
                    type: "warning",
                    title: "Action Error",
                }
            );
        }
    }
    
    willUnmount() {
        if (this._searchTimeout) {
            clearTimeout(this._searchTimeout);
        }
    }
}

WarehouseDashboard.template = 'warehousing_system.WarehouseDashboard';

registry.category("actions").add("warehouse_inventory_dashboard", WarehouseDashboard);

export default WarehouseDashboard;