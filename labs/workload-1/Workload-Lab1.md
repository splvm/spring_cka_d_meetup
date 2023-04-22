# Workload-1

The lab notes here mainly focus on how to use Deployment and ReplicaSet to manage the pods. Also trying to find out how the deployment and replicaset work under the hood. **How to prepare the yaml files for deployment and replicaset will not be covered in this lab.**

## 1. Preparing

### 1.1 Reading
- [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [ReplicaSet](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/)
- [Controller](https://kubernetes.io/docs/concepts/architecture/controller/)
- Kubernetes in Action 2nd edition, Chapter 13
- Kubernetes in Action 2nd edition, Chapter 14

### 1.2 Source Code
- [Kubernetes in Action 2nd edition](https://github.com/luksa/kubernetes-in-action-2nd-edition/tree/master)


## 2. Why Deployment and ReplicaSet?
- Availability
  - How to make sure the service is always available?
    - Certain number of pods are always running
    - If a pod is down, a new one will be created
- Maintainability
  - How to rollout out a new version of the service?
    - Create a new pod with the new version containers
- Scalibility (**Deployment is not the ultimate solution for scaling**)
  - How to scale the service?
    - Increase the number of pods
    - Decrease the number of pods

### 2.1 Lab Commands
- `k apply -f SETUP/ -R` # Create the pods and services
  - Note: Please use the SETUP folder in Chapter 13 source code
- `k get pods` # Check the pods
- `k edit pod kiada-001` # Edit the pod to mess up the kiada image
- `k get pods` # Check the pods with one pod down

### 2.2 Group the pods together
- It will be great if I can group the pods together and manage them as a group.
![Replicaset](https://drek4537l1klr.cloudfront.net/luksa3/v-15/Figures/13_img_0001.png)

## 3. ReplicaSet
ReplicaSets select and manage pods using labels. **Labels for a replicaset and the pod template must match, otherwise k8s will not create the pods.**

### 3.1 Lab Commands
- `k apply -f rs.kiada.yaml` # Create the replicaset
- `k get rs` # Check the replicaset: 4 pods should be ready
  - :warning: **Looks like the replicaset will not promise the desired number of pods are always ready.**
- `k delete pod kiada-001` # Delete the problematic pod
- `k get pods` # Check the pods
- `k get rs` # Check the replicaset: 4 pods should be ready

> Note: When you create a replicaset, existing pods with the same labels will be adopted and managed by the replicaset.

- Delete a ReplicaSet
  - Delete a replicaset without deleting all the pods managed by the replicaset.
    - `k delete rs kiada --cascade=orphan`
    - `k get rs kiada`

- Pod ownership
  In the pod yaml file, there is a field `metadata.ownerReferences` which is used to record the owner of the pod.
  - `kubectl get po <pod-name> -o yaml`
  ```yaml
  ownerReferences:
  - apiVersion: apps/v1
    blockOwnerDeletion: true
    controller: true
    kind: ReplicaSet
    name: kiada
    uid: 9d659338-7e2b-4c8a-ae8d-81d7d2d97964
  ```
- Pod naming
  The name of the replicaset will be used as the prefix for the pods name.
  - `k edit po <kiada-pod-name>`
  - Check field `metadata.generateName`
- Updating a ReplicaSet
  - Scaling a ReplicaSet up and down
    - `k get rs kiada -w`
    - `k scale rs kiada --replicas=6`

- Scale down to zero
  - Scale down to zero will delete all pods but not the replicaset. This could be used when you want to refresh all pods.
  - `k get po -l app=kiada -w`
  - `k scale rs kiada --replicas=0`

### 3.2 Lab Cleanup
- `k delete all --all` # Delete all the pods and services in default namespace

## 4. Deployment
Workloads are usually deployed through a Deployment. However, deployment is not the one to manage the pods. It is the underneath ReplicaSet that manages the pods. The deployment is used to manage the ReplicaSet.

![Relationship between Deployment, ReplicaSet and Pods](https://drek4537l1klr.cloudfront.net/luksa3/v-15/Figures/14_img_0001.png)

### 4.1 Lab Commands
- `k apply -f SETUP/ -R` # Create the pods and services
- `k get deploy` # We don't have any deployment yet
- `k apply -f deploy.kiada.yaml` # Create the deployment
- `k get deploy` # Inspect the deployment
- `k describe deploy kiada` # Inspect the deployment
- :question: **Will the exiting pods and replicaset be adopted by the deployment?**
- `k get po` # Inspect the pods
- `k get rs` # Inspect the replicasets

- Deployment naming
  When you create a deployment, the deployment name will be used as the prefix for the replicaset name. There will also be a suffix from the label `pod-template-hash`. We should be able to find the `pod-template-hash` using `k edit rs kiada`.
  - `k edit rs kiada` # Show the replicaset selector

- Scaling a Deployment
  Scaling a deployment is pretty much the same as scaling a replicaset. The actual work is done by the replicaset controller.
  - `k scale deploy kiada --replicas 5` # Scale up
  - `k scale deploy kiada --replicas 2` # Scale down
  - `k get po -w` # Watch the pods creation and deletion

- :question: **Will deployment always keep a desired number of healthy pods?**
  - `k get deploy kiada -w` # Watch the deployment
  - `k edit pod kiada-<suffix>` # Mess up the pod
  - `k get po`

- Deleting a deployment and reserving the pods and replicaset
  - `k delete deploy kiada --cascade=orphan` # Delete the deployment but keep the replicaset and pods
  - `k get rs` # Check the replicaset
  - `k get po` # Check the pods
  - **When you create deployment again, it will try to adopt the existing replicas and pods.**

### 4.2 Lab Commands: Update a deployment

#### 4.2.1 Update strategies
  - Currently, there are two update strategies: `RollingUpdate` and `Recreate`. The default strategy is `RollingUpdate`.
  - ![The difference between the Recreate and the RolliongUpdate strategies](https://drek4537l1klr.cloudfront.net/luksa3/v-15/Figures/14_img_0004.png)

#### 4.2.2 Update using `recreate` strategy
  - `k delete rs kiada` # Delete the replicaset that is not created by a deployment
  - `k get pod -l app=kiada -w` # Watch the pods creation and deletion
  - `k apply -f deploy.kiada.0.6.recreate.yaml` # Create the deployment
  - The previous replicaset will be kept and scale down to 0
    - `k get rs -L ver` # Show the replicaset version
    ![Updating a Deployment](https://drek4537l1klr.cloudfront.net/luksa3/v-15/Figures/14_img_0005.png)

> :warning: **The `recreate` strategy will delete all the old pods all at once. This will cause the service to be unavailable.**

#### 4.2.3 Rolling update 
  With the `Recreate` strategy, all pods will be deleted simultaneously and then recreated. Down time will be introduced during the update. Solution to resolve the down time issue is to use the `RollingUpdate` strategy. The `RollingUpdate` strategy will update the pods one by one or in a pace defined by the customers. (75 - 125).
  - How it works?
  - ![What happens with the ReplicaSets, Pods, and the Service during a rolling update](https://drek4537l1klr.cloudfront.net/luksa3/v-15/Figures/14_img_0006.png)
  - Configuration
    ```yaml
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: kiada
    spec:
      strategy:
        type: RollingUpdate
        rollingUpdate:
          maxSurge: 0
          maxUnavailable: 1
      minReadySeconds: 10
      replicas: 3
      selector:
      ...
    ```

- Show the rollout update details
  - Optional: `k delete rs <old-rs>` # Delete the old replicaset
  - Optional: `k get rs -w` # Watch the replicaset creation and deletion
  - `k apply -f deploy.kiada.0.7.rollingUpdate.yaml`
  - `k rollout status deploy kiada` # Show the rollout status, need to run immediately after the `apply` command
  - Optional: `k get pod -l pod-template-hash=<value> -w` # Show the pods

- Show the rollout update using a test client
  ```bash
  kubectl run -it --rm --restart=Never kiada-client --image curlimages/curl -- sh -c \
  'while true; do curl -s http://kiada | grep "Request processed by"; done'
  ```

#### 4.2.4 Configuring how many Pods are replaced at a time
`maxSurge` and `maxUnavailable` are used to control how many pods are replaced at a time.

- `maxSurge` is the maximum number of pods that can be created over the desired number of pods. It can be a number or a percentage. The default value is 25%.
  - `maxSurge: 0` # Maximum number of pods at a certain time is the desired number of pods
  - `maxSurge: 1` # Maximum number of pods at a certain time is the desired number of pods + 1
  - `maxSurge: 50%` # 50% more than the desired number of pods
- `maxUnavailable` is the maximum number of pods that can be unavailable during the update. It can be a number or a percentage. The default value is 25%.
  - `maxUnavailable: 0` # No pods will be deleted
  - `maxUnavailable: 1` # One pod will be deleted
  - `maxUnavailable: 50%` # 50% of the desired number of pods will be deleted

- Test
  - `k apply -f deploy.kiada.0.6.recreate.yaml`
  - Update the replicas to 8
  - Set `maxSurge: 0` and `maxUnavailable: 2` in `deploy.kiada.0.7.rollingUpdate.yaml`
  - `k get po --show-labels`
  - `k get po -l pod-template-hash=5c96bc9585 -w` # Watch the pods
  - `k apply -f deploy.kiada.0.7.rollingUpdate.yaml`

#### 4.2.5 Pausing the rollout process
I personally don't think this is a good idea. It would be easier to just test by change the image version for the container you want to update. However, I am not sure this is a good idea test a pod owned by the deployment.
- `k rollout pause deploy kiada` # Pause the rollout

#### 4.2.6 Updating to a faulty version
Instead of using `k rollout pause deploy kiada` to pause the rollout and check if the new version is good, we can make k8s to do the work automatically.

We can use the `minReadySeconds` to define how long a pod should be operated well before it is considered as ready. If the pod is not ready for the defined time, the rollout will be paused.

> Note: `minReadySeconds` will be reset when the pod is restarted.

- `k apply -f deploy.kiada.0.8.minReadySeconds60.yaml`
- `k describe deploy kiada` # Check the `minReadySeconds` value
- Check the conditions for the deploy.

### Rolling back a Deployment
With deployment, we can rollback to a previous version easily with the following command.

- `k rollout undo deploy kiada` # Rollback to the previous version
- `k applyf -f deploy.kiada.0.7.rollingUpdate.yaml` # Update the image to 0.7
- Display rollout history for a deployment
  `k rollout history deploy kiada`
- Rollback to a specific version
  `k rollout undo deploy kiada --to-revision=1` 

