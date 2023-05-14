# Workload-Lab2: StatefulSets and DaemonSets

## 1. StatefulSets Demo

### 1.1. Why StatefulSets?
- What is stateful workload?
  The software that needs to maintain its state to function is called **stateful workload**. The state have to be maintained whenever restart or relocated. Stateful workloads are also well known for the difficulty of scaling, as you cannot increase or remove replicas without thinking about their state. To make a software stateless, the underlying data storage have to support this.
- Why stateful workload?
  Share data pods on different nodes. (Read and write to the same `PersistentVolume.)

  - Example: You cannot scale the deployment `quiz` to more than one replica, as multiple MongoDB instances cannot share the same pair of `PersistentVolume` and `PersistentVolumeClaim`.
    - **To resolve this**, you can use multiple `deployment` for each replica of quiz. Each deployment will have **ONE** replica with dedicated `PersistentVolume` and `PersistentVolumeClaim`. **However, you will need another service to expose all the deployments.** The solution makes the architecture more complex and intimidating.

### 1.2. Lab Commands: Why StatefulSets?
- Create the AKS cluster:
  `az aks create -g k8sLearn -n workload --node-count 2 --node-vm-size standard_d2a_v4 --enable-addons monitoring --enable-msi-auth-for-monitoring --generate-ssh-keys`
- Connect to cluster:
  `az aks get-credentials -g k8sLearn -n workload`
- Create namespace kiada:
  `k create namespace kiada`
- Deploy setup pods:
  `k apply -n kiada -f SETUP -R`
- Make sure setup done:
  `k get po -n kiada`
- Go to kiada namespace:
  `kubens kiada`
- Check the status of the quiz deployment:
  `k get deploy`
- Scale up the quiz deployment:
  `k scale deployment quiz --replicas=3`
- Check the status of the quiz pods:
  `k get pod -l app=quiz`
- Check why the new pods failed:
  `k describe pod <pod-name>`
  `k logs <pod-name>`
  `k logs <pod-name> -c mongo`
  `k logs <pod-name> -c mongo | grep -i "exception"`
- Failure overview:
  - ![Failure overview](https://drek4537l1klr.cloudfront.net/luksa3/v-15/Figures/15_img_0001.png)

### 1.3. StatefulSets vs Deployments
- How to make replicas in StatefulSets replacable.
  - With deployments, we can replace replicas with new ones easily since they are stateless.
  - With StatefulSets, when we replace a down replica, we need to provide the replacement the same network identity (DNS) and state as the replaced replica.
    - Network
    - Storage

- Deploying Pods with a StatefulSet
  - Elements in the statefulset template
    - Pod template
    - Number of replicas
    - Label selector
    - PersistentVolumeClaim template
  - StatefulSet Specifcations
    - In a StatefulSet, each pod has its own storage. This means the pods are not replica to each other.
    - The names of pods are randomly generated but with unique ordinal numbers.
    - When a pod got deleted or replaced, the new one will have the same name as the old one. The same PVC will be mounted to the new pod.
    - Pods in a StatefulSet are created one by one like rolloing update.
    - Scale like a deployment. When scale down, we can choose to delete the PVC or keep it.

### 1.4. Headless Service
In a StatefulSet, the network identity of each pod is provided by the associated headless service. Following are the specifications of a headless service:
- ClusterIP: A headless doesn't have a cluster IP.
- DNS: It will create DNS record for each pod.
- Overview:
  - ![Headless Service](https://drek4537l1klr.cloudfront.net/luksa3/v-15/Figures/15_img_0005.png)

How do we distribute the traffic to the pods with headless service?
- [What Is DNS Load Balancing?](https://www.nginx.com/resources/glossary/dns-load-balancing/#:~:text=DNS%20load%20balancing%20is%20the,made%20accessible%20via%20the%20Internet.)

### 1.5. Lab Commands: Deploy a StatefulSet
- Check the headless service file `svc.quiz-pods.yaml`
- Check the quiz svc:
  `k get svc`
  `k get svc quiz -o yaml`
- Deploy the headless service:
  `k apply -f svc.quiz-pods.yaml`
- Check the headless service:
  `k get svc`
- Deploy the StatefulSet:
  `k apply -f sts.quiz.yaml`
- Check the deployment status:
  `k rollout status sts quiz`
- Check the pods:
  `k get pods -l app=quiz`
- Check the errors: 
  `k logs quiz-0 -c quiz-api`
  `k logs quiz-0 -c mongo | grep -i "exception"`
- Fix error by:
  ```bash
  kubectl exec -it quiz-0 -c mongo -- mongosh --quiet --eval 'rs.initiate({
  _id: "quiz",
  members: [
    {_id: 0, host: "quiz-0.quiz-pods.kiada.svc.cluster.local:27017"},
    {_id: 1, host: "quiz-1.quiz-pods.kiada.svc.cluster.local:27017"},
    {_id: 2, host: "quiz-2.quiz-pods.kiada.svc.cluster.local:27017"}]})'
  ```
- Check the pods again:
  `k get pods -l app=quiz`
- Inspecting a pod on `ownerReferences`:
  `k edit pod quiz-0`
- Check the PVC:
  `k get pvc -l app=quiz`
- Import data:
  `k apply -f pod.quiz-data-importer.yaml`
- Check the primary replica of MongoDB: 
  `k exec quiz-1 -c mongo -- mongosh kiada --quiet --eval 'rs.hello().primary'`

## 2. StatefulSets: Node Failure Handling
Pods in a StatefulSet are special because each of them has a special PersistentVolumeClaim. When we delete a pod, we can choose either to delete the PVC or keep it. Default is keep. Normally, you don't want to delete the data when you delete a pod.

### 2.1. Lab Commands: Delete a Pod
- Watch the pods:
  `k get po -l app=quiz -o wide -w`
- Delete a pod:
  `k delete po quiz-1`
What is the name of the new pod?
Which node the new pod got placed? Why?

### 2.2. Node failure handling
- ReplicaSet
  When a node failed, the replicaset controller will create a new pod on another node. As the pod is stateless, the new pod will be able to serve the traffic without any problem.
- Does StatefulSet share the same schema in node failure handling?

- Commands to simulate node failure:
  `k get node`
  `k node-shell <node-name>`
  - Check if `ifconfig` is installed:
    `ifconfig`
  - Install `ifconfig`:
    `apt-get update`
    `apt-get install net-tools`
  - Watch the pods while take the node down:
    `k get pods -l app=quiz -w`
    `k get nodes -w`
    `sudo ifconfig eth0 down`
    `ps -aux | grep kubelet`
    `chmod 666 /usr/local/bin/kubelet`
    `kill -i <pid>`
  - Can we delete the quiz-1 pod when the node is down?
    `k delete pod quiz-1`

## 3. DaemonSets Demo
- Special about DaemonSets
  - ![DaemonSets runa Pod replica on each node](https://drek4537l1klr.cloudfront.net/luksa3/v-15/Figures/16.1.png)
- Workflow of the DaemonSets Controller
  - ![The DaemonSets controller loop](https://drek4537l1klr.cloudfront.net/luksa3/v-15/Figures/16.2.png)

- Demo 
  - Add Prometheus as a helm repo
    `helm repo add prometheus-community https://prometheus-community.github.io/helm-charts`
  - Update helm repo
    `helm repo update`
  - Create a namespace for Prometheus
    `k create namespace prometheus`
  - Install Prometheus using helm
    `helm install prometheus prometheus-community/prometheus -n prometheus`
  - Check deployment
    `k get all`
    `helm history prometheus -n prometheus`
  - Check Prometheus UI
    `k port-forward <prometheus-server-pod> 9090:9090`
  - Visit Prometheus UI
    `http://localhost:9090`

  - Briefly about Prometheus
    - Architecture
      - ![Prometheus architecture](https://prometheus.io/assets/architecture.png)

  - Scale up the cluster
    - Get the name of the nodepool
      - `az aks nodepool list --cluster-name workload --resource-group k8sLearn`
    - Watch the DaemonSet
      - `k get ds -w`
    - Scale the node pool
      - `az aks nodepool scale --cluster-name workload --resource-group k8sLearn --name nodepool1 --node-count 3`