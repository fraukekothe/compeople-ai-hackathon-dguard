import google.cloud.secretmanager as secretmanager

def get_secret(project_id, secret_id, version_id):

    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the secret version.
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

    # Access the secret version.
    response = client.access_secret_version(name=name)
    payload = response.payload.data.decode("UTF-8")

    return payload
