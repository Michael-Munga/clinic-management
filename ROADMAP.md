# Clinic Management — System Architecture & Roadmap

> **Odoo Version:** 19.0 Community / Enterprise  
> **Module Name:** `clinic_management`  
> **Status:** Active Development (Phase 7 next — Final Phase!)

---

## 1. Executive Overview

A complete clinic operations management system built natively in Odoo 19. It replaces paper records and spreadsheets with a single integrated system where receptionists book appointments, doctors record consultations and prescribe medication, and patients view their history via a self-service portal.

---

## 2. The Four User Roles & Scopes

| Role | Who they are | Scope & Permissions in the System |
| :--- | :--- | :--- |
| **Receptionist** | Front desk staff | Registers patients, books/manages all appointments across doctors, checks doctor availability (read-only doctors list). Cannot see medical diagnoses or write prescriptions. |
| **Doctor** | Medical staff | Sees **only their own assigned appointments** and patients. Records consultations, diagnoses, and writes prescriptions. Cannot manage clinic configuration or delete patient records. |
| **Manager** | Clinic owner / Admin | Full CRUD control across all models (Doctors, Patients, Appointments, Consultations, Prescriptions, Specialties, Clinic Configuration). |
| **Patient** | Patient / Client | Logs into the customer web portal (`/my/appointments`, `/my/prescriptions`) to view their own upcoming bookings, past history, and prescriptions. Strictly row-locked to their own record. |

----

## 3. Data Models Architecture

```
                    ┌─────────────────────────┐
                    │    clinic.specialty     │
                    └────────────▲────────────┘
                                 │ specialty_id
┌─────────────────────────┐ ┌────┴────────────────────┐
│      res.partner        │ │      hr.employee        │
└────────────▲────────────┘ └──────────▲──────────────┘
             │ _inherits               │ _inherits
┌────────────┴────────────┐ ┌──────────┴──────────────┐
│     clinic.patient      │ │      clinic.doctor      │
│ (PAT-0001, age, blood)  │ │(license, fee, user_id)  │
└────────────▲────────────┘ └──────────▲──────────────┘
             │ patient_id              │ doctor_id
             └───────────┬─────────────┘
                         │
              ┌──────────▼──────────┐
              │ clinic.appointment  │ (Draft -> Confirmed -> In Progress -> Done)
              └──────────▲──────────┘ (Calendar, Conflict Prevention)
                         │ appointment_id
              ┌──────────▼──────────┐
              │ clinic.consultation │ (Diagnosis, symptoms, clinical notes)
              └──────────▲──────────┘
                         │ consultation_id
              ┌──────────▼──────────┐
              │ clinic.prescription │ (Date, doctor, patient)
              └──────────▲──────────┘
                         │ One2many
            ┌────────────▼──────────────┐
            │ clinic.prescription.line  │ (Medication, dosage, freq, duration)
            └───────────────────────────┘
```

---

## 4. Phase-by-Phase Roadmap

### ✅ Phase 1: Foundations & Architecture (COMPLETED)
- [x] Module manifest (`__manifest__.py`) with strict sequential dependency and data load order.
- [x] `clinic.specialty`: Database model, unique code constraint (`models.Constraint`), and archive support (`active = fields.Boolean`).
- [x] `clinic.patient`: Delegation inheritance (`_inherits = {'res.partner': 'partner_id'}`), unique `patient_code`, computed `age` with `@api.depends('birthdate')`.
- [x] `clinic.doctor`: Delegation inheritance (`_inherits = {'hr.employee': 'employee_id'}`), Many2one to specialty, monetary consultation fee with currency.
- [x] Odoo 19 Security scaffolding: `ir.module.category` ➔ `res.groups.privilege` ➔ `res.groups` (Receptionist, Doctor, Manager).
- [x] Basic Views, Window Actions, and Menus.

---

### ✅ Phase 2: Appointments Engine & Security Scoping (COMPLETED)
- [x] `clinic.appointment`: Relational booking model connecting `clinic.patient` and `clinic.doctor`.
- [x] Related field shortcut: `specialty_id = fields.Many2one(..., related='doctor_id.specialty_id')`.
- [x] Status Pipeline: `Draft ➔ Confirmed ➔ In Progress ➔ Done / Cancelled`.
- [x] Interactive `<header>` buttons executing Python actions (`action_confirm`, `action_start_consultation`, `action_done`, `action_cancel`).
- [x] Conflict Detector: Python constraint (`@api.constrains`) with `self.search()` preventing double-booking the same doctor during overlapping time windows.
- [x] Odoo 19 UI Views:
  - `<list>` with dynamic bootstrap color decorations based on state.
  - `<form>` with responsive 2-column `<group>` grid and statusbar widget.
  - `<calendar>` view colored by doctor with weekly schedule blocks.
  - `<search>` view with quick filters and Odoo 19 group-by syntax (`<group name="group_by">`).
- [x] Two-Tier Security Scoping:
  - `ir.model.access.csv` table permissions.
  - `ir.rule` row-level security: Doctor sees only appointments where `doctor_id.user_id == user.id`.
  - Clean group hierarchy using `[(6, 0, [IDs])]` to isolate Doctor from Receptionist.
  - Menu scoping: Configuration and Doctors menus hidden from doctors.
  - Automated user creation on Doctor creation (`@api.model_create_multi`).

---

### ✅ Phase 3: Clinical Records — Consultations & Prescriptions (COMPLETED)
- [x] **1. Consultations (`clinic.consultation`):**
  - Links to `appointment_id`, `patient_id`, `doctor_id`.
  - Date, diagnosis, symptoms, examination notes.
  - State: `draft ➔ done`.
