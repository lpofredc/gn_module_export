"""
    Définition des routes du module export
"""

import os
import logging
import threading

from pathlib import Path
from datetime import datetime

from sqlalchemy.orm.exc import NoResultFound
from flask import (
    Blueprint,
    request,
    current_app,
    send_from_directory,
    Response,
    render_template,
    jsonify,
    flash,
    copy_current_request_context
)
from flask_cors import cross_origin
from flask_admin.contrib.sqla import ModelView
from flask_admin.helpers import is_form_submitted
from flask_admin import Admin

from pypnusershub.db.models import User

from geonature.utils.utilssqlalchemy import (
    json_resp, to_json_resp,
    GenericQuery
)
from geonature.core.gn_permissions import decorators as permissions
from geonature.utils.env import DB


from .repositories import (
    ExportRepository, EmptyDataSetError, generate_swagger_spec,
)
from .models import Export, CorExportsRoles, Licences
from .utils_export import thread_export_data


LOGGER = current_app.logger
LOGGER.setLevel(logging.DEBUG)

blueprint = Blueprint('exports', __name__)
blueprint.template_folder = os.path.join(blueprint.root_path, 'templates')
blueprint.static_folder = os.path.join(blueprint.root_path, 'static')
repo = ExportRepository()


"""
#################################################################
    Configuration de l'admin
#################################################################
"""


class ExportView(ModelView):
    """
        Création d'une class pour gérer le formulaire d'administration Export
    """
    def __init__(self, session):
        # Référence au model utilisé
        super(ExportView, self).__init__(Export, session)

    def validate_form(self, form):
        """
            validation personnalisée du form
        """
        # Essai de récupérer en BD la vue sql déclarée
        # Delete n'a pas d'attribut view_name
        view_name = getattr(form, 'view_name', '')
        schema_name = getattr(form, 'schema_name', '')
        geometry_field = getattr(form, 'geometry_field', None)
        geometry_srid = getattr(form, 'geometry_srid', None)
        if (is_form_submitted() and view_name and schema_name):
            try:
                query = GenericQuery(
                    DB.session, view_name.data, schema_name.data,
                    geometry_field=geometry_field.data, filters=[]
                )
                query.return_query()

                if geometry_field.data and geometry_srid.data is None:
                    raise KeyError(
                        "field Geometry srid is mandatory with Geometry field"
                    )

            except Exception as exp:
                flash(exp, category='error')
                return False

        return super(ExportView, self).validate_form(form)

# create flask admin for export
admin = Admin(
  current_app,
  name="Backoffice d'administration du module export",
  template_mode='bootstrap3',
  url='/exports/admin',
  endpoint='export_module'
)

# Add views to flask admin
admin.add_view(ExportView(DB.session))
admin.add_view(ModelView(CorExportsRoles, DB.session))
admin.add_view(ModelView(Licences, DB.session))


EXPORTS_DIR = os.path.join(current_app.static_folder, 'exports')
os.makedirs(EXPORTS_DIR, exist_ok=True)
SHAPEFILES_DIR = os.path.join(current_app.static_folder, 'shapefiles')
MOD_CONF_PATH = os.path.join(blueprint.root_path, os.pardir, 'config')

# HACK when install the module, the config of the module is not yet available
# we cannot use current_app.config['EXPORT']
try:
    MOD_CONF = current_app.config['EXPORTS']
    API_URL = MOD_CONF['MODULE_URL']
except KeyError:
    API_URL = ''

ASSETS = os.path.join(blueprint.root_path, 'assets')

"""
#################################################################
    Configuration de swagger
#################################################################
"""


@blueprint.route('/swagger/')
@blueprint.route('/swagger/<int:id_export>', methods=['GET'])
def swagger_ui(id_export=None):
    """
        Génération de l'interface de swagger
    """
    if not id_export:
        id_export = ""

    return render_template(
        'index.html',
        API_ENDPOINT=API_URL,
        id_export=id_export
    )


