from odoo import fields, models


class ClinicSpecialty(models.Model):
    """
    ClinicSpecialty model represents medical specialties (e.g., Cardiology, Pediatrics).
    It is a standalone model with its own database table: 'clinic_specialty'.
    """
    _name = 'clinic.specialty'
    _description = 'Clinic Specialty'

    # Name of the specialty. translate=True enables multi-language support.
    name = fields.Char(string='Name', required=True, translate=True)

    # Short code identifying the specialty (e.g., CARD, PED). size=8 limits length.
    code = fields.Char(string='Code', required=True, size=8)

    # Detailed notes or description of this specialty.
    description = fields.Text(string='Description')

    # Special Odoo field: when active=False, records are 'archived' (hidden by default)
    # instead of being permanently deleted from PostgreSQL.
    active = fields.Boolean(string='Active', default=True)

    # In Odoo 19, SQL constraints are declared using models.Constraint objects.
    # This prevents duplicate specialty codes at the database level.
    _code_uniq = models.Constraint(
        'unique (code)',
        'The specialty code must be unique!',
    )