- [x] **2. Prescriptions (`clinic.prescription` & `clinic.prescription.line`):**
  - Parent model: `clinic.prescription` (Patient, Doctor, Date, Consultation link).
  - Child model: `clinic.prescription.line` (Medication Name, Dosage, Frequency, Duration).
  - Linked via `One2many` ➔ embedded editable spreadsheet table in the form view.
- [x] **3. Workflow Connection:**
  - Clicking "Start Consultation" on `clinic.appointment` automatically opens or creates the linked Consultation record.
- [x] **4. Security & Scoping:**
  - Table permissions in `ir.model.access.csv` and row-level `ir.rule` scoping to ensure doctors only access their own consultations and prescriptions.

---

### ✅ Phase 4: Smart Buttons & Audit Chatter (COMPLETED)
- [x] Inherited `mail.thread` and `mail.activity.mixin` on Appointment, Consultation, and Prescription.
- [x] Configured field tracking (`tracking=True`) for automatic status & doctor change auditing.
- [x] Modern `<chatter/>` widget integrated on Appointment, Consultation, and Prescription form views (Log Notes, Send Message, Schedule Activity).
- [x] Stat / Smart Buttons at top of form sheets:
  - Patient form: Appointments Count (`action_view_appointments`), Prescriptions Count (`action_view_prescriptions`).
  - Doctor form: Appointments Count (`action_view_appointments`), Consultations Count (`action_view_consultations`).
  - Appointment form: Consultation Stat Button (`action_view_consultation`).

---

### ✅ Phase 5: Wizards & Workflow Helpers (COMPLETED)
- [x] Dedicated `wizard/` package with `models.TransientModel` implementations.
- [x] "Cancel Appointment" Wizard (`appointment.cancel.wizard`):
  - Pop-up modal dialog (`target="new"`).
  - Mandatory cancellation reason input.
  - Automatically moves state to `cancel`, logs reason in Chatter, and closes dialog.
- [x] "Schedule Follow-up" Wizard (`appointment.followup.wizard`):
  - Launched directly from completed consultations.
  - Pre-fills patient, doctor, and recommended 2-week date.
  - Generates new draft appointment and posts audit confirmation into consultation chatter.

---

### ✅ Phase 6: PDF Reports (COMPLETED)
- [x] Dedicated `report/` package for QWeb templating engine.
- [x] **Printable Prescription PDF** (`clinic_management.report_prescription_document`):
  - Official clinic letterhead wrapper (`web.external_layout`).
  - Patient Information Card (Name, Code, Age, Blood Type, Allergies).
  - Prescribing Doctor Card (Name, Specialty, License Number, Contact).
  - Formatted Rx Medications Table with dosage, frequency, duration, instructions.
  - Doctor's General Advice & Instructions box.
  - Doctor's Signature & Medical Stamp line.
  - 1-Click "Print Prescription" action button in form header + top Print menu.
- [x] **Daily Doctor Schedule PDF** (`clinic_management.report_doctor_schedule_document`):
  - Formatted timetable of appointments filtered by active status.
  - Patient contact, vitals, time slots, and clinical notes.
  - Bound directly to `clinic.doctor` Print menu.

---

### ✅ Phase 7: Patient Portal & REST API (COMPLETED)
- [x] **Patient Web Portal**:
  - Live counter badges on `/my` dashboard via `_prepare_home_portal_values`.
  - Accessible at `/my/appointments` (list view with status pills, pagination, and sorting).
  - Appointment details view at `/my/appointments/<id>` (doctor info, time schedule, notes).
  - Prescriptions list view at `/my/prescriptions` with medications count and status.
  - Prescription details view at `/my/prescriptions/<id>` with full Rx table and doctor's advice.
  - 1-Click PDF Prescription download at `/my/prescriptions/<id>/pdf` using Phase 6 QWeb report engine.
- [x] **Strict Patient Record Scoping**:
  - Row-level `ir.rule` security (`[('patient_id.partner_id', '=', user.partner_id.id)]`).
  - Read access granted to `base.group_portal` for appointments, prescriptions, and `hr.employee.public`.
  - Full data isolation: Patients can NEVER peek into another patient's medical records (verified with redirect).
- [x] **REST API (`/api/v1`)**:
  - `GET /api/v1/appointments`: JSON list with optional filtering by doctor, patient, date, or status.
  - `GET /api/v1/appointments/<id>`: Detailed JSON view of single appointment.
  - `POST /api/v1/appointments`: Validates JSON payload, creates appointment, and enforces overlap constraints with structured JSON errors (HTTP 400 vs 201).
  - `GET /api/v1/doctors`: Doctor directory for reception kiosks.

---

## 5. Odoo 19 Development Rules & Standards

1. **XML Views:** Always use `<list>` instead of the deprecated `<tree>`.
2. **Search Views:** Group-by sections must use `<group name="group_by">` without obsolete `expand="0"` or `string="..."` attributes.
3. **Database Constraints:** Use Python `models.Constraint('unique (col)', 'Message')` instead of the legacy `_sql_constraints` tuple list.
4. **Security Privileges:** Odoo 19 uses `res.groups.privilege` as the bridge between `ir.module.category` and `res.groups`.
5. **ORM Commands:** Use `(6, 0, [ids])` to cleanly set or replace Many2many relations without retaining legacy links.
6. **Multi-Record Creation:** Always use `@api.model_create_multi` for `create(self, vals_list)`.
7. **Recordsets & `self`:** In computed fields and business methods, always iterate with `for record in self:`.
