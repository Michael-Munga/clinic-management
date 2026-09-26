# -*- coding: utf-8 -*-
from markupsafe import Markup, escape
from odoo import fields, models


class AppointmentCancelWizard(models.TransientModel):
    """
    =============================================================================
    PHASE 5: APPOINTMENT CANCELLATION WIZARD (TransientModel)
    =============================================================================
    Why models.TransientModel instead of models.Model?
    - models.Model stores permanent data in PostgreSQL tables that live forever.
    - models.TransientModel creates temporary database tables designed specifically
      for interactive pop-up dialogs (wizards).
    - Data stored in TransientModels is automatically purged by an Odoo vacuum cron job.

    How this Wizard works:
    1. A user clicks "Cancel" on an Appointment.
    2. A pop-up dialog opens (target="new") prompting for a mandatory cancellation reason.
    3. The user enters their reason and clicks "Confirm Cancellation".
    4. This model updates the appointment, moves its status to 'cancel',
       and logs the cancellation reason into the Appointment's Chatter timeline!
    5. The pop-up dialog closes automatically via 'ir.actions.act_window_close'.
    =============================================================================
    """
    _name = 'appointment.cancel.wizard'
    _description = 'Cancel Appointment Wizard'

    # The appointment being cancelled.
    # readonly=True ensures the user cannot accidentally switch which appointment is being cancelled.
    appointment_id = fields.Many2one(
        'clinic.appointment',
        string='Appointment',
        required=True,
        readonly=True,
    )

    # The mandatory reason explaining why the appointment is being cancelled.
    cancellation_reason = fields.Text(
        string='Reason for Cancellation',
        required=True,
        help='Explain why this appointment is being cancelled (e.g., patient emergency, doctor unavailable).',
    )

    def action_confirm_cancellation(self):
        """
        Executes the cancellation workflow:
        1. Ensures this wizard is running on a single record (ensure_one).
        2. Copies the cancellation reason to the appointment record.
        3. Moves the appointment state from confirmed/draft to 'cancel'.
        4. Writes an audit message directly into the Appointment's Chatter thread!
        5. Returns act_window_close to close the modal dialog.
        """
        self.ensure_one()

        appointment = self.appointment_id

        # 1. Save reason on the appointment
        appointment.cancellation_reason = self.cancellation_reason

        # 2. Call the appointment's cancel workflow method
        appointment.action_cancel()

        # 3. Post an audit note into the appointment's Chatter timeline.
        # PEDAGOGICAL NOTE (Odoo 19 HTML Rendering & Security):
        # In Odoo 19, passing a raw python string to message_post() causes Odoo to
        # escape HTML tags (< becomes &lt;) as a security measure against XSS attacks.
        # To tell Odoo "This HTML is safe to render as bold text and line breaks",
        # we wrap it with Markup() from 'markupsafe', while using escape() on user input!
        appointment.message_post(
            body=Markup(
                f"<b>Appointment Cancelled</b><br/>"
                f"<b>Reason:</b> {escape(self.cancellation_reason)}"
            ),
            message_type='comment',
            subtype_xmlid='mail.mt_note',
        )

        # 4. Special Odoo Action: Closes the pop-up modal dialog and returns to the underlying form
        return {'type': 'ir.actions.act_window_close'}
