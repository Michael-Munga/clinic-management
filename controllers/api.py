# -*- coding: utf-8 -*-
# =============================================================================
# CLINIC MANAGEMENT - REST API CONTROLLER
# =============================================================================
# In modern enterprise architectures, external systems need programmatic access
# to Odoo:
# - Self-service check-in kiosks at the clinic lobby
# - Mobile apps for patients or doctors
# - Third-party lab integrations or website booking widgets
#
# ARCHITECTURAL CONCEPTS DEMONSTRATED:
# 1. Native HTTP JSON endpoints using 'request.make_json_response'.
# 2. CSRF Exemption ('csrf=False') for stateless programmatic REST requests.
# 3. Request parsing via 'request.get_json_data()'.
# 4. Input validation and structured HTTP status codes (200, 201, 400, 404).
# 5. Integration with Odoo Constraints (catching 'ValidationError' from business models).
# =============================================================================

from datetime import datetime
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import ValidationError, UserError, AccessError


class ClinicApiController(http.Controller):
    """
    REST API controller exposing clinic operations via clean JSON endpoints.
    Base path: /api/v1/...
    """

    # Helper serializer method
    def _serialize_appointment(self, appointment):
        """Transforms a clinic.appointment record into a clean JSON dictionary."""
        return {
            'id': appointment.id,
            'name': appointment.name,
            'patient': {
                'id': appointment.patient_id.id,
                'name': appointment.patient_id.name,
                'patient_code': appointment.patient_id.patient_code,
                'phone': appointment.patient_id.phone or '',
            },
            'doctor': {
                'id': appointment.doctor_id.id,
                'name': appointment.doctor_id.name,
                'specialty': appointment.specialty_id.name if appointment.specialty_id else '',
            },
            'appointment_datetime': fields.Datetime.to_string(appointment.appointment_datetime),
            'duration_minutes': appointment.duration,
            'appointment_end_datetime': fields.Datetime.to_string(appointment.appointment_end_datetime) if appointment.appointment_end_datetime else '',
            'state': appointment.state,
            'notes': appointment.notes or '',
        }

    # =========================================================================
    # 1. GET /api/v1/appointments - List & Filter Appointments
    # =========================================================================
    @http.route(
        '/api/v1/appointments',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False,
    )
    def api_get_appointments(self, **kwargs):
        """
        Retrieves a list of appointments.

        QUERY PARAMETERS (all optional):
        - doctor_id: filter by doctor ID (e.g. ?doctor_id=1)
        - patient_id: filter by patient ID (e.g. ?patient_id=2)
        - state: filter by status (e.g. ?state=confirmed)
        - date: filter by date (e.g. ?date=2026-09-30)

        RETURNS: JSON array of serialized appointments.
        """
        Appointment = request.env['clinic.appointment'].sudo()
        domain = []

        if kwargs.get('doctor_id'):
            domain.append(('doctor_id', '=', int(kwargs['doctor_id'])))

        if kwargs.get('patient_id'):
            domain.append(('patient_id', '=', int(kwargs['patient_id'])))

        if kwargs.get('state'):
            domain.append(('state', '=', kwargs['state']))

        if kwargs.get('date'):
            # Filter appointments on a specific calendar day
            start_date = f"{kwargs['date']} 00:00:00"
            end_date = f"{kwargs['date']} 23:59:59"
            domain.extend([
                ('appointment_datetime', '>=', start_date),
                ('appointment_datetime', '<=', end_date),
            ])

        appointments = Appointment.search(domain, order='appointment_datetime asc', limit=100)
        data = [self._serialize_appointment(appt) for appt in appointments]

        return request.make_json_response({
            'status': 'success',
            'count': len(data),
            'appointments': data,
        }, status=200)

    # =========================================================================
    # 2. GET /api/v1/appointments/<id> - Single Appointment Detail
    # =========================================================================
    @http.route(
        '/api/v1/appointments/<int:appointment_id>',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False,
    )
    def api_get_appointment_detail(self, appointment_id, **kwargs):
        """Retrieves details of a single appointment by ID."""
        appointment = request.env['clinic.appointment'].sudo().browse(appointment_id)
        if not appointment.exists():
            return request.make_json_response({
                'status': 'error',
                'message': f"Appointment with ID {appointment_id} not found",
            }, status=404)

        return request.make_json_response({
            'status': 'success',
            'appointment': self._serialize_appointment(appointment),
        }, status=200)

    # =========================================================================
    # 3. POST /api/v1/appointments - Book a New Appointment
    # =========================================================================
    @http.route(
        '/api/v1/appointments',
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False,
    )
    def api_create_appointment(self, **kwargs):
        """
        Creates a new appointment from a JSON request body.

        EXPECTED JSON BODY:
        {
            "patient_id": 1,
            "doctor_id": 2,
            "appointment_datetime": "2026-09-30 14:00:00",
            "duration": 30,           (optional, defaults to 30)
            "notes": "Follow-up visit" (optional)
        }

        ERROR HANDLING:
        - 400 Bad Request: Missing fields, invalid date format, or overlapping booking conflict.
        - 201 Created: Successfully booked appointment.
        """
        try:
            body = request.get_json_data()
        except Exception:
            return request.make_json_response({
                'status': 'error',
                'message': "Invalid JSON payload in request body",
            }, status=400)

        if not body:
            return request.make_json_response({
                'status': 'error',
                'message': "Request body is empty",
            }, status=400)

        # Validate mandatory fields
        required_fields = ['patient_id', 'doctor_id', 'appointment_datetime']
        missing = [f for f in required_fields if f not in body]
        if missing:
            return request.make_json_response({
                'status': 'error',
                'message': f"Missing required fields: {', '.join(missing)}",
            }, status=400)

        # Validate Patient & Doctor existence
        Patient = request.env['clinic.patient'].sudo()
        Doctor = request.env['clinic.doctor'].sudo()

        patient = Patient.browse(body['patient_id'])
        if not patient.exists():
            return request.make_json_response({
                'status': 'error',
                'message': f"Patient ID {body['patient_id']} does not exist",
            }, status=400)

        doctor = Doctor.browse(body['doctor_id'])
        if not doctor.exists():
            return request.make_json_response({
                'status': 'error',
                'message': f"Doctor ID {body['doctor_id']} does not exist",
            }, status=400)

        # Prepare values for creation
        vals = {
            'patient_id': patient.id,
            'doctor_id': doctor.id,
            'appointment_datetime': body['appointment_datetime'],
            'duration': body.get('duration', 30),
            'notes': body.get('notes', ''),
            'state': 'draft',
        }

        # Attempt creation:
        # Note: If the doctor has an overlapping schedule, Odoo's @api.constrains
        # method in 'clinic.appointment' will raise a ValidationError!
        try:
            appointment = request.env['clinic.appointment'].sudo().create(vals)
        except ValidationError as e:
            # Overlapping schedule or other business constraint violation
            return request.make_json_response({
                'status': 'error',
                'error_type': 'ConstraintViolation',
                'message': str(e),
            }, status=400)
        except Exception as e:
            return request.make_json_response({
                'status': 'error',
                'error_type': type(e).__name__,
                'message': str(e),
            }, status=400)

        return request.make_json_response({
            'status': 'success',
            'message': 'Appointment booked successfully',
            'appointment': self._serialize_appointment(appointment),
        }, status=201)

    # =========================================================================
    # 4. GET /api/v1/doctors - Directory of Doctors for Booking Kiosks
    # =========================================================================
    @http.route(
        '/api/v1/doctors',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False,
    )
    def api_get_doctors(self, **kwargs):
        """Returns the list of active doctors with their specialties."""
        doctors = request.env['clinic.doctor'].sudo().search([])
        data = [{
            'id': doc.id,
            'name': doc.name,
            'specialty': doc.specialty_id.name if doc.specialty_id else '',
            'license_number': doc.license_number or '',
            'work_email': doc.work_email or '',
            'work_phone': doc.work_phone or '',
        } for doc in doctors]

        return request.make_json_response({
            'status': 'success',
            'count': len(data),
            'doctors': data,
        }, status=200)
