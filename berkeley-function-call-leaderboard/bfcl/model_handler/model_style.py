from enum import Enum


# TODO: Use all caps for enum values to maintain consistency
class ModelStyle(Enum):
    """
    An enumeration of different model styles/architectures used in the system. Each enum value represents a different model provider or architecture style.
    
    Enum Values:
        Gorilla (str): Represents Gorilla model style
        OpenAI (str): Represents GPT-style models from OpenAI
        Anthropic (str): Represents Claude models from Anthropic
        Mistral (str): Represents Mistral models
        Google (str): Represents Google models
        AMAZON (str): Represents Amazon models
        FIREWORK_AI (str): Represents Firework AI models
        NEXUS (str): Represents Nexus models
        OSSMODEL (str): Represents open source models
        COHERE (str): Represents Cohere models
        WRITER (str): Represents Writer models
        NOVITA_AI (str): Represents Novita AI models
    """
    Gorilla: str = "gorilla"
    OpenAI: str = "gpt"
    Anthropic: str = "claude"
    Mistral: str = "mistral"
    Google: str = "google"
    AMAZON: str = "amazon"
    FIREWORK_AI: str = "firework_ai"
    NEXUS: str = "nexus"
    OSSMODEL: str = "ossmodel"
    COHERE: str = "cohere"
    WRITER: str = "writer"
    NOVITA_AI: str = "novita_ai"
