import json
from google import genai
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class TripPreferences(BaseModel):
    budget: str
    duration: int
    start_date: datetime
    end_date: datetime
    start_location: str
    destination: str
    purpose: str
    travel_style: str
    dietary_preferences: Optional[List[str]] = []
    interests: Optional[List[str]] = []
    mobility_requirements: Optional[str] = None
    accommodation_type: Optional[str] = None
    walking_tolerance: Optional[str] = None
    specific_interests: Optional[dict] = None
    hidden_gems_preference: Optional[bool] = False


class TripPlanner:

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def _generate(self, prompt: str) -> str:
        try:
            response = self.client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )

            if response.text:
                return response.text.strip()

            return ""

        except Exception as e:
            print("Gemini API Error:", e)
            return f"Error generating response: {str(e)}"

    def _get_destination_info(self, destination: str) -> dict:

        prompt = f"""
You are TripWise AI, a smart travel planning assistant.

Research-style knowledge task for the destination: {destination}

Return ONLY valid JSON using exactly these keys:

{{
    "attractions": [],
    "hidden_gems": [],
    "restaurants": [],
    "experiences": []
}}

Requirements:
- attractions: 5 popular attractions
- hidden_gems: 3 less-touristy places
- restaurants: 5 food recommendations
- experiences: 4 memorable local experiences
- Keep each item short and useful.
- Do not add markdown or explanations outside the JSON.
"""

        response = self._generate(prompt)

        try:
            response = response.replace("```json", "").replace("```", "").strip()
            start = response.find("{")
            end = response.rfind("}")

            if start != -1 and end != -1:
                return json.loads(response[start:end + 1])

        except Exception:
            pass

        return {
            "attractions": [],
            "hidden_gems": [],
            "restaurants": [],
            "experiences": []
        }

    def generate_itinerary(self, preferences: TripPreferences) -> str:

        destination_info = self._get_destination_info(
            preferences.destination
        )

        attractions = destination_info.get("attractions", [])
        hidden_gems = destination_info.get("hidden_gems", [])
        restaurants = destination_info.get("restaurants", [])
        experiences = destination_info.get("experiences", [])

        if preferences.travel_style == "Relaxed":
            style_instruction = """
Travel style: RELAXED

Plan a slower-paced trip:
- Include fewer major activities each day.
- Leave meaningful free time between activities.
- Avoid overcrowding the schedule.
- Prioritize comfortable exploration and longer breaks.
"""

        elif preferences.travel_style == "Packed":
            style_instruction = """
Travel style: PACKED

Plan an active trip:
- Include more activities and attractions each day.
- Use nearby attractions efficiently.
- Minimize unnecessary idle time.
- Keep the schedule realistic despite having more activities.
"""

        else:
            style_instruction = """
Travel style: BALANCED

Plan a balanced trip:
- Combine sightseeing with reasonable breaks.
- Include a moderate number of activities each day.
- Avoid both an empty schedule and an overcrowded schedule.
"""

        prompt = f"""
You are TripWise AI, a personalized travel planner.

Create a realistic {preferences.duration}-day itinerary for:

Destination: {preferences.destination}
Starting Location: {preferences.start_location}
Dates: {preferences.start_date.strftime("%Y-%m-%d")} to {preferences.end_date.strftime("%Y-%m-%d")}
Budget: {preferences.budget}
Purpose: {preferences.purpose}
Travel Style: {preferences.travel_style}
Interests: {", ".join(preferences.interests or ["General sightseeing"])}
Dietary Preferences: {", ".join(preferences.dietary_preferences or ["No restrictions"])}
Mobility: {preferences.mobility_requirements or "No special requirements"}
Walking Tolerance: {preferences.walking_tolerance or "Moderate"}
Accommodation: {preferences.accommodation_type or "Mid-range"}

{style_instruction}

Destination information:
Popular attractions: {", ".join(attractions)}
Hidden gems: {", ".join(hidden_gems)}
Restaurants: {", ".join(restaurants)}
Local experiences: {", ".join(experiences)}

Follow these rules:

1. Keep the itinerary realistic.
2. Adjust the number of activities according to the selected travel style.
3. Group nearby places together to reduce unnecessary travel.
4. Consider the user's walking tolerance and mobility needs.
5. Match food suggestions with dietary preferences.
6. Respect the user's budget.
7. Include a mix of major attractions and local experiences.
8. Include hidden gems when requested.
9. Mention practical transportation suggestions.
10. Include approximate activity and food costs when useful.
11. Include some free or low-cost alternatives.
12. Do not make the itinerary overcrowded unless the user selected Packed.

Use this exact structure:

TRIP OVERVIEW
- Destination:
- Duration:
- Purpose:
- Travel style:
- Budget:
- Best way to get around:

DAY 1
Morning:
Afternoon:
Evening:

DAY 2
Morning:
Afternoon:
Evening:

Continue the same structure for all days.

BUDGET GUIDE
- Accommodation:
- Food:
- Transportation:
- Activities:
- Estimated total:

TRAVEL TIPS
- Weather:
- Local transport:
- Booking advice:
- Important local tip:

Do not invent exact ticket prices or availability.
Clearly use approximate wording for costs.
"""

        itinerary = self._generate(prompt)

        if not itinerary or itinerary.startswith("Error generating"):
            return "Unable to generate the itinerary right now. Please try again."

        return itinerary.strip()

    def refine_suggestions(
        self,
        preferences: TripPreferences,
        feedback: str
    ) -> str:

        prompt = f"""
You are TripWise AI.

Improve the travel plan based on the user's feedback.

Destination: {preferences.destination}
Duration: {preferences.duration} days
Budget: {preferences.budget}
Purpose: {preferences.purpose}
Travel Style: {preferences.travel_style}
Interests: {", ".join(preferences.interests or [])}
Dietary preferences: {", ".join(preferences.dietary_preferences or [])}
Walking tolerance: {preferences.walking_tolerance}
Accommodation: {preferences.accommodation_type}

The selected travel style is {preferences.travel_style}.
Keep the revised itinerary consistent with this pace.

User feedback:
{feedback}

Return an improved itinerary.

Keep the useful parts of the original plan, but make changes that directly address the user's feedback.

Use this structure:

TRIP OVERVIEW

DAY 1
Morning:
Afternoon:
Evening:

Continue for all days.

BUDGET GUIDE

TRAVEL TIPS
"""

        response = self._generate(prompt)

        if not response or response.startswith("Error generating"):
            return "Sorry, I couldn't refine your itinerary right now."

        return response.strip()