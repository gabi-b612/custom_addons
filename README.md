wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_amd64.deb


# CONFIG ODOO CONF

[options]

; DATABASE
db_host = False
db_port = False
db_user = odoo
db_password = 
dbfilter = ^%d$
list_db = True

; SERVER
xmlrpc_port = 8069
longpolling_port = 8072
proxy_mode = False

; SECURITY
admin_passwd = <ton mot de passe>

; ADDONS
addons_path = /home/odoo/odoo18/odoo/addons,/home/odoo/.local/share/Odoo/addons/18.0,/home/odoo/odoo18/addons,/home/odoo/odoo18/enterprise,/home/odoo/odoo18/custom_addons

; DATA
data_dir = /home/odoo/.local/share/Odoo
logfile = /home/odoo/odoo18/odoo.log

; LOGS
log_level = info

; PERFORMANCE (LOCAL)
workers = 0
max_cron_threads = 1
