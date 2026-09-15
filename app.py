import os
from datetime import datetime, timedelta

import streamlit as st
from dotenv import load_dotenv

from utils.trip_planner import TripPlanner, TripPreferences


st.set_page_config(
    page_title="TripWise AI",
    page_icon="✈️",
    layout="wide"
)

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key and "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]

if not api_key:
    st.error("Gemini API key is missing.")
    st.stop()

planner = TripPlanner(api_key)


# ---------- UI ----------

st.title("✈️ TripWise AI")
st.caption("Your AI-powered personal travel planner")

st.divider()


if "page" not in st.session_state:
    st.session_state.page = "form"

if "preferences" not in st.session_state:
    st.session_state.preferences = None

if "itinerary" not in st.session_state:
    st.session_state.itinerary = None


# =========================================================
# FORM
# =========================================================

if st.session_state.page == "form":

    st.header("🌍 Plan Your Trip")
    st.write("Tell TripWise a few things about your journey.")

    with st.container(border=True):

        col1, col2 = st.columns(2)

        with col1:
            start_location = st.text_input(
                "📍 Starting location",
                placeholder="Bhopal, India"
            )

            destination = st.text_input(
                "🌎 Destination",
                placeholder="Dubai, UAE"
            )

            budget = st.text_input(
                "💰 Budget",
                placeholder="₹50,000"
            )

            purpose = st.selectbox(
                "🎯 Purpose",
                [
                    "Leisure",
                    "Business",
                    "Adventure",
                    "Cultural",
                    "Relaxation"
                ]
            )

        with col2:
            start_date = st.date_input(
                "📅 Start date",
                min_value=datetime.today()
            )

            duration = st.number_input(
                "🗓️ Duration (days)",
                1,
                30,
                3
            )

            accommodation = st.selectbox(
                "🏨 Accommodation",
                [
                    "Budget",
                    "Mid-range",
                    "Luxury",
                    "Boutique",
                    "Apartment/Airbnb"
                ]
            )

            mobility = st.selectbox(
                "🚶 Mobility",
                [
                    "No special requirements",
                    "Minimal walking",
                    "Wheelchair accessible",
                    "Prefer public transport"
                ]
            )

    st.subheader("🧭 Travel Style")

    travel_style = st.radio(
        "Choose your preferred pace",
        ["Relaxed", "Balanced", "Packed"],
        horizontal=True
    )

    st.caption(
        {
            "Relaxed": "More free time and fewer activities.",
            "Balanced": "A mix of sightseeing and breaks.",
            "Packed": "More activities and efficient sightseeing."
        }[travel_style]
    )

    st.subheader("🍴 Food & Interests")

    col1, col2 = st.columns(2)

    with col1:
        dietary = st.multiselect(
            "Dietary preferences",
            [
                "Vegetarian",
                "Vegan",
                "Halal",
                "Gluten-free",
                "None"
            ]
        )

        cuisines = st.multiselect(
            "Preferred cuisines",
            [
                "Local",
                "Indian",
                "Italian",
                "Japanese",
                "Mexican",
                "Mediterranean"
            ]
        )

    with col2:
        interests = st.multiselect(
            "Interests",
            [
                "History & Culture",
                "Food & Dining",
                "Nature & Outdoors",
                "Shopping",
                "Art & Museums",
                "Nightlife",
                "Local Experiences"
            ]
        )

        amenities = st.multiselect(
            "Hotel amenities",
            [
                "Wi-Fi",
                "Pool",
                "Gym",
                "Restaurant",
                "Room Service"
            ]
        )

    col1, col2 = st.columns(2)

    with col1:
        walking = st.slider(
            "🚶 Walking tolerance (hours/day)",
            0,
            12,
            4
        )

    with col2:
        hidden_gems = st.checkbox(
            "✨ Include hidden gems"
        )

    st.write("")

    if st.button(
        "✨ Generate My Trip",
        type="primary",
        use_container_width=True
    ):

        if not start_location or not destination or not budget:
            st.warning(
                "Please fill in starting location, destination and budget."
            )
            st.stop()

        end_date = start_date + timedelta(days=int(duration))

        preferences = TripPreferences(
            budget=budget,
            duration=int(duration),
            start_date=datetime.combine(
                start_date,
                datetime.min.time()
            ),
            end_date=datetime.combine(
                end_date,
                datetime.min.time()
            ),
            start_location=start_location,
            destination=destination,
            purpose=purpose,
            travel_style=travel_style,
            dietary_preferences=dietary,
            interests=interests,
            mobility_requirements=mobility,
            accommodation_type=accommodation,
            walking_tolerance=f"{walking} hours",
            specific_interests={
                "cuisines": cuisines,
                "amenities": amenities
            },
            hidden_gems_preference=hidden_gems
        )

        st.session_state.preferences = preferences
        st.session_state.itinerary = None
        st.session_state.page = "result"

        st.rerun()


# =========================================================
# RESULT
# =========================================================

else:

    p = st.session_state.preferences

    st.header("🧳 Your Trip Plan")

    st.caption(
        f"{p.start_location} → {p.destination} • "
        f"{p.duration} days"
    )

    # Trip summary
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("📅 Duration", f"{p.duration} days")
    col2.metric("💰 Budget", p.budget)
    col3.metric("🧭 Style", p.travel_style)
    col4.metric("🎯 Purpose", p.purpose)

    st.divider()

    # Generate itinerary
    if st.session_state.itinerary is None:

        with st.spinner("✨ Creating your personalized itinerary..."):

            st.session_state.itinerary = (
                planner.generate_itinerary(p)
            )

    st.subheader("🗺️ Itinerary")

    with st.container(border=True):
        st.markdown(st.session_state.itinerary)

    st.write("")

    # Download
    st.download_button(
        "📥 Download Itinerary",
        st.session_state.itinerary,
        file_name=f"TripWise_{p.destination.replace(' ', '_')}.txt",
        mime="text/plain",
        use_container_width=True
    )

    st.write("")

    # Actions
    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "🔄 Plan Another Trip",
            use_container_width=True
        ):
            st.session_state.page = "form"
            st.session_state.preferences = None
            st.session_state.itinerary = None
            st.rerun()

    with col2:
        if st.button(
            "✨ Refine Itinerary",
            use_container_width=True
        ):
            st.session_state.show_refine = True

    if st.session_state.get("show_refine", False):

        feedback = st.text_area(
            "What would you like to change?",
            placeholder=(
                "Example: Add more outdoor activities "
                "and reduce expensive restaurants."
            )
        )

        if st.button("Update Trip"):

            if feedback.strip():

                with st.spinner("Updating your itinerary..."):

                    st.session_state.itinerary = (
                        planner.refine_suggestions(
                            p,
                            feedback
                        )
                    )

                st.session_state.show_refine = False
                st.rerun()

            else:
                st.warning("Please enter your feedback.")

    with st.expander("💡 Travel Tips"):

        st.markdown(
            """
            - Check local weather before travelling.
            - Confirm attraction opening hours.
            - Keep some flexible time in your schedule.
            - Carry required travel documents.
            - Use local transportation where practical.
            """
        )

st.divider()

st.caption(
    "TripWise AI • Personalized travel planning with Gemini"
)