@blueprint.route('/swagger-ressources/', methods=['GET'])
@blueprint.route('/swagger-ressources/<int:id_export>', methods=['GET'])
def swagger_ressources(id_export=None):
    """
        Génération des spécifications swagger
    """

    # return jsonify(swagger_example)
    if not id_export:
        swagger_spec = render_template('/swagger/main_swagger_doc.json')
        return Response(swagger_spec)

    # Si l'id export exist et que les droits sont définis
    try:
        export = Export.query.filter(Export.id == id_export).one()
    except (NoResultFound, EmptyDataSetError):
        return jsonify({"message": "no export with this id"}), 404

    # Si un fichier de surcouche est défini
    file_name = 'api_specification_' + str(id_export) + '.json'
    path = Path(blueprint.template_folder, 'swagger', file_name)

    if path.is_file():
        swagger_spec = render_template('/swagger/' + file_name)
        return Response(swagger_spec)

    # Génération automatique des spécification
    export_parameters = generate_swagger_spec(id_export)

    swagger_spec = render_template(
        '/swagger/generic_swagger_doc.json',
        export_nom=export.label,
        export_description=export.desc,
        export_path="{}/api/{}".format(API_URL, id_export),
        export_parameters=export_parameters,
        licence_nom=export.licence.name_licence,
        licence_description=export.licence.url_licence
    )

    return Response(swagger_spec)


"""
#################################################################
    Configuration des routes qui permettent de réaliser les exports
#################################################################
"""


@blueprint.route('/<int:id_export>/<export_format>', methods=['GET'])
@cross_origin(
    supports_credentials=True,
    allow_headers=['content-type', 'content-disposition'],
    expose_headers=['Content-Type', 'Content-Disposition', 'Authorization'])
@permissions.check_cruved_scope(
    'E', True, module_code='EXPORTS',
    redirect_on_expiration=current_app.config.get('URL_APPLICATION'),
    redirect_on_invalid_token=current_app.config.get('URL_APPLICATION')
    )
def getOneExportThread(id_export, export_format, info_role):
    """
        Run export with thread
    """
    if (
        id_export < 1
        or
        export_format not in blueprint.config.get('export_format_map')
    ):
        return to_json_resp({'api_error': 'InvalidExport'}, status=404)

    current_app.config.update(
        export_format_map=blueprint.config['export_format_map']
    )

    filters = {f: request.args.get(f) for f in request.args}

    try:
        @copy_current_request_context
        def get_data(id_export, export_format, info_role, filters, user):
            thread_export_data(
                id_export, export_format, info_role, filters, user
            )

        # Test if export is allowed
        try:
            repo.get_export_is_allowed(id_export, info_role)
        except Exception:
            return to_json_resp(
                {'message': "Not Allowed"},
                status=403
            )

        # Test if user have an email
        try:
            user = (
                DB.session.query(User)
                .filter(User.id_role == info_role.id_role)
                .one()
            )
            if not user.email:
                return to_json_resp(
                    {'message': "Error : user doesn't have email"},
                    status=500
                )
        except NoResultFound:
            return to_json_resp(
                {'message': "Error : user doesn't exist"},
                status=500
            )

        # Run export
        a = threading.Thread(
            name="export_data",
            target=get_data,
            kwargs={
                "id_export": id_export,
                "export_format": export_format,
                "info_role": info_role,
                "filters": filters,
                "user": user
            }
        )
        a.start()

        return to_json_resp(
            {'message': 'En cours de traitement vous allez recevoir un couriel'},  # noqua
            status=200
        )

    except Exception as e:
        LOGGER.critical('%s', e)
        if current_app.config['DEBUG']:
            raise
        return to_json_resp({'api_error': 'LoggedError'}, status=400)


@blueprint.route('/', methods=['GET'])
@permissions.check_cruved_scope(
    'R', True, module_code='EXPORTS',
    redirect_on_expiration=current_app.config.get('URL_APPLICATION'),
    redirect_on_invalid_token=current_app.config.get('URL_APPLICATION')
    )
@json_resp
def getExports(info_role):
    """
        Fonction qui renvoie la liste des exports
        accessible pour un role donné
    """
    try:
        exports = repo.get_allowed_exports(info_role)
    except NoResultFound:
        return {'api_error': 'NoResultFound',
                'message': 'Configure one or more export'}, 404
    except Exception as e:
        LOGGER.critical('%s', str(e))
        return {'api_error': 'LoggedError'}, 400
    else:
        return [export.as_dict(recursif=True) for export in exports]


