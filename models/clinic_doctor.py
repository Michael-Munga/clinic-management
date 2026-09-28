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

    # One2many relation connecting all appointments assigned to this doctor.
    # Enables easy access in Python logic and QWeb report loops!
    appointment_ids = fields.One2many(
        'clinic.appointment',
        'doctor_id',
        string='Appointments',
    )

    # Database-level unique constraint on doctor license number.
    _license_number_uniq = models.Constraint(
        'unique (license_number)',
        'The license number must be unique!',
    )

    # =========================================================================
    # PHASE 4: SMART BUTTONS (DOCTOR METRICS & JUMP NAVIGATION)
    # =========================================================================
    # Allows clinic managers and doctors to immediately see and jump to:
    # 1. All appointments assigned to this doctor.
    # 2. All medical consultations completed by this doctor.
    # =========================================================================

    appointment_count = fields.Integer(
        string='Appointments Count',
        compute='_compute_appointment_count',
        help='Total number of appointments scheduled with this doctor',
    )
    consultation_count = fields.Integer(
        string='Consultations Count',
        compute='_compute_consultation_count',
        help='Total medical consultations performed by this doctor',
    )

    def _compute_appointment_count(self):
        """Counts appointments for this doctor using fast SQL COUNT."""
        for record in self:
            record.appointment_count = self.env['clinic.appointment'].search_count([
                ('doctor_id', '=', record.id),
            ])

    def _compute_consultation_count(self):
        """Counts consultations conducted by this doctor using fast SQL COUNT."""
        for record in self:
            record.consultation_count = self.env['clinic.consultation'].search_count([
                ('doctor_id', '=', record.id),
            ])

    def action_view_appointments(self):
        """
        Opens a pre-filtered window displaying all appointments assigned to this doctor.
        Sets 'default_doctor_id' in context so newly created appointments default to this doctor.
        """
        self.ensure_one()
        return {
            'name': f"Appointments - {self.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.appointment',
            'view_mode': 'list,form,calendar',
            'domain': [('doctor_id', '=', self.id)],
            'context': {'default_doctor_id': self.id},
        }

    def action_view_consultations(self):
        """
        Opens a pre-filtered window displaying all consultations conducted by this doctor.
        """
        self.ensure_one()
        return {
            'name': f"Consultations - {self.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.consultation',
            'view_mode': 'list,form',
            'domain': [('doctor_id', '=', self.id)],
            'context': {'default_doctor_id': self.id},
        }

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

    def write(self, vals):
        """
        Automated User Provisioning on Update:
        If an existing doctor record is updated with a work_email and has no user_id,
        Odoo automatically creates/finds the res.users account and links it!
        """
        doctor_group = self.env.ref('clinic_management.group_clinic_doctor', raise_if_not_found=False)
        res = super().write(vals)
        if 'work_email' in vals or 'name' in vals:
            for record in self:
                if record.work_email and not record.user_id:
                    user = self.env['res.users'].search([('login', '=', record.work_email)], limit=1)
                    if not user:
                        user_vals = {
                            'name': record.name or record.work_email,
                            'login': record.work_email,
                            'email': record.work_email,
                        }
                        if doctor_group:
                            user_vals['groups_id'] = [(4, doctor_group.id)]
                        user = self.env['res.users'].create(user_vals)
                    elif doctor_group and doctor_group not in user.groups_id:
                        user.write({'groups_id': [(4, doctor_group.id)]})
                    record.user_id = user.id
        return res
