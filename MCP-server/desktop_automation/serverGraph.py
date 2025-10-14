from configparser import SectionProxy
from azure.core.credentials import AccessToken
from msgraph import GraphServiceClient
from msgraph.generated.users.item.user_item_request_builder import UserItemRequestBuilder
from msgraph.generated.users.item.send_mail.send_mail_post_request_body import (
    SendMailPostRequestBody)
from msgraph.generated.models.message import Message
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.models.file_attachment import FileAttachment
from azure.core.credentials import AccessToken
from pptx import Presentation
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

import zipfile, os

class ServerGraph:
    settings: SectionProxy
    user_client: GraphServiceClient

    def __init__(self, config: SectionProxy, access_token: str):
        self.settings = config
        graph_scopes = self.settings['graphUserScopes'].split(' ')

        credential = SimpleAccessTokenCredential(access_token)
        self.user_client = GraphServiceClient(credential, graph_scopes)

    async def get_user(self) -> dict:
        # Only request specific properties using $select
        query_params = UserItemRequestBuilder.UserItemRequestBuilderGetQueryParameters(
            select=['displayName', 'mail', 'userPrincipalName']
        )
        request_config = UserItemRequestBuilder.UserItemRequestBuilderGetRequestConfiguration(
            query_parameters=query_params
        )
        user = await self.user_client.me.get(request_configuration=request_config)
        result = f"Initiated graph client with : {user.display_name} {user.mail or user.user_principal_name})" # type: ignore
        print(result)
        return {"result": result, "user": user}
    
    async def send_mail_without_attachment(self,
                        subject: str,
                        body: str,
                        recipients: list=[],
    ) -> str:
        print("Sending mail without attachment\nSubject: ", subject)
        print("Body: ", body)
        print("Recipient: ", recipients)
        message = Message()
        message.subject = subject

        message.body = ItemBody()
        message.body.content_type = BodyType.Html
        message.body.content = body

        # Add recipients
        message.to_recipients = []
        for email in recipients:
            to_recipient = Recipient()
            to_recipient.email_address = EmailAddress()
            to_recipient.email_address.address = email
            message.to_recipients.append(to_recipient)

        request_body = SendMailPostRequestBody()
        request_body.message = message

        try:
            await self.user_client.me.send_mail.post(body=request_body)
            print("email sent successfully")
            return "email without attachment sent successfully"
        except Exception as e:
            print("email sent failed", str(e))
            return f"Failed to send email without attachment: {str(e)}"
    
    async def send_mail_with_attachment(self,
                        subject: str,
                        recipients: list=[],
                        attachment_name: str = "Architecture of DEXIA.pptx"
    ) -> str:
        print("Sending mail with attachment\nSubject: ", subject)
        print("Recipient: ", recipients)
        print("Attachment name: ", attachment_name)
        message = Message()
        message.subject = subject

        # Check if attachment is a zip file
        if not attachment_name.lower().endswith('.zip'):
            error_msg = f"Error: Attachment '{attachment_name}' is not a zip file."
            print(error_msg)
            return error_msg
        
        # Add recipients
        message.to_recipients = []
        for email in recipients:
            to_recipient = Recipient()
            to_recipient.email_address = EmailAddress()
            to_recipient.email_address.address = email
            message.to_recipients.append(to_recipient)

        # Add powerpoint
        attachment_file_path = "generated_presentations/" + attachment_name
        if not os.path.exists(attachment_file_path):
            error_msg = f"Error: Attachment file '{attachment_file_path}' not found."
            print(error_msg)
            return error_msg

        with open(attachment_file_path, 'rb') as f:
            pptx_content = f.read()
        attachment = FileAttachment()
        attachment.name = attachment_name
        attachment.content_type = "application/zip"
        attachment.content_bytes = pptx_content
        message.attachments = [attachment]
        
        # Get Speaker Notes
        speaker_notes = get_speaker_notes(attachment_file_path)
        print("speaker notes: ", speaker_notes[:50])

        # Summary of speaker notes
        print("Generating summary")
        summary = summarize_speaker_notes(speaker_notes)
        message.body = ItemBody()
        message.body.content_type = BodyType.Html
        message.body.content = summary

        # Create request body
        request_body = SendMailPostRequestBody()
        request_body.message = message

        try:
            print("sending email with attachment")
            await self.user_client.me.send_mail.post(body=request_body)
            print("email with attachment sent successfully")
            return "email with attachment sent successfully"
        except Exception as e:
            print("Failed to send email with attachment", str(e))
            return f"Failed to send email with attachment: {str(e)}"


### Authentication Methods ###
class SimpleAccessTokenCredential:
    def __init__(self, token: str) -> None:
        self.token = token

    def get_token(self, *args, **kwargs):
        # Return an AccessToken object with a far future expiry
        return AccessToken(self.token, 9999999999)
    
### Helpers
"""
    Function to extract out speaker notes from generated zip file containing pptx and images
    May encounter concurrency issues
"""
def get_speaker_notes(filepath: str) -> str:
    zip_path = filepath
    file_name = "presentation.pptx"

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extract(file_name, "extracted_files")
    pptx_path = f"extracted_files/{file_name}"
    prs = Presentation(pptx_path)
    speaker_notes = ""
    for i, slide in enumerate(prs.slides, 1):
        notes_slide = slide.notes_slide
        notes_text = notes_slide.notes_text_frame.text if notes_slide and notes_slide.notes_text_frame else ""
        speaker_notes += notes_text
    return speaker_notes

def summarize_speaker_notes(notes: str) -> str:
    llm = AzureChatOpenAI(
        azure_deployment=os.getenv("GPTO3_MINI_DEPLOYMENT_NAME"),
        openai_api_version=os.getenv("GPTO3_MINI_API_VERSION"), # type: ignore
        api_key=os.getenv("GPTO3_MINI_API_KEY"),
        azure_endpoint=os.getenv("GPTO3_MINI_API_BASE"),
        temperature=1 # O3-mini/reasoning models do not support temperature parameter so have to fix this to 1
    )
    system_prompt = "Summarize the following speaker notes in html format, with headers and bullet points."
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=notes),
    ])

    return str(response.content)