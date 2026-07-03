from agent_controller import AgentController
import llm_client
import runpod

def main():
    # Fail fast with one clear message listing everything missing, instead of a
    # confusing crash deep inside the OpenAI/Pinecone SDK on whichever call happens
    # to run first.
    llm_client.validate_startup_config()

    agent_controller = AgentController()
    runpod.serverless.start({"handler": agent_controller.get_response})


if __name__ == "__main__":
    main()