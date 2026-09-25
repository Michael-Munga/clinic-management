from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ClinicAppointment(models.Model):
    """
    ClinicAppointment represents an operational booking between a patient and a doctor.
    Database table created by Odoo: 'clinic_appointment'.
    """
    _name = 'clinic.appointment'
    _description = 'Clinic Appointment'
    # _order controls the default SQL sorting: newest appointments first.
    _order = 'appointment_datetime desc, id desc'

    # =========================================================================
    # 1. IDENTIFIERS & SEQUENCES
    # =========================================================================
    # Reference code for the appointment (e.g. APPT-0001).
    # copy=False ensures that when duplicating an appointment, the reference isn't duplicated.
    name = fields.Char(
        string='Appointment Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New',
    )

    # =========================================================================
    # 2. RELATIONAL FIELDS (Many2one)
    # =========================================================================
    # Many2one creates a FOREIGN KEY column in PostgreSQL.
    # In PostgreSQL, this column is named 'patient_id' and stores the integer ID of the patient.
    patient_id = fields.Many2one(
        'clinic.patient',
        string='Patient',
        required=True,
        # ondelete='cascade': If a patient is deleted, their appointments are also deleted.
        ondelete='cascade',
        index=True,
    )

    doctor_id = fields.Many2one(
        'clinic.doctor',
        string='Doctor',
        required=True,
        # ondelete='restrict': Prevents deleting a doctor if they have appointments in the database!
        ondelete='restrict',
        index=True,
    )

    # RELATED FIELD:
    # A read-only shortcut that displays the doctor's specialty automatically on the appointment form.
    specialty_id = fields.Many2one(
        'clinic.specialty',
        string='Specialty',
        related='doctor_id.specialty_id',
        readonly=True,
        store=True,
    )

    # Link to the generated Consultation
    consultation_id = fields.Many2one(
        'clinic.consultation',
        string='Consultation',
        readonly=True,
        copy=False,
    )

    # =========================================================================
    # 3. DATE, TIME & DURATION
    # =========================================================================
    appointment_datetime = fields.Datetime(
        string='Date & Time',
        required=True,
        default=fields.Datetime.now,
        index=True,
    )

    # Duration in minutes (e.g., 30 mins, 45 mins, 60 mins).
    duration = fields.Integer(
        string='Duration (Minutes)',
        default=30,
        required=True,
    )

    # COMPUTED END DATETIME:
    # Automatically calculates when the appointment ends: appointment_datetime + duration.
    # store=True stores this in PostgreSQL so Odoo's Calendar view can draw the event box!
    appointment_end_datetime = fields.Datetime(
        string='End Date & Time',
        compute='_compute_end_datetime',
        store=True,
    )

    # =========================================================================
    # 4. LIFECYCLE & WORKFLOW (Selection Field)
    # =========================================================================
    # Selection fields store the key (e.g., 'draft') in PostgreSQL,
    # but display the human-readable label (e.g., 'Draft') in the web browser.
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        copy=False,
        index=True,
    )

    cancellation_reason = fields.Text(string='Cancellation Reason')
    notes = fields.Text(string='Notes')

    # =========================================================================
    # 5. BUSINESS LOGIC & CONSTRAINTS
    # =========================================================================
    @api.depends('appointment_datetime', 'duration')
    def _compute_end_datetime(self):
        """
        Calculates appointment_end_datetime whenever start time or duration changes.
        Remember: 'self' is a Recordset, so we ALWAYS loop over 'record in self'.
        """
        for record in self:
            if record.appointment_datetime and record.duration:
                record.appointment_end_datetime = record.appointment_datetime + timedelta(
                    minutes=record.duration
                )
            else:
                record.appointment_end_datetime = record.appointment_datetime

    @api.constrains('doctor_id', 'appointment_datetime', 'duration', 'state')
    def _check_doctor_double_booking(self):
        """
        Prevents scheduling overlapping appointments for the same doctor.
        @api.constrains triggers whenever doctor, time, or duration changes.
        """
        for record in self:
            # Cancelled appointments do not block the doctor's calendar
            if record.state == 'cancel' or not record.doctor_id or not record.appointment_datetime:
                continue

            # Search PostgreSQL for any existing appointment for this doctor that overlaps
            domain = [
                ('id', '!=', record.id),
                ('doctor_id', '=', record.doctor_id.id),
                ('state', '!=', 'cancel'),
                ('appointment_datetime', '<', record.appointment_end_datetime),
                ('appointment_end_datetime', '>', record.appointment_datetime),
            ]
            overlapping_appointments = self.search(domain)

            if overlapping_appointments:
                first_conflict = overlapping_appointments[0]
                raise ValidationError(
                    f"Conflict Detected! Dr. {record.doctor_id.name} already has an appointment "
                    f"({first_conflict.name}) booked from "
                    f"{first_conflict.appointment_datetime} to {first_conflict.appointment_end_datetime}.\n"
                    f"Please choose a different time or doctor."
                )

    # =========================================================================
    # 6. WORKFLOW BUTTON ACTIONS (Called by buttons on the form view)
    # =========================================================================
    def action_confirm(self):
        """Moves appointment from Draft to Confirmed."""
        for record in self:
            record.state = 'confirmed'

    def action_start_consultation(self):
        """
        Moves appointment from Confirmed to In Progress, automatically creates a
        linked Consultation record, and opens the Consultation form!
        """
        self.ensure_one()
        self.state = 'in_progress'

        if not self.consultation_id:
            consultation = self.env['clinic.consultation'].create({
                'appointment_id': self.id,
                'name': f"CONS/{self.name or self.id}",
                'diagnosis': 'Pending assessment',
            })
            self.consultation_id = consultation.id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Consultation',
            'res_model': 'clinic.consultation',
            'res_id': self.consultation_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_done(self):
        """Moves appointment to Done."""
        for record in self:
            record.state = 'done'

    def action_cancel(self):
        """Moves appointment to Cancelled."""
        for record in self:
            record.state = 'cancel'

    def action_reset_to_draft(self):
        """Resets a cancelled appointment back to Draft."""
        for record in self:
            record.state = 'draft'
