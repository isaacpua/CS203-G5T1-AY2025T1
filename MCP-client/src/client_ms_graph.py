from configparser import SectionProxy
from azure.identity import DeviceCodeCredential
from msgraph.graph_service_client import GraphServiceClient

class ClientMsGraph:
    settings: SectionProxy
    device_code_credential: DeviceCodeCredential
    user_client: GraphServiceClient

    def __init__(self, config: SectionProxy):
        self.settings = config
        client_id = self.settings['clientId']
        tenant_id = self.settings['tenantId']
        graph_scopes = self.settings['graphUserScopes'].split(' ')
        self.device_code_details = {}

        def save_device_code(device_code, user_code, expires_on):
            self.device_code_details = {
                "verification_link": device_code,
                "user_code": user_code,
                "expires_on": expires_on,
            }

        self.device_code_credential = DeviceCodeCredential(client_id, tenant_id = tenant_id)
        self.user_client = GraphServiceClient(self.device_code_credential, graph_scopes)

    async def get_user_token(self):
        graph_scopes = self.settings['graphUserScopes']
        access_token = self.device_code_credential.get_token(graph_scopes)
        return access_token.token