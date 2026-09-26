from odoo import fields, models


class ClinicConsultation(models.Model):
    """
    ClinicConsultation represents the medical record created by a doctor
    during or after an appointment.
    """
    # =========================================================================
    # PHASE 4: AUDIT CHATTER INHERITANCE
    # =========================================================================
    # Provides internal doctor notes, collaboration, and field change auditing.
    # =========================================================================
    _name = 'clinic.consultation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Clinic Consultation'
    _order = 'consultation_date desc, id desc'

    # Reference code for the consultation (e.g., CONS-0001)
    name = fields.Char(
        string='Consultation Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New',
        tracking=True,
    )

    # =========================================================================
    # 1. APPOINTMENT, PATIENT & DOCTOR LINKS
    # =========================================================================
    appointment_id = fields.Many2one(
        'clinic.appointment',
        string='Appointment',
        required=True,
        ondelete='cascade',
        index=True,
    )

    # RELATED FIELDS:
    # Patient and Doctor are automatically pulled from the linked appointment!
    # store=True saves them in PostgreSQL for fast search and row-level security.
    patient_id = fields.Many2one(
        'clinic.patient',
        string='Patient',
        related='appointment_id.patient_id',
        store=True,
        readonly=True,
    )

    doctor_id = fields.Many2one(
        'clinic.doctor',
        string='Doctor',
        related='appointment_id.doctor_id',
        store=True,
        readonly=True,
    )

    consultation_date = fields.Datetime(
        string='Consultation Date',
        default=fields.Datetime.now,
        required=True,
    )

    # =========================================================================
    # 2. CLINICAL FINDINGS
    # =========================================================================
    symptoms = fields.Text(string='Symptoms / Chief Complaint')
    # tracking=True: Logs any revision to the medical diagnosis into the audit timeline!
    diagnosis = fields.Text(string='Diagnosis', required=True, tracking=True)
    examination_notes = fields.Text(string='Examination Notes')

    # =========================================================================
    # 3. RELATIONS (One2many to Prescriptions)
    # =========================================================================
    # A single consultation can spawn one or more prescriptions.
    prescription_ids = fields.One2many(
        'clinic.prescription',
        'consultation_id',
        string='Prescriptions',
    )

    # =========================================================================
    # 4. LIFECYCLE
    # =========================================================================
    state = fields.Selection(
        selection=[
            ('draft', 'In Progress'),
            ('done', 'Completed'),
        ],
        string='Status',
        default='draft',
        required=True,
        copy=False,
        # tracking=True: Automatically records when the doctor completes or reopens a consultation
        tracking=True,
    )

    def action_done(self):
        """Marks consultation as Completed."""
        for record in self:
            record.state = 'done'
            # Also ensure the linked appointment is marked as Done!
            if record.appointment_id and record.appointment_id.state != 'done':
                record.appointment_id.action_done()

    def action_reset_to_draft(self):
        """Reopens the consultation for editing."""
        for record in self:
            record.state = 'draft'

    # =========================================================================
    # PHASE 5: SCHEDULE FOLLOW-UP WIZARD LAUNCHER
    # =========================================================================
    def action_open_followup_wizard(self):
        """
        Triggered when a doctor clicks 'Schedule Follow-Up' on a consultation.
        
        HOW THIS MODAL IS PRE-FILLED:
        - 'target': 'new' opens the pop-up modal dialog box.
        - 'context': Passes:
            * 'default_consultation_id': Links back to this consultation.
            * 'default_patient_id': Pre-selects the patient from this consultation.
            * 'default_doctor_id': Pre-selects the doctor who conducted this consultation.
        """
        self.ensure_one()
        return {
            'name': 'Schedule Follow-Up',
            'type': 'ir.actions.act_window',
            'res_model': 'appointment.followup.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_consultation_id': self.id,
                'default_patient_id': self.patient_id.id,
                'default_doctor_id': self.doctor_id.id,
            },
        }
