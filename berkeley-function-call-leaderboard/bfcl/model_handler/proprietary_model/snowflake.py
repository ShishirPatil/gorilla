from bfcl.model_handler.proprietary_model.nvidia import NvidiaHandler


class SnowflakeHandler(NvidiaHandler):
    
    @classmethod
    def supported_models(cls):
        return [
            'snowflake/arctic',
        ]
