# Guide to Inference Logs

> An inference log is included along with the llm response in the results file to help you analyze and debug the model's performance, and to better understand the model behavior. To enable a more detailed log, use the `--include_inference_input_log` flag (or `-i` for short) in the generation command.

## Log Structure

The log is structured as a list of dictionaries, representing a conversational interaction between the model, system, and user. There are four types of roles in the log:

1. **`user`**: Represents the user's input or query.
2. **`assistant`**: Represents the model's raw response.
3. **`tool`**: Represents the output of a function execution, if the model makes a valid function call. Each function call results in a separate `tool` entry.
4. **`handler_log`**: Represents internal logs from the inference pipeline. These entries indicate various stages and events within the pipeline, including:

   - **`handler_log:inference_input`**: Snapshot of the fully-transformed input just before it's sent to the model API endpoint. Useful for debugging input integrity and format.
     - Available only if the `--include_inference_input_log` or `-i` flag is set in the generation command.
     - This section can be verbose and may affect log readability; it is generally not necessary for most analyses.
   - **`handler_log:decode_success`**: Indicates the successful decoding of the model's raw response, with the decoded response included in the content field. Following this, any function calls are executed, and the current turn continues.
   - **`handler_log:empty_response`**: Indicates that the model handler returned an empty response (e.g., no function call) based on the decoding strategy. When this occurs, the pipeline proceeds to the next turn.
   - **`handler_log:decode_failure`**: Indicates a failure in decoding the raw model response, with the raw response included in the content field. The pipeline then proceeds to the next turn.
   - **`handler_log:force_quit`**: Indicates that the model handler has forcefully ended the conversation after the model made 20 unsuccessful attempts within one turn or task (the count reset at each turn). No further turns are processed for this entry.

## Single Turn Categories

For single-turn categories, the only log entry available is `handler_log:inference_input`, because there is no interaction with the model or system.
