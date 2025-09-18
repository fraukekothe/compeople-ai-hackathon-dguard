# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import google.auth
from google.adk.agents import Agent


from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv
import psycopg2

from app.utils.gcp import get_secret

load_dotenv(override=True)

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "europe-west1")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

# Load and render the Jinja2 template for root_agent
template_dir = os.path.dirname(__file__)
env = Environment(loader=FileSystemLoader(template_dir))
template = env.get_template("medication_data_agent_prompt.j2")
medication_data_agent_instruction = template.render()


def search_medication_database(query: str) -> str:
    """
    Searches the AlloyDB medicine_details table for medications and their side effects.
    Args:
        query: A sql SELECT query for the alloy db postgres database
        e.g. SELECT "Medicine Name", "Composition", "Uses", "Side_effects", "Image URL", "Manufacturer", "Excellent Review", "Average Review", "Poor Review"
            FROM medicine_details
            WHERE LOWER("Side_effects") LIKE headache
    Returns:
        String with rows: Medicine Name, Composition, Uses, Side_effects, Image URL, Manufacturer, Excellent Review, Average Review, Poor Review
    """
    print(query)

    user = os.getenv("POSTGRES_USER")
    password = get_secret(
        project_id=project_id,
        secret_id=os.getenv("POSTGRES_PASSWORD_SECRET"),
        version_id=1,
    )
    dbname = "medicine_details"

    cleaned_query = query.strip().lower()
    if not cleaned_query.startswith("select"):
        return "Nur SELECT-Statements sind erlaubt."
    if ";" in cleaned_query:
        if cleaned_query.count(";") > 1 or not cleaned_query.rstrip().endswith(";"):
            return "Nur ein einzelnes SELECT-Statement ohne weitere SQL-Befehle ist erlaubt."
        query = query.rstrip().rstrip(";")

    try:
        conn = psycopg2.connect(dbname=dbname, user=user, password=password, port=5432)
        cur = conn.cursor()

        try:
            cur.execute(query)
            rows = cur.fetchall()
        finally:
            cur.close()
            conn.close()
    except Exception as e:
        return f"Database error: {e}"

    if not rows:
        return "No results found for the query."

    return "\n".join([", ".join(map(str, row)) for row in rows])


medication_data_agent = Agent(
    name="medication_data_agent",
    model="gemini-2.5-flash",
    instruction=medication_data_agent_instruction,
    tools=[search_medication_database],
)


if __name__ == "__main__":
    result = search_medication_database("headache")
    print(result)