@blueprint.route('/api/<int:id_export>', methods=['GET'])
@permissions.check_cruved_scope(
    'R', True, module_code='EXPORTS',
    redirect_on_expiration=current_app.config.get('URL_APPLICATION'),
    redirect_on_invalid_token=current_app.config.get('URL_APPLICATION')
)
@json_resp
def get_one_export_api(id_export, info_role):
    """
        Fonction qui expose les exports disponibles à un role
            sous forme d'api

        Le requetage des données se base sur la classe GenericQuery qui permet
            de filter les données de façon dynamique en respectant des
            conventions de nommage

        Parameters
        ----------
        limit : nombre limit de résultats à retourner
        offset : numéro de page

        FILTRES :
            nom_col=val: Si nom_col fait partie des colonnes
                de la vue alors filtre nom_col=val
            ilikenom_col=val: Si nom_col fait partie des colonnes
                de la vue et que la colonne est de type texte
                alors filtre nom_col ilike '%val%'
            filter_d_up_nom_col=val: Si nom_col fait partie des colonnes
                de la vue et que la colonne est de type date
                alors filtre nom_col >= val
            filter_d_lo_nom_col=val: Si nom_col fait partie des colonnes
                de la vue et que la colonne est de type date
                alors filtre nom_col <= val
            filter_d_eq_nom_col=val: Si nom_col fait partie des colonnes
                de la vue et que la colonne est de type date
                alors filtre nom_col == val
            filter_n_up_nom_col=val: Si nom_col fait partie des colonnes
                de la vue et que la colonne est de type numérique
                alors filtre nom_col >= val
            filter_n_lo_nom_col=val: Si nom_col fait partie des colonnes
                de la vue et que la colonne est de type numérique
                alors filtre nom_col <= val
        ORDONNANCEMENT :
            orderby: char
                Nom du champ sur lequel baser l'ordonnancement
            order: char (asc|desc)
                Sens de l'ordonnancement

        Returns
        -------
        json
        {
            'total': Nombre total de résultat,
            'total_filtered': Nombre total de résultat après filtration,
            'page': Numéro de la page retournée,
            'limit': Nombre de résultats,
            'items': données au format Json ou GeoJson
        }


            order by : @TODO
    """
    # Test if export is allowed
    try:
        repo.get_export_is_allowed(id_export, info_role)
    except Exception:
        return (
            {'message': "Not Allowed"},
            403
        )

    limit = request.args.get('limit', default=1000, type=int)
    offset = request.args.get('offset', default=0, type=int)

    args = request.args.to_dict()
    if "limit" in args:
        args.pop("limit")
    if "offset" in args:
        args.pop("offset")
    filters = {f: args.get(f) for f in args}

    current_app.config.update(
        export_format_map=blueprint.config['export_format_map']
    )

    export, columns, data = repo.get_by_id(
        info_role, id_export, with_data=True, export_format='json',
        filters=filters, limit=limit, offset=offset
    )

    return data


# TODO : Route desactivée car à évaluer
# @blueprint.route('/etalab', methods=['GET'])
def etalab_export():
    """
        TODO : METHODE NON FONCTIONNELLE A EVALUEE
    """
    if not blueprint.config.get('etalab_export'):
        return to_json_resp(
            {'api_error': 'EtalabDisabled',
             'message': 'Etalab export is disabled'}, status=501)

    from datetime import time
    from geonature.utils.env import DB
    from .rdf import OccurrenceStore

    conf = current_app.config.get('EXPORTS')
    export_etalab = conf.get('etalab_export')
    seeded = False
    if os.path.isfile(export_etalab):
        seeded = True
        midnight = datetime.combine(datetime.today(), time.min)
        mtime = datetime.fromtimestamp(os.path.getmtime(export_etalab))
        ts_delta = mtime - midnight

    if not seeded or ts_delta.total_seconds() < 0:
        store = OccurrenceStore()
        query = GenericQuery(
            DB.session, 'export_occtax_sinp', 'pr_occtax',
            geometry_field=None, filters=[]
        )
        data = query.return_query()
        for record in data.get('items'):
            event = store.build_event(record)
            obs = store.build_human_observation(event, record)
            store.build_location(obs, record)
            occurrence = store.build_occurrence(event, record)
            organism = store.build_organism(occurrence, record)
            identification = store.build_identification(organism, record)
            store.build_taxon(identification, record)
        try:
            with open(export_etalab, 'w+b') as xp:
                store.save(store_uri=xp)
        except FileNotFoundError:
            response = Response(
                response="FileNotFoundError : {}".format(
                    export_etalab
                ),
                status=500,
                mimetype='application/json'
            )
            return response

    return send_from_directory(
        os.path.dirname(export_etalab), os.path.basename(export_etalab)
    )
