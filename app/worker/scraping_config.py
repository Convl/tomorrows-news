from langchain_core.prompts import SystemMessagePromptTemplate

# Template for event extraction system message
EVENT_EXTRACTION_SYSTEM_TEMPLATE = SystemMessagePromptTemplate.from_template(
    """
You will be given a markdown-converted webpage by the user that should contain a news article, a blog post, a press release, or a similar piece of substantive content. Note that it may also contain other elements from the webpage that the content was hosted on, such as navigational elements, teasers for other articles, advertisements, etc. If such elements are present, you must ignore them and only focus on the substantive content.
If the substantive content contains information about upcoming events that are relevant to the following topic, you need to extract that information.
Topic name: {topic_name}
Topic description: {topic_description}
When determining the date of an upcoming event, keep in mind that today's date is {current_date}, and that the substantive content you are looking at was published on {publish_date}.
All extracted information should be in the following language: {language}.
Notice that the point of this task is to help in creating a forward planner with a list of upcoming events relating to the given topic, to be used by e.g. journalists or business analysts.
Therefore, you should only extract information about events that 1. lie in the future, 2. are specific enough to serve as actionable items in a forward planner, and 3. are important enough to be newsworthy. In general, mere plans or expectations are not sufficient, nor are vague dates or mere deadlines, unless they seem unusually interesting or important.
"""
    # # Examples of events that are sufficiently specific and important:
    # - The German parliament plans to vote on a new law about combatting hate speech on the 20th of August 2030. (date specific, event specific and important, actionable)
    # - The next hearing in the criminal case against the owner of the restaurant chain Blockhouse will take place on the 10th of July 2029, at 10:00 AM. (date and time specific, event specific and important, actionable)
    # - If Sony's board of directors cannot agree on a new CEO by the end of the year, the title will automatically pass to the company's founder. (date specific, event specific and important, actionable)
    # # Examples of events that are NOT sufficiently specific or important:
    # - The German government plans to install a comittee for reviewing recent changes to the criminal code by the end of the year (date not specific, event somewhat vague, not actionable)
    # - Some pundits suspect that the French president will issue his resignation at his annual address on the 1st of January next year. (date specific, event important, but mere suspicion that the event might happen is not sufficient)
    # - The new law is expected to cause rents to go up once it takes effect on the 1st of January 2030. (starting date specific, but this is a broader, long-term development, not a specific event)
    # - The defendant has until the 20th of July 2031 to decide whether to appeal the verdict. (date specific, but this is merely a deadline, not an actual event)
    # - KPMG is hosting a seminar on best practices in accouting for students and young professionals (date specific, event specific, but not important / newsworthy)
    # - If the defendant does not comply with the court's order within two weeks, he will have to pay a fine of 10.000 Euro (date specific, event specific, but not important / newsworthy)
    # - Politician X expects that a decision on the new law will be made within the month of May (date vague, mere expectation)
)

# Template for source extraction system message
SOURCE_EXTRACTION_SYSTEM_TEMPLATE = SystemMessagePromptTemplate.from_template(
    """
You will be given a markdown-converted webpage by the user that should contain a news article, a blog post, a press release, or a similar piece of substantive content. Note that it may also contain other elements from the webpage that the content was hosted on, such as navigational elements, links and teasers for other articles, advertisements, etc. If such elements are present, you must ignore them and only focus on the substantive content.
If there are links to other webpages WITHIN the substantive content that are relevant to the following topic, you need to extract those links (and, if possible, the title and publication date of the linked webpage).
All links in your response must be absolute links, but the links found on the page may be either absolute or relative to the page on which they are found or relative to the base url. Keep absolute links as they are, but bear in mind the rules regarding URL resolution when resolving relative links to absolute links:
The URL on which the links are found is: {url}
Topic name: {topic_name}
Topic description: {topic_description}
"""
)

EVENT_MERGE_SYSTEM_TEMPLATE = SystemMessagePromptTemplate.from_template(
    """
You will be given the title and description of two events. 
Your response should indicate whether the two events both refer to the same real-world event, just with different wording and possibly different details, or whether they refer to different real-world events.
If they refer to the same real-world event, your response should intelligently merge their titles and descriptions into a single title and description.
If they refer to different real-world events, leave the other fields in your response blank.
If one of the events refers to some specific part / subsection of the other event (e.g., the first event is about a rock festival, and the second event is about the much-anticipated return of some band as a headliner in that festival), you should consider them to refer to the same real-world-event, and your response should intelligently merge their titles and descriptions into a single title and description.
When merging, try to preserve the most important information from both events.
However, if there is contradictory information, you should prioritize the information from the second event.

Title of first event: {title_1}
Description of first event: {description_1}
Title of second event: {title_2}
Description of second event: {description_2}
"""
)
