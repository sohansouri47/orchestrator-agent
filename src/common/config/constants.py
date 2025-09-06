class LlmConfig:
    class Anthropic:
        HAIKU_3_MODEL = "anthropic/claude-3-haiku-20240307"
        SONET_4_MODEL = "anthropic/claude-sonnet-4-20250514"
        OPUS_4_MODEL = "anthropic/claude-opus-4-20250514"

    class Google:
        GOOGLE_1_5_MODEL = "gemini/gemini-1.5-pro-latest"


class Routes:
    SEND_TEXT = "/chat"
    SEND_VOICE = "/voice"


class Constants:
    USER_ROLE = "RANDOM_USER_ROLE"
