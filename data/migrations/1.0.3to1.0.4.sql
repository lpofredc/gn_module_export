------------------------------------------------------------------------
-- Mise à jour du schéma gn_exports entre les versions 1.0.3 et 1.0.4 --
------------------------------------------------------------------------

-- Ajout de la Licence ouverte v2 d'Etalab dans les licences par défaut
INSERT INTO gn_exports.t_licences (name_licence, url_licence) VALUES
    ('Licence Ouverte/Open Licence Version 2.0', 'https://www.etalab.gouv.fr/wp-content/uploads/2017/04/ETALAB-Licence-Ouverte-v2.0.pdf');

-- Amélioration des performances et du contenu de la vue SINP par défaut
-- Ajout du champs "nom_valide", des infos taxonomiques, du CA, des acteurs du JDD dans cette vue
-- Amélioration des noms de champs plus lisibles
-- Complément des commentaires des champs

DROP VIEW gn_exports.v_synthese_sinp;
CREATE OR REPLACE VIEW gn_exports.v_synthese_sinp AS
 WITH jdd_acteurs AS (  
 SELECT
    d.id_dataset,
    string_agg(DISTINCT concat(COALESCE(orga.nom_organisme, ((roles.nom_role::text || ' '::text) || roles.prenom_role::text)::character varying), ' : ', nomencl.label_default), ' | '::text) AS acteurs
   FROM gn_meta.t_datasets d
     JOIN gn_meta.cor_dataset_actor act ON act.id_dataset = d.id_dataset
     JOIN ref_nomenclatures.t_nomenclatures nomencl ON nomencl.id_nomenclature = act.id_nomenclature_actor_role
     LEFT JOIN utilisateurs.bib_organismes orga ON orga.id_organisme = act.id_organism
     LEFT JOIN utilisateurs.t_roles roles ON roles.id_role = act.id_role
  GROUP BY d.id_dataset
)
 SELECT s.id_synthese AS "ID_synthese",
    s.entity_source_pk_value AS "ID_source",
    s.unique_id_sinp AS "ID_perm_SINP",
    s.unique_id_sinp_grp AS "ID_perm_GRP_SINP",
    s.date_min AS "Date_debut",
    s.date_max AS "Date_fin",
    t.cd_nom AS "CD_nom",
    t.cd_ref AS "CD_ref",
    s.meta_v_taxref AS "Version_Taxref",
    s.nom_cite AS "Nom_cite",
    t.nom_valide AS "Nom_valide",
    t.regne AS "Regne",
    t.group1_inpn AS "Group1_INPN",
    t.group2_inpn AS "Group2_INPN",
    t.classe AS "Classe",
    t.ordre AS "Ordre",
    t.famille AS "Famille",
    t.id_rang AS "Rang_taxo",
    s.count_min AS "Nombre_min",
    s.count_max AS "Nombre_max",
    s.altitude_min AS "Altitude_min",
    s.altitude_max AS "Altitude_max",
    s.observers AS "Observateurs",
    s.determiner AS "Determinateur",
    s.validator AS "Validateur",
    s.sample_number_proof AS "Numero_preuve",
    s.digital_proof AS "Preuve_numerique",
    s.non_digital_proof AS "Preuve_non_numerique",
    s.the_geom_4326 AS geom,
    s.comment_context AS "Comment_releve",
    s.comment_description AS "Comment_occurrence",
    s.meta_create_date AS "Date_creation",
    s.meta_update_date AS "Date_modification",
    COALESCE(s.meta_update_date, s.meta_create_date) AS "Derniere_action",
    d.unique_dataset_id AS "JDD_UUID",
    d.dataset_name AS "JDD_nom",
    jdd_acteurs.acteurs AS "JDD_acteurs",
    af.unique_acquisition_framework_id AS "CA_UUID",
    af.acquisition_framework_name AS "CA_nom",
    public.st_astext(s.the_geom_4326) AS "WKT_4326",
    public.ST_x(s.the_geom_point) AS "X_centroid_4326",
    public.ST_y(s.the_geom_point) AS "Y_centroid_4326",
    n1.label_default AS "Nature_objet_geo",
    n2.label_default AS "Methode_regroupement",
    n3.label_default AS "Methode_obs",
    n4.label_default AS "Technique_obs",
    n5.label_default AS "Statut_biologique",
    n6.label_default AS "Etat_biologique",
    n7.label_default AS "Naturalite",
    n8.label_default AS "Preuve_existante",
    n9.label_default AS "Precision_diffusion",
    n10.label_default AS "Stade_vie",
    n11.label_default AS "Sexe",
    n12.label_default AS "Objet_denombrement",
    n13.label_default AS "Type_denombrement",
    n14.label_default AS "Niveau_sensibilite",
    n15.label_default AS "Statut_observation",
    n16.label_default AS "Floutage_DEE",
    n17.label_default AS "Statut_source",
    n18.label_default AS "Type_info_geo",
    n19.label_default AS "Methode_determination"
   FROM gn_synthese.synthese s
     JOIN taxonomie.taxref t ON t.cd_nom = s.cd_nom
     JOIN gn_meta.t_datasets d ON d.id_dataset = s.id_dataset
     JOIN jdd_acteurs ON jdd_acteurs.id_dataset = s.id_dataset
     JOIN gn_meta.t_acquisition_frameworks af ON d.id_acquisition_framework = af.id_acquisition_framework
     JOIN gn_synthese.t_sources sources ON sources.id_source = s.id_source
     LEFT JOIN ref_nomenclatures.t_nomenclatures n1 ON s.id_nomenclature_geo_object_nature = n1.id_nomenclature
     LEFT JOIN ref_nomenclatures.t_nomenclatures n2 ON s.id_nomenclature_grp_typ = n2.id_nomenclature
     LEFT JOIN ref_nomenclatures.t_nomenclatures n3 ON s.id_nomenclature_obs_meth = n3.id_nomenclature
     LEFT JOIN ref_nomenclatures.t_nomenclatures n4 ON s.id_nomenclature_obs_technique = n4.id_nomenclature
     LEFT JOIN ref_nomenclatures.t_nomenclatures n5 ON s.id_nomenclature_bio_status = n5.id_nomenclature
     LEFT JOIN ref_nomenclatures.t_nomenclatures n6 ON s.id_nomenclature_bio_condition = n6.id_nomenclature
     LEFT JOIN ref_nomenclatures.t_nomenclatures n7 ON s.id_nomenclature_naturalness = n7.id_nomenclature
     LEFT JOIN ref_nomenclatures.t_nomenclatures n8 ON s.id_nomenclature_exist_proof = n8.id_nomenclature
     LEFT JOIN ref_nomenclatures.t_nomenclatures n9 ON s.id_nomenclature_diffusion_level = n9.id_nomenclature
     LEFT JOIN ref_nomenclatures.t_nomenclatures n10 ON s.id_nomenclature_life_stage = n10.id_nomenclature
     LEFT JOIN ref_nomenclatures.t_nomenclatures n11 ON s.id_nomenclature_sex = n11.id_nomenclature
     LEFT JOIN ref_nomenclatures.t_nomenclatures n12 ON s.id_nomenclature_obj_count = n12.id_nomenclature
     LEFT JOIN ref_nomenclatures.t_nomenclatures n13 ON s.id_nomenclature_type_count = n13.id_nomenclature
     LEFT JOIN ref_nomenclatures.t_nomenclatures n14 ON s.id_nomenclature_sensitivity = n14.id_nomenclature
     LEFT JOIN ref_nomenclatures.t_nomenclatures n15 ON s.id_nomenclature_observation_status = n15.id_nomenclature
     LEFT JOIN ref_nomenclatures.t_nomenclatures n16 ON s.id_nomenclature_blurring = n16.id_nomenclature
     LEFT JOIN ref_nomenclatures.t_nomenclatures n17 ON s.id_nomenclature_source_status = n17.id_nomenclature
     LEFT JOIN ref_nomenclatures.t_nomenclatures n18 ON s.id_nomenclature_info_geo_type = n18.id_nomenclature
     LEFT JOIN ref_nomenclatures.t_nomenclatures n19 ON s.id_nomenclature_determination_method = n19.id_nomenclature
