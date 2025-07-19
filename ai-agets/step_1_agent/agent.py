import os
import asyncio
from google.adk.agents import Agent
#from google.adk.models.lite_llm import liteLlm
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore")
import logging
logging.basicConfig(level=logging.ERROR)

load_dotenv()
MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"
MODEL_GPT_4O = "openai/gpt-4.1"
MODEL_CLAUDE_SONNET = "anthropic/claude-sonnet-4-20250514"

def get_weather(city: str) -> str:
    """ retrive the current weather report for a given or specified city.
    Args:
    city (str): the name of the city.
    Returns:
    dict: a dictionary containing the current weather report.
    Includes a 'status' key ('success' or 'error').
              If 'success', includes a 'report' key with weather details.
              If 'error', includes an 'error_message' key.
    """

    print(f"--- Tool: get_weather called for city: {city} ---") # Log tool execution
    city_normalized = city.lower().replace(" ", "") # Basic normalization

    # Mock weather data
    mock_weather_db = {
        "newyork": {"status": "success", "report": "The weather in New York is sunny with a temperature of 25°C."},
        "london": {"status": "success", "report": "It's cloudy in London with a temperature of 15°C."},
        "tokyo": {"status": "success", "report": "Tokyo is experiencing light rain and a temperature of 18°C."},
    }

    if city_normalized in mock_weather_db:
        return mock_weather_db[city_normalized] # type: ignore
    else:
        return {"status": "error", "error_message": f"Sorry, I don't have weather information for '{city}'."} # type: ignore

AGENT_MODEL = MODEL_GEMINI_2_0_FLASH


try:
    weather_agent = Agent(
        name="Weather_agent",
        model=AGENT_MODEL,       
        description="Provides weather information for specific cities.",
        instruction ="You are a helpful weather assistant."
                    "When the user asks for the weather in a specific city, "
                    "use the 'get_weather' tool to find the information. "
                    "If the tool returns an error, inform the user politely. "
                    "If the tool is successful, present the weather report clearly.",
                    tools=[get_weather],
    )
except Exception as e:
    print(f"Error initializing the weather agent: {e}") # Log error

    
APP_NAME = "weather_tutorial_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

async def setup_session_and_runner():
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id = USER_ID,
        session_id= SESSION_ID
    )
    print(f"Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'")

    runner = Runner(
        agent= weather_agent,
        session_service = session_service,
        app_name=APP_NAME
    )
    print(f"Runner created for agent '{runner.agent.name}'.")
    return session,runner


async def call_agent_async(query:str) -> str | None:
      print(f"\n>>> User Query: {query}")
      content = types.Content(role='user', parts=[types.Part(text=query)])
      final_response_text = "Agent did not produce a final response."
      session, runner = await setup_session_and_runner()
      events = runner.run_async(user_id=USER_ID,session_id=SESSION_ID,new_message=content)
      async for event in events:
           if event.is_final_response():
                if event.content and event.content.parts:
                     final_response_text = event.content.parts[0].text
                elif event.actions and event.actions.escalate: # Handle potential errors/escalations
                     final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
                break
      #print(final_response_text)
      return final_response_text

response = asyncio.run(call_agent_async(query="What is the weather like in London?"))
# Uncomment the line below to run the agent with a sample query
print(response) # This will print the response from the agent

