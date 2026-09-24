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
    'depends': ['base', 'hr'],
    'data': [
        'security/clinic_security.xml',
        'security/ir.model.access.csv',
    ],
    'application': True,
    'installable': True,
}
