from odoo import api, fields, models


class ClinicDoctor(models.Model):
    """
    ClinicDoctor represents a medical doctor working in the clinic.

    DELEGATION INHERITANCE (_inherits):
    Doctors are employees of the clinic! By delegating to 'hr.employee' via 'employee_id',
    every doctor gets all HR features (department, manager, job position, work email/phone,
    name) without duplicating employee logic.
    """
    _name = 'clinic.doctor'
    _description = 'Clinic Doctor'
    _inherits = {'hr.employee': 'employee_id'}

    # Link to the underlying HR employee record.
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        index=True,
    )

    # RELATIONAL FIELD (Many2one):
    # Links each doctor to their medical specialty (e.g., Dr. Alice -> Cardiology).
    # ondelete='restrict' prevents someone from accidentally deleting a specialty
    # if there are doctors currently assigned to it!
    specialty_id = fields.Many2one(
        'clinic.specialty',
        string='Specialty',
        ondelete='restrict',
    )
    license_number = fields.Char(string='License Number')

    # MONETARY FIELD:
    # A float field tailored for financial amounts. It automatically formats with the
    # currency symbol based on the 'currency_id' field on the model.
    consultation_fee = fields.Monetary(string='Consultation Fee')

    # RELATED FIELD:
    # Fetches the currency from the linked employee (employee_id.currency_id).
    # readonly=True ensures users cannot manually change this derived currency here.
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='employee_id.currency_id',
        readonly=True,
    )
    biography = fields.Text(string='Biography')

    # Database-level unique constraint on doctor license number.
    _license_number_uniq = models.Constraint(
        'unique (license_number)',
        'The license number must be unique!',
    )

    @api.model_create_multi
    def create(self, vals_list):
        """
        Automated User Provisioning:
        When a manager registers a doctor with a work_email, Odoo automatically:
        1. Checks if a login account (res.users) already exists for this email.
        2. If not, creates the res.users account with the 'Clinic Doctor' security badge.
        3. Links user_id behind the scenes without the manager ever touching it!
        """
        doctor_group = self.env.ref('clinic_management.group_clinic_doctor', raise_if_not_found=False)
        for vals in vals_list:
            email = vals.get('work_email')
            if email and not vals.get('user_id'):
                user = self.env['res.users'].search([('login', '=', email)], limit=1)
                if not user:
                    user_vals = {
                        'name': vals.get('name') or email,
                        'login': email,
                        'email': email,
                    }
                    if doctor_group:
                        user_vals['groups_id'] = [(4, doctor_group.id)]
                    user = self.env['res.users'].create(user_vals)
                elif doctor_group and doctor_group not in user.groups_id:
                    user.write({'groups_id': [(4, doctor_group.id)]})
                vals['user_id'] = user.id
        return super().create(vals_list)
