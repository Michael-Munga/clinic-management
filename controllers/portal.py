# -*- coding: utf-8 -*-
# =============================================================================
# CLINIC MANAGEMENT - PATIENT PORTAL CONTROLLER
# =============================================================================
# In Odoo, the Customer Portal provides external stakeholders (in our case,
# Clinic Patients) with a secure, self-service web interface where they can:
# 1. View their upcoming and past appointments.
# 2. Review prescribed medications and dosage instructions.
# 3. Download official PDF prescriptions directly from their web browser!
#
# ARCHITECTURAL CONCEPTS DEMONSTRATED:
# 1. Controller Inheritance: Extending Odoo's core 'CustomerPortal'.
# 2. Portal Counters: Adding badges to the main /my dashboard.
# 3. Record Security in Controllers: Verifying access rights & record rules.
# 4. Pagination & Sorting: Using 'portal_pager' and sorting dictionaries.
# 5. Dynamic PDF Generation: Calling the QWeb report engine from Python HTTP.
# =============================================================================

from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class ClinicCustomerPortal(CustomerPortal):
    """
    Extends Odoo's core CustomerPortal to integrate medical clinic records.
    By subclassing CustomerPortal, our custom routes (/my/appointments, /my/prescriptions)
    automatically inherit Odoo's portal layout, breadcrumbs, user session handling,
    and responsive styling.
    """

    # =========================================================================
    # 1. PORTAL HOME VALUES & COUNTERS
    # =========================================================================
    def _prepare_home_portal_values(self, counters):
        """
        Extends the dictionary of counter values displayed on the main /my portal page.

        HOW IT WORKS:
        When a user visits '/my', Odoo calls '_prepare_home_portal_values' with a set
        of requested 'counters'. If our counter keys are present, we query PostgreSQL
        for the total count of records belonging to the logged-in patient.

        :param counters: list or set of string keys requested by the UI (e.g. ['appointment_count'])
        :return: dictionary mapping counter keys to integer counts
        """
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        # Check read access rights before executing queries
        Appointment = request.env['clinic.appointment']
        Prescription = request.env['clinic.prescription']

        if 'appointment_count' in counters:
            values['appointment_count'] = (
                Appointment.search_count([('patient_id.partner_id', '=', partner.id)])
                if Appointment.check_access_rights('read', raise_exception=False)
                else 0
            )

        if 'prescription_count' in counters:
            values['prescription_count'] = (
                Prescription.search_count([('patient_id.partner_id', '=', partner.id)])
                if Prescription.check_access_rights('read', raise_exception=False)
                else 0
            )

        return values

    # =========================================================================
    # 2. APPOINTMENTS LIST ROUTE
    # =========================================================================
    @http.route(
        ['/my/appointments', '/my/appointments/page/<int:page>'],
        type='http',
        auth='user',
        website=True,
    )
    def portal_my_appointments(self, page=1, sortby=None, **kw):
        """
        Renders the patient's appointment history with sorting and pagination.

        ROUTE PARAMETERS:
        - type='http': Returns standard HTML response rendered by QWeb.
        - auth='user': Requires the user to be logged in. Unauthenticated visitors
                       are automatically redirected to the Odoo login page.
        - website=True: Injects website framework context (menus, footer, assets).
        """
        values = self._prepare_portal_layout_values()
        Appointment = request.env['clinic.appointment']
        partner = request.env.user.partner_id

        # Base domain: ONLY appointments linked to the logged-in user's partner record!
        # This matches our ir.rule in clinic_security.xml for defense-in-depth.
        domain = [('patient_id.partner_id', '=', partner.id)]

        # Sorting options available in the portal UI dropdown
        searchbar_sortings = {
            'date': {'label': _('Date (Newest)'), 'order': 'appointment_datetime desc'},
            'date_asc': {'label': _('Date (Oldest)'), 'order': 'appointment_datetime asc'},
            'doctor': {'label': _('Doctor'), 'order': 'doctor_id'},
            'state': {'label': _('Status'), 'order': 'state'},
        }

        # Default sorting if none selected
        if not sortby or sortby not in searchbar_sortings:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # Total count for pagination
        appointment_count = Appointment.search_count(domain)

        # Build pager (10 appointments per page)
        pager = portal_pager(
            url="/my/appointments",
            url_args={'sortby': sortby},
            total=appointment_count,
            page=page,
            step=10,
        )

        # Execute query with limit and offset
        appointments = Appointment.search(
            domain,
            order=order,
            limit=10,
            offset=pager['offset'],
        )

        values.update({
            'appointments': appointments,
            'page_name': 'appointment',
            'pager': pager,
            'default_url': '/my/appointments',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("clinic_management.portal_my_appointments", values)

    # =========================================================================
    # 3. APPOINTMENT DETAIL ROUTE
    # =========================================================================
    @http.route(
        ['/my/appointments/<int:appointment_id>'],
        type='http',
        auth='user',
        website=True,
    )
    def portal_appointment_detail(self, appointment_id, **kw):
        """
        Renders a detailed page for a specific appointment.
        Includes security checks to prevent users from peeking at other patients' records.
        """
        try:
            appointment = request.env['clinic.appointment'].browse(appointment_id)
            # Enforce access rights and row-level ir.rule
            appointment.check_access_rights('read')
            appointment.check_access_rule('read')
        except (AccessError, MissingError):
            # If the appointment doesn't exist or belongs to someone else, redirect back safely
            return request.redirect('/my/appointments')

        values = self._prepare_portal_layout_values()
        values.update({
            'appointment': appointment,
            'page_name': 'appointment_detail',
        })
        return request.render("clinic_management.portal_appointment_page", values)

    # =========================================================================
    # 4. PRESCRIPTIONS LIST ROUTE
    # =========================================================================
    @http.route(
        ['/my/prescriptions', '/my/prescriptions/page/<int:page>'],
        type='http',
        auth='user',
        website=True,
    )
    def portal_my_prescriptions(self, page=1, sortby=None, **kw):
        """
        Renders the patient's medical prescriptions list with pagination.
        """
        values = self._prepare_portal_layout_values()
        Prescription = request.env['clinic.prescription']
        partner = request.env.user.partner_id

        domain = [('patient_id.partner_id', '=', partner.id)]

        searchbar_sortings = {
            'date': {'label': _('Date (Newest)'), 'order': 'date desc, id desc'},
            'date_asc': {'label': _('Date (Oldest)'), 'order': 'date asc, id asc'},
            'doctor': {'label': _('Doctor'), 'order': 'doctor_id'},
        }

        if not sortby or sortby not in searchbar_sortings:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        prescription_count = Prescription.search_count(domain)

        pager = portal_pager(
            url="/my/prescriptions",
            url_args={'sortby': sortby},
            total=prescription_count,
            page=page,
            step=10,
        )

        prescriptions = Prescription.search(
            domain,
            order=order,
            limit=10,
            offset=pager['offset'],
        )

        values.update({
            'prescriptions': prescriptions,
            'page_name': 'prescription',
            'pager': pager,
            'default_url': '/my/prescriptions',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("clinic_management.portal_my_prescriptions", values)

    # =========================================================================
    # 5. PRESCRIPTION DETAIL ROUTE
    # =========================================================================
    @http.route(
        ['/my/prescriptions/<int:prescription_id>'],
        type='http',
        auth='user',
        website=True,
    )
    def portal_prescription_detail(self, prescription_id, **kw):
        """
        Renders the prescription detail page showing all medication lines,
        instructions, and a button to download the PDF.
        """
        try:
            prescription = request.env['clinic.prescription'].browse(prescription_id)
            prescription.check_access_rights('read')
            prescription.check_access_rule('read')
        except (AccessError, MissingError):
            return request.redirect('/my/prescriptions')

        values = self._prepare_portal_layout_values()
        values.update({
            'prescription': prescription,
            'page_name': 'prescription_detail',
        })
        return request.render("clinic_management.portal_prescription_page", values)

    # =========================================================================
    # 6. DOWNLOAD PRESCRIPTION PDF ROUTE
    # =========================================================================
    @http.route(
        ['/my/prescriptions/<int:prescription_id>/pdf'],
        type='http',
        auth='user',
        website=True,
    )
    def portal_prescription_download_pdf(self, prescription_id, **kw):
        """
        Dynamically renders and returns the official Prescription PDF report
        using the QWeb report engine built in Phase 6.

        HOW IT WORKS:
        1. Validates that the record belongs to the calling user.
        2. Calls 'ir.actions.report._render_qweb_pdf' passing our report XML ID.
        3. Returns the binary stream with 'Content-Disposition: attachment'
           so the browser automatically downloads the file.
        """
        try:
            prescription = request.env['clinic.prescription'].browse(prescription_id)
            prescription.check_access_rights('read')
            prescription.check_access_rule('read')
        except (AccessError, MissingError):
            return request.redirect('/my/prescriptions')

        # OFFICIAL ODOO 19 STANDARD PATTERN:
        # Instead of manually querying ir.actions.report and constructing HTTP headers,
        # CustomerPortal provides the built-in helper method 'self._show_report()'!
        # It handles:
        # 1. Company context elevation via .sudo()
        # 2. Rendering QWeb templates via _render_qweb_pdf
        # 3. Reading filename from model._get_report_base_filename()
        # 4. Generating Content-Disposition and Content-Type response headers
        return self._show_report(
            model=prescription,
            report_type='pdf',
            report_ref='clinic_management.action_report_clinic_prescription',
            download=True,
        )

