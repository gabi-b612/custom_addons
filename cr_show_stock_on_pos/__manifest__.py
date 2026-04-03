# -*- coding: utf-8 -*-
# Part of Creyox Technologies

{
    "name": "POS Stock Management | Real-Time Stock Visibility in POS | Advanced POS Inventory Control | "
            "Stock Threshold Alerts for POS | Odoo POS Stock Integration",
    "author": "Creyox Technologies",
    "website": "https://www.creyox.com",
    "support": "support@creyox.com",
    "depends": ["base", "point_of_sale", "stock"],
    "category": "Point Of Sale",
    "description": """The POS Stock Management module in Odoo is a powerful tool designed to enhance inventory 
    control within the Point of Sale system. This module provides real-time stock visibility, allowing businesses 
    to monitor product quantities directly on the POS interface with options for on-hand or forecasted stock display.

    The module introduces configurable stock thresholds to prevent overselling, alerting users with customizable 
    messages and confirmation dialogs when stock levels are low. Features like disabling negative quantity products, 
    hiding out-of-stock items, and displaying stock trend indicators ensure precise inventory management. It seamlessly 
    integrates with Odoo’s inventory system, synchronizing stock across multiple locations and logging detailed 
    transactions for audit purposes.

    With dynamic stock updates and robust user feedback, this module streamlines POS operations, reduces errors, 
    and enhances decision-making for retail businesses.

    POS Stock Management,
    Real-Time Stock Visibility,
    Stock Threshold Alerts,
    Advanced POS Inventory Control,
    Odoo POS Stock Integration,
    Negative Stock Prevention,
    Stock Trend Indicators,
    Multi-Location Stock Sync,
    How to manage stock in Odoo POS?,
    How does the module prevent overselling in POS?,
    Can this module display stock trends in POS?,
    How does the stock threshold feature work?,
    How to configure stock visibility in Odoo POS?,
    How does this module enhance inventory tracking in POS?,
    POS Stock Management in Odoo,
    Real-Time Stock Visibility in Odoo,
    Stock Threshold Alerts in Odoo,
    Advanced POS Inventory Control in Odoo,
    Odoo POS Stock Integration in Odoo,
    Negative Stock Prevention in Odoo,
    Stock Trend Indicators in Odoo,
    Multi-Location Stock Sync in Odoo,
    """,
    "license": "OPL-1",
    "version": "18.0.1.0.4",
    "summary": """
        The POS Stock Management module is designed to enhance inventory control within Odoo’s Point of Sale system 
        by providing real-time stock visibility and threshold-based restrictions. Users can configure stock display 
        to show either on-hand or forecasted quantities, tailoring the system to their operational needs. The module 
        introduces a stock threshold feature that prevents overselling by prompting users with confirmation dialogs 
        when adding products would reduce stock below a defined limit.

        The POS Stock Management module also integrates seamlessly with Odoo’s inventory system to provide robust 
        stock tracking. It supports features like disabling negative quantity products, displaying stock trend 
        indicators, and synchronizing stock across multiple locations, ensuring accurate and efficient POS operations.

        POS Stock Management,
        Real-Time Stock Visibility,
        Stock Threshold Alerts,
        Advanced POS Inventory Control,
        Odoo POS Stock Integration,
        Negative Stock Prevention,
        Stock Trend Indicators,
        Multi-Location Stock Sync,
        How to manage stock in Odoo POS?,
        How does the module prevent overselling in POS?,
        Can this module display stock trends in POS?,
        How does the stock threshold feature work?,
        How to configure stock visibility in Odoo POS?,
        How does this module enhance inventory tracking in POS?,
        POS Stock Management in Odoo,
        Real-Time Stock Visibility in Odoo,
        Stock Threshold Alerts in Odoo,
        Advanced POS Inventory Control in Odoo,
        Odoo POS Stock Integration in Odoo,
        Negative Stock Prevention in Odoo,
        Stock Trend Indicators in Odoo,
        Multi-Location Stock Sync in Odoo,
    """,
    "data": [
        "views/res_cofig_settings_views.xml",
        "views/product_template_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "cr_show_stock_on_pos/static/src/xml/product_item.xml",
            "cr_show_stock_on_pos/static/src/css/product_quantity.scss",
            "cr_show_stock_on_pos/static/src/css/pos_stock_display.css",
            "cr_show_stock_on_pos/static/src/js/pos_location.js",
            "cr_show_stock_on_pos/static/src/js/pos_payment_screen.js",
            "cr_show_stock_on_pos/static/src/js/pos_session.js",
            "cr_show_stock_on_pos/static/src/js/deny_order.js",
            "cr_show_stock_on_pos/static/src/js/order_summary.js",
        ],
    },
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": True,
    "images": [
        "static/description/banner.png",
    ],
    "price": 30,
    "currency": "USD",
}