;

COMMENT ON COLUMN gn_exports.v_synthese_sinp."ID_synthese" IS 'Identifiant de la donnée dans la table synthese';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."ID_source" IS 'Identifiant de la donnée dans la table source';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."ID_perm_SINP" IS 'Identifiant permanent de l''occurrence';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."ID_perm_GRP_SINP" IS 'Identifiant permanent du regroupement attribué par la plateforme régionale ou thématique';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Date_debut" IS 'Date du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus ancienne de la période d''imprécision.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Date_fin" IS 'Date du jour, dans le système local de l''observation dans le système grégorien. En cas d’imprécision, cet attribut représente la date la plus récente de la période d''imprécision.';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."CD_nom" IS 'Identifiant Taxref du nom de l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."CD_ref" IS 'Identifiant Taxref du taxon correspondant à l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Version_Taxref" IS 'Version de Taxref utilisée';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Nom_cite" IS 'Nom de l''objet utilisé dans la donnée source';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Nom_valide" IS 'Nom valide de l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Regne" IS 'Règne de l''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Group1_INPN" IS 'Groupe INPN (1) de l''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Group2_INPN" IS 'Groupe INPN (2) de l''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Classe" IS 'Classe de l''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Ordre" IS 'Ordre de l''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Famille" IS 'Famille de l''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Rang_taxo" IS 'Rang taxonomique de l''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Nombre_min" IS 'Nombre minimal d''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Nombre_max" IS 'Nombre maximal d''objet dénombré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Altitude_min" IS 'Altitude minimale';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Altitude_max" IS 'Altitude maximale';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Observateurs" IS 'Personne(s) ayant procédé à l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Determinateur" IS 'Personne ayant procédé à la détermination';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Validateur" IS 'Personne ayant procédé à la validation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Numero_preuve" IS 'Numéro de l''échantillon de la preuve';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Preuve_numerique" IS 'Adresse web à laquelle on pourra trouver la preuve numérique ou l''archive contenant toutes les preuves numériques (image(s), sonogramme(s), film(s), séquence(s) génétique(s)...)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Preuve_non_numerique" IS 'Indique si une preuve existe ou non. Par preuve on entend un objet physique ou numérique permettant de démontrer l''existence de l''occurrence et/ou d''en vérifier l''exactitude';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."geom" IS 'Géometrie de la localisation de l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Comment_releve" IS 'Description libre du contexte de l''observation, aussi succincte et précise que possible';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Comment_occurrence" IS 'Description libre de l''observation, aussi succincte et précise que possible';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Date_creation" IS 'Date de création de la donnée';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Date_modification" IS 'Date de la dernière modification de la données';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Derniere_action" IS 'Date de la dernière action sur l''objet observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."JDD_UUID" IS 'Identifiant unique du jeu de données';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."JDD_nom" IS 'Nom du jeu de données';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."JDD_acteurs" IS 'Acteurs du jeu de données';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."CA_UUID" IS 'Identifiant unique du cadre d''acquisition';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."CA_nom" IS 'Nom du cadre d''acquisition';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."WKT_4326" IS 'Géométrie complète de la localisation en projection WGS 84 (4326)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."X_centroid_4326" IS 'Latitude du centroïde de la localisation en projection WGS 84 (4326)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Y_centroid_4326" IS 'Longitude du centroïde de la localisation en projection WGS 84 (4326)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Nature_objet_geo" IS 'Classe associée au concept de localisation géographique';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Methode_regroupement" IS 'Description de la méthode ayant présidé au regroupement, de façon aussi succincte que possible : champ libre';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Methode_obs" IS 'Méthode d''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Technique_obs" IS 'Indique de quelle manière on a pu constater la présence d''un sujet d''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Statut_biologique" IS 'Comportement général de l''individu sur le site d''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Etat_biologique" IS 'Code de l''état biologique de l''organisme au moment de l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Naturalite" IS 'Naturalité de l''occurrence, conséquence de l''influence anthropique directe qui la caractérise';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Preuve_existante" IS 'Indique si une preuve existe ou non';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Precision_diffusion" IS 'Niveau maximal de précision de la diffusion souhaitée par le producteur vers le grand public';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Stade_vie" IS 'Stade de développement du sujet de l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Sexe" IS 'Sexe du sujet de l''observation';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Objet_denombrement" IS 'Objet sur lequel porte le dénombrement';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Type_denombrement" IS 'Méthode utilisée pour le dénombrement (INSPIRE)';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Niveau_sensibilite" IS 'Indique si l''observation ou le regroupement est sensible d''après les principes du SINP et à quel degré';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Statut_observation" IS 'Indique si le taxon a été observé directement/indirectement (indices de présence), ou bien non observé';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Floutage_DEE" IS 'Indique si un floutage a été effectué avant (par le producteur) ou lors de la transformation en DEE';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Statut_source" IS 'Indique si la DS de l’observation provient directement du terrain (via un document informatisé ou une base de données), d''une collection, de la littérature, ou n''est pas connu';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Type_info_geo" IS 'Type d''information géographique';
COMMENT ON COLUMN gn_exports.v_synthese_sinp."Methode_determination" IS 'Description de la méthode utilisée pour déterminer le taxon lors de l''observation';
