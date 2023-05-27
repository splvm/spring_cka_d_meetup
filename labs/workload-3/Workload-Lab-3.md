# Pod Lifecycle

## Understand the pod's status

### Prepare the environment
- Create a pod
  - `k apply -f pod.kiada.yaml`
- Compare the original yaml file with the one that is created by kubernetes.
  - `k get po kiada -o yaml > dep-kiada.yaml`
- > Note: Kubernetes will add the status section to the yaml file.

:question: How can we use the status section?

### Pod's phase
The following diagram shows the details of a pod's lifecycle. 
![The phases of a Kubernetes pod](https://drek4537l1klr.cloudfront.net/luksa3/v-14/Figures/06image002.png)

- **Display a pod's phase**
You can get the a pod's phase trhough the yaml file.
  - Commands
    - `k get po kiada -o yaml | grep phase`
    - `k get po kiada -o json | jq .status.phase`
    - `k describe po kiada`
      - You can see the status of the pod.
Command `k get pods` works only when the pod is is in healthy status.

### Understanding pod conditions 

- List of pod conditions
  - PodScheduled: Indicates whether or not the pod has been scheduled to a node.
  - Initialized: The pod's init containers have all completed successfully.
  - ContainersReady: All containers in the pod indicate that they are ready. This is a necessary but not sufficient condition for the entire pod to be ready.
  - Ready: The pod is ready to provide services to its clients.
- The transition of the pod's conditions during its lifecycle
  - ![The transition of the pod's conditions during its lifecycle](https://drek4537l1klr.cloudfront.net/luksa3/v-14/Figures/06image003.png)

- Commands to get the conditions of a pod
  - `k get po kiada -o json | jq .status.conditions`
  - `k describe po kiada`
  - `k get po kiada -o jsonpath='{.status.conditions}'`
  - `k get po kiada -o jsonpath='{.status.conditions[1].status}'`

### Understanding the container status 

**Container status actually provides more information for cluster admin, as it is the client in the pod and the culprit of pod issues.**
- Container status sample: 
```yaml
containerStatuses:
  - containerID: containerd://0438d79e6fc85d56e8db532ded6977819e5162bbeb185b58b3a18e6cf3c77c07
    image: docker.io/luksa/kiada-ssl-proxy:0.1
    imageID: docker.io/luksa/kiada-ssl-proxy@sha256:ee9fc6cfe26a53c53433fdb7ce0d49c5e1bffb889adf4d7b8783ae9f273ecfe7
    lastState: {}
    name: envoy
    ready: true
    restartCount: 0
    started: true
    state:
      running:
        startedAt: "2022-11-19T06:06:56Z"
  - containerID: containerd://99c7390e6caed24e87e40b581b68d832b64f80778857213e652741389c9c5f48
    image: docker.io/luksa/kiada:0.2
    imageID: docker.io/luksa/kiada@sha256:901847a775d8ab631df844c40555a8cbfd2c5ab2b9d9a0913d5216b07db7b1d9
    lastState: {}
    name: kiada
    ready: true
    restartCount: 0
    started: true
    state:
      running:
        startedAt: "2022-11-19T06:06:51Z"
```

- Fields details:
  - `state`: current state of the container
  - `lastState`: state of the previous container after it has terminated. 
  - `restartCount`: how many times it restarts.

- Status illustration
![The possible states of a container](https://drek4537l1klr.cloudfront.net/luksa3/v-14/Figures/06image004.png)

- **Displaying the status of the pods's containers**
  - Commands
    - `k describe po kiada`
    - `k get po kiada -o json | jq .status.containerStatuses`
    - `k get po kiada-init -o json | jq .status`
  - Messing up a pod
    - Update `pod.kiada-ssl.yaml` by setting very low memory limit.
      ```yaml
      resources:
        limits:
          cpu: 300m
          memory: 1Mi
      ```
    - Check pod status by `k describe pod kiada-ssl`

### Checking the container's health using liveness probes

A process can stay in deadlock status without stopping. Thus, the container will not be restarted. In order to restart the unhealthy container forcely, we want to use liveness probes.

> :exclamation: **Note: Liveness probes can only be used in the pod's regular containers. They can't be defined in init containers.**

- Types of liveness probes
  - **HTTP GET**: Send http get request to container's IP address and expect success response in time. Otherwise, the container is considered unhealthy.
  - **TCP Socket**: Establish a TCP connection to a specific port of the container successfully. Otherwise, mark container as unhealthy.
  - **Exec**: Run a command inside the container.
    - `k exec kiada-ssl -c envoy -- ls`
    - `k exec kiada-ssl -c kiada -- ls`

- Sample of liveness probe
  ```yaml
  livenessProbe:
    httpGet:
      path: /ready
      port: admin
    initialDelaySeconds: 10
    periodSeconds: 5
    timeoutSeconds: 2
    failureThreshold: 3
  ```
- Liveness probe fields explanation
  ![The configuration and operation of a liveness probe](https://drek4537l1klr.cloudfront.net/luksa3/v-14/Figures/06image007.png)

- Liveness probe verification through log
  - Check liveness probe in `pod.kiada-liveness.yaml`
  - Commands
    - `k apply -f pod.kiada-liveness.yaml`
    - `k logs kiada-liveness -c kiada -f`
    - `k exec kiada-liveness -c envoy -- tail -f /tmp/envoy.admin.log`
    - `k get events --field-selector involvedObject.name=kiada-ssl`
    - :question: Why we cannot check envoy log through `k logs` command?
  - Fail Envoy liveness probe
    - `k port-forward kiada-liveness 9901:9901`
    - `curl -X POST http://localhost:9901/healthcheck/fail`
    - Visit address "localhost:9901" in browser and click "quitquitquit" button.
    - K8s will restart the container
    - :question: How a container that fails its liveness probe is restarted?
      - `k logs kiada-liveness -c envoy -p`
      - Sample 
        ```
        [2023-05-20 20:07:28.204][1][info][main] [source/server/server.cc:554] starting main dispatch loop
        [2023-05-20 20:09:22.508][1][warning][main] [source/server/server.cc:493]         caught SIGTERM
        [2023-05-20 20:09:22.508][1][info][main] [source/server/server.cc:613] shutting         down server instance
        [2023-05-20 20:09:22.508][1][info][main] [source/server/server.cc:560] main         dispatch loop exited
        [2023-05-20 20:09:22.509][1][info][main] [source/server/server.cc:606] exiting
        ```

### Using a startup probe when an application is slow to start 
If an application lake minutes to start, then short time liveness probe could prevent the container from reaching expected status. Although we can achieve longer delay by configuring `initialDelaySeconds`, `periodSeconds` and `failureThreshold`, it will introduce negative effect on the normal operation of the applicaiton. For example, it will take longer to detect the failure of the application.

To deal with this, K8s provide startup probe. Only the startup probe will be executed when we start the container. Once the startup probe is successful, K8s will switch to use the liveness probe.

- Start up probe sample
  ```yaml
  ...
  containers:
  - name: kiada
    image: luksa/kiada:0.1
    ports:
    - name: http
      containerPort: 8080
    startupProbe:
      httpGet:
        path: /
        port: http
      periodSeconds: 10
      failureThreshold:  12
    livenessProbe:
      httpGet:
        path: /
        port: http
      periodSeconds: 5
      failureThreshold: 2
  ```

- Failure is normal for a startup probe
  A failure just means the application is ready yet.
- Startup probe + liveness probe
  ![Combine startup probe and liveness probe](https://drek4537l1klr.cloudfront.net/luksa3/v-15/Figures/06image009.png)

- Creating effective liveness probe handlers
  - A liveness probe is needed, otherwise your application will remain in unhealthy status and need a manual restart.
  - Expose a specific health-check endpoint and make sure no authentication is needed for the entpoint.
  - A liveness probe should only check the status of the target application. No dependent applications should be checked.
  - Keeping probes light. Use less CPU and memory.




