import ovh
import common.infradmin_logs
import dns.resolver

class Ovh:
    def __init__(self):
        self.o_client = None
        self.l_domains = []
        self.o_logger = common.infradmin_logs.O_LOGGER

    def connect(self, s_app_key: str, s_app_secret: str, s_consumer_key: str):
        # Configuration de l'API OVH
        self.o_client = ovh.Client(
            endpoint='ovh-eu',  # Utilisez 'ovh-eu' si vous utilisez les services OVH en Europe
            application_key=s_app_key,
            application_secret=s_app_secret,
            consumer_key=s_consumer_key
        )
        self.o_logger.info('Connected to OVH')

    def get_domains(self):
        self.l_domains = self.o_client.get('/domain')

    def create_cname(self, s_domain_name: str, s_cname_name: str, s_target_name: str):

        # Définition des paramètres pour l'enregistrement CNAME
        d_enregistrement_cname = {
            "subDomain": s_cname_name,
            "zone": s_domain_name,
            "target": s_target_name,
            "ttl": 3600,  # Temps de vie (TTL) de l'enregistrement en secondes
        }
        self.o_logger.info(f'Creating CNAME {s_cname_name} for the domain {s_domain_name} with target {s_target_name}')

        # Création de l'enregistrement CNAME
        self.o_client.post('/domain/zone/{}/record'.format(s_domain_name), **d_enregistrement_cname)
        self.o_logger.info(f'CNAME {s_cname_name} successfully added')

    def delete_cname(self, s_domain_name: str, s_cname_name: str):
        # Récupérer les informations de l'enregistrement CNAME à supprimer
        d_record_id = self.o_client.get('/domain/zone/{}/record'.format(s_domain_name), fieldType='CNAME',
                subDomain=s_cname_name)[0]['id']

        # Supprimer l'enregistrement CNAME
        self.o_client.delete('/domain/zone/{}/record/{}'.format(s_domain_name, d_record_id))
        self.o_logger.info(f'CNAME {s_cname_name} successfully deleted')

    def check_cname(self, s_domain: str, s_cname: str):
        try:
            # Résolvez les enregistrements DNS pour le domaine spécifié
            l_answers = dns.resolver.resolve(s_domain, 'CNAME')

            # Vérifiez si le CNAME recherché est présent parmi les enregistrements résolus
            for rdata in l_answers:
                if rdata.target.to_unicode() == s_cname:
                    return True
            return False
        except dns.resolver.NXDOMAIN:
            self.o_logger.error("Le domaine spécifié n'existe pas.")
        except dns.resolver.NoAnswer:
            self.o_logger.info("Aucun enregistrement CNAME trouvé.")
        except dns.resolver.NoNameservers:
            self.o_logger.error("Aucun serveur de noms trouvé.")
        except Exception as e:
            self.o_logger.error("Une erreur s'est produite :", e)
            return False

