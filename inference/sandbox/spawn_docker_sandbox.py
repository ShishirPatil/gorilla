import docker

client = docker.from_env()

#build a new image from the Dockerfile
image, build_logs = client.images.build(path = '../', quiet=False)

# uncomment for debugging the build logs
# for chunk in build_logs:
#     if 'stream' in chunk:
#         for line in chunk['stream'].splitlines():
#             print(line)

# run a new container using the image built above and run the code produced by the llm. Print the stdout for the user to see
output = client.containers.run(image) #read_only=True, , remove=True, privileged=False
print(output)