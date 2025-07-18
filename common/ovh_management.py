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

    def create_a_record(self, s_domain_name: str, s_subdomain: str, s_ip_address: str, i_ttl: int = 3600):
        """
        Create an A record for a subdomain
        :param s_domain_name: domain name
        :param s_subdomain: subdomain name
        :param s_ip_address: IP address
        :param i_ttl: TTL in seconds
        """
        d_record_params = {
            "subDomain": s_subdomain,
            "target": s_ip_address,
            "ttl": i_ttl,
        }
        self.o_logger.info(f'Creating A record {s_subdomain}.{s_domain_name} -> {s_ip_address}')
        
        try:
            self.o_client.post(f'/domain/zone/{s_domain_name}/record', 
                             fieldType='A', **d_record_params)
            self.o_logger.info(f'A record {s_subdomain}.{s_domain_name} successfully created')
        except Exception as e:
            self.o_logger.error(f'Error creating A record: {e}')
            raise

    def update_a_record(self, s_domain_name: str, s_subdomain: str, s_ip_address: str, i_ttl: int = 3600):
        """
        Update an existing A record
        :param s_domain_name: domain name
        :param s_subdomain: subdomain name
        :param s_ip_address: new IP address
        :param i_ttl: TTL in seconds
        """
        try:
            # Get existing A record
            records = self.o_client.get(f'/domain/zone/{s_domain_name}/record', 
                                      fieldType='A', subDomain=s_subdomain)
            
            if not records:
                self.o_logger.warning(f'No A record found for {s_subdomain}.{s_domain_name}')
                return False
            
            record_id = records[0]['id']
            
            # Update the record
            self.o_client.put(f'/domain/zone/{s_domain_name}/record/{record_id}',
                            target=s_ip_address, ttl=i_ttl)
            
            self.o_logger.info(f'A record {s_subdomain}.{s_domain_name} updated to {s_ip_address}')
            return True
            
        except Exception as e:
            self.o_logger.error(f'Error updating A record: {e}')
            return False

    def delete_a_record(self, s_domain_name: str, s_subdomain: str):
        """
        Delete an A record
        :param s_domain_name: domain name
        :param s_subdomain: subdomain name
        """
        try:
            # Get A record ID
            records = self.o_client.get(f'/domain/zone/{s_domain_name}/record', 
                                      fieldType='A', subDomain=s_subdomain)
            
            for record in records:
                record_id = record['id']
                self.o_client.delete(f'/domain/zone/{s_domain_name}/record/{record_id}')
                self.o_logger.info(f'A record {s_subdomain}.{s_domain_name} successfully deleted')
                
        except Exception as e:
            self.o_logger.error(f'Error deleting A record: {e}')
            raise

    def refresh_zone(self, s_domain_name: str):
        """
        Refresh the DNS zone to apply changes
        :param s_domain_name: domain name
        """
        try:
            self.o_client.post(f'/domain/zone/{s_domain_name}/refresh')
            self.o_logger.info(f'Zone {s_domain_name} refreshed successfully')
        except Exception as e:
            self.o_logger.error(f'Error refreshing zone {s_domain_name}: {e}')
            raise

    def list_records(self, s_domain_name: str, s_record_type: str = None):
        """
        List all records for a domain
        :param s_domain_name: domain name
        :param s_record_type: record type filter (A, CNAME, etc.)
        :return: list of records
        """
        try:
            params = {}
            if s_record_type:
                params['fieldType'] = s_record_type
                
            records = self.o_client.get(f'/domain/zone/{s_domain_name}/record', **params)
            return records
        except Exception as e:
            self.o_logger.error(f'Error listing records for {s_domain_name}: {e}')
            return []