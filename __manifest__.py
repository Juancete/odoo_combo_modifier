{'name': 'Odoo Combo Modifier',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Permite modificar las cantidades de los componentes de un combo en pedidos y facturas.',
    'description': """Este módulo extiende la funcionalidad de Odoo para permitir la modificación de los componentes de un producto de tipo 'combo' directamente desde las líneas de pedido de venta y las líneas de factura. Los usuarios pueden ajustar las cantidades de los ítems internos del combo e incluso eliminar componentes.",""",
    'author': 'Juan Contardo',
    'website': 'http://www.winner-pak.com.ar',
    'depends': ['sale_management', 'account', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'wizards/combo_modifier_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_combo_modifier/static/src/js/combo_modifier.js',
            'odoo_combo_modifier/static/src/xml/combo_modifier_templates.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}

