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

    # =========================================================================
    # PHASE 4: SMART BUTTONS (COMPUTED COUNTS & JUMP-NAVIGATION)
    # =========================================================================
    # In Odoo, Smart Buttons (or Stat Buttons) sit in the top-right corner of a form.
    # They require two pieces in Python:
    # 1. A computed Integer field to show the live count on the badge.
    # 2. An action method (action_view_*) that executes when the user clicks the badge,
    #    returning an 'ir.actions.act_window' dictionary that opens a pre-filtered list.
    # =========================================================================

    # COMPUTED COUNT FIELDS:
    # We do NOT use store=True here because we want this count to always reflect the
    # exact real-time number of appointments/prescriptions without needing a database trigger.
    appointment_count = fields.Integer(
        string='Appointments Count',
        compute='_compute_appointment_count',
        help='Total number of appointments booked for this patient',
    )
    prescription_count = fields.Integer(
        string='Prescriptions Count',
        compute='_compute_prescription_count',
        help='Total number of prescriptions issued to this patient',
    )

    def _compute_appointment_count(self):
        """
        Calculates the appointment count for each patient record.
        
        PEDAGOGICAL NOTE:
        We use self.env['model.name'].search_count(domain) instead of len(self.env['model'].search(domain)).
        Why?
        - search_count runs an optimized SQL query: "SELECT COUNT(*) FROM clinic_appointment WHERE patient_id = X".
        - search() would fetch all columns of every appointment into Python memory first, which is slow for large data.
        """
        for record in self:
            record.appointment_count = self.env['clinic.appointment'].search_count([
                ('patient_id', '=', record.id),
            ])

    def _compute_prescription_count(self):
        """
        Calculates the prescription count for each patient record via fast SQL COUNT.
        """
        for record in self:
            record.prescription_count = self.env['clinic.prescription'].search_count([
                ('patient_id', '=', record.id),
            ])

    # =========================================================================
    # SMART BUTTON ACTION METHODS (Called when the user clicks the button)
    # =========================================================================
    def action_view_appointments(self):
        """
        Triggered when clicking the Appointments smart button on the Patient form.
        
        UNDERSTANDING THE RETURNED DICTIONARY:
        - self.ensure_one(): Safety check. Ensures this method is running on a single patient record,
          not a multi-record set, preventing errors when reading self.id.
        - 'type': 'ir.actions.act_window': Tells Odoo's web client to open a view window.
        - 'res_model': 'clinic.appointment': Specifies which model's views to load.
        - 'view_mode': 'list,form,calendar': Allowed view switchers (starts in list view).
        - 'domain': [('patient_id', '=', self.id)]:
            CRITICAL! This SQL WHERE clause filters the appointments so the user ONLY sees
            appointments belonging to THIS specific patient.
        - 'context': {'default_patient_id': self.id}:
            CONVENIENCE SHORTCUT! If the receptionist views this filtered list and clicks
            the "New" button to book an appointment, Odoo automatically pre-fills the
            'patient_id' dropdown with this patient!
        """
        self.ensure_one()
        return {
            'name': f"Appointments - {self.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.appointment',
            'view_mode': 'list,form,calendar',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

    def action_view_prescriptions(self):
        """
        Triggered when clicking the Prescriptions smart button on the Patient form.
        Opens a pre-filtered list of prescriptions for this patient.
        """
        self.ensure_one()
        return {
            'name': f"Prescriptions - {self.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.prescription',
            'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }
