class NoAPIKeyError(Exception):
    def __init__(self):
        self.message = "❗️Please fill in the API keys in the function_credential_config.json file. If you do not provide the API keys, the executable test category results will be inaccurate."
        super().__init__(self.message)
        
        
class BadAPIStatusError(Exception):
    def __init__(self, errors, error_rate):
        self.errors = errors
        self.error_rate = error_rate