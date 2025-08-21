{
    'name': 'Memo Backend Dashboard ',
    'version': '16.0.1',
    'author': "Maduka Sopulu",
    'category': 'ERP',
    'summary': 'ODOO Base customizable dashboard for office memo',
    'depends': ['base', 'web', 'company_memo', 'portal', 'board', 'sale'],
    'description': "ODOO Base Extension to customize modules for portal users",
    "data": [
        # 'security/ir.model.access.csv',
        'static/templates/dashboard.xml',
        'security/ir.model.access.csv',
        'views/sales_dashboard.xml',
    ],
    
    'assets': {
        'web.assets_backend': [
        '/memo_dashboard/static/src/components/**/*.js',
        '/memo_dashboard/static/src/components/**/*.xml',
        '/memo_dashboard/static/src/components/**/*.scss',
        ],
        
    },
}
