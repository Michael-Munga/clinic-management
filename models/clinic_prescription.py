from odoo import fields, models


class ClinicPrescription(models.Model):
    """
    ClinicPrescription represents a doctor's medication order for a patient.
    Can be created directly or spawned from a consultation.
    """
    # =========================================================================
    # PHASE 4: AUDIT CHATTER INHERITANCE
    # =========================================================================
    # Gives prescriptions audit tracking, doctor notes, and activity scheduling.
    # =========================================================================
    _name = 'clinic.prescription'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Clinic Prescription'
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Prescription Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New',
        tracking=True,
    )

    # =========================================================================
    # 1. LINKS TO CONSULTATION, PATIENT & DOCTOR
    # =========================================================================
    consultation_id = fields.Many2one(
        'clinic.consultation',
        string='Consultation',
        ondelete='cascade',
        index=True,
    )

    patient_id = fields.Many2one(
        'clinic.patient',
        string='Patient',
        required=True,
        index=True,
        tracking=True,
    )

    doctor_id = fields.Many2one(
        'clinic.doctor',
        string='Doctor',
        required=True,
        index=True,
        tracking=True,
    )

    date = fields.Date(
        string='Prescription Date',
        default=fields.Date.today,
        required=True,
        tracking=True,
    )

    # =========================================================================
    # 2. PARENT -> CHILD RELATION (One2many to Prescription Lines)
    # =========================================================================
    # line_ids connects to 'clinic.prescription.line' via foreign key 'prescription_id'.
    # In the UI, this renders as an interactive spreadsheet grid!
    line_ids = fields.One2many(
        'clinic.prescription.line',
        'prescription_id',
        string='Medications',
    )

    instructions = fields.Text(
        string='Advice / Instructions',
    )

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
        ],
        string='Status',
        default='draft',
        required=True,
        copy=False,
        # tracking=True: Logs prescription confirmation into chatter
        tracking=True,
    )

    def action_confirm(self):
        """Confirms the prescription (locks it for printing)."""
        for record in self:
            record.state = 'confirmed'

    def action_reset_to_draft(self):
        """Reopens the prescription for editing."""
        for record in self:
            record.state = 'draft'

    def _get_report_base_filename(self):
        """
        Official Odoo Report Naming Convention:
        Used by ir.actions.report and CustomerPortal._show_report to compute
        the default downloaded PDF filename cleanly without manual string formatting.
        """
        self.ensure_one()
        return f'Prescription - {self.name}'


class ClinicPrescriptionLine(models.Model):
    """
    ClinicPrescriptionLine represents a single drug entry inside a prescription.
    """
    _name = 'clinic.prescription.line'
    _description = 'Prescription Line'

    # Foreign Key back to the parent prescription.
    # ondelete='cascade': Deleting a prescription removes all its lines automatically.
    prescription_id = fields.Many2one(
        'clinic.prescription',
        string='Prescription',
        required=True,
        ondelete='cascade',
        index=True,
    )

    medication_name = fields.Char(
        string='Medication',
        required=True,
    )

    dosage = fields.Char(
        string='Dosage',
        required=True,
    )

    frequency = fields.Char(
        string='Frequency',
        required=True,
    )

    duration = fields.Char(
        string='Duration',
        required=True,
    )

    notes = fields.Char(
        string='Special Instructions',
    )
