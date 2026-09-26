# -*- coding: utf-8 -*-
from datetime import timedelta
from markupsafe import Markup, escape
from odoo import api, fields, models


class AppointmentFollowupWizard(models.TransientModel):
    """
    =============================================================================
    PHASE 5: SCHEDULE FOLLOW-UP WIZARD (TransientModel)
    =============================================================================
    Purpose in Clinic Operations:
    When a doctor completes a consultation, they often tell the patient to return
    for a review in 1 or 2 weeks.

    Instead of manually navigating to the Appointments menu and re-entering the
    patient, doctor, and clinical context, this wizard:
    1. Pops up directly from the completed Consultation form (target="new").
    2. Automatically pre-fills the Patient and Doctor from the consultation.
    3. Defaults the follow-up date to 14 days (2 weeks) in the future.
    4. Upon confirmation, creates a new 'clinic.appointment' record in Draft status.
    5. Logs the follow-up booking in the Consultation's Chatter timeline!
    6. Opens the newly created appointment form on the screen for the doctor/staff!
    =============================================================================
    """
    _name = 'appointment.followup.wizard'
    _description = 'Schedule Follow-Up Wizard'

    # The consultation that spawned this follow-up request
    consultation_id = fields.Many2one(
        'clinic.consultation',
        string='Source Consultation',
        required=True,
        readonly=True,
    )

    # Pre-filled patient (readonly to prevent scheduling for the wrong person)
    patient_id = fields.Many2one(
        'clinic.patient',
        string='Patient',
        required=True,
        readonly=True,
    )

    # Pre-filled doctor (can be changed if follow-up is with a specialist)
    doctor_id = fields.Many2one(
        'clinic.doctor',
        string='Doctor',
        required=True,
    )

    # Follow-up date: defaults to 2 weeks (14 days) from now
    followup_datetime = fields.Datetime(
        string='Follow-Up Date & Time',
        required=True,
        default=lambda self: fields.Datetime.now() + timedelta(days=14),
    )

    duration = fields.Integer(
        string='Duration (Minutes)',
        default=30,
        required=True,
    )

    notes = fields.Text(
        string='Follow-Up Reason / Clinical Instructions',
        help='Specific instructions for the follow-up visit (e.g., review blood test results, check wound healing).',
    )

    def action_confirm_followup(self):
        """
        Creates the follow-up appointment:
        1. Validates inputs.
        2. Creates a new 'clinic.appointment' record.
        3. Logs an audit entry in the Consultation's Chatter.
        4. Returns an action to open the newly created appointment.
        """
        self.ensure_one()

        # 1. Prepare values for the new appointment
        appointment_vals = {
            'patient_id': self.patient_id.id,
            'doctor_id': self.doctor_id.id,
            'appointment_datetime': self.followup_datetime,
            'duration': self.duration,
            'notes': (
                f"Follow-up for Consultation {self.consultation_id.name}.\n"
                f"Instructions: {self.notes or 'Routine review'}"
            ),
            'state': 'draft',
        }

        # 2. Create the appointment record in the database
        new_appointment = self.env['clinic.appointment'].create(appointment_vals)

        # 3. Log a record in the source Consultation's Chatter thread
        # Using Markup() ensures <b> and <br/> render as bold text and line breaks in the UI!
        self.consultation_id.message_post(
            body=Markup(
                f"<b>Follow-Up Scheduled</b><br/>"
                f"<b>Date:</b> {self.followup_datetime}<br/>"
                f"<b>Doctor:</b> {escape(self.doctor_id.name)}<br/>"
                f"<b>Appointment Ref:</b> {escape(new_appointment.name)}"
            ),
            message_type='comment',
            subtype_xmlid='mail.mt_note',
        )

        # 4. Open the newly created appointment form view for immediate review
        return {
            'name': 'Follow-Up Appointment',
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.appointment',
            'res_id': new_appointment.id,
            'view_mode': 'form',
            'target': 'current',
        }
