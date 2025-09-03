{
    'name': 'Tender Bid Management',
    'version': '1.0',
    'summary': 'Manage construction tenders linked to CRM leads',
    'category': 'Sales',
    'author': 'Your Company',
    'depends': ['base', 'crm', 'documents', 'project', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/tender_bid_security.xml',
        'views/tender_bid_views.xml',
        'views/crm_lead_extension_views.xml',
        'views/crm_lead_boq_views.xml',
        'views/tender_document_views.xml',
        'data/automations.xml',
        'data/sequence_data.xml',
        'data/cron_data.xml'
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
