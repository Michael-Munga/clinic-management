from odoo import fields, models


class ClinicConsultation(models.Model):
    """
    ClinicConsultation represents the medical record created by a doctor
    during or after an appointment.
    """
    _name = 'clinic.consultation'
    _description = 'Clinic Consultation'
    _order = 'consultation_date desc, id desc'

    # Reference code for the consultation (e.g., CONS-0001)
    name = fields.Char(
        string='Consultation Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New',
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
    diagnosis = fields.Text(string='Diagnosis', required=True)
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
