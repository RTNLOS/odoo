{
    'name': 'Memo Website Dashboard ',
    'version': '16.0.1',
    'author': "Maduka Sopulu",
    'category': 'ERP',
    'summary': 'ODOO Base customizable dashboard for office memo',
    'depends': ['base', 'website', 'company_memo', 'portal', 'website_payment'],
    'description': "ODOO Base Extension to customize modules for portal users",
    "data": [
        # 'security/ir.model.access.csv',
        'static/templates/dashboard.xml',
        'security/ir.model.access.csv',
        'views/memo_view.xml',
    ],
    # 'qweb': [
    #     'static/xml/partials.xml',
    # ],
    'assets': {
        'web.assets_frontend': [
        '/office_dashboard/static/src/js/dashboard.js',
        '/office_dashboard/static/src/js/realtime_dashboard.js',
        '/office_dashboard/static/src/js/realtime_frame_dashboard.js',
        '/office_dashboard/static/src/css/dashboard.css',
        '/office_dashboard/static/src/css/style.css',
        '/office_dashboard/static/src/js/plugins/perfect-scrollbar.min.js',
        '/office_dashboard/static/src/js/plugins/smooth-scrollbar.min.js',
        '/office_dashboard/static/src/js/plugins/chartjs.min.js',
        '/office_dashboard/static/src/js/plugins/blockUI.min.js',
        ],
        
    },
}
