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

import datetime
import os
from typing import Optional

import google.auth
from google.adk.agents import Agent

from google.adk.tools.agent_tool import AgentTool


from jinja2 import Environment, FileSystemLoader
from atlassian import Confluence
from dotenv import load_dotenv

from app.medication_data_agent import medication_data_agent
from app.utils.gcp import get_secret


load_dotenv(override=True)

_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "europe-west1")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

# Load and render the Jinja2 template for root_agent
template_dir = os.path.dirname(__file__)
env = Environment(loader=FileSystemLoader(template_dir))
template = env.get_template("root_agent_prompt.j2")
root_agent_instruction = template.render()


def create_confluence_page(
    medication: str,
    side_effect: str,
    dose: Optional[str] = None,
    intake_duration: Optional[str] = None,
    side_effect_intensity: Optional[int] = None,
    symptoms: Optional[str] = None,
    other_medications: Optional[list] = None,
    taken_with_meal: Optional[str] = None,
    age_of_patient: Optional[int] = None,
    weight_of_patient: Optional[int] = None,
    gender_of_patient: Optional[str] = None,
    underlying_condition: Optional[list] = None,
    known_allergies: Optional[list] = None,
) -> str:
    """
    Description:
    Creates a Confluence Page to document an adverse drug reaction (ADR).
    The page includes structured patient data, medication details, and information about the reported side effect.

    Parameters:

    medication (string, required): The name of the medicine taken.
    side_effect (string, required): The observed side effect (e.g., "headache", "nausea").
    dose (string): The dosage of the medicine (e.g., "500mg", "1 tablet").
    intake_duration (string): The duration of intake (e.g., "5 days", "2 weeks").
    side_effect_intensity (int): The severity or intensity of the side effect (e.g., "mild", "moderate", "severe") from 1 to 10.
    symptoms (string): Other symptoms reported by the patient.
    other_medications (array of strings): Other medications taken at the same time.
    taken_with_meal (enum: before, during, after, none): Timing of the intake relative to meals.
    age_of_patient (integer): Age of the patient in years.
    weight_of_patient (integer): Weight of the patient in kilograms.
    gender_of_patient (enum: m, f, d): Gender of the patient (m = male, f = female, d = diverse).
    underlying_condition (array of strings): List of relevant pre-existing medical conditions.
    known_allergies (array of strings): Known allergies of the patient.
    """

    confluence_secret_id = os.getenv("CONFLUENCE_SECRET_ID")
    confluence_secret_version = os.getenv("CONFLUENCE_SECRET_VERSION")

    confluence_page = {
        "title": f"Adverse Drug Reaction: {medication} - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "content": f"""
            <h2>Record of Side Effects</h2>
            <table border="1" cellpadding="5" cellspacing="0">
                <tr><th>Medication</th><td>{medication}</td></tr>
                <tr><th>Side Effect</th><td>{side_effect}</td></tr>
                <tr><th>Dose</th><td>{dose or ""}</td></tr>
                <tr><th>Intake Duration</th><td>{intake_duration or ""}</td></tr>
                <tr><th>Side Effect Intensity</th><td>{side_effect_intensity or ""}</td></tr>
                <tr><th>Symptoms</th><td>{symptoms or ""}</td></tr>
                <tr><th>Other Medications</th><td>{other_medications or ""}</td></tr>
                <tr><th>Taken With Meal</th><td>{taken_with_meal or ""}</td></tr>
                <tr><th>Age of Patient</th><td>{age_of_patient or ""}</td></tr>
                <tr><th>Weight of Patient</th><td>{weight_of_patient or ""}</td></tr>
                <tr><th>Gender of Patient</th><td>{gender_of_patient or ""}</td></tr>
                <tr><th>Underlying Conditions</th><td>{underlying_condition or ""}</td></tr>
                <tr><th>Known Allergies</th><td>{known_allergies or ""}</td></tr>
            </table>
        """,
    }

    base_url = "https://compeople.atlassian.net/wiki"
    confluence = Confluence(
        url=base_url,
        username=os.getenv("CONFLUENCE_USERNAME"),
        password=get_secret(
            project_id=project_id,
            secret_id=confluence_secret_id,
            version_id=confluence_secret_version,
        ),
    )

    created = confluence.create_page(
        space="GC",
        title=confluence_page["title"],
        body=confluence_page["content"],
        parent_id="389185556",
    )
    if not created:
        return "Failed to create Confluence page."
    webui_path = created["_links"]["webui"]
    full_url = base_url + webui_path
    print(full_url)
    return f"Confluence page created at url: {full_url}, "


root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash",
    instruction=root_agent_instruction,
    tools=[AgentTool(agent=medication_data_agent), create_confluence_page],
)
