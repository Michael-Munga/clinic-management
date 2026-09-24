from odoo import api, fields, models


class ClinicPatient(models.Model):
    _name = 'clinic.patient'
    _description = 'Clinic Patient'
    _inherits = {'res.partner': 'partner_id'}

    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
        auto_join=True,
        index=True,
    )
    patient_code = fields.Char(string='Patient Code', required=True, copy=False)
    birthdate = fields.Date(string='Birthdate')
    age = fields.Integer(string='Age', compute='_compute_age', store=True)
    blood_type = fields.Selection(
        selection=[
            ('a_pos', 'A+'),
            ('a_neg', 'A-'),
            ('b_pos', 'B+'),
            ('b_neg', 'B-'),
            ('ab_pos', 'AB+'),
            ('ab_neg', 'AB-'),
            ('o_pos', 'O+'),
            ('o_neg', 'O-'),
        ],
        string='Blood Type',
    )
    allergies = fields.Text(string='Allergies')
    emergency_contact_name = fields.Char(string='Emergency Contact Name')
    emergency_contact_phone = fields.Char(string='Emergency Contact Phone')

    _patient_code_uniq = models.Constraint(
        'unique (patient_code)',
        'The patient code must be unique!',
    )

    @api.depends('birthdate')
    def _compute_age(self):
        today = fields.Date.today()
        for record in self:
            if record.birthdate:
                birthdate = record.birthdate
                record.age = (
                    today.year
                    - birthdate.year
                    - int((today.month, today.day) < (birthdate.month, birthdate.day))
                )
            else:
                record.age = 0
