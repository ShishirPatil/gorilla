from bfcl._openfunctions_evaluation import get_args, main
from dotenv import load_dotenv

if __name__ == "__main__":
    # TODO: Should we load the .env file here?
    load_dotenv(dotenv_path="./.env", verbose=True, override=True)
    
    main(get_args())