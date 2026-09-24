from odoo import fields, models


class ClinicSpecialty(models.Model):
    _name = 'clinic.specialty'
    _description = 'Clinic Specialty'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True, size=8)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)

    _code_uniq = models.Constraint(
        'unique (code)',
        'The specialty code must be unique!',
    )
