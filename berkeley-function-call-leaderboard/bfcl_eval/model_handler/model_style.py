from enum import Enum


# TODO: Use all caps for enum values to maintain consistency
class ModelStyle(Enum):
    Gorilla = "gorilla"
    OpenAI_Completions = "openai-completions"
    OpenAI_Responses = "openai-responses"
    Anthropic = "claude"
    Mistral = "mistral"
    GOOGLE = "google"
    AMAZON = "amazon"
    FIREWORK_AI = "firework_ai"
    NEXUS = "nexus"
    OSSMODEL = "ossmodel"
    COHERE = "cohere"
    WRITER = "writer"
    NOVITA_AI = "novita_ai"
