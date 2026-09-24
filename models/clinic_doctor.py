from odoo import fields, models


class ClinicDoctor(models.Model):
    _name = 'clinic.doctor'
    _description = 'Clinic Doctor'
    _inherits = {'hr.employee': 'employee_id'}

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        auto_join=True,
        index=True,
    )
    specialty_id = fields.Many2one(
        'clinic.specialty',
        string='Specialty',
        ondelete='restrict',
    )
    license_number = fields.Char(string='License Number')
    consultation_fee = fields.Monetary(string='Consultation Fee')
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='employee_id.currency_id',
        readonly=True,
    )
    biography = fields.Text(string='Biography')

    _license_number_uniq = models.Constraint(
        'unique (license_number)',
        'The license number must be unique!',
    )
