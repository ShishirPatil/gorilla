import os
import json

"""
NegationAPIPairManager Interface
"""
class NegationAPIPairManager:
    def __init__(self):
        return None
    
    def get_success(self, forward_call):
        # return a single backward call that have previously been reported successful
        # this backward call will be used to perform the reversion if requested
        raise NotImplementedError
    
    def get_failure(self, forward_call):
        # return a list of backward calls that have previously been reported unsuccessful
        raise NotImplementedError
    
    def insert_log(self, forward_call, backward_call, result):
        # insert a new entry or log to the negation manager
        raise NotImplementedError

"""
Simple NegationManager with JSON based key-value pair storage
"""
class NaiveNegationAPIPairManager(NegationAPIPairManager):
    def __init__(self, reverse_log_json_path):
        self.reverse_log_path = os.path.join(reverse_log_json_path, "negation_log.json")

    def get_success(self, forward_call):
        logs = {}
        try:
            with open(self.reverse_log_path, "r") as reverse_log:
                logs = json.load(reverse_log)
                if forward_call in logs:
                    if "true" in logs[forward_call]:
                        return logs[forward_call]["true"][0]
    
        except Exception as e:
            pass

        return None

    def get_failure(self, forward_call):
        logs = {}
        try:
            with open(self.reverse_log_path, "r") as reverse_log:
                logs = json.load(reverse_log)
                if forward_call in logs:
                    if "false" in logs[forward_call]:
                        return logs[forward_call]["false"]
    
        except Exception as e:
            pass

        return None

    def insert_log(self, forward_call, backward_call, result):
        logs = {}
        try:
            with open(self.reverse_log_path, "r") as reverse_log:
                logs = json.load(reverse_log)
    
        except Exception as e:
            pass

        with open(self.reverse_log_path, "w") as reverse_log:
            if forward_call not in logs:
                logs[forward_call] = {}
            
            result = str(result).lower()
            if result in logs[forward_call]:
                logs[forward_call][result].append(backward_call)
            else:
                logs[forward_call][result] = [backward_call]

            json.dump(logs, reverse_log)
