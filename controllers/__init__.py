# -*- coding: utf-8 -*-
# Controllers Package Initialization
# =============================================================================
# In Odoo, controllers handle HTTP web requests, including:
# 1. Customer / Patient Portal web pages (HTML rendering via QWeb)
# 2. REST API endpoints (JSON responses for kiosks, mobile apps, integrations)
# =============================================================================
from . import portal
from . import api
