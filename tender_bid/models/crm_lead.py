from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    tender_bid_ids = fields.One2many('tender.bid', 'tender_ref', string='Tender Bids')
    tender_no = fields.Char(string='Tender Number')
    emd_amount = fields.Monetary(string='EMD Amount', currency_field='currency_id')
    bg_amount = fields.Monetary(string='Bank Guarantee Amount', currency_field='currency_id')
    submission_date = fields.Date(string='Tender Submission Date')
    boq_line_ids = fields.One2many('tender.boq.line', 'lead_id', string="BOQ Lines")

    tender_bid_count = fields.Integer(string='Tender Bids', compute='_compute_tender_bid_count')
    boq_line_count = fields.Integer(string='BOQ Lines', compute='_compute_boq_line_count')

    # Survey General Info
    survey_date = fields.Date(string="Survey Date")
    survey_team_ids = fields.Many2many('res.users', string="Survey Team")
    survey_location = fields.Char(string="Survey Location")

    # Site & Technical Observations
    site_accessibility = fields.Selection([
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ], string="Site Accessibility")
    existing_infrastructure = fields.Text(string="Existing Infrastructure")
    utilities_availability = fields.Selection([
        ('available', 'Available'),
        ('limited', 'Limited'),
        ('not_available', 'Not Available'),
    ], string="Utilities Availability")
    utilities_remarks = fields.Char(string="Utilities Details / Remarks")
    topographical_details = fields.Text(string="Topographical Details")
    soil_details = fields.Text(string="Soil / Geotechnical / Environmental Notes")
    weather_notes = fields.Text(string="Weather/Rain/Climate Notes")
    soil_contaminated = fields.Boolean(string="Soil Contaminated")
    weather_risk = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], string="Weather Risk")

    # Measurements & Drawings
    area_sqm = fields.Float(string="Total Surveyed Area (sqm)")
    reference_drawing_ids = fields.Many2many(
        'ir.attachment',
        'crm_lead_survey_attachment_rel',
        'lead_id',
        'attachment_id',
        string="Reference Drawings/Plans"
    )

    # Risks & Recommendations
    access_constraints = fields.Text(string="Access Constraints")
    key_observations = fields.Text(string="Key Observations")
    safety_concerns = fields.Text(string="Safety Concerns")
    risk_assessment = fields.Text(string="Preliminary Risk Assessment")
    risk_score = fields.Float(string="Risk Score", compute='_compute_risk_score', store=True)

    # Other Info
    nearby_facilities = fields.Text(string="Nearby Facilities")
    survey_approval_status = fields.Selection([
        ('draft', 'Draft'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
    ], string="Survey Approval Status", default='draft')

    @api.depends('site_accessibility', 'soil_contaminated', 'weather_risk')
    def _compute_risk_score(self):
        for rec in self:
            score = 0
            if rec.site_accessibility == 'poor':
                score += 30
            if rec.soil_contaminated:
                score += 40
            if rec.weather_risk == 'high':
                score += 20
            rec.risk_score = min(score, 100)

    @api.constrains('survey_date', 'area_sqm')
    def _check_survey_fields(self):
        for rec in self:
            if rec.area_sqm and rec.area_sqm <= 0:
                raise ValidationError("Total Surveyed Area must be positive.")

    @api.onchange('utilities_availability')
    def _onchange_utilities_availability(self):
        for rec in self:
            if rec.utilities_availability == 'not_available':
                rec.utilities_remarks = 'No utilities available on site.'
            else:
                rec.utilities_remarks = ''

    @api.depends('tender_bid_ids')
    def _compute_tender_bid_count(self):
        for rec in self:
            rec.tender_bid_count = self.env['tender.bid'].search_count([('tender_ref', '=', rec.id)])

    @api.depends('boq_line_ids')
    def _compute_boq_line_count(self):
        for rec in self:
            rec.boq_line_count = self.env['tender.boq.line'].search_count([('lead_id', '=', rec.id)])

    def open_tender_bids(self):
        self.ensure_one()
        return {
            'name': 'Tender Bids',
            'type': 'ir.actions.act_window',
            'res_model': 'tender.bid',
            'view_mode': 'kanban,list,form',
            'target': 'current',
            'domain': [('tender_ref', '=', self.id)],
            'context': {'default_tender_ref': self.id},
        }

    def open_boq_lines(self):
        self.ensure_one()
        return {
            'name': 'BOQ Lines',
            'type': 'ir.actions.act_window',
            'res_model': 'tender.boq.line',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('lead_id', '=', self.id)],
            'context': {'default_lead_id': self.id},
        }


class TenderBoqLine(models.Model):
    _name = 'tender.boq.line'
    _description = 'Tender BOQ Line'

    name = fields.Char(string='BOQ Number', required=True, copy=False, readonly=True, default='New')
    lead_id = fields.Many2one('crm.lead', string="Lead", ondelete='cascade', required=True)
    item_code = fields.Char(string="Item Code", required=True)
    description = fields.Char(string="Description")
    quantity = fields.Float(string="Quantity", required=True)
    unit = fields.Char(string="Unit of Measure", required=True)
    rate = fields.Float(string="Rate", required=True)
    amount = fields.Float(string="Amount", required=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('tender.boq.line') or 'New'
        return super(TenderBoqLine, self).create(vals)
