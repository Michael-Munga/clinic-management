from odoo import api, fields, models


class ClinicPatient(models.Model):
    """
    ClinicPatient represents a patient in the clinic.

    DELEGATION INHERITANCE (_inherits):
    Instead of recreating contact fields (name, email, phone, address), this model
    delegates to Odoo's core 'res.partner' model via the 'partner_id' Many2one field.
    - When a ClinicPatient is created, Odoo automatically creates a linked res.partner.
    - Any field on res.partner (such as 'name') can be read and written directly on
      clinic.patient as if it were a native field!
    """
    _name = 'clinic.patient'
    _description = 'Clinic Patient'
    _inherits = {'res.partner': 'partner_id'}

    # The link to the parent partner record.
    # ondelete='cascade' ensures deleting the patient record cleans up the partner link.
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
        index=True,
    )

    # Unique medical identifier for the patient. copy=False ensures that duplicating
    # a patient does not copy the same code to the new record.
    patient_code = fields.Char(string='Patient Code', required=True, copy=False)
    birthdate = fields.Date(string='Birthdate')

    # COMPUTED FIELD:
    # 'age' is calculated dynamically from 'birthdate'.
    # store=True stores the computed value in PostgreSQL so it can be sorted and searched.
    age = fields.Integer(string='Age', compute='_compute_age', store=True)

    # SELECTION FIELD:
    # A dropdown list defined by pairs of (database_value, display_label).
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

    # Database-level unique constraint on patient_code.
    _patient_code_uniq = models.Constraint(
        'unique (patient_code)',
        'The patient code must be unique!',
    )

    @api.depends('birthdate')
    def _compute_age(self):
        """
        Computes the patient's age in full years based on the current date.
        @api.depends('birthdate') tells Odoo to recompute whenever birthdate changes.
        """
        today = fields.Date.today()
        for record in self:
            if record.birthdate:
                birthdate = record.birthdate
                # Calculate age considering whether the birthday has occurred this year
                record.age = (
                    today.year
                    - birthdate.year
                    - int((today.month, today.day) < (birthdate.month, birthdate.day))
                )
            else:
                record.age = 0
