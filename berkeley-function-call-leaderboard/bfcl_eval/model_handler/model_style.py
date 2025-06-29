from enum import Enum


# TODO: Use all caps for enum values to maintain consistency
class ModelStyle(Enum):
    """
    An enumeration of different model styles/architectures used in the system. Each enum value represents a different model type with its associated identifier string.
    
    Enum Values:
        Gorilla (str): Represents Gorilla model style ('gorilla')
        OpenAI (str): Represents OpenAI GPT model style ('gpt')
        Anthropic (str): Represents Anthropic Claude model style ('claude')
        Mistral (str): Represents Mistral model style ('mistral')
        Google (str): Represents Google model style ('google')
        AMAZON (str): Represents Amazon model style ('amazon')
        FIREWORK_AI (str): Represents Firework AI model style ('firework_ai')
        NEXUS (str): Represents Nexus model style ('nexus')
        OSSMODEL (str): Represents open source model style ('ossmodel')
        COHERE (str): Represents Cohere model style ('cohere')
        WRITER (str): Represents Writer model style ('writer')
        NOVITA_AI (str): Represents Novita AI model style ('novita_ai')
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
