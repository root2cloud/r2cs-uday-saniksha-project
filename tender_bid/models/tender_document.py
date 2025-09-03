from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import base64
import logging

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    tender_no = fields.Char(string='Tender Number', copy=False, index=True)
    tender_document_ids = fields.One2many('tender.document', 'lead_id', string='Tender Documents')


class TenderDocument(models.Model):
    _name = 'tender.document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Tender Document'

    name = fields.Char(string='Document Name', required=True)
    lead_id = fields.Many2one('crm.lead', string='Related Lead', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Related Partner')
    document_type = fields.Selection([
        ('tender_notice', 'Tender Notice'),
        ('nit', 'NIT'),
        ('corrigendum', 'Corrigendum'),
        ('other', 'Other'),
    ], string='Document Type', default='other', required=True)
    attachment = fields.Binary(string='File', required=True)
    attachment_filename = fields.Char(string='File Name')
    upload_date = fields.Datetime(string='Upload Date', default=fields.Datetime.now)
    document_ref = fields.Many2one('documents.document', string='Document Reference')

    # document_folder_path = fields.Char(string='Document Folder Path', compute='_compute_document_folder_path',
    #                                    store=True)

    @api.onchange('lead_id')
    def _onchange_lead_id(self):
        if self.lead_id:
            self.partner_id = self.lead_id.partner_id.id
        else:
            self.partner_id = False

    @api.depends('lead_id')
    def _compute_document_folder_path(self):
        for rec in self:
            rec.document_folder_path = f'Tender/{rec.lead_id.tender_no or "Undefined"}'

    @api.constrains('lead_id')
    def _check_lead_has_tender_no(self):
        for rec in self:
            if not rec.lead_id or not rec.lead_id.tender_no:
                raise ValidationError(_('Related Lead must have Tender Number set.'))

    # def upload_to_documents_folder(self):
    #     Documents = self.env['documents.document']
    #     Folder = self.env['documents.folder']
    #
    #     for rec in self:
    #         try:
    #             base_folder = Folder.search([('name', '=', 'Tender'), ('parent_folder_id', '=', False)], limit=1)
    #             if not base_folder:
    #                 base_folder = Folder.create({'name': 'Tender'})
    #
    #             folder = Folder.search([
    #                 ('name', '=', rec.lead_id.tender_no),
    #                 ('parent_folder_id', '=', base_folder.id),
    #             ], limit=1)
    #             if not folder:
    #                 folder = Folder.create({
    #                     'name': rec.lead_id.tender_no,
    #                     'parent_folder_id': base_folder.id,
    #                 })
    #
    #             if rec.attachment:
    #                 datas = rec.attachment
    #                 if isinstance(datas, bytes):
    #                     datas = base64.b64encode(datas).decode()
    #                 vals = {
    #                     'name': rec.attachment_filename or rec.name,
    #                     'folder_id': folder.id,
    #                     'datas': datas,
    #                     'datas_fname': rec.attachment_filename or rec.name,
    #                 }
    #                 doc = Documents.create(vals)
    #                 rec.document_ref = doc.id
    #         except Exception as e:
    #             _logger.error(f"Failed uploading document for tender {rec.lead_id.tender_no}: {e}")


