from langchain_core.prompts import SystemMessagePromptTemplate

# Template for event extraction system message
EVENT_EXTRACTION_SYSTEM_TEMPLATE = SystemMessagePromptTemplate.from_template(
    """
You will be given a markdown-converted webpage by the user.
If the webpage contains information about upcoming events that are relevant to the following topic, you need to extract that information.
Topic name: {topic_name}
Topic description: {topic_description}
Topic country: {topic_country}
Notice that today's date is {current_date}.
You should only extract information about events that will **take place in the future** and are **relevant to the topic**.
All extracted information should be in {language}.
Notice that the point of this task is to create a forward planner with a list of upcoming events relating to the given topic, to be used by e.g. journalists or business analysts.
Therefore, you should only extract events which are specific enough to be used as actionable items in a forward planner.
Examples of events that are specific enough:
- The German parliament plans to vote on a new law about combatting hate speech on the 20th of August 2025. (date specific, event specific, actionable)
- The next hearing in the criminal case against the former president of the United States will take place on the 10th of July 2025, at 10:00 AM. (date and time specific, event specific, actionable)
Examples of events that are NOT specific enough:
- The German government plans to install a comittee for reviewing recent changes to the criminal code by the end of the year (date not specific, event somewhat vague, not actionable)
- Some pundits suspect that the French president will issue his resignation at his annual address on the 1st of January 2026. (date specific, event specific, but mere suspicion that event might happen is not sufficient)
- The new law is expected to cause rents to go up once it takes effect on the 1st of January 2026. (starting date specific, but this is a broader, long-term development, not a specific event)
"""
)

# Template for source extraction system message
SOURCE_EXTRACTION_SYSTEM_TEMPLATE = SystemMessagePromptTemplate.from_template(
    """
You will be given a markdown-converted webpage by the user.
If the webpage contains links to other webpages that are relevant to the following topic, you need to extract those links. 
Do not change anything about the links that you extracted, like replacing hyphens or dashes with tildes. 
Topic name: {topic_name}
Topic description: {topic_description}
Topic country: {topic_country}
"""
)
EVENT_MERGE_SYSTEM_TEMPLATE = SystemMessagePromptTemplate.from_template(
    """
You will be given the title and description of two events. 
Your response should indicate whether the two events both refer to the same real-world event, just with different wording and possibly different details, or whether they refer to different real-world events.
If they refer to different real-world events, leave the other fields in your response blank.
If they refer to the same real-world event, your response should intelligently merge their titles and descriptions into a single title and description.
When merging, try to preserve the most important information from both events.
However, if there is contradictory information, you should prioritize the information from the second event.

Title of first event: {title_1}
Description of first event: {description_1}
Title of second event: {title_2}
Description of second event: {description_2}
"""
)
