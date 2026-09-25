{
    'name': 'Clinic Management',
    'version': '19.0.1.0.0',
    'summary': 'Manage clinic operations, patients, and appointments',
    'description': '''
Clinic Management
=================
Module for managing clinic operations, patient records, and appointments.
''',
    'author': 'Daudi',
    'category': 'Industry',
    'license': 'LGPL-3',

    # DEPENDENCIES:
    # 'base': provides core Odoo features and the 'res.partner' model (used by patients).
    # 'hr': provides employee management and 'hr.employee' (used by doctors).
    'depends': ['base', 'hr'],

    # DATA LOADING ORDER:
    # Odoo loads files sequentially from top to bottom. Order is critical:
    # 1. Security groups must exist before access rules reference them.
    # 2. Access rules (CSV) must exist before views are accessed.
    # 3. Views define the UI layouts for each model.
    # 4. Actions reference models and define how views are opened.
    # 5. Menus link to actions to display in the navigation sidebar.
    'data': [
        'security/clinic_security.xml',
        'security/ir.model.access.csv',
        'views/clinic_specialty_views.xml',
        'views/clinic_patient_views.xml',
        'views/clinic_doctor_views.xml',
        'views/clinic_appointment_views.xml',
        'views/clinic_consultation_views.xml',
        'views/clinic_prescription_views.xml',
        'views/clinic_actions.xml',
        'views/clinic_menus.xml',
    ],

    # When True, this module appears as a standalone app in the App switcher grid.
    'application': True,
    'installable': True,
}
