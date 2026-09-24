#!/bin/bash

# 1. Change directory to ~/odoo-dev so relative paths resolve correctly
cd ~/odoo-dev

# 2. Activate the virtual environment
source ~/odoo-dev/venv/bin/activate

# 3. Kill any process already holding port 8069
echo "Killing any process holding port 8069..."
PID=$(lsof -ti:8069)
if [ -n "$PID" ]; then
    kill -9 $PID 2>/dev/null
    sleep 1
fi

# 4. Start Odoo with configuration, database, module update, reload, and debug logging
echo "Starting Odoo at http://localhost:8069"
python odoo/odoo-bin -c config/odoo.conf -d odoo -u clinic_management --dev=reload --log-level=debug
