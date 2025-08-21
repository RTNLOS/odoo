from odoo import http
from odoo.http import request

class CustomerWarehouseDashboardController(http.Controller):
    
    @http.route(['/warehouse', '/warehouse/dashboard'], type='http', auth='user', website=True)
    def render_customer_dashboard(self, **kw):
        return request.render('warehousing_system.customer_warehouse_dashboard_template', {
            'current_page': 'dashboard'
        })
    
    @http.route('/warehouse/customer/dashboard/data', type='json', auth='user', csrf=False)
    def dashboard_data(self, filters=None, **kw):
        filters = filters or {}
        data = request.env['stock.picking'].sudo().get_customer_warehouse_dashboard_data(filters)
        return data
    
    # route for ALL list views
    @http.route('/warehouse/view/<string:view_type>', type='http', auth='user', website=True)
    def warehouse_list_view(self, view_type, **kw):
        view_map = {
            'inventory': {'cardSelected': 'all_inventory', 'title': 'All Inventory'},
            'outbound': {'cardSelected': 'dispatchedItems', 'title': 'Outbound Dispatch Orders'},
            'inbound': {'cardSelected': 'toBePutInStock', 'title': 'Inbound Shipments'},
        }
        
        if view_type not in view_map:
            view_map[view_type] = {'cardSelected': view_type, 'title': kw.get('title', 'Detail View')}
        
        action_data = {
            'cardSelected': view_map[view_type]['cardSelected'],
            'filterData': {
                'vessel': kw.get('vessel', ''),
                'location_id': kw.get('location_id')
            }
        }
        
        data = request.env['stock.picking'].sudo().get_customer_dashboard_detail(action_data)

        return request.render('warehousing_system.customer_warehouse_detail_template', {
            'records': data.get('records', []),
            'headers': data.get('headers', []),
            'title': view_map[view_type]['title'],
            'current_page': view_type
        })

    # This route is for card clicks that aren't direct sidebar links
    @http.route('/warehouse/customer/dashboard/list', type='http', auth='user', website=True)
    def customer_inventory_list_redirect(self, cardSelected=None, title=None, **kw):
        params = {
            'title': title,
            'vessel': kw.get('vessel', ''),
            'location_id': kw.get('location_id', '')
        }
        query_string = '&'.join([f"{key}={value}" for key, value in params.items() if value])
        redirect_url = f"/warehouse/view/{cardSelected}?{query_string}"
        return request.redirect(redirect_url)

    @http.route('/warehouse/get_locations', type='json', auth='user', methods=['POST'], csrf=False)
    def get_stock_locations(self, **kw):
        """
        Provides a list of internal stock locations for the current company.
        This endpoint is called via AJAX to populate the 'Store Location' dropdown.
        """
        try:
            location_model = request.env['stock.location']
            locations = location_model.search_read(
                [('usage', '=', 'internal')],
                ['id', 'display_name']
            )
            return [{'id': loc['id'], 'name': loc['display_name']} for loc in locations]
        except Exception as e:
            return {'error': str(e), 'locations': []}