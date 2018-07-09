from datetime import datetime
from enum import IntEnum

from geonature.utils.env import DB
from geonature.utils.utilssqlalchemy import serializable


class Format(IntEnum):
    CSV = 1
    JSON = 2
    RDF = 4


format_map_ext = {
    Format.CSV: 'csv',
    Format.JSON: 'json',
    Format.RDF: 'rdf'
}

format_map_mime = {
    Format.CSV: 'text/csv',
    Format.JSON: 'application/json',
    Format.RDF: 'application/rdf+xml'
}


class Standard(IntEnum):
    NONE = 0
    SINP = 1
    DWC = 2
    ABCD = 4
    EML = 8


standard_map_label = {
    Standard.NONE: 'RAW',
    Standard.SINP: 'SINP',
    Standard.DWC: 'DarwinCore',
    Standard.ABCD: 'ABCD Schema',
    Standard.EML: 'EML'
}


@serializable
class ExportType(DB.Model):
    __tablename__ = 't_exports'
    __table_args__ = {'schema': 'gn_exports', 'extend_existing': True}
    id = DB.Column(DB.Integer, primary_key=True, nullable=False)
    label = DB.Column(DB.Text, nullable=False)
    selection = DB.Column(DB.Text, nullable=False)


@serializable
class Export(DB.Model):
    __tablename__ = 't_exports_logs'
    __table_args__ = {'schema': 'gn_exports', 'extend_existing': True}
    id = DB.Column(DB.TIMESTAMP(timezone=False),
                   primary_key=True, nullable=False)
    start = DB.Column(DB.DateTime)
    end = DB.Column(DB.DateTime)
    format = DB.Column(DB.Integer, nullable=False)
    status = DB.Column(DB.Numeric, default=-2)
    log = DB.Column(DB.UnicodeText)
    id_export = DB.Column(DB.Integer(),
                          DB.ForeignKey('gn_exports.t_exports.id'))
    type = DB.relationship('ExportType',
                           foreign_keys='Export.id_export',
                           backref=DB.backref('ExportType', lazy='joined'))
    id_role = DB.Column(
        DB.Integer(), DB.ForeignKey('utilisateurs.t_roles.id_role'))

    def __init__(self, label, format, id_role=None):
        self.id = datetime.utcnow()
        self.format = int(format)
        self.type = ExportType.query.filter_by(label=label).first()
        self.selection = str(self.type.selection)
        self.label = str(self.type.label)
        self.date = self.start

    def __repr__(self):
        return "<Export(id='{}', label='{}', selection='{}', format='{}', extension='{}', date='{}')>".format(  # noqa E501
            self.id, self.type.label, str(self.type.selection), self.format, format_map_ext[self.format], self.start)  # noqa E